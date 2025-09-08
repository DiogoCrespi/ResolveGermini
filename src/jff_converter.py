from pathlib import Path
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET


JFLAP_HEADER = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n<!--Created with JFLAP 7.1-->\n'


def _serialize_jflap_xml(root: ET.Element) -> str:
	# Serializa e ajusta elementos vazios para formato <tag/> (sem espaço), e adiciona header/comentário
	raw = ET.tostring(root, encoding="unicode")
	# Normalizações para JFLAP
	raw = raw.replace("<initial />", "<initial/>")
	raw = raw.replace("<final />", "<final/>")
	raw = raw.replace("<read />", "<read/>")
	raw = raw.replace("<automaton />", "<automaton></automaton>")
	# Adiciona header/comment
	return JFLAP_HEADER + raw


class JFFMealyBuilder:
	def __init__(self) -> None:
		self.doc = ET.Element("structure")
		type_el = ET.SubElement(self.doc, "type")
		type_el.text = "mealy"
		self.automaton = ET.SubElement(self.doc, "automaton")
		self._has_state = False

	def add_state(self, state_id: int, name: str, x: float, y: float, initial: bool = False, final: bool = False) -> None:
		st = ET.SubElement(self.automaton, "state", {"id": str(state_id), "name": name})
		ET.SubElement(st, "x").text = str(x)
		ET.SubElement(st, "y").text = str(y)
		if initial:
			ET.SubElement(st, "initial")
		if final:
			ET.SubElement(st, "final")
		self._has_state = True

	def add_transition(self, from_id: int, to_id: int, read: Optional[str]) -> None:
		tr = ET.SubElement(self.automaton, "transition")
		ET.SubElement(tr, "from").text = str(from_id)
		ET.SubElement(tr, "to").text = str(to_id)
		ET.SubElement(tr, "read").text = (read or "")

	def to_string(self) -> str:
		# Evita automaton vazio
		if not self._has_state:
			self.add_state(0, "q0", 100.0, 100.0, initial=True)
		return _serialize_jflap_xml(self.doc)

	def write(self, path: str) -> None:
		Path(path).parent.mkdir(parents=True, exist_ok=True)
		Path(path).write_text(self.to_string(), encoding="utf-8")


class JFFFABuilder:
	def __init__(self) -> None:
		self.doc = ET.Element("structure")
		type_el = ET.SubElement(self.doc, "type")
		type_el.text = "fa"
		self.automaton = ET.SubElement(self.doc, "automaton")
		self._has_state = False

	def add_state(self, state_id: int, name: str, x: float, y: float, initial: bool = False, final: bool = False) -> None:
		st = ET.SubElement(self.automaton, "state", {"id": str(state_id), "name": name})
		ET.SubElement(st, "x").text = str(x)
		ET.SubElement(st, "y").text = str(y)
		if initial:
			ET.SubElement(st, "initial")
		if final:
			ET.SubElement(st, "final")
		self._has_state = True

	def add_transition(self, from_id: int, to_id: int, read: Optional[str]) -> None:
		tr = ET.SubElement(self.automaton, "transition")
		ET.SubElement(tr, "from").text = str(from_id)
		ET.SubElement(tr, "to").text = str(to_id)
		ET.SubElement(tr, "read").text = (read or "")

	def to_string(self) -> str:
		# Evita automaton vazio
		if not self._has_state:
			self.add_state(0, "q0", 100.0, 100.0, initial=True)
			self.add_transition(0, 0, "a")
		return _serialize_jflap_xml(self.doc)


def json_to_mealy_jff(data: Dict[str, Any]) -> str:
	builder = JFFMealyBuilder()
	# Placeholder mínimo
	builder.add_state(0, "q0", 100.0, 100.0, initial=True)
	return builder.to_string()


def json_to_fa_jff(data: Dict[str, Any]) -> str:
	builder = JFFFABuilder()
	fa = data.get("fa")
	if not fa:
		qs = data.get("questoes", [])
		if qs and isinstance(qs[0], dict):
			fa = qs[0].get("fa")

	if not fa:
		# Placeholder de 2 estados com transições simples
		builder.add_state(0, "q0", 100.0, 100.0, initial=True)
		builder.add_state(1, "q1", 200.0, 100.0, final=True)
		builder.add_transition(0, 1, "a")
		builder.add_transition(1, 1, "b")
		return builder.to_string()

	states: List[Dict[str, Any]] = fa.get("states", [])
	transitions: List[Dict[str, Any]] = fa.get("transitions", [])

	# Posicionamento simples em grid
	for idx, st in enumerate(states):
		state_id = int(st.get("id", idx))
		name = st.get("name", f"q{state_id}")
		initial = bool(st.get("initial", False))
		final = bool(st.get("final", False))
		x = 100.0 + (idx % 6) * 100.0
		y = 100.0 + (idx // 6) * 100.0
		builder.add_state(state_id, name, x, y, initial=initial, final=final)

	for tr in transitions:
		from_id = int(tr.get("from"))
		to_id = int(tr.get("to"))
		read = tr.get("read")
		builder.add_transition(from_id, to_id, read)

	return builder.to_string()


def write_mealy_jff_file(data: Dict[str, Any], out_path: str) -> None:
	jff = json_to_mealy_jff(data)
	Path(out_path).parent.mkdir(parents=True, exist_ok=True)
	Path(out_path).write_text(jff, encoding="utf-8")


def write_fa_jff_file(data: Dict[str, Any], out_path: str) -> None:
	jff = json_to_fa_jff(data)
	Path(out_path).parent.mkdir(parents=True, exist_ok=True)
	Path(out_path).write_text(jff, encoding="utf-8")
