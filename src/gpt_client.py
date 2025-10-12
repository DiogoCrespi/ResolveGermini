import json
import re
import os
from typing import List, Dict, Any

from tenacity import retry, wait_exponential, stop_after_attempt
from ratelimit import limits, sleep_and_retry
import openai
from pathlib import Path

from .config import OPENAI_API_KEY, GPT_MODEL, RATE_LIMIT_PER_MINUTE

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY não definida. Use .env ou variável de ambiente.")

# Configurar cliente OpenAI
openai.api_key = OPENAI_API_KEY

ANSWER_MODE = os.getenv("ANSWER_MODE", "fa").lower().strip()
USER_PROMPT = os.getenv("USER_PROMPT", "").strip()

# Carrega exemplo de formato (se existir)
FORMAT_EXAMPLE = None
for candidate in ["Pilha.xml", "Turing_optimized.xml", "Automato_Finito.xml", "Automato_Finito.jff"]:
    p = Path(candidate)
    if p.exists() and p.is_file():
        FORMAT_EXAMPLE = p.read_text(encoding="utf-8")
        break

SYSTEM_PROMPT_BASE_FA = (
    "[PERSONA E OBJETIVO]\n"
    "Você é um especialista em Linguagens Formais, Autômatos e Teoria da Computação. Seu objetivo é utilizar a base de conhecimento detalhada abaixo como sua única fonte de referência para analisar e resolver problemas. Você deve realizar transformações de gramáticas, aplicar algoritmos de reconhecimento e provar propriedades de linguagens, baseando-se estritamente nas definições e procedimentos fornecidos.\n\n"
    "[BASE DE CONHECIMENTO UNIFICADA]\n\n"
    "DEFINIÇÕES FUNDAMENTAIS\n\n"
    "Gramática (G): Uma 4-tupla G = (V, Σ, R, S), onde:\n"
    "- V: Conjunto finito de variáveis (não-terminais)\n"
    "- Σ: Conjunto finito de terminais, disjunto de V (Σ ∩ V = ∅)\n"
    "- R: Conjunto finito de regras de produção da forma X → Y\n"
    "- S ∈ V: A variável inicial\n\n"
    "Gramática Livre de Contexto (GLC): Uma gramática onde todas as regras em R são da forma A → α, com A ∈ V (uma única variável no lado esquerdo) e α ∈ (V ∪ Σ)* (uma string de variáveis e/ou terminais).\n\n"
    "Derivação Direta (⇒): A forma sentencial uAv deriva diretamente uwv (notação: uAv ⇒ uwv) se A → w é uma regra em R.\n\n"
    "Derivação (⇒*): A forma sentencial u deriva v (notação: u ⇒* v) se u=v ou se existe uma sequência de derivações diretas de u para v.\n\n"
	"Linguagem de uma Gramática (L(G)): O conjunto de todas as strings de terminais w que podem ser derivadas a partir de S. Formalmente: L(G) = {w ∈ Σ* | S ⇒* w}.\n\n"
	"EXEMPLOS DE LINGUAGENS COM NOTAÇÃO SIMPLES:\n"
	"- L1 = {a^n b^n | n > 0} = {ab, aabb, aaabbb, ...}\n"
	"- L2 = {a^n b^m b^m a^n | n > 0 e m > 0} = {abba, aabbbaa, aaabbbbaaa, ...}\n"
	"- L3 = {a^n b^m | m > n ≥ 0} = {b, ab, aab, abb, aabb, aaabb, ...}\n"
	"- L4 = {w ∈ {a,b}* | w tem igual número de a's e b's} = {ab, ba, aabb, abab, baba, ...}\n\n"
    "TRANSFORMAÇÕES E FORMAS NORMAIS\n\n"
    "Procedimento de Simplificação (Ordem Importante):\n"
    "1. Remover produções-ε (A → ε): Para cada regra R → uAv, adicione uma nova regra R → uv. Se R contém múltiplas ocorrências de A, adicione regras para todas as combinações de remoção. A regra S → ε é mantida apenas se ε ∈ L(G).\n"
    "2. Remover produções unitárias (A → B): Para cada regra unitária A → B, remova-a e adicione regras A → α para toda regra não-unitária B → α. Repita até que nenhuma produção unitária reste.\n"
    "3. Remover símbolos inúteis: Variáveis que não geram strings terminais ou que são inalcançáveis a partir de S.\n\n"
    "Forma Normal de Chomsky (FNC): Todas as regras devem ter uma das seguintes formas:\n"
    "- A → BC (onde A, B, C ∈ V)\n"
    "- A → a (onde a ∈ Σ)\n"
    "- S → ε (apenas se a linguagem contém a string vazia)\n\n"
    "Forma Normal de Greibach (FNG): Todas as regras são da forma A → aα, onde a ∈ Σ e α ∈ V*.\n\n"
    "AUTÔMATOS DE PILHA (AP) E RECONHECIMENTO\n\n"
    "Autômato de Pilha (AP/PDA): Um 6-tuplo (Q, Σ, Γ, δ, q₀, F). Reconhece todas as linguagens livres de contexto.\n\n"
    "Conversão GLC → AP: Uma GLC pode ser convertida para um AP não-determinístico de 3 estados (q_start, q_loop, q_accept) que simula derivações leftmost:\n"
    "- Início: Empilhar o marcador de fundo $ e o símbolo inicial S\n"
    "- Expansão (topo é Variável): Para cada regra A → w, existe uma transição δ(q_loop, ε, A) = {(q_loop, w)}\n"
    "- Casamento (topo é Terminal): Se o topo da pilha é um terminal a e o símbolo de entrada é a, consome-se a entrada e desempilha-se o terminal: δ(q_loop, a, a) = {(q_loop, ε)}\n"
    "- Aceitação: A string é aceita se a entrada for consumida e a pilha contiver apenas o marcador $\n\n"
    "Algoritmo CYK (Cocke-Younger-Kasami):\n"
    "- Requisito: A gramática deve estar na Forma Normal de Chomsky (FNC)\n"
    "- Objetivo: Determinar se uma string w de tamanho n pertence a L(G)\n"
    "- Procedimento: Constrói uma tabela V_{i,j} onde cada entrada contém o conjunto de variáveis que podem gerar a substring w_{i,j}\n"
    "- Base (j=i): V_{i,i} = {A | (A → wᵢ) ∈ R}\n"
    "- Recorrência (j>i): V_{i,j} = {A | (A → BC) ∈ R e ∃ k, i ≤ k < j, tal que B ∈ V_{i,k} e C ∈ V_{k+1,j}}\n"
    "- Resultado: w ∈ L(G) se, e somente se, S ∈ V_{1,n}\n\n"
    "LEMA DO BOMBEAMENTO para GLCs: Para toda GLC L, existe um comprimento de bombeamento p tal que qualquer string s ∈ L com |s| ≥ p pode ser dividida em s=uvxyz, satisfazendo:\n"
    "- |vy| > 0\n"
    "- |vxy| ≤ p\n"
    "- Para todo i ≥ 0, a string uvⁱxyⁱz também pertence a L\n\n"
    "[INSTRUÇÕES DE RESPOSTA]\n"
    "Para cada questão do texto, retorne EM JSON VÁLIDO o objeto: {\n"
    "  \"questoes\": [\n"
    "    {\n"
    "      \"id\": \"Q1\",\n"
    "      \"enunciado\": \"...\",\n"
    "      \"alternativas\": [],\n"
    "      \"correta\": null,\n"
    "      \"explicacao\": \"S -> aSb | aSbb | e\",\n"
    "      \"pda\": {\n"
    "        \"type\": \"pda\",\n"
    "        \"states\": [ { \"id\": 0, \"name\": \"q0\", \"initial\": true, \"final\": false, \"label\": \"Le 'a's\" }, { \"id\": 1, \"name\": \"q1\", \"initial\": false, \"final\": true, \"label\": \"Aceitacao\" } ],\n"
    "        \"transitions\": [ { \"from\": 0, \"to\": 0, \"read\": \"a\", \"pop\": \"Z\", \"push\": \"XZ\" }, { \"from\": 0, \"to\": 1, \"read\": \"b\", \"pop\": \"X\", \"push\": \"\" } ]\n"
    "      },\n"
    "      \"cyk_result\": null\n"
    "    }\n"
    "  ]\n"
    "}\n\n"
    "REGRAS DE RESPOSTA (SEJA CONCISO E DIRETO):\n"
    "1) SEM TEXTO fora do JSON\n"
    "2) Para questões de GRAMÁTICA LIVRE DE CONTEXTO: no campo 'explicacao', RETORNE APENAS as regras de produção da GLC. FORMATO: 'S -> r1 | r2, A -> ra1 | ...'. Use 'e' para epsilon. EXEMPLO: Para L2 = {a^n b^m b^m a^n | n > 0 e m > 0}, use S -> aSa | aMa, M -> bMb | bb\n"
    "3) Para questões de AUTÔMATO DE PILHA (PDA): NÃO use o campo 'fa', use APENAS o campo 'pda' com type='pda'. Estados devem ter 'label' descritivo. Transições devem incluir 'read', 'pop' e 'push'. Use 'Z' como símbolo inicial da pilha\n"
    "4) Para questões de ALGORITMO CYK: no campo 'cyk_result', retorne 'true' se a cadeia pertence à linguagem, 'false' caso contrário, seguido da tabela CYK detalhada\n"
    "5) Para questões de FORMA NORMAL DE CHOMSKY/GREIBACH: no campo 'explicacao', mostre a conversão passo a passo seguindo os procedimentos da base de conhecimento\n"
    "6) Para LEMA DO BOMBEAMENTO (provar que NÃO é livre de contexto): no campo 'explicacao', siga as 5 etapas: 1) Assuma L livre de contexto e escolha p>0; 2) Escolha w ∈ L com |w| > p; 3) Mostre que w = uvxyz com |vxy| ≤ p e |vy| ≥ 1; 4) Demonstre que uv^ixy^iz ∉ L para algum i ≥ 0; 5) Conclua que L não é livre de contexto\n"
    "7) Para questões de SIMPLIFICAÇÃO DE GRAMÁTICAS: siga a ordem: remover ε-produções, remover produções unitárias, remover símbolos inúteis\n"
    "8) Para questões de DERIVAÇÕES: mostre derivações leftmost detalhadas com notação ⇒. EXEMPLO: Para L2 = {a^n b^m b^m a^n}, com S -> aSa | aMa, M -> bMb | bb: S ⇒ aSa ⇒ aaSaa ⇒ aaMaa ⇒ aabMbaa ⇒ aabbbaa\n"
    "9) Para questões de PROPRIEDADES DE FECHAMENTO: cite se GLCs são fechadas sob união, concatenação, fecho de Kleene (sim) ou interseção e complementação (não)\n"
    "IMPORTANTE: Se o contexto menciona 'autômato de pilha', 'pushdown' ou 'PDA', use APENAS o campo 'pda', NÃO use 'fa'.\n\n"
    "DIRETRIZES DE CONCISÃO E FORMATAÇÃO:\n"
    "- Seja DIRETO e OBJETIVO\n"
    "- Evite explicações longas ou redundantes\n"
    "- Foque nos RESULTADOS e PROCESSOS essenciais\n"
    "- Para bombeamento: mostre apenas os 5 passos essenciais\n"
    "- Para CYK: mostre apenas a tabela final e resultado\n"
    "- Para conversões: mostre apenas os passos principais\n"
    "- Para derivações: mostre apenas a sequência de passos\n"
    "- NÃO repita informações já dadas no enunciado\n\n"
    "FORMATAÇÃO ESTRUTURADA:\n"
    "- Use quebras de linha (\\n) para separar seções\n"
    "- Use numeração para passos (1., 2., 3.)\n"
    "- Use títulos claros (ex: '1. Eliminar ε-produções:')\n"
    "- Use listas com marcadores (-) para itens\n"
    "- Separe claramente cada etapa do processo\n"
    "- Exemplo de formatação para conversões:\n"
    "  '1. Eliminar ε-produções:\\nVariáveis anuláveis: {B, A, S}\\nGramática resultante: S → AB | A | B\\n\\n2. Eliminar produções unitárias:\\nFechos: U(S)={S,A,B}\\nGramática resultante: S → AB | aBa | aa | a'\n"
    "- Exemplo de formatação para bombeamento:\n"
    "  '1. Assuma L livre de contexto com comprimento p\\n2. Escolha w = a^p b^p c^p\\n3. w = uvxyz com |vxy| ≤ p, |vy| ≥ 1\\n4. Para i=0: uxz ∉ L (contradição)\\n5. L não é livre de contexto'\n"
    "- Exemplo de formatação para CYK:\n"
    "  'Tabela CYK para w=aab:\\nV[1,1]={A}, V[2,2]={A}, V[3,3]={B}\\nV[1,2]={S}, V[2,3]={}\\nV[1,3]={}\\nResultado: w ∉ L(G)'\n"
    "- Exemplo de formatação para derivações:\n"
    "  'Derivação leftmost para aabbbaa:\\nS ⇒ aSa ⇒ aaSaa ⇒ aaMaa ⇒ aabMbaa ⇒ aabbbaa'"
)

