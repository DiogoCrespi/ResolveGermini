import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

from .config import INPUT_DIR_DEFAULT, OUTPUT_DIR_DEFAULT, MAX_QUEST_PER_BLOCK, AI_MODEL, MAX_PARALLEL_WORKERS, ENABLE_DESKTOP_COPY
from .extractor import extract_text
from .ai_client import extract_with_ai, merge_blocks, segment_text_into_questions, validate_grammars, generate_turing_tests
from .jff_converter import write_mealy_jff_file, write_fa_jff_file, write_pda_jff_file, write_turing_jff_file
from .validator_parallel import run_validator_background


STATUS_FILE = "status.json"
ANSWER_MODE = os.getenv("ANSWER_MODE", "fa").lower().strip()


def load_status(out_dir: Path) -> Dict[str, Any]:
	path = out_dir / STATUS_FILE
	if not path.exists():
		return {}
	return json.loads(path.read_text(encoding="utf-8"))


def save_status(out_dir: Path, status: Dict[str, Any]) -> None:
	(out_dir).mkdir(parents=True, exist_ok=True)
	(out_dir / STATUS_FILE).write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


def _sanitize_id(raw_id: str) -> str:
	s = (raw_id or "").strip()
	s = s.replace(" ", "_")
	return s


def _copy_to_desktop_immediately(stem: str, out_dir: Path, q: Dict[str, Any], solved_subdir: str) -> None:
	"""
	Copia imediatamente os arquivos de uma questão resolvida para a área de trabalho.
	Permite que o usuário trabalhe enquanto o sistema processa outras questões.
	"""
	try:
		desktop = Path.home() / "Desktop" / "resolvidas"
		desktop.mkdir(parents=True, exist_ok=True)
		
		qid = _sanitize_id(q.get("id") or "Q")
		base = f"{stem}_{qid}"
		
		# Determinar se é questão de Turing para decidir cópia de TXT
		is_turing = bool(q.get("turing") and isinstance(q.get("turing"), dict) and q.get("turing", {}).get("type") == "turing")
		# Copiar arquivo TXT (pular para Turing)
		if not is_turing:
			txt_src = out_dir / f"{base}.txt"
			if txt_src.exists():
				txt_dst = desktop / f"{base}.txt"
				shutil.copy2(txt_src, txt_dst)
		
		# Copiar arquivo JFF (se existir e não estiver em modo QA)
		if ANSWER_MODE != "qa":
			jff_src = out_dir / solved_subdir / f"{base}.jff"
			if jff_src.exists():
				jff_dst = desktop / f"{base}.jff"
				shutil.copy2(jff_src, jff_dst)
		
		print(f"📋 {qid} ({'JFF' if is_turing else 'TXT + JFF'}) copiado para área de trabalho: {desktop}")
		
	except Exception as e:
		print(f"⚠️  Erro ao copiar {qid} para área de trabalho: {e}")


