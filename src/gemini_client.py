import json
import re
import os
from typing import List, Dict, Any

from tenacity import retry, wait_exponential, stop_after_attempt
from ratelimit import limits, sleep_and_retry
import requests
from pathlib import Path

from .config import GEMINI_API_KEY, GEMINI_MODEL, RATE_LIMIT_PER_MINUTE

if not GEMINI_API_KEY:
	raise RuntimeError("GEMINI_API_KEY não definida. Use .env ou variável de ambiente.")

ANSWER_MODE = os.getenv("ANSWER_MODE", "fa").lower().strip()
USER_PROMPT = os.getenv("USER_PROMPT", "").strip()

# Carrega exemplo de formato (se existir)
FORMAT_EXAMPLE = None
for candidate in ["Pilha.xml", "Automato_Finito.xml", "Automato_Finito.jff"]:
	p = Path(candidate)
	if p.exists() and p.is_file():
		FORMAT_EXAMPLE = p.read_text(encoding="utf-8")
		break

SYSTEM_PROMPT_BASE_FA = (
	"Você é um especialista em Teoria da Computação focado em linguagens livres de contexto. Para cada questão do texto, "
	"retorne EM JSON VÁLIDO o objeto: {\n"
	"  \"questoes\": [\n"
	"    {\n"
	"      \"id\": \"Q1\",\n"
	"      \"enunciado\": \"...\",\n"
	"      \"alternativas\": [],\n"
	"      \"correta\": null,\n"
	"      \"explicacao\": \"S -> aSb | aSbb | e\",\n"
	"      \"pda\": {\n"
	"        \"type\": \"pda\",\n"
	"        \"states\": [ { \"id\": 0, \"name\": \"q0\", \"initial\": true, \"final\": false, \"label\": \"Le 'a's\" }, { \"id\": 1, \"name\": \"q1\", \"initial\": false, \"final\": true, \"label\": \"Aceitacao\" } ],\n"
	"        \"transitions\": [ { \"from\": 0, \"to\": 0, \"read\": \"a\", \"pop\": \"Z\", \"push\": \"XZ\" }, { \"from\": 0, \"to\": 1, \"read\": \"b\", \"pop\": \"X\", \"push\": \"\" } ]\n"
	"      },\n"
	"      \"cyk_result\": null\n"
	"    }\n"
	"  ]\n"
	"}\n"
	"Regras: 1) SEM TEXTO fora do JSON. 2) Para questões de GRAMÁTICA LIVRE DE CONTEXTO: no campo 'explicacao', RETORNE APENAS as regras de produção da GLC. FORMATO: 'S -> r1 | r2, A -> ra1 | ...'. Use 'e' para epsilon. 3) Para questões de AUTÔMATO DE PILHA (PDA): NÃO use o campo 'fa', use APENAS o campo 'pda' com type='pda'. Estados devem ter 'label' descritivo. Transições devem incluir 'read', 'pop' e 'push'. Use 'Z' como símbolo inicial da pilha. 4) Para questões de ALGORITMO CYK: no campo 'cyk_result', retorne 'true' se a cadeia pertence à linguagem, 'false' caso contrário, seguido da tabela CYK. 5) Para questões de FORMA NORMAL DE GREIBACH: no campo 'explicacao', mostre a conversão passo a passo. 6) Para LEMA DO BOMBEAMENTO (provar que NÃO é livre de contexto): no campo 'explicacao', siga as 5 etapas: 1) Assuma L livre de contexto e escolha p>0; 2) Escolha w ∈ L com |w| > p; 3) Mostre que w = uvxyz com |vxy| ≤ p e |vy| ≥ 1; 4) Demonstre que uv^ixy^iz ∉ L para algum i ≥ 0; 5) Conclua que L não é livre de contexto. IMPORTANTE: Se o contexto menciona 'autômato de pilha', 'pushdown' ou 'PDA', use APENAS o campo 'pda', NÃO use 'fa'."
)

