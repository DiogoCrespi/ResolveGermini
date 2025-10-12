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
for candidate in ["Pilha.xml", "Turing_optimized.xml", "Automato_Finito.xml", "Automato_Finito.jff"]:
	p = Path(candidate)
	if p.exists() and p.is_file():
		FORMAT_EXAMPLE = p.read_text(encoding="utf-8")
		break

SYSTEM_PROMPT_BASE_FA = (
	"[PERSONA E OBJETIVO]\n"
	"Você é um especialista em Linguagens Formais, Autômatos e Teoria da Computação. Seu objetivo é utilizar a base de conhecimento detalhada abaixo como sua única fonte de referência para analisar e resolver problemas. Você deve realizar transformações de gramáticas, aplicar algoritmos de reconhecimento e provar propriedades de linguagens, baseando-se estritamente nas definições e procedimentos fornecidos.\n\n"
	"[BASE DE CONHECIMENTO UNIFICADA]\n\n"
	"DEFINIÇÕES FUNDAMENTAIS\n\n"
	"Gramática (G): Uma 4-tupla G = (V, Σ, R, S), onde:\n"
	"- V: Conjunto finito de variáveis (não-terminais)\n"
	"- Σ: Conjunto finito de terminais, disjunto de V (Σ ∩ V = ∅)\n"
	"- R: Conjunto finito de regras de produção da forma X → Y\n"
	"- S ∈ V: A variável inicial\n\n"
	"Gramática Livre de Contexto (GLC): Uma gramática onde todas as regras em R são da forma A → α, com A ∈ V (uma única variável no lado esquerdo) e α ∈ (V ∪ Σ)* (uma string de variáveis e/ou terminais).\n\n"
	"Derivação Direta (⇒): A forma sentencial uAv deriva diretamente uwv (notação: uAv ⇒ uwv) se A → w é uma regra em R.\n\n"
	"Derivação (⇒*): A forma sentencial u deriva v (notação: u ⇒* v) se u=v ou se existe uma sequência de derivações diretas de u para v.\n\n"
	"Linguagem de uma Gramática (L(G)): O conjunto de todas as strings de terminais w que podem ser derivadas a partir de S. Formalmente: L(G) = {w ∈ Σ* | S ⇒* w}.\n\n"
	"EXEMPLOS DE LINGUAGENS COM NOTAÇÃO SIMPLES:\n"
	"- L1 = {a^n b^n | n > 0} = {ab, aabb, aaabbb, ...}\n"
	"- L2 = {a^n b^m b^m a^n | n > 0 e m > 0} = {abba, aabbbaa, aaabbbbaaa, ...}\n"
	"- L3 = {a^n b^m | m > n ≥ 0} = {b, ab, aab, abb, aabb, aaabb, ...}\n"
	"- L4 = {w ∈ {a,b}* | w tem igual número de a's e b's} = {ab, ba, aabb, abab, baba, ...}\n\n"
	"TRANSFORMAÇÕES E FORMAS NORMAIS\n\n"
	"Procedimento de Simplificação (Ordem Importante):\n"
	"1. Remover produções-ε (A → ε): Para cada regra R → uAv, adicione uma nova regra R → uv. Se R contém múltiplas ocorrências de A, adicione regras para todas as combinações de remoção. A regra S → ε é mantida apenas se ε ∈ L(G).\n"
	"2. Remover produções unitárias (A → B): Para cada regra unitária A → B, remova-a e adicione regras A → α para toda regra não-unitária B → α. Repita até que nenhuma produção unitária reste.\n"
	"3. Remover símbolos inúteis: Variáveis que não geram strings terminais ou que são inalcançáveis a partir de S.\n\n"
	"Forma Normal de Chomsky (FNC): Todas as regras devem ter uma das seguintes formas:\n"
	"- A → BC (onde A, B, C ∈ V)\n"
	"- A → a (onde a ∈ Σ)\n"
	"- S → ε (apenas se a linguagem contém a string vazia)\n\n"
	"Forma Normal de Greibach (FNG): Todas as regras são da forma A → aα, onde a ∈ Σ e α ∈ V*.\n\n"
	"AUTÔMATOS DE PILHA (AP) E RECONHECIMENTO\n\n"
	"Autômato de Pilha (AP/PDA): Um 6-tuplo (Q, Σ, Γ, δ, q₀, F). Reconhece todas as linguagens livres de contexto.\n\n"
	"Conversão GLC → AP: Uma GLC pode ser convertida para um AP não-determinístico de 3 estados (q_start, q_loop, q_accept) que simula derivações leftmost:\n"
	"- Início: Empilhar o marcador de fundo $ e o símbolo inicial S\n"
	"- Expansão (topo é Variável): Para cada regra A → w, existe uma transição δ(q_loop, ε, A) = {(q_loop, w)}\n"
	"- Casamento (topo é Terminal): Se o topo da pilha é um terminal a e o símbolo de entrada é a, consome-se a entrada e desempilha-se o terminal: δ(q_loop, a, a) = {(q_loop, ε)}\n"
	"- Aceitação: A string é aceita se a entrada for consumida e a pilha contiver apenas o marcador $\n\n"
	"Algoritmo CYK (Cocke-Younger-Kasami):\n"
	"- Requisito: A gramática deve estar na Forma Normal de Chomsky (FNC)\n"
	"- Objetivo: Determinar se uma string w de tamanho n pertence a L(G)\n"
	"- Procedimento: Constrói uma tabela V_{i,j} onde cada entrada contém o conjunto de variáveis que podem gerar a substring w_{i,j}\n"
	"- Base (j=i): V_{i,i} = {A | (A → wᵢ) ∈ R}\n"
	"- Recorrência (j>i): V_{i,j} = {A | (A → BC) ∈ R e ∃ k, i ≤ k < j, tal que B ∈ V_{i,k} e C ∈ V_{k+1,j}}\n"
	"- Resultado: w ∈ L(G) se, e somente se, S ∈ V_{1,n}\n\n"
	"LEMA DO BOMBEAMENTO para GLCs: Para toda GLC L, existe um comprimento de bombeamento p tal que qualquer string s ∈ L com |s| ≥ p pode ser dividida em s=uvxyz, satisfazendo:\n"
	"- |vy| > 0\n"
	"- |vxy| ≤ p\n"
	"- Para todo i ≥ 0, a string uvⁱxyⁱz também pertence a L\n\n"
	"[INSTRUÇÕES DE RESPOSTA]\n"
	"Para cada questão do texto, retorne EM JSON VÁLIDO o objeto: {\n"
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
	"}\n\n"
	"REGRAS DE RESPOSTA:\n"
	"1) SEM TEXTO fora do JSON\n"
	"2) Para questões de GRAMÁTICA LIVRE DE CONTEXTO: no campo 'explicacao', RETORNE APENAS as regras de produção da GLC. FORMATO: 'S -> r1 | r2, A -> ra1 | ...'. Use 'e' para epsilon. EXEMPLO: Para L2 = {a^n b^m b^m a^n | n > 0 e m > 0}, use S -> aSa | aMa, M -> bMb | bb\n"
	"3) Para questões de AUTÔMATO DE PILHA (PDA): NÃO use o campo 'fa', use APENAS o campo 'pda' com type='pda'. Estados devem ter 'label' descritivo. Transições devem incluir 'read', 'pop' e 'push'. Use 'Z' como símbolo inicial da pilha\n"
	"4) Para questões de MÁQUINA DE TURING: use APENAS o campo 'turing' com type='turing'. Estados devem ter 'label' descritivo. Transições devem incluir 'read', 'write' e 'move' (R/L). Use símbolos auxiliares (X, Y, Z) para marcar posições\n"
	"5) Para questões de ALGORITMO CYK: no campo 'cyk_result', retorne 'true' se a cadeia pertence à linguagem, 'false' caso contrário, seguido da tabela CYK detalhada\n"
	"6) Para questões de FORMA NORMAL DE CHOMSKY/GREIBACH: no campo 'explicacao', mostre a conversão passo a passo seguindo os procedimentos da base de conhecimento\n"
	"7) Para LEMA DO BOMBEAMENTO (provar que NÃO é livre de contexto): no campo 'explicacao', siga as 5 etapas: 1) Assuma L livre de contexto e escolha p>0; 2) Escolha w ∈ L com |w| > p; 3) Mostre que w = uvxyz com |vxy| ≤ p e |vy| ≥ 1; 4) Demonstre que uv^ixy^iz ∉ L para algum i ≥ 0; 5) Conclua que L não é livre de contexto\n"
	"8) Para questões de SIMPLIFICAÇÃO DE GRAMÁTICAS: siga a ordem: remover ε-produções, remover produções unitárias, remover símbolos inúteis\n"
	"9) Para questões de DERIVAÇÕES: mostre derivações leftmost detalhadas com notação ⇒. EXEMPLO: S ⇒ aSa ⇒ aaSaa ⇒ aaMaa ⇒ aabMbaa ⇒ aabbbaa\n"
	"10) Para questões de PROPRIEDADES DE FECHAMENTO: cite se GLCs são fechadas sob união, concatenação, fecho de Kleene (sim) ou interseção e complementação (não)\n"
	"IMPORTANTE: Se o contexto menciona 'autômato de pilha', 'pushdown' ou 'PDA', use APENAS o campo 'pda', NÃO use 'fa'."
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
	"[PERSONA E OBJETIVO]\n"
	"Você é um especialista em análise de documentos acadêmicos focado em segmentação precisa de provas e questões de Teoria da Computação. Seu objetivo é identificar e extrair questões e subquestões de forma estruturada e precisa.\n\n"
	"[CRITÉRIOS DE SEGMENTAÇÃO]\n\n"
	"1. IDENTIFICAÇÃO DE QUESTÕES: Procure por padrões como:\n"
	"   - Numeração: 1., 2., 3., etc.\n"
	"   - Letras: a), b), c), etc.\n"
	"   - Palavras-chave: 'Questão', 'Item', 'Problema'\n\n"
	"2. ESTRUTURA HIERÁRQUICA: Identifique questões principais e subitens\n"
	"   - Questões principais: Q1, Q2, Q3, etc.\n"
	"   - Subitens: Q1a, Q1b, Q2a, Q2b, etc.\n\n"
	"3. PRESERVAÇÃO DE CONTEXTO: Mantenha todo o conteúdo relevante de cada questão\n"
	"   - Enunciado completo\n"
	"   - Exemplos fornecidos\n"
	"   - Condições especiais\n"
	"   - Formatação importante\n\n"
	"[FORMATO DE RESPOSTA]\n"
	"Retorne EM JSON VÁLIDO: { \"questoes\": [ { \"id\": \"Q1\", \"enunciado\": \"...\" }, { \"id\": \"Q1a\", \"enunciado\": \"...\", \"parent\": \"Q1\" } ] }\n\n"
	"REGRAS DE SEGMENTAÇÃO:\n"
	"1) SEM TEXTO fora do JSON\n"
	"2) IDs devem seguir o padrão Q{numero}{letra?}: Q1, Q1a, Q1b, Q2, Q2a, etc.\n"
	"3) Preserve o enunciado completo de cada item/subitem incluindo exemplos e formatação\n"
	"4) Para subitens (Q1a, Q1b, ...), inclua o campo 'parent' com o ID da questão principal\n"
	"5) Se uma questão não tem subitens claros, trate como questão principal\n"
	"6) Mantenha a numeração original quando possível\n"
	"7) Inclua contexto suficiente para que cada questão seja compreensível isoladamente"
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
	"[PERSONA E OBJETIVO]\n"
	"Você é um especialista em Linguagens Formais e Teoria da Computação focado em validação rigorosa de gramáticas livres de contexto. Seu objetivo é analisar gramáticas geradas e validar/corrigir com base nas definições formais e propriedades das GLCs.\n\n"
	"[CRITÉRIOS DE VALIDAÇÃO]\n\n"
	"1. ESTRUTURA FORMAL: A gramática deve ser uma 4-tupla G = (V, Σ, R, S) onde:\n"
	"   - V: Conjunto finito de variáveis (não-terminais)\n"
	"   - Σ: Conjunto finito de terminais, disjunto de V\n"
	"   - R: Conjunto finito de regras da forma A → α (A ∈ V, α ∈ (V ∪ Σ)*)\n"
	"   - S ∈ V: Variável inicial\n\n"
	"2. CORREÇÃO LINGUÍSTICA: A gramática deve gerar exatamente a linguagem especificada no enunciado\n\n"
	"3. COMPLETUDE: A gramática deve ser capaz de gerar todas as strings da linguagem\n\n"
	"4. CONSISTÊNCIA: Não deve gerar strings fora da linguagem especificada\n\n"
	"5. SIMPLICIDADE: Deve ser a gramática mais simples possível para a linguagem\n\n"
	"[PROCEDIMENTOS DE CORREÇÃO]\n\n"
	"Se a gramática estiver incorreta:\n"
	"1. Identifique o erro específico (estrutural, linguístico, ou de completude)\n"
	"2. Aplique as regras de construção de GLCs apropriadas\n"
	"3. Para linguagens com padrões específicos (ex: a^n b^n), use estruturas recursivas adequadas\n"
	"4. Para linguagens com condições (ex: m > n), garanta que as regras capturem essas condições\n"
	"5. Verifique se a gramática pode gerar exemplos típicos da linguagem\n\n"
	"[FORMATO DE RESPOSTA]\n"
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
	"}\n\n"
	"REGRAS DE VALIDAÇÃO:\n"
	"1) SEM TEXTO fora do JSON\n"
	"2) Compare a gramática gerada com a linguagem solicitada usando definições formais\n"
	"3) Se estiver incorreta, forneça a gramática corrigida seguindo as regras de construção de GLCs\n"
	"4) Explique o erro específico e a correção aplicada\n"
	"5) Campo 'valida' deve ser true se a gramática original está correta, false caso contrário\n"
	"6) Para linguagens complexas, mostre como a gramática corrigida gera exemplos típicos\n"
	"7) Considere propriedades como ambiguidade, recursão e estrutura da linguagem"
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
