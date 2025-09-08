import re
from typing import List, Dict, Any

# Cabeçalhos de questão (genéricos)
QUESTION_HEADER_REGEX = re.compile(r"(?im)^(quest(ão|ao)\s*\d+|quest(ão|ao)|q\.?\s*\d+|\d+\))\s*[:\-\.]?\s*")
# Itens de lista tipo a), b), c) no início da linha
LETTER_ITEM_REGEX = re.compile(r"^(?P<label>[a-z])\)\s+(?P<text>.+)$")
# Alternativas de múltipla escolha (A), B), C), D))
ALTERNATIVE_REGEX = re.compile(r"^(?:[A-D][\)\.]\s+)(.*)$")


def _split_letter_items(lines: List[str]) -> List[Dict[str, Any]]:
	entries: List[Dict[str, Any]] = []
	current = None
	for line in lines:
		strip = line.strip()
		m = LETTER_ITEM_REGEX.match(strip)
		if m:
			# Novo item
			if current:
				entries.append(current)
			label = m.group("label")
			text = m.group("text")
			current = {"id": f"Q{len(entries)+1}", "text": f"{label}) {text}", "alternativas": []}
		else:
			if current is None:
				continue
			alt = ALTERNATIVE_REGEX.match(strip)
			if alt:
				current["alternativas"].append(alt.group(1))
			else:
				current["text"] += "\n" + line
	if current:
		entries.append(current)
	return entries


def _split_generic(lines: List[str]) -> List[Dict[str, Any]]:
	entries: List[Dict[str, Any]] = []
	current = None
	for line in lines:
		if QUESTION_HEADER_REGEX.match(line.strip()):
			if current:
				entries.append(current)
			current = {"id": f"Q{len(entries)+1}", "text": line.strip(), "alternativas": []}
		else:
			if current is None:
				continue
			alt = ALTERNATIVE_REGEX.match(line.strip())
			if alt:
				current["alternativas"].append(alt.group(1))
			else:
				current["text"] += "\n" + line
	if current:
		entries.append(current)
	return entries


def split_questions(raw_text: str, max_per_block: int = 30) -> List[List[Dict[str, Any]]]:
	lines = raw_text.splitlines()
	# 1) Tentar detectar questionário por itens de letra (a), b), c) ...)
	letter_entries = _split_letter_items(lines)
	entries: List[Dict[str, Any]]
	if len(letter_entries) >= 2:
		entries = letter_entries
	else:
		# 2) Fallback para detecção genérica
		entries = _split_generic(lines)

	# Agrupar em blocos
	blocks: List[List[Dict[str, Any]]] = []
	for i in range(0, len(entries), max_per_block):
		blocks.append(entries[i : i + max_per_block])
	return blocks
