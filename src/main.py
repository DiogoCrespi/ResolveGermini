import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, List

from .config import INPUT_DIR_DEFAULT, OUTPUT_DIR_DEFAULT, MAX_QUEST_PER_BLOCK
from .extractor import extract_text
from .splitter import split_questions
from .gemini_client import extract_with_gemini, merge_blocks
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


def _write_per_question_outputs(stem: str, out_dir: Path, merged: Dict[str, Any], jff_type: str, solved_subdir: str) -> None:
	questions = merged.get("questoes", [])
	solved_dir = out_dir / solved_subdir
	solved_dir.mkdir(parents=True, exist_ok=True)
	for idx, q in enumerate(questions, start=1):
		base = f"{stem}_Q{idx}"
		# TXT por questão (continua em out/)
		txt_path = out_dir / f"{base}.txt"
		alts = q.get("alternativas", [])
		correta = q.get("correta") or ""
		exp = q.get("explicacao") or ""
		content_lines = [q.get("enunciado") or q.get("text") or ""]
		for j, alt in enumerate(alts):
			content_lines.append(f"{chr(65+j)}) {alt}")
		if correta:
			content_lines.append(f"Correta: {correta}")
		if exp:
			content_lines.append(f"Explicacao: {exp}")
		txt_path.write_text("\n".join(content_lines), encoding="utf-8")
		# JSON por questão (continua em out/)
		json_path = out_dir / f"{base}.json"
		json_path.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")
		# JFF por questão (vai para subpasta resolvidas/)
		per_data = {"questoes": [q]}
		jff_path = solved_dir / f"{base}.jff"
		if jff_type == "mealy":
			write_mealy_jff_file(per_data, str(jff_path))
		elif jff_type == "fa":
			write_fa_jff_file(per_data, str(jff_path))


def _write_concatenated_answers(stem: str, out_dir: Path, merged: Dict[str, Any]) -> None:
	# Gera um TXT com respostas curtas concatenadas (modo QA)
	questions = merged.get("questoes", [])
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
	out_path = out_dir / f"{stem}_respostas.txt"
	out_path.write_text("\n".join(lines), encoding="utf-8")


def process_file(file_path: Path, out_dir: Path, jff_type: str = "fa", refresh: bool = False, solved_subdir: str = "resolvidas") -> None:
	status = load_status(out_dir)
	fname = file_path.name
	entry = status.get(fname, {})

	txt_path = out_dir / f"{file_path.stem}.txt"
	if refresh:
		entry = {}

	if not entry.get("text_extracted"):
		text = extract_text(str(file_path), str(txt_path))
		entry["text_extracted"] = True
		entry["blocks_done"] = 0
		status[fname] = entry
		save_status(out_dir, status)
	else:
		text = txt_path.read_text(encoding="utf-8")

	# Dividir em blocos e manter referência plana às entradas detectadas
	blocks = split_questions(text, MAX_QUEST_PER_BLOCK)
	flat_entries: List[Dict[str, Any]] = [q for block in blocks for q in block]
	responses: List[Dict[str, Any]] = []

	start_idx = 0 if refresh else int(entry.get("blocks_done", 0))
	for i in range(start_idx, len(blocks)):
		block = blocks[i]
		block_text = "\n\n".join([q["text"] + ("\n" + "\n".join([f"{chr(65+j)}) {alt}" for j, alt in enumerate(q.get("alternativas", []))])) for q in block])
		res = extract_with_gemini(block_text)
		responses.append(res)
		entry["blocks_done"] = i + 1
		status[fname] = entry
		save_status(out_dir, status)

	json_out = out_dir / f"{file_path.stem}.json"
	if not refresh and json_out.exists():
		prev = json.loads(json_out.read_text(encoding="utf-8"))
		responses.insert(0, prev)

	merged = merge_blocks(responses) if responses else (json.loads(json_out.read_text(encoding="utf-8")) if json_out.exists() else {"questoes": []})

	# Se não veio nada do Gemini, criar questões placeholder a partir das entradas detectadas
	if not merged.get("questoes") and flat_entries:
		merged["questoes"] = []
		for idx, e in enumerate(flat_entries, start=1):
			merged["questoes"].append({
				"id": f"Q{idx}",
				"enunciado": e.get("text", ""),
				"alternativas": e.get("alternativas", []),
				"correta": None,
				"explicacao": "",
				"fa": {}  # sem FA => gerador cria placeholder válido
			})

	json_out.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

	# Geração consolidada conforme modo
	if ANSWER_MODE == "qa":
		_write_concatenated_answers(file_path.stem, out_dir, merged)
	else:
		jff_out = out_dir / f"{file_path.stem}.jff"
		if jff_type == "mealy":
			write_mealy_jff_file(merged, str(jff_out))
		elif jff_type == "fa":
			write_fa_jff_file(merged, str(jff_out))
		else:
			raise NotImplementedError("Tipos moore/dfa ainda não implementados")

	# Saídas por questão
	_write_per_question_outputs(file_path.stem, out_dir, merged, jff_type, solved_subdir)

	entry["done"] = True
	status[fname] = entry
	save_status(out_dir, status)


def main() -> None:
	parser = argparse.ArgumentParser(description="Extrair questões e gerar JFF")
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