SYSTEM_PROMPT_QA = (
    "Você é um assistente para resolver questões dissertativas ou de múltipla escolha. "
    "Responda de forma MUITO SUCINTA, objetiva e ESTRITAMENTE conforme as instruções do usuário. "
    "Use SOMENTE o enunciado da pergunta e o PROMPT_DO_USUÁRIO fornecido. Não utilize outras fontes ou contexto implícito. "
    "Se o PROMPT_DO_USUÁRIO determinar um formato específico (por exemplo, apenas uma expressão regular), RETORNE APENAS esse conteúdo no campo 'resposta', sem justificativas. "
    "Retorne EM JSON VÁLIDO: {\n"
    "  \"questoes\": [ { \"id\": \"Q1\", \"enunciado\": \"...\", \"resposta\": \"...\" } ]\n"
    "}\n"
    "NÃO inclua texto fora do JSON."
)

SEGMENT_PROMPT = (
    "Você é um segmentador de provas. Dado o TEXTO COMPLETO, retorne EM JSON VÁLIDO uma lista de questões e subquestões. "
    "Formato: { \"questoes\": [ { \"id\": \"Q1\", \"enunciado\": \"...\" }, { \"id\": \"Q1a\", \"enunciado\": \"...\", \"parent\": \"Q1\" } ] } . "
    "Regras: 1) Sem texto fora do JSON. 2) IDs devem ter padrão Q{numero}{letra?}, por exemplo Q1, Q1a, Q1b, Q2, Q2a. 3) Preserve o enunciado completo de cada item/subitem (inclua exemplos se fizerem parte do enunciado). 4) Para subitens (Q1a, Q1b, ...), inclua o campo 'parent' com o ID da questão principal (ex.: 'Q1')."
)