SYSTEM_PROMPT_QA = (
	"Você é um assistente para resolver questões dissertativas ou de múltipla escolha. "
	"Responda de forma MUITO SUCINTA, objetiva e ESTRITAMENTE conforme as instruções do usuário. "
	"Use SOMENTE o enunciado da pergunta e o PROMPT_DO_USUÁRIO fornecido. Não utilize outras fontes ou contexto implícito. "
	"Se o PROMPT_DO_USUÁRIO determinar um formato específico (por exemplo, apenas uma expressão regular), RETORNE APENAS esse conteúdo no campo 'resposta', sem justificativas. "
	"Retorne EM JSON VÁLIDO: {\n"
	"  \"questoes\": [ { \"id\": \"Q1\", \"enunciado\": \"...\", \"resposta\": \"...\" } ]\n"
	"}\n"
	"NÃO inclua texto fora do JSON."
)

SEGMENT_PROMPT = (
	"Você é um segmentador de provas. Dado o TEXTO COMPLETO, retorne EM JSON VÁLIDO uma lista de questões e subquestões. "
	"Formato: { \"questoes\": [ { \"id\": \"Q1\", \"enunciado\": \"...\" }, { \"id\": \"Q1a\", \"enunciado\": \"...\", \"parent\": \"Q1\" } ] } . "
	"Regras: 1) Sem texto fora do JSON. 2) IDs devem ter padrão Q{numero}{letra?}, por exemplo Q1, Q1a, Q1b, Q2, Q2a. 3) Preserve o enunciado completo de cada item/subitem (inclua exemplos se fizerem parte do enunciado). 4) Para subitens (Q1a, Q1b, ...), inclua o campo 'parent' com o ID da questão principal (ex.: 'Q1')."
)

if ANSWER_MODE == "qa":
	SYSTEM_PROMPT = SYSTEM_PROMPT_QA
else:
	SYSTEM_PROMPT = SYSTEM_PROMPT_BASE_FA + ("\n\nEXEMPLO DE FORMATO JFLAP (SIGA EXATAMENTE O FORMATO):\n" + FORMAT_EXAMPLE if FORMAT_EXAMPLE else "")

API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def _extract_json_from_text(text: str) -> Dict[str, Any]:
	try:
		return json.loads(text)
	except Exception:
		pass
	start_idx = text.find("{")
	while start_idx != -1:
		depth = 0
		for i in range(start_idx, len(text)):
			c = text[i]
			if c == '{':
				depth += 1
			elif c == '}':
				depth -= 1
				if depth == 0:
					candidate = text[start_idx:i+1]
					try:
						return json.loads(candidate)
					except Exception:
						break
		start_idx = text.find("{", start_idx + 1)
	return {"questoes": []}


@sleep_and_retry
@limits(calls=RATE_LIMIT_PER_MINUTE, period=60)
@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
def extract_with_gemini(block_text: str) -> Dict[str, Any]:
	# Monta o prompt considerando o modo QA (com PROMPT_DO_USUÁRIO) ou FA
	if ANSWER_MODE == "qa":
		prompt = (
			f"{SYSTEM_PROMPT}\n\n"
			+ (f"PROMPT_DO_USUÁRIO (SIGA À RISCA):\n{USER_PROMPT}\n\n" if USER_PROMPT else "")
			+ "INSTRUÇÕES:\n- Responda SOMENTE com o conteúdo solicitado pelo PROMPT_DO_USUÁRIO.\n- Não explique, não justifique, não adicione exemplos.\n- Se não aplicável, responda 'N/A'.\n\n"
			+ f"PERGUNTA (ENUNCIADO):\n{block_text}\n"
		)
	else:
		prompt = f"{SYSTEM_PROMPT}\n\nTEXTO:\n\n{block_text}\n"
	payload = {
		"contents": [
			{
				"parts": [
					{"text": prompt}
				]
			}
		]
	}
	headers = {
		"Content-Type": "application/json",
		"X-goog-api-key": GEMINI_API_KEY,
	}
	resp = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=120)
	resp.raise_for_status()
	data = resp.json()
	candidates = data.get("candidates", [])
	if not candidates:
		return {"questoes": []}
	parts = candidates[0].get("content", {}).get("parts", [])
	if not parts or "text" not in parts[0]:
		return {"questoes": []}
	text = parts[0]["text"]
	return _extract_json_from_text(text)


