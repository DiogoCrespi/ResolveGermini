import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, List

from .config import INPUT_DIR_DEFAULT, OUTPUT_DIR_DEFAULT, MAX_QUEST_PER_BLOCK
from .extractor import extract_text
from .gemini_client import extract_with_gemini, merge_blocks, segment_text_into_questions
from .jff_converter import write_mealy_jff_file, write_fa_jff_file


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


def _write_per_question_outputs(stem: str, out_dir: Path, q: Dict[str, Any], jff_type: str, solved_subdir: str) -> None:
	qid = _sanitize_id(q.get("id") or "Q")
	base = f"{stem}_{qid}"
	alts = q.get("alternativas", [])
	correta = q.get("correta") or ""
	exp = q.get("explicacao") or ""
	# TXT
	txt_path = out_dir / f"{base}.txt"
	content_lines = [q.get("enunciado") or q.get("text") or ""]
	for j, alt in enumerate(alts):
		content_lines.append(f"{chr(65+j)}) {alt}")
	if correta:
		content_lines.append(f"Correta: {correta}")
	if exp:
		content_lines.append(f"Explicacao: {exp}")
	txt_path.write_text("\n".join(content_lines), encoding="utf-8")
	# JSON por questão
	json_path = out_dir / f"{base}.json"
	json_path.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")
	# JFF por questão
	solved_dir = out_dir / solved_subdir
	solved_dir.mkdir(parents=True, exist_ok=True)
	jff_path = solved_dir / f"{base}.jff"
	per_data = {"questoes": [q]}
	if jff_type == "mealy":
		write_mealy_jff_file(per_data, str(jff_path))
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


def process_file(file_path: Path, out_dir: Path, jff_type: str = "fa", refresh: bool = False, solved_subdir: str = "resolvidas") -> None:
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

	# 3) Fase 2: processar cada questão
	done_ids = set(entry.get("questions_done", []))
	processed_questions: List[Dict[str, Any]] = []
	for q in questions:
		qid = _sanitize_id(q.get("id") or "")
		if qid in done_ids:
			processed_questions.append(q)
			continue
		# Enriquecer a questão com FA (modo FA) ou resposta curta (modo QA)
		enunciado = q.get("enunciado") or q.get("text") or ""
		if ANSWER_MODE == "qa":
			resp = extract_with_gemini(enunciado)
			qr = (resp.get("questoes") or [None])[0] or {}
			if "resposta" in qr:
				q["resposta"] = qr["resposta"]
		else:
			# FA: pedir ao Gemini um FA para este enunciado
			resp = extract_with_gemini(enunciado)
			qr = (resp.get("questoes") or [None])[0] or {}
			# Incorporar possíveis campos retornados (fa, alternativas, correta, explicacao)
			for k in ["fa", "alternativas", "correta", "explicacao"]:
				if k in qr:
					q[k] = qr[k]
		# Saídas por questão
		_write_per_question_outputs(file_path.stem, out_dir, q, jff_type, solved_subdir)
		processed_questions.append(q)
		# atualizar status
		done_ids.add(qid)
		entry["questions_done"] = list(done_ids)
		status[fname] = entry
		save_status(out_dir, status)

	# 4) Consolidados
	if ANSWER_MODE == "qa":
		_write_concatenated_answers(file_path.stem, out_dir, processed_questions)
	else:
		consolidated = {"questoes": processed_questions}
		jff_out = out_dir / f"{file_path.stem}.jff"
		write_fa_jff_file(consolidated, str(jff_out))


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

	files = list(inp.glob("*.pdf")) + list(inp.glob("*.docx"))
	for f in files:
		try:
			process_file(f, out, jff_type=args.jff_type, refresh=args.refresh, solved_subdir=args.solved_dir)
		except Exception as e:
			print(f"Erro ao processar {f.name}: {e}")


if __name__ == "__main__":
	main()