if ANSWER_MODE == "qa":
    SYSTEM_PROMPT = SYSTEM_PROMPT_QA
else:
    SYSTEM_PROMPT = SYSTEM_PROMPT_BASE_FA + ("\n\nEXEMPLO DE FORMATO JFLAP (SIGA EXATAMENTE O FORMATO):\n" + FORMAT_EXAMPLE if FORMAT_EXAMPLE else "")


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
def extract_with_gpt(block_text: str) -> Dict[str, Any]:
    # Monta o prompt considerando o modo QA (com PROMPT_DO_USUÁRIO) ou FA
    if ANSWER_MODE == "qa":
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            + (f"PROMPT_DO_USUÁRIO (SIGA À RISCA):\n{USER_PROMPT}\n\n" if USER_PROMPT else "")
            + "INSTRUÇÕES:\n- Responda SOMENTE com o conteúdo solicitado pelo PROMPT_DO_USUÁRIO.\n- Não explique, não justifique, não adicione exemplos.\n- Se não aplicável, responda 'N/A'.\n\n"
            + f"PERGUNTA (ENUNCIADO):\n{block_text}\n"
        )
    else:
        prompt = f"{SYSTEM_PROMPT}\n\nTEXTO:\n\n{block_text}\n"
    
    try:
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.1,
            timeout=120
        )
        
        text = response.choices[0].message.content
        return _extract_json_from_text(text)
        
    except Exception as e:
        print(f"Erro na chamada GPT: {e}")
        return {"questoes": []}