@sleep_and_retry
@limits(calls=RATE_LIMIT_PER_MINUTE, period=60)
@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
def segment_text_into_questions(full_text: str) -> Dict[str, Any]:
	prompt = f"{SEGMENT_PROMPT}\n\nTEXTO COMPLETO:\n\n{full_text}\n"
	payload = {
		"contents": [
			{
				"parts": [
					{"text": prompt}
				]
			}
		]
	}
	headers = {
		"Content-Type": "application/json",
		"X-goog-api-key": GEMINI_API_KEY,
	}
	resp = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=180)
	resp.raise_for_status()
	data = resp.json()
	candidates = data.get("candidates", [])
	if not candidates:
		return {"questoes": []}
	parts = candidates[0].get("content", {}).get("parts", [])
	if not parts or "text" not in parts[0]:
		return {"questoes": []}
	text = parts[0]["text"]
	return _extract_json_from_text(text)


SYSTEM_PROMPT_GRAMMAR_VALIDATION = (
	"Você é um especialista em Teoria da Computação focado em validação de gramáticas livres de contexto. "
	"Analise as questões fornecidas e valide/corrija as gramáticas geradas. "
	"Para cada questão, retorne EM JSON VÁLIDO: {\n"
	"  \"questoes\": [\n"
	"    {\n"
	"      \"id\": \"Q1a\",\n"
	"      \"enunciado\": \"...\",\n"
	"      \"gramatica_original\": \"S -> AB | CD\",\n"
	"      \"gramatica_corrigida\": \"S -> AB, A -> aA | a, B -> bB | e\",\n"
	"      \"explicacao_correcao\": \"A gramática original estava incorreta porque...\",\n"
	"      \"valida\": true\n"
	"    }\n"
	"  ]\n"
	"}\n"
	"Regras: 1) SEM TEXTO fora do JSON. 2) Compare a gramática gerada com a linguagem solicitada. "
	"3) Se estiver incorreta, forneça a gramática corrigida. 4) Explique brevemente o erro e a correção. "
	"5) Campo 'valida' deve ser true se a gramática original está correta, false caso contrário."
)


@sleep_and_retry
@limits(calls=RATE_LIMIT_PER_MINUTE, period=60)
@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
def validate_grammars(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
	"""Valida e corrige gramáticas de questões de linguagens livres de contexto"""
	
	# Filtrar apenas questões que têm gramáticas (explicacao)
	grammar_questions = []
	for q in questions:
		if q.get("explicacao") and q.get("explicacao").strip():
			grammar_questions.append(q)
	
	if not grammar_questions:
		return {"questoes": []}
	
	# Montar prompt com todas as questões
	questions_text = ""
	for q in grammar_questions:
		questions_text += f"ID: {q.get('id', '')}\n"
		questions_text += f"Enunciado: {q.get('enunciado', '')}\n"
		questions_text += f"Contexto: {q.get('contexto', '')}\n"
		questions_text += f"Gramática gerada: {q.get('explicacao', '')}\n\n"
	
	prompt = f"{SYSTEM_PROMPT_GRAMMAR_VALIDATION}\n\nQUESTÕES PARA VALIDAÇÃO:\n\n{questions_text}"
	
	payload = {
		"contents": [
			{
				"parts": [
					{"text": prompt}
				]
			}
		]
	}
	headers = {
		"Content-Type": "application/json",
		"X-goog-api-key": GEMINI_API_KEY,
	}
	resp = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=120)
	resp.raise_for_status()
	data = resp.json()
	candidates = data.get("candidates", [])
	if not candidates:
		return {"questoes": []}
	parts = candidates[0].get("content", {}).get("parts", [])
	if not parts or "text" not in parts[0]:
		return {"questoes": []}
	text = parts[0]["text"]
	return _extract_json_from_text(text)


def merge_blocks(blocks_results: List[Dict[str, Any]]) -> Dict[str, Any]:
	merged: Dict[str, Any] = {"questoes": []}
	for br in blocks_results:
		qs = br.get("questoes", [])
		merged["questoes"].extend(qs)
	return merged
