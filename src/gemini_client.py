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

# Carrega exemplo de formato (se existir)
FORMAT_EXAMPLE = None
for candidate in ["Automato_Finito.xml", "Automato_Finito.jff"]:
	p = Path(candidate)
	if p.exists() and p.is_file():
		FORMAT_EXAMPLE = p.read_text(encoding="utf-8")
		break

SYSTEM_PROMPT_BASE_FA = (
	"Você é um extrator e sintetizador de autômatos finitos. Para cada questão do texto, "
	"retorne EM JSON VÁLIDO o objeto: {\n"
	"  \"questoes\": [\n"
	"    {\n"
	"      \"id\": \"Q1\",\n"
	"      \"enunciado\": \"...\",\n"
	"      \"alternativas\": [],\n"
	"      \"correta\": null,\n"
	"      \"explicacao\": \"...\",\n"
	"      \"fa\": {\n"
	"        \"alphabet\": [\"a\", \"b\"],\n"
	"        \"states\": [ { \"id\": 0, \"name\": \"q0\", \"initial\": true, \"final\": false }, { \"id\": 1, \"name\": \"q1\", \"initial\": false, \"final\": true } ],\n"
	"        \"transitions\": [ { \"from\": 0, \"to\": 1, \"read\": \"a\" }, { \"from\": 1, \"to\": 0, \"read\": \"a\" }, { \"from\": 0, \"to\": 0, \"read\": \"b\" }, { \"from\": 1, \"to\": 1, \"read\": \"b\" } ]\n"
	"      }\n"
	"    }\n"
	"  ]\n"
	"}\n"
	"Regras: 1) SEM TEXTO fora do JSON. 2) Se não houver FA aplicável, use fa com arrays vazios. 3) read vazio representa epsilon. 4) IDs dos estados devem ser inteiros e únicos. 5) Marque exatamente um estado initial=true."
)

SYSTEM_PROMPT_QA = (
	"Você é um assistente para resolver questões dissertativas ou de múltipla escolha. "
	"Responda de forma MUITO SUCINTA, no menor texto possível, mantendo precisão. "
	"Retorne EM JSON VÁLIDO: {\n"
	"  \"questoes\": [ { \"id\": \"Q1\", \"enunciado\": \"...\", \"resposta\": \"... (máx 1-2 frases)\" } ]\n"
	"}\n"
	"NÃO inclua texto fora do JSON."
)

SEGMENT_PROMPT = (
	"Você é um segmentador de provas. Dado o TEXTO COMPLETO, retorne EM JSON VÁLIDO uma lista de questões e subquestões. "
	"Formato: { \"questoes\": [ { \"id\": \"Q1\", \"enunciado\": \"...\" }, { \"id\": \"Q1a\", \"enunciado\": \"...\" } ] } . "
	"Regras: 1) Sem texto fora do JSON. 2) IDs devem ter padrão Q{numero}{letra?}, por exemplo Q1, Q1a, Q1b, Q2, Q2a. 3) Preserve o enunciado completo de cada item/subitem (inclua exemplos se fizerem parte do enunciado)."
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


def merge_blocks(blocks_results: List[Dict[str, Any]]) -> Dict[str, Any]:
	merged: Dict[str, Any] = {"questoes": []}
	for br in blocks_results:
		qs = br.get("questoes", [])
		merged["questoes"].extend(qs)
	return merged