@sleep_and_retry
@limits(calls=RATE_LIMIT_PER_MINUTE, period=60)
@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
def segment_text_into_questions_gpt(full_text: str) -> Dict[str, Any]:
    prompt = f"{SEGMENT_PROMPT}\n\nTEXTO COMPLETO:\n\n{full_text}\n"
    
    try:
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.1,
            timeout=180
        )
        
        text = response.choices[0].message.content
        return _extract_json_from_text(text)
        
    except Exception as e:
        print(f"Erro na segmentação GPT: {e}")
        return {"questoes": []}


SYSTEM_PROMPT_GRAMMAR_VALIDATION = (
    "Você é um especialista em Teoria da Computação focado em validação de gramáticas livres de contexto. "
    "Analise as questões fornecidas e valide/corrija as gramáticas geradas. "
    "Para cada questão, retorne EM JSON VÁLIDO: {\n"
    "  \"questoes\": [\n"
    "    {\n"
    "      \"id\": \"Q1a\",\n"
    "      \"enunciado\": \"...\",\n"
    "      \"gramatica_original\": \"S -> AB | CD\",\n"
    "      \"gramatica_corrigida\": \"S -> AB, A -> aA | a, B -> bB | e\",\n"
    "      \"explicacao_correcao\": \"A gramática original estava incorreta porque...\",\n"
    "      \"valida\": true\n"
    "    }\n"
    "  ]\n"
    "}\n"
    "Regras: 1) SEM TEXTO fora do JSON. 2) Compare a gramática gerada com a linguagem solicitada. "
    "3) Se estiver incorreta, forneça a gramática corrigida. 4) Explique brevemente o erro e a correção. "
    "5) Campo 'valida' deve ser true se a gramática original está correta, false caso contrário.\n\n"
    "DIRETRIZES DE CONCISÃO:\n"
    "- Seja DIRETO e OBJETIVO\n"
    "- Evite explicações longas ou redundantes\n"
    "- Foque nos PROBLEMAS essenciais\n"
    "- Explique apenas o necessário para entender a correção\n"
    "- NÃO repita informações já dadas no enunciado"
)


