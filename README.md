## Automação de Extração e Conversão para JFF (Python + PyInstaller)

Aplicação que:
- Lê arquivos .pdf e .docx de uma pasta de entrada
- Extrai e divide questões em blocos (até 30 por bloco)
- Envia ao Gemini e coleta respostas estruturadas (JSON)
- Converte o retorno para arquivos .jff (JFLAP)
- Mantém `status.json` para retomada segura

### Requisitos
- Python 3.10+
- Windows 10/11
- Chave de API do Gemini em variável de ambiente `GEMINI_API_KEY` (ou `.env`)

### Instalação
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Configuração
Crie um arquivo `.env` (ou use suas variáveis de ambiente):
```
GEMINI_API_KEY=seu_token
GEMINI_MODEL=gemini-1.5-pro
INPUT_DIR=lerpdf
OUTPUT_DIR=out
MAX_QUEST_PER_BLOCK=30
```

### Execução
```bash
python -m src.main --in %INPUT_DIR% --out %OUTPUT_DIR%
```
Argumentos:
- `--in` pasta de entrada (padrão: `INPUT_DIR`)
- `--out` pasta de saída (padrão: `OUTPUT_DIR`)
- `--type` tipo de automato JFLAP (mealy|moore|dfa) (padrão: mealy)

### Empacotamento (.exe)
```bash
pyinstaller --onefile --name automato_app src\main.py
```
O executável ficará em `dist\automato_app.exe`.

### Estrutura de Saída
- `status.json`: progresso por arquivo e por bloco
- `*.txt`: texto extraído dos pdf/docx
- `*.json`: respostas do Gemini
- `*.jff`: arquivo JFLAP gerado

### Observações
- O parser de questões é heurístico; ajuste `splitter` conforme seu padrão de prova.
- Valide os `.jff` no JFLAP (incluímos verificação básica na geração).
