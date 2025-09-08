import re
from typing import List, Dict, Any, Tuple, Optional

# Cabeçalhos tipo "Questão 2", "2)", "2.", "Q2"
QUESTION_HEADER_REGEX = re.compile(r"(?im)^(?:quest(?:ão|ao)\s*(?P<qnum>\d+)|q\s*(?P<qnum2>\d+)|(?P<qnum3>\d+)[\)\.])\s*(?:[-–—:]\s*)?.*")
# Subitens a), b), c) ... (flexível com espaços e ponto)
LETTER_ITEM_REGEX = re.compile(r"^(?P<label>[a-z])\s*[\)\.]\s+(?P<text>.+)$")
# Alternativas de múltipla escolha A), B), C), D)
ALTERNATIVE_REGEX = re.compile(r"^(?:[A-D][\)\.]\s+)(.*)$")


def _parse_question_number(line: str) -> Optional[str]:
	m = QUESTION_HEADER_REGEX.match(line.strip())
	if not m:
		return None
	return m.group('qnum') or m.group('qnum2') or m.group('qnum3')


def _split_sections_by_question(lines: List[str]) -> List[Tuple[Optional[str], List[str]]]:
	sections: List[Tuple[Optional[str], List[str]]] = []
	current_qnum: Optional[str] = None
	current_lines: List[str] = []
	for line in lines:
		qnum = _parse_question_number(line)
		if qnum is not None:
			if current_lines:
				sections.append((current_qnum, current_lines))
			current_qnum = qnum
			current_lines = [line]
		else:
			if current_qnum is None and not current_lines:
				current_lines = [line]
			else:
				current_lines.append(line)
	if current_lines:
		sections.append((current_qnum, current_lines))
	return sections


def _split_letter_items_within_section(qnum: Optional[str], sec_lines: List[str]) -> List[Dict[str, Any]]:
	entries: List[Dict[str, Any]] = []
	current: Optional[Dict[str, Any]] = None
	for line in sec_lines:
		strip = line.strip()
		m = LETTER_ITEM_REGEX.match(strip)
		if m:
			if current:
				entries.append(current)
			label = m.group("label")
			text = m.group("text")
			qid = f"Q{qnum}{label}" if qnum else None
			current = {"id": qid if qid else "", "text": f"{label}) {text}", "alternativas": [], "_label": label}
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


def _fallback_letter_grouping(lines: List[str]) -> List[Dict[str, Any]]:
	"""Quando não há cabeçalhos numéricos, agrupa blocos iniciados por 'a)' como Q1a, Q1b, ...; próximo 'a)' vira Q2a..."""
	entries: List[Dict[str, Any]] = []
	current: Optional[Dict[str, Any]] = None
	section_num = 0
	for line in lines:
		strip = line.strip()
		m = LETTER_ITEM_REGEX.match(strip)
		if m:
			label = m.group("label")
			text = m.group("text")
			if label == 'a':
				# novo grupo
				if current:
					entries.append(current)
				section_num += 1
				current = {"id": f"Q{section_num}a", "text": f"a) {text}", "alternativas": [], "_label": 'a'}
			else:
				# subitem do mesmo grupo
				if current is None:
					# se começar por b) sem a), cria grupo implícito
					section_num += 1
					current = {"id": f"Q{section_num}{label}", "text": f"{label}) {text}", "alternativas": [], "_label": label}
				else:
					qid = f"Q{section_num}{label}"
					# fecha anterior e inicia novo
					entries.append(current)
					current = {"id": qid, "text": f"{label}) {text}", "alternativas": [], "_label": label}
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
	# remove rótulo interno auxiliar
	for e in entries:
		e.pop("_label", None)
	return entries


def split_questions(raw_text: str, max_per_block: int = 30) -> List[List[Dict[str, Any]]]:
	lines = raw_text.splitlines()
	sections = _split_sections_by_question(lines)
	entries: List[Dict[str, Any]] = []

	for qnum, sec_lines in sections:
		subitems = _split_letter_items_within_section(qnum, sec_lines)
		if subitems:
			# garante IDs quando qnum ausente (não deveria ocorrer aqui)
			for e in subitems:
				if not e.get("id") and qnum:
					e["id"] = f"Q{qnum}{e.get('_label','')}"
				e.pop("_label", None)
			entries.extend(subitems)
			continue
		gen = _split_generic(sec_lines)
		if gen:
			if qnum and gen:
				for gi, g in enumerate(gen, start=1):
					g["id"] = f"Q{qnum}" if len(gen) == 1 else f"Q{qnum}_{gi}"
			entries.extend(gen)

	if not entries:
		entries = _fallback_letter_grouping(lines)
		if not entries:
			entries = _split_generic(lines)

	blocks: List[List[Dict[str, Any]]] = []
	for i in range(0, len(entries), max_per_block):
		blocks.append(entries[i : i + max_per_block])
	return blocks
