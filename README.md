## Automação de Extração e Conversão para JFF (Python + PyInstaller)

Aplicação que:
- Lê arquivos .pdf e .docx de uma pasta de entrada
- Extrai e divide questões em blocos (até 30 por bloco)
- Envia para modelos de IA (Gemini, ChatGPT ou DeepSeek) e coleta respostas estruturadas (JSON)
- Converte o retorno para arquivos .jff (JFLAP)
- Mantém `status.json` para retomada segura

### Modelos de IA Suportados
- **Gemini** (Google) - Recomendado
- **ChatGPT** (OpenAI) - GPT-3.5/GPT-4
- **DeepSeek** - Modelo alternativo

### Requisitos
- Python 3.10+
- Windows 10/11
- Chave de API de pelo menos um modelo de IA (ver configuração abaixo)

### Instalação
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Configuração
Crie um arquivo `.env` (ou use suas variáveis de ambiente):

#### Para usar Gemini (Recomendado):
```
AI_MODEL=gemini
GEMINI_API_KEY=sua_chave_gemini
GEMINI_MODEL=gemini-2.0-flash
INPUT_DIR=lerpdf
OUTPUT_DIR=out
MAX_QUEST_PER_BLOCK=30
```

#### Para usar ChatGPT:
```
AI_MODEL=gpt
OPENAI_API_KEY=sua_chave_openai
GPT_MODEL=gpt-4o-mini
INPUT_DIR=lerpdf
OUTPUT_DIR=out
MAX_QUEST_PER_BLOCK=30
```

#### Para usar DeepSeek:
```
AI_MODEL=deepseek
DEEPSEEK_API_KEY=sua_chave_deepseek
DEEPSEEK_MODEL=deepseek-chat
INPUT_DIR=lerpdf
OUTPUT_DIR=out
MAX_QUEST_PER_BLOCK=30
```

### Execução

#### Execução Simples (Script PowerShell):
```bash
.\run_all.ps1
```

#### Execução Manual:
```bash
python -m src.main --in %INPUT_DIR% --out %OUTPUT_DIR%
```
Argumentos:
- `--in` pasta de entrada (padrão: `INPUT_DIR`)
- `--out` pasta de saída (padrão: `OUTPUT_DIR`)
- `--type` tipo de automato JFLAP (mealy|moore|dfa) (padrão: fa)

### Seleção de Modelo de IA
O sistema detecta automaticamente qual modelo usar baseado na variável `AI_MODEL`:
- `gemini` - Usa Google Gemini
- `gpt` - Usa OpenAI ChatGPT  
- `deepseek` - Usa DeepSeek

Se não especificado, usa Gemini por padrão.

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

### Otimizações Implementadas
- **Processamento Paralelo**: Acelera significativamente o Gemini 2.5 usando múltiplas threads
- **Cópia Imediata**: Questões são copiadas para `Desktop/resolvidas` (apenas TXT e JFF)
- **Geração Inteligente de JFF**: Gera arquivos JFF apenas para questões que realmente precisam
- **Feedback em Tempo Real**: Mostra progresso e permite trabalho simultâneo

### Configurações de Performance
```bash
# Processamento paralelo (padrão: 4 threads)
set MAX_PARALLEL_WORKERS=4

# Cópia para área de trabalho (padrão: habilitado)
set ENABLE_DESKTOP_COPY=true

# Rate limiting (padrão: 30 req/min)
set RATE_LIMIT_PER_MINUTE=30
```

### Observações
- O parser de questões é heurístico; ajuste `splitter` conforme seu padrão de prova.
- Valide os `.jff` no JFLAP (incluímos verificação básica na geração).
- Para mais detalhes sobre configuração de modelos de IA, consulte `CONFIGURACAO_IA.md`.
- **Trabalhe enquanto processa**: Questões são copiadas imediatamente para a área de trabalho (TXT + JFF).

### Troubleshooting
- **Erro de cota**: Sua conta atingiu o limite. Tente outro modelo de IA.
- **Chave inválida**: Verifique se a chave de API está correta no `.env`.
- **Modelo não suportado**: Use `gemini`, `gpt` ou `deepseek` na variável `AI_MODEL`.