def _question_needs_jff(q: Dict[str, Any]) -> bool:
	"""
	Determina se uma questão realmente precisa de um arquivo JFF.
	Retorna True apenas para questões que solicitam autômatos, PDAs ou estruturas visuais.
	"""
	enunciado = (q.get("enunciado") or "").lower()
	contexto = (q.get("contexto") or "").lower()
	
	# Palavras-chave que indicam necessidade de JFF
	jff_keywords = [
		"construa", "construir", "desenhe", "desenhar", "crie", "criar",
		"autômato", "automato", "pushdown", "pda", "pilha",
		"máquina", "maquina", "turing", "turing machine", "mt",
		"estados", "transições", "transicoes", "diagrama", "grafo", 
		"estrutura", "visual"
	]
	
	# Verificar se o enunciado ou contexto contém palavras-chave de JFF
	texto_completo = f"{enunciado} {contexto}"
	has_jff_keywords = any(keyword in texto_completo for keyword in jff_keywords)
	
	# Verificar se a questão tem campos de autômato preenchidos
	has_automaton_data = (
		(q.get("pda") and isinstance(q.get("pda"), dict) and q.get("pda").get("type") == "pda") or
		(q.get("fa") and isinstance(q.get("fa"), dict) and q.get("fa").get("type") in ["fa", "dfa", "nfa"]) or
		(q.get("mealy") and isinstance(q.get("mealy"), dict) and q.get("mealy").get("type") == "mealy") or
		(q.get("moore") and isinstance(q.get("moore"), dict) and q.get("moore").get("type") == "moore") or
		(q.get("turing") and isinstance(q.get("turing"), dict) and q.get("turing").get("type") == "turing")
	)
	
	# Verificar se é uma questão que NÃO precisa de JFF (apenas gramática, teoria, etc.)
	no_jff_keywords = [
		"defina gramática", "defina glc", "gramática livre de contexto",
		"regras de produção", "derivação", "derivacao",
		"lema do bombeamento", "bombeamento", "prove que",
		"algoritmo cyk", "cyk", "forma normal", "simplifique",
		"explique", "demonstre", "mostre que", "caracterize"
	]
	
	has_no_jff_keywords = any(keyword in texto_completo for keyword in no_jff_keywords)
	
	# A questão precisa de JFF se:
	# 1. Tem palavras-chave de JFF E tem dados de autômato, OU
	# 2. Tem palavras-chave de JFF E NÃO tem palavras-chave de "não JFF"
	return (has_jff_keywords and has_automaton_data) or (has_jff_keywords and not has_no_jff_keywords)


def _write_per_question_outputs(stem: str, out_dir: Path, q: Dict[str, Any], jff_type: str, solved_subdir: str) -> None:
	qid = _sanitize_id(q.get("id") or "Q")
	base = f"{stem}_{qid}"
	alts = q.get("alternativas", [])
	correta = q.get("correta") or ""
	exp = q.get("explicacao") or ""
	# TXT
	# Em modo QA, salvar TXT por questão dentro de out/solved_subdir
	if ANSWER_MODE == "qa":
		solved_dir = out_dir / solved_subdir
		solved_dir.mkdir(parents=True, exist_ok=True)
		txt_path = solved_dir / f"{base}.txt"
	else:
		txt_path = out_dir / f"{base}.txt"
	content_lines = [q.get("enunciado") or q.get("text") or ""]
	for j, alt in enumerate(alts):
		content_lines.append(f"{chr(65+j)}) {alt}")
	if correta:
		content_lines.append(f"Correta: {correta}")
	if exp:
		content_lines.append(f"Explicacao: {exp}")
	# incluir resposta quando existir (modo QA)
	resp_txt = (q.get("resposta") or "").strip()
	if resp_txt:
		content_lines.append(f"Resposta: {resp_txt}")
	# incluir cyk_result quando existir (questoes de CYK)
	cyk_result = (q.get("cyk_result") or "").strip()
	if cyk_result:
		content_lines.append(f"CYK: {cyk_result}")
	txt_path.write_text("\n".join(content_lines), encoding="utf-8")
	# JSON por questão
	json_path = out_dir / f"{base}.json"
	json_path.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")
	# JFF por questão (apenas quando NÃO estiver em modo QA e a questão realmente precisar de JFF)
	if ANSWER_MODE != "qa":
		# Verificar se a questão realmente precisa de um arquivo JFF
		needs_jff = _question_needs_jff(q)
		
		if needs_jff:
			solved_dir = out_dir / solved_subdir
			solved_dir.mkdir(parents=True, exist_ok=True)
			jff_path = solved_dir / f"{base}.jff"
			per_data = {"questoes": [q]}
			
			# Detectar se é questão de PDA baseado no contexto ou campo pda
			contexto = (q.get("contexto") or "").lower()
			is_pda_question = (
				("autômato de pilha" in contexto or "pushdown" in contexto or "pda" in contexto or "pilha" in contexto) and
				("construa" in contexto or "construir" in contexto) and
				(q.get("pda") and isinstance(q.get("pda"), dict) and q.get("pda").get("type") == "pda")
			)
			is_turing_question = (
				("máquina" in contexto or "maquina" in contexto or "turing" in contexto or "turing machine" in contexto or "mt" in contexto)
				and (q.get("turing") and isinstance(q.get("turing"), dict) and q.get("turing").get("type") == "turing")
			)
			
			if jff_type == "mealy":
				write_mealy_jff_file(per_data, str(jff_path))
			elif is_pda_question:
				write_pda_jff_file(per_data, str(jff_path))
			elif is_turing_question:
				write_turing_jff_file(per_data, str(jff_path))
			elif jff_type == "fa":
				write_fa_jff_file(per_data, str(jff_path))


