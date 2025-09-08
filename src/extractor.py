from pathlib import Path
from typing import Optional

from pdfminer.high_level import extract_text as pdf_extract_text
import mammoth


def extract_text(input_path: str, output_path: Optional[str] = None) -> str:
	p = Path(input_path)
	if not p.exists() or not p.is_file():
		raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

	text: str
	suffix = p.suffix.lower()
	if suffix == ".pdf":
		text = pdf_extract_text(input_path)
	elif suffix in {".docx"}:
		with open(input_path, "rb") as f:
			result = mammoth.extract_raw_text(f)
			text = result.value
	else:
		raise ValueError("Tipo de arquivo não suportado. Use .pdf ou .docx")

	if output_path:
		Path(output_path).parent.mkdir(parents=True, exist_ok=True)
		Path(output_path).write_text(text, encoding="utf-8")

	return text