@sleep_and_retry
@limits(calls=RATE_LIMIT_PER_MINUTE, period=60)
@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
def validate_grammars_gpt(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Valida e corrige gramáticas de questões de linguagens livres de contexto"""
    
    # Filtrar apenas questões que têm gramáticas (explicacao)
    grammar_questions = []
    for q in questions:
        if q.get("explicacao") and q.get("explicacao").strip():
            grammar_questions.append(q)
    
    if not grammar_questions:
        return {"questoes": []}
    
    # Montar prompt com todas as questões
    questions_text = ""
    for q in grammar_questions:
        questions_text += f"ID: {q.get('id', '')}\n"
        questions_text += f"Enunciado: {q.get('enunciado', '')}\n"
        questions_text += f"Contexto: {q.get('contexto', '')}\n"
        questions_text += f"Gramática gerada: {q.get('explicacao', '')}\n\n"
    
    prompt = f"{SYSTEM_PROMPT_GRAMMAR_VALIDATION}\n\nQUESTÕES PARA VALIDAÇÃO:\n\n{questions_text}"
    
    try:
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.1,
            timeout=120
        )
        
        text = response.choices[0].message.content
        return _extract_json_from_text(text)
        
    except Exception as e:
        print(f"Erro na validação GPT: {e}")
        return {"questoes": []}


def merge_blocks(blocks_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {"questoes": []}
    for br in blocks_results:
        qs = br.get("questoes", [])
        merged["questoes"].extend(qs)
    return merged