def _write_concatenated_answers(stem: str, out_dir: Path, questions: List[Dict[str, Any]]) -> None:
	lines: List[str] = []
	for idx, q in enumerate(questions, start=1):
		qid = q.get("id") or f"Q{idx}"
		enun = (q.get("enunciado") or q.get("text") or "").strip()
		resp = (q.get("resposta") or "").strip()
		if enun:
			lines.append(f"[{qid}] {enun}")
		if resp:
			lines.append(f"Resposta: {resp}")
		lines.append("")
	(out_dir / f"{stem}_respostas.txt").write_text("\n".join(lines), encoding="utf-8")


def _write_concatenated_explanations(stem: str, out_dir: Path, questions: List[Dict[str, Any]], solved_subdir: str) -> None:
	lines: List[str] = []
	for idx, q in enumerate(questions, start=1):
		qid = q.get("id") or f"Q{idx}"
		exp = (q.get("explicacao") or "").strip()
		if exp:
			lines.append(f"[{qid}] {exp}")
	if not lines:
		return
	solved_dir = out_dir / solved_subdir
	solved_dir.mkdir(parents=True, exist_ok=True)
	(solved_dir / f"{stem}_explicacoes.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _process_single_question(q: Dict[str, Any], stem: str, out_dir: Path, jff_type: str, solved_subdir: str, status: Dict[str, Any], fname: str) -> Dict[str, Any]:
	"""
	Processa uma única questão e retorna o resultado.
	Usado para processamento paralelo.
	"""
	qid = _sanitize_id(q.get("id") or "")
	
	try:
		# Enriquecer a questão com FA (modo FA) ou resposta curta (modo QA)
		enunciado = q.get("enunciado") or q.get("text") or ""
		contexto = q.get("contexto") or ""
		
		if ANSWER_MODE == "qa":
			full_prompt = enunciado if not contexto else (contexto.strip() + "\n\nSubitem:\n" + enunciado)
			resp = extract_with_ai(full_prompt)
			qr = (resp.get("questoes") or [None])[0] or {}
			if "resposta" in qr:
				q["resposta"] = qr["resposta"]
		else:
			# FA: pedir ao modelo de IA um FA para este enunciado, incluindo contexto da questão-mãe quando houver
			full_prompt = enunciado if not contexto else (contexto.strip() + "\n\nSubitem:\n" + enunciado)
			resp = extract_with_ai(full_prompt)
			qr = (resp.get("questoes") or [None])[0] or {}
			# Incorporar possíveis campos retornados (fa, pda, turing, alternativas, correta, explicacao, cyk_result)
			for k in ["fa", "pda", "turing", "alternativas", "correta", "explicacao", "cyk_result"]:
				if k in qr:
					q[k] = qr[k]
		
		# Saídas por questão
		_write_per_question_outputs(stem, out_dir, q, jff_type, solved_subdir)
		
		# Copiar imediatamente para área de trabalho (se habilitado)
		if ENABLE_DESKTOP_COPY:
			_copy_to_desktop_immediately(stem, out_dir, q, solved_subdir)
		
		# Informar se a questão precisa ou não de JFF
		if ANSWER_MODE != "qa":
			needs_jff = _question_needs_jff(q)
			if needs_jff:
				print(f"✅ {qid}: Gerando arquivo JFF (autômato/PDA/Turing)")
			else:
				print(f"ℹ️  {qid}: Pulando JFF (questão de gramática/teoria)")
		
		return q
		
	except Exception as e:
		print(f"❌ Erro ao processar {qid}: {e}")
		return q


def _write_grammar_corrections(stem: str, out_dir: Path, corrections: List[Dict[str, Any]], solved_subdir: str) -> None:
	"""Escreve arquivo com correções das gramáticas"""
	lines: List[str] = []
	lines.append("=== CORREÇÕES DAS GRAMÁTICAS ===\n")
	
	for corr in corrections:
		qid = corr.get("id", "")
		enunciado = corr.get("enunciado", "")
		gramatica_original = corr.get("gramatica_original", "")
		gramatica_corrigida = corr.get("gramatica_corrigida", "")
		explicacao = corr.get("explicacao_correcao", "")
		valida = corr.get("valida", False)
		
		lines.append(f"[{qid}] {enunciado}")
		lines.append(f"Gramática original: {gramatica_original}")
		
		if valida:
			lines.append("✅ GRAMÁTICA CORRETA")
		else:
			lines.append("❌ GRAMÁTICA INCORRETA")
			lines.append(f"Gramática corrigida: {gramatica_corrigida}")
			if explicacao:
				lines.append(explicacao)
		
		lines.append("")  # Linha em branco
	
	solved_dir = out_dir / solved_subdir
	solved_dir.mkdir(parents=True, exist_ok=True)
	txt_path = solved_dir / f"{stem}_correcoes_gramaticas.txt"
	txt_path.write_text("\n".join(lines), encoding="utf-8")


def _write_turing_tests(stem: str, out_dir: Path, tests: List[Dict[str, Any]], solved_subdir: str) -> None:
	"""Escreve arquivo com testes para máquinas de Turing"""
	lines: List[str] = []
	lines.append("=== TESTES PARA MÁQUINAS DE TURING ===\n")
	
	for test in tests:
		qid = test.get("id", "")
		enunciado = test.get("enunciado", "")
		testes_corretos = test.get("testes_corretos", [])
		testes_errados = test.get("testes_errados", [])
		
		lines.append(f"[{qid}] {enunciado}")
		lines.append("")
		lines.append("✅ Testes CORRETOS (devem ser aceitos):")
		for i, teste in enumerate(testes_corretos, 1):
			lines.append(f"  {i}. {teste}")
		lines.append("")
		lines.append("❌ Testes ERRADOS (devem ser rejeitados):")
		for i, teste in enumerate(testes_errados, 1):
			lines.append(f"  {i}. {teste}")
		lines.append("")
		lines.append("-" * 50)
		lines.append("")
	
	solved_dir = out_dir / solved_subdir
	solved_dir.mkdir(parents=True, exist_ok=True)
	txt_path = solved_dir / f"{stem}_testes_turing.txt"
	txt_path.write_text("\n".join(lines), encoding="utf-8")


def _process_external_files_for_validation(inp: Path, out_dir: Path, solved_subdir: str) -> None:
	"""Processa arquivos externos (.jff, *_correcoes_gramaticas.txt) para validação/correção"""
	
	# Buscar arquivos .jff
	jff_files = list(inp.glob("*.jff"))
	for jff_file in jff_files:
		try:
			# Copiar .jff para pasta resolvidas
			dst_dir = out_dir / solved_subdir
			dst_dir.mkdir(parents=True, exist_ok=True)
			dst = dst_dir / jff_file.name
			shutil.copy2(jff_file, dst)
			print(f"📋 {jff_file.name} copiado para {dst}")
		except Exception as e:
			print(f"Erro ao processar {jff_file.name}: {e}")
	
	# Buscar arquivos de correções
	corrections_files = list(inp.glob("*_correcoes_gramaticas.txt"))
	for corr_file in corrections_files:
		try:
			# Copiar correções para pasta resolvidas
			dst_dir = out_dir / solved_subdir
			dst_dir.mkdir(parents=True, exist_ok=True)
			dst = dst_dir / corr_file.name
			shutil.copy2(corr_file, dst)
			print(f"📋 {corr_file.name} copiado para {dst}")
		except Exception as e:
			print(f"Erro ao processar {corr_file.name}: {e}")
	
	# Copiar para Desktop se habilitado
	if ENABLE_DESKTOP_COPY:
		desktop = Path.home() / "Desktop" / "resolvidas"
		desktop.mkdir(parents=True, exist_ok=True)
		
		for file_list, file_type in [(jff_files, "JFF"), (corrections_files, "Correções")]:
			for file_path in file_list:
				try:
					shutil.copy2(file_path, desktop / file_path.name)
					print(f"📋 {file_path.name} ({file_type}) copiado para Desktop")
				except Exception as e:
					print(f"Erro ao copiar {file_path.name} para Desktop: {e}")


def process_file(file_path: Path, out_dir: Path, jff_type: str = "fa", refresh: bool = False, solved_subdir: str = "resolvidas") -> None:
	print(f"🤖 Processando com modelo de IA: {AI_MODEL.upper()}")
	status = load_status(out_dir)
	fname = file_path.name
	entry = status.get(fname, {})

	# 1) Extrair texto completo
	txt_path = out_dir / f"{file_path.stem}.txt"
	if refresh or not entry.get("text_extracted"):
		text = extract_text(str(file_path), str(txt_path))
		entry["text_extracted"] = True
		status[fname] = entry
		save_status(out_dir, status)
	else:
		text = txt_path.read_text(encoding="utf-8")

	# 2) Fase 1: segmentação com Gemini
	segmented_path = out_dir / f"{file_path.stem}_segmented.json"
	if refresh or not segmented_path.exists():
		seg = segment_text_into_questions(text)
		(segmented_path).write_text(json.dumps(seg, ensure_ascii=False, indent=2), encoding="utf-8")
		entry["segmented"] = True
		entry["questions_done"] = []
		status[fname] = entry
		save_status(out_dir, status)
	else:
		seg = json.loads(segmented_path.read_text(encoding="utf-8"))

	questions: List[Dict[str, Any]] = seg.get("questoes", [])

	# Propagar contexto: mapear enunciados de pais (Q1, Q2, ...) e anexar aos subitens (Q1a, Q1b...)
	parent_enunciado: Dict[str, str] = {}
	for q in questions:
		qid = (q.get("id") or "").strip()
		if qid and qid[-1].isdigit():
			parent_enunciado[qid] = (q.get("enunciado") or q.get("text") or "")
	for q in questions:
		qid = (q.get("id") or "").strip()
		if qid and not qid[-1].isdigit():
			parent_id = qid.rstrip("abcdefghijklmnopqrstuvwxyz")
			ctx = parent_enunciado.get(parent_id, "")
			if ctx:
				q["contexto"] = ctx

	# Propagar resultados de questões anteriores para questões subsequentes
	# Isso permite que Q2 acesse o resultado da Q1, Q3 acesse Q2, etc.
	previous_results: Dict[str, str] = {}
	for i, q in enumerate(questions):
		qid = (q.get("id") or "").strip()
		if qid and qid[-1].isdigit():  # Questão principal (Q1, Q2, Q3...)
			# Adicionar contexto de questões anteriores
			if previous_results:
				contexto_anterior = "\\n\\n---\\n\\n".join([f"Resultado da {qid_ant}:\\n{resultado}" for qid_ant, resultado in previous_results.items()])
				if "contexto" in q:
					q["contexto"] = q["contexto"] + "\\n\\n" + contexto_anterior
				else:
					q["contexto"] = contexto_anterior

	# 3) Fase 2: processar cada questão
	done_ids = set(entry.get("questions_done", []))
	processed_questions: List[Dict[str, Any]] = []
	
	# Separar questões já processadas das que precisam ser processadas
	questions_to_process = []
	for q in questions:
		qid = _sanitize_id(q.get("id") or "")
		if qid in done_ids:
			# Carregar dados completos da questão já processada
			json_path = out_dir / f"{file_path.stem}_{qid}.json"
			if json_path.exists():
				try:
					q_complete = json.loads(json_path.read_text(encoding="utf-8"))
					processed_questions.append(q_complete)
					# Armazenar resultado para questões subsequentes
					if qid[-1].isdigit():  # Questão principal
						explicacao = q_complete.get("explicacao", "")
						if explicacao:
							previous_results[qid] = explicacao
				except Exception as e:
					print(f"⚠️  Erro ao carregar {qid}: {e}, usando dados básicos")
					processed_questions.append(q)
			else:
				processed_questions.append(q)
		else:
			questions_to_process.append(q)
	
	if questions_to_process:
		# Verificar se há dependências entre questões (questões que referenciam "exercício anterior")
		has_dependencies = any(
			"exercício anterior" in (q.get("enunciado") or "").lower() or 
			"resultante do" in (q.get("enunciado") or "").lower() or
			"anterior" in (q.get("enunciado") or "").lower()
			for q in questions_to_process
		)

		if has_dependencies:
			# Processamento sequencial para questões com dependências
			print(f"🔄 Processando {len(questions_to_process)} questões sequencialmente (há dependências entre questões)...")
			if ENABLE_DESKTOP_COPY:
				print("📋 Cada questão será copiada para a área de trabalho (TXT + JFF) assim que resolvida")
			print()

			# Processar questões sequencialmente
			for q in questions_to_process:
				qid = _sanitize_id(q.get("id") or "")
				
				# Adicionar contexto de questões anteriores já processadas
				if previous_results:
					contexto_anterior = "\\n\\n---\\n\\n".join([f"Resultado da {qid_ant}:\\n{resultado}" for qid_ant, resultado in previous_results.items()])
					if "contexto" in q:
						q["contexto"] = q["contexto"] + "\\n\\n" + contexto_anterior
					else:
						q["contexto"] = contexto_anterior

				try:
					result = _process_single_question(q, file_path.stem, out_dir, jff_type, solved_subdir, status, fname)
					processed_questions.append(result)

					# Armazenar resultado para questões subsequentes
					if qid[-1].isdigit():  # Questão principal
						explicacao = result.get("explicacao", "")
						if explicacao:
							previous_results[qid] = explicacao

					# Atualizar status imediatamente
					done_ids.add(qid)
					entry["questions_done"] = list(done_ids)
					status[fname] = entry
					save_status(out_dir, status)

					print(f"✅ {qid} processada com sucesso!")

				except Exception as e:
					print(f"❌ Erro ao processar {qid}: {e}")
					processed_questions.append(q)  # Adicionar mesmo com erro

			print(f"🎉 Todas as {len(questions_to_process)} questões foram processadas!")
		else:
			# Processamento paralelo para questões independentes
			max_workers = min(len(questions_to_process), MAX_PARALLEL_WORKERS)
			
			print(f"🚀 Processando {len(questions_to_process)} questões em paralelo ({max_workers} threads)...")
			if ENABLE_DESKTOP_COPY:
				print("📋 Cada questão será copiada para a área de trabalho assim que resolvida")
			print("⏱️  Você pode trabalhar enquanto o sistema processa as questões!")
			print()
			
			# Processar questões em paralelo
			with ThreadPoolExecutor(max_workers=max_workers) as executor:
				# Submeter todas as questões para processamento paralelo
				future_to_question = {
					executor.submit(_process_single_question, q, file_path.stem, out_dir, jff_type, solved_subdir, status, fname): q
					for q in questions_to_process
				}
				
				# Coletar resultados conforme ficam prontos
				for future in as_completed(future_to_question):
					q = future_to_question[future]
					qid = _sanitize_id(q.get("id") or "")
					
					try:
						result = future.result()
						processed_questions.append(result)
						
						# Atualizar status imediatamente
						done_ids.add(qid)
						entry["questions_done"] = list(done_ids)
						status[fname] = entry
						save_status(out_dir, status)
						
						print(f"✅ {qid} processada com sucesso!")
						
					except Exception as e:
						print(f"❌ Erro ao processar {qid}: {e}")
						processed_questions.append(q)  # Adicionar mesmo com erro
			
			print(f"🎉 Todas as {len(questions_to_process)} questões foram processadas!")
	else:
		print("ℹ️  Todas as questões já foram processadas anteriormente.")

	# 4) Consolidados
	if ANSWER_MODE == "qa":
		_write_concatenated_answers(file_path.stem, out_dir, processed_questions)
	else:
		# Filtrar apenas questões que realmente precisam de JFF para o arquivo consolidado
		jff_questions = [q for q in processed_questions if _question_needs_jff(q)]
		
		if jff_questions:
			consolidated = {"questoes": jff_questions}
			jff_out = out_dir / f"{file_path.stem}.jff"
			write_fa_jff_file(consolidated, str(jff_out))
			print(f"📁 Arquivo JFF consolidado criado com {len(jff_questions)} questões que precisam de JFF")
		else:
			print("ℹ️  Nenhuma questão precisa de arquivo JFF consolidado")
		
		# Explicações consolidadas em um único TXT dentro de out/solved_subdir
		_write_concatenated_explanations(file_path.stem, out_dir, processed_questions, solved_subdir)
		
		# 5) Validação das gramáticas (apenas para questões com gramáticas)
		print("Validando gramáticas...")
		corrections = validate_grammars(processed_questions)
		if corrections.get("questoes"):
			_write_grammar_corrections(file_path.stem, out_dir, corrections["questoes"], solved_subdir)
			print(f"Correções salvas em: {out_dir / solved_subdir / f'{file_path.stem}_correcoes_gramaticas.txt'}")
		else:
			print("Nenhuma gramática encontrada para validação.")
		
		# 6) Geração de testes para Máquinas de Turing
		print("\nGerando testes para Máquinas de Turing...")
		turing_tests = generate_turing_tests(processed_questions)
		if turing_tests.get("questoes"):
			_write_turing_tests(file_path.stem, out_dir, turing_tests["questoes"], solved_subdir)
			print(f"✅ Testes de Turing salvos em: {out_dir / solved_subdir / f'{file_path.stem}_testes_turing.txt'}")
		else:
			print("ℹ️  Nenhuma questão de Turing encontrada para geração de testes.")


def main() -> None:
	parser = argparse.ArgumentParser(description="Extrair e processar questões")
	parser.add_argument("--in", dest="inp", default=INPUT_DIR_DEFAULT)
	parser.add_argument("--out", dest="out", default=OUTPUT_DIR_DEFAULT)
	parser.add_argument("--type", dest="jff_type", default="fa", choices=["mealy", "fa", "moore", "dfa"])
	parser.add_argument("--refresh", dest="refresh", action="store_true", help="Reexecuta do zero e ignora JSON prévio")
	parser.add_argument("--solved-dir", dest="solved_dir", default="resolvidas", help="Subpasta de out/ para salvar JFFs por questão")
	args = parser.parse_args()

	inp = Path(args.inp)
	out = Path(args.out)
	out.mkdir(parents=True, exist_ok=True)

	# Processar arquivos PDF/DOCX (processamento completo)
	files = list(inp.glob("*.pdf")) + list(inp.glob("*.docx"))
	for f in files:
		try:
			process_file(f, out, jff_type=args.jff_type, refresh=args.refresh, solved_subdir=args.solved_dir)
			
			# Executar validador em background após processar cada arquivo
			try:
				run_validator_background(f, out)
			except Exception as e:
				print(f"⚠️  Erro no validador paralelo: {e}")
				
		except Exception as e:
			print(f"Erro ao processar {f.name}: {e}")
	
	# Processar arquivos externos (.jff, *_correcoes_gramaticas.txt) para validação/correção
	print("\n🔍 Processando arquivos externos para validação/correção...")
	_process_external_files_for_validation(inp, out, args.solved_dir)


if __name__ == "__main__":
	main()
