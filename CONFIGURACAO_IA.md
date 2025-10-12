# Configuração de Modelos de IA

Este projeto agora suporta **Gemini**, **ChatGPT** e **DeepSeek** como modelos de IA para processamento de questões.

## Como Configurar

### 1. Escolher o Modelo

Defina a variável de ambiente `AI_MODEL` para escolher entre os modelos:

```bash
# Para usar Gemini (padrão)
set AI_MODEL=gemini

# Para usar ChatGPT
set AI_MODEL=gpt

# Para usar DeepSeek
set AI_MODEL=deepseek
```

### 2. Configurar Chaves de API

#### Para Gemini:
```bash
set GEMINI_API_KEY=sua_chave_gemini_aqui
set GEMINI_MODEL=gemini-2.0-flash
```

#### Para ChatGPT:
```bash
set OPENAI_API_KEY=sua_chave_openai_aqui
set GPT_MODEL=gpt-4o-mini
```

#### Para DeepSeek:
```bash
set DEEPSEEK_API_KEY=sua_chave_deepseek_aqui
set DEEPSEEK_MODEL=deepseek-chat
```

### 3. Modelos Disponíveis

#### Gemini:
- `gemini-2.0-flash` (padrão)
- `gemini-1.5-pro`
- `gemini-1.5-flash`

#### ChatGPT:
- `gpt-4o-mini` (padrão - mais econômico)
- `gpt-3.5-turbo`
- `gpt-4o`
- `gpt-4`

#### DeepSeek:
- `deepseek-chat` (padrão)
- `deepseek-coder`

## Exemplo de Uso

### Usando Gemini:
```bash
set AI_MODEL=gemini
set GEMINI_API_KEY=sua_chave_aqui
python -m src.main
```

### Usando ChatGPT:
```bash
set AI_MODEL=gpt
set OPENAI_API_KEY=sua_chave_openai_aqui
set GPT_MODEL=gpt-4o-mini
python -m src.main
```

### Usando DeepSeek:
```bash
set AI_MODEL=deepseek
set DEEPSEEK_API_KEY=sua_chave_deepseek_aqui
set DEEPSEEK_MODEL=deepseek-chat
python -m src.main
```

## Instalação de Dependências

Para usar ChatGPT, instale a biblioteca OpenAI:
```bash
pip install openai==0.28.1
```

Para usar Gemini, instale a biblioteca Google:
```bash
pip install google-generativeai==0.7.2
```

Para usar DeepSeek, a biblioteca requests já está incluída:
```bash
pip install requests==2.31.0
```

Ou instale todas as dependências:
```bash
pip install -r requirements.txt
```

## Configurações de Otimização

### Processamento Paralelo
```bash
# Número máximo de threads paralelas (padrão: 4)
set MAX_PARALLEL_WORKERS=4

# Para Gemini 2.5 (mais lento), use mais threads
set MAX_PARALLEL_WORKERS=6

# Para Gemini 2.0 (mais rápido), use menos threads
set MAX_PARALLEL_WORKERS=2
```

### Cópia para Área de Trabalho
```bash
# Habilitar cópia imediata de questões resolvidas (padrão: true)
set ENABLE_DESKTOP_COPY=true

# Desabilitar se não quiser cópia automática
set ENABLE_DESKTOP_COPY=false
```

### Rate Limiting
```bash
# Ajustar limite de requisições por minuto (padrão: 30)
set RATE_LIMIT_PER_MINUTE=30

# Para APIs mais lentas, reduzir o limite
set RATE_LIMIT_PER_MINUTE=20
```

## Notas Importantes

1. **Custos**: ChatGPT e DeepSeek podem ter custos associados dependendo do seu plano
2. **Rate Limits**: Todos os modelos têm limites de taxa configuráveis via `RATE_LIMIT_PER_MINUTE`
3. **Qualidade**: Diferentes modelos podem produzir resultados com qualidades diferentes
4. **Disponibilidade**: Verifique se sua chave de API tem acesso ao modelo escolhido
5. **Processamento Paralelo**: Acelera significativamente o Gemini 2.5, permitindo trabalho simultâneo
6. **Cópia Imediata**: Questões são copiadas para `Desktop/resolvidas_automato` assim que resolvidas

## Troubleshooting

### Erro "You exceeded your current quota"
- Sua conta OpenAI atingiu o limite de uso
- Verifique seu plano de billing na OpenAI
- Considere usar Gemini como alternativa

### Erro "OPENAI_API_KEY não definida"
- Certifique-se de definir a variável de ambiente corretamente
- Verifique se a chave está no formato correto (sk-...)

### Erro "402 Payment Required" (DeepSeek)
- Sua conta DeepSeek precisa de créditos ou está em modo pago
- Verifique seu saldo na plataforma DeepSeek
- Considere usar Gemini como alternativa gratuita

### Erro "Modelo não suportado"
- Verifique se o modelo especificado está disponível em sua conta
- Use um dos modelos listados acima
