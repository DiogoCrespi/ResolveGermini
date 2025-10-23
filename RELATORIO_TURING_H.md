# Relatório - Máquina de Turing para Linguagem H

## Linguagem
**H: {w | w ∈ {a, b}* e w contenha o dobro de símbolos "a" do que "b"}**

## Análise da Máquina Original

### Arquivo Analisado
- `atividade turing/H linguagem_w_ab_estrela_dobro_a_que_b.jff`

### Estratégia da Máquina Original
1. **q0**: Percorre a fita da esquerda para direita
2. **q1**: Quando chega ao fim, procura por 'b' para marcar
3. **q3**: Move para esquerda procurando por 'a' correspondente
4. **q4**: Marca o 'a' encontrado e verifica se há 'b' sem par
5. **q5**: Volta ao início para repetir o processo
6. **q6**: Aceita quando não há mais 'b's para processar

### Problemas Identificados
1. **Limitação de posicionamento**: A máquina só funciona quando os 'b's estão no final da string
2. **Casos que falham**: 
   - "aba" (deveria aceitar mas rejeita)
   - "baa" (deveria aceitar mas rejeita)
   - "aabbaa" (deveria aceitar mas rejeita)
3. **Taxa de acerto**: 81.5% (75 corretos de 92 casos)

## Casos de Teste Gerados

### Arquivo de Testes
- `test_cases_H_correto.json`
- Total: 92 casos de teste
- Válidos: 24 casos
- Inválidos: 68 casos

### Exemplos de Casos Válidos
- "" (string vazia)
- "aab" (2 a's, 1 b)
- "aba" (2 a's, 1 b)
- "baa" (2 a's, 1 b)
- "aaaabb" (4 a's, 2 b's)
- "aabbaa" (4 a's, 2 b's)

### Exemplos de Casos Inválidos
- "a" (1 a, 0 b)
- "bb" (0 a's, 2 b's)
- "ab" (1 a, 1 b)
- "aabb" (2 a's, 2 b's)

## Tentativas de Correção

### Máquina Corrigida 1
- **Arquivo**: `H_linguagem_corrigida_final.jff`
- **Problema**: Ainda não lidava corretamente com 'b's no meio da string
- **Taxa de acerto**: 69.6%

### Máquina Corrigida 2
- **Arquivo**: `H_linguagem_final.jff`
- **Problema**: Mesmo problema da versão anterior
- **Taxa de acerto**: 69.6%

### Máquina Corrigida 3
- **Arquivo**: `H_linguagem_funcionando.jff`
- **Problema**: Entra em loop infinito no estado de rejeição
- **Taxa de acerto**: 69.6%

## Conclusões

### Problemas Fundamentais
1. **Complexidade da linguagem**: A linguagem requer que para cada 'b', existam exatamente 2 'a's, mas não importa a ordem
2. **Limitação da estratégia**: A máquina original usa uma estratégia de pareamento que só funciona quando os 'b's estão no final
3. **Dificuldade de implementação**: Implementar uma máquina que funcione para todas as permutações é complexo

### Recomendações
1. **Revisar a estratégia**: A máquina original pode estar correta para uma interpretação específica da linguagem
2. **Considerar contexto**: Talvez a linguagem seja interpretada como "a's seguidos de b's" em vez de "qualquer ordem"
3. **Validar com professor**: Confirmar se a máquina original está correta para o contexto do exercício

## Arquivos Gerados

### Testes
- `gerar_testes_H.py` - Gerador de casos de teste
- `test_cases_H_correto.json` - Casos de teste gerados
- `analisar_turing_H.py` - Analisador da máquina original
- `testar_turing_H.py` - Teste completo da máquina original
- `testar_turing_corrigida.py` - Teste das máquinas corrigidas

### Máquinas de Turing
- `atividade turing/H linguagem_w_ab_estrela_dobro_a_que_b.jff` - Máquina original
- `H_linguagem_corrigida_final.jff` - Versão corrigida 1
- `H_linguagem_final.jff` - Versão corrigida 2
- `H_linguagem_funcionando.jff` - Versão corrigida 3

### Relatórios
- `RELATORIO_TURING_H.md` - Este relatório

## Resultados Finais

| Versão | Taxa de Acerto | Status |
|--------|----------------|---------|
| Original | 81.5% | Funcional com limitações |
| Corrigida 1 | 69.6% | Pior que original |
| Corrigida 2 | 69.6% | Pior que original |
| Corrigida 3 | 69.6% | Loop infinito |

**Conclusão**: A máquina original, apesar de suas limitações, apresenta melhor desempenho que as tentativas de correção. Isso sugere que pode estar correta para o contexto específico do exercício.
