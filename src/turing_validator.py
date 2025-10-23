"""
Validador e Corretor Automático de Máquinas de Turing
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Tuple, Optional
import sys
import os

# Adicionar o diretório src ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar Gemini de forma simplificada
def call_gemini(prompt: str, response_format: str = "json"):
    """
    Wrapper simplificado para chamar Gemini
    """
    try:
        import google.generativeai as genai
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada no .env")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp'))
        
        response = model.generate_content(prompt)
        
        if response_format == "json":
            import json
            import re
            # Tentar extrair JSON da resposta
            text = response.text
            # Procurar por blocos JSON
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group())
            return {}
        
        return response.text
    except Exception as e:
        print(f"Erro ao chamar Gemini: {e}")
        return None


def parse_jff(jff_content: str) -> Dict[str, Any]:
    """
    Parse arquivo JFF e extrai estrutura da máquina
    """
    try:
        root = ET.fromstring(jff_content)
        
        # Verificar se é Turing
        type_elem = root.find('type')
        if type_elem is None or type_elem.text != 'turing':
            return {'error': 'Não é uma Máquina de Turing'}
        
        automaton = root.find('automaton')
        if automaton is None:
            return {'error': 'Estrutura de autômato não encontrada'}
        
        # Extrair estados
        states = {}
        initial_state = None
        final_states = set()
        
        for state in automaton.findall('state'):
            state_id = state.get('id')
            state_name = state.get('name', f'q{state_id}')
            label_elem = state.find('label')
            label = label_elem.text if label_elem is not None and label_elem.text else ''
            
            states[state_id] = {
                'name': state_name,
                'label': label
            }
            
            if state.find('initial') is not None:
                initial_state = state_id
            if state.find('final') is not None:
                final_states.add(state_id)
        
        # Extrair transições
        transitions = []
        for trans in automaton.findall('transition'):
            from_state = trans.find('from').text
            to_state = trans.find('to').text
            read_elem = trans.find('read')
            write_elem = trans.find('write')
            move_elem = trans.find('move')
            
            read_char = read_elem.text if read_elem is not None and read_elem.text else ''
            write_char = write_elem.text if write_elem is not None and write_elem.text else ''
            move_dir = move_elem.text if move_elem is not None else 'R'
            
            transitions.append({
                'from': from_state,
                'to': to_state,
                'read': read_char,
                'write': write_char,
                'move': move_dir
            })
        
        return {
            'states': states,
            'initial_state': initial_state,
            'final_states': final_states,
            'transitions': transitions
        }
    
    except Exception as e:
        return {'error': f'Erro ao fazer parse do JFF: {e}'}


def simulate_turing(jff_content: str, input_string: str, max_steps: int = 10000) -> Dict[str, Any]:
    """
    Simula execução de uma Máquina de Turing
    """
    machine = parse_jff(jff_content)
    
    if 'error' in machine:
        return {
            'accepted': None,
            'error': machine['error'],
            'steps': 0,
            'execution_log': []
        }
    
    # Configuração inicial
    tape = list(input_string) if input_string else []
    head_pos = 0
    current_state = machine['initial_state']
    steps = 0
    execution_log = []
    
    states = machine['states']
    final_states = machine['final_states']
    transitions = machine['transitions']
    
    while steps < max_steps:
        # Verificar se atingiu estado final
        if current_state in final_states:
            return {
                'accepted': True,
                'steps': steps,
                'execution_log': execution_log,
                'final_state': states[current_state]['name'],
                'final_tape': ''.join(tape),
                'error': None
            }
        
        # Ler caractere atual
        if head_pos < 0:
            return {
                'accepted': False,
                'steps': steps,
                'execution_log': execution_log,
                'error': 'Cabeçote saiu da fita pela esquerda',
                'final_state': states[current_state]['name']
            }
        
        # Expandir fita se necessário
        while head_pos >= len(tape):
            tape.append('')
        
        current_char = tape[head_pos] if tape[head_pos] else ''
        
        # Buscar transição aplicável
        applicable_trans = None
        for trans in transitions:
            if trans['from'] == current_state:
                if trans['read'] == current_char:
                    applicable_trans = trans
                    break
                elif trans['read'] == '' and current_char == '':
                    applicable_trans = trans
                    break
        
        if applicable_trans is None:
            return {
                'accepted': False,
                'steps': steps,
                'execution_log': execution_log,
                'error': f"Sem transição para estado {states[current_state]['name']} com símbolo '{current_char}'",
                'final_state': states[current_state]['name'],
                'final_tape': ''.join(tape),
                'position': head_pos
            }
        
        # Aplicar transição
        old_state = current_state
        tape[head_pos] = applicable_trans['write']
        current_state = applicable_trans['to']
        
        # Log
        if steps < 100:
            execution_log.append({
                'step': steps + 1,
                'from_state': states[old_state]['name'],
                'to_state': states[current_state]['name'],
                'read': current_char,
                'write': applicable_trans['write'],
                'move': applicable_trans['move'],
                'position': head_pos
            })
        
        # Mover cabeçote
        if applicable_trans['move'] == 'R':
            head_pos += 1
        elif applicable_trans['move'] == 'L':
            head_pos -= 1
        
        steps += 1
    
    return {
        'accepted': False,
        'steps': steps,
        'execution_log': execution_log,
        'error': f'Timeout após {max_steps} passos',
        'final_state': states[current_state]['name']
    }


def validate_machine(jff_content: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Valida máquina contra casos de teste
    """
    results = []
    passed = 0
    failed = 0
    
    for test in test_cases:
        input_str = test['input']
        expected = test['expected']
        
        result = simulate_turing(jff_content, input_str)
        actual = result.get('accepted', False)
        
        status = 'PASS' if actual == expected else 'FAIL'
        
        if status == 'PASS':
            passed += 1
        else:
            failed += 1
        
        results.append({
            'input': input_str,
            'expected': expected,
            'actual': actual,
            'status': status,
            'steps': result.get('steps', 0),
            'error': result.get('error')
        })
    
    return {
        'total_tests': len(test_cases),
        'passed': passed,
        'failed': failed,
        'is_valid': failed == 0,
        'results': results
    }


def analyze_machine(jff_content: str, language_desc: str) -> Dict[str, Any]:
    """
    Analisa máquina e identifica problemas usando IA
    """
    machine = parse_jff(jff_content)
    
    if 'error' in machine:
        return {'issues': [], 'error': machine['error']}
    
    issues = []
    
    # Análise 1: Verificar transições faltantes
    states = machine['states']
    transitions = machine['transitions']
    
    # Construir mapa de transições por estado
    trans_by_state = {}
    for trans in transitions:
        from_state = trans['from']
        read_char = trans['read']
        
        if from_state not in trans_by_state:
            trans_by_state[from_state] = set()
        trans_by_state[from_state].add(read_char)
    
    # Análise 2: Detectar não-determinismo
    for state_id in states:
        if state_id not in trans_by_state:
            continue
        
        # Contar transições para cada símbolo
        symbol_count = {}
        for trans in transitions:
            if trans['from'] == state_id:
                key = (trans['read'], trans['to'])
                if trans['read'] not in symbol_count:
                    symbol_count[trans['read']] = []
                symbol_count[trans['read']].append(trans)
        
        # Detectar duplicatas
        for symbol, trans_list in symbol_count.items():
            if len(trans_list) > 1:
                # Verificar se são realmente diferentes
                unique_trans = set()
                for t in trans_list:
                    unique_trans.add((t['to'], t['write'], t['move']))
                
                if len(unique_trans) > 1:
                    issues.append({
                        'severity': 'WARNING',
                        'type': 'NON_DETERMINISM',
                        'state': states[state_id]['name'],
                        'symbol': symbol,
                        'message': f"Estado {states[state_id]['name']} tem múltiplas transições para '{symbol}'",
                        'suggestion': 'Remover transições duplicadas ou usar máquina não-determinística'
                    })
    
    return {
        'issues': issues,
        'machine_structure': {
            'num_states': len(states),
            'num_transitions': len(transitions),
            'initial_state': states[machine['initial_state']]['name'],
            'final_states': [states[s]['name'] for s in machine['final_states']]
        }
    }


def generate_test_cases_with_ai(language_desc: str, num_positive: int = 5, num_negative: int = 5) -> List[Dict[str, Any]]:
    """
    Gera casos de teste usando IA
    """
    prompt = f"""
Gere casos de teste para a seguinte linguagem de Máquina de Turing:

Linguagem: {language_desc}

Gere:
- {num_positive} casos VÁLIDOS (devem ser aceitos)
- {num_negative} casos INVÁLIDOS (devem ser rejeitados)

Para cada caso, forneça:
1. A entrada (string)
2. Se deve ser aceito (true/false)
3. Razão (explicação breve)

Formato de resposta JSON:
{{
  "test_cases": [
    {{"input": "exemplo", "expected": true, "reason": "explicação"}},
    ...
  ]
}}
"""
    
    try:
        response = call_gemini(prompt, response_format="json")
        
        if isinstance(response, dict) and 'test_cases' in response:
            return response['test_cases']
        
        # Fallback: parsear resposta
        import json
        try:
            data = json.loads(response)
            return data.get('test_cases', [])
        except:
            return []
    
    except Exception as e:
        print(f"Erro ao gerar casos de teste: {e}")
        return []


def auto_fix_machine_with_ai(jff_content: str, language_desc: str, failed_tests: List[Dict[str, Any]]) -> Optional[str]:
    """
    Corrige automaticamente usando IA
    """
    machine = parse_jff(jff_content)
    
    if 'error' in machine:
        return None
    
    # Preparar contexto para a IA
    failed_info = []
    for test in failed_tests:
        failed_info.append({
            'input': test['input'],
            'expected': test['expected'],
            'actual': test['actual'],
            'error': test.get('error', 'Desconhecido')
        })
    
    prompt = f"""
Analise esta Máquina de Turing e corrija os problemas identificados:

LINGUAGEM: {language_desc}

ESTRUTURA ATUAL:
- Estados: {len(machine['states'])}
- Transições: {len(machine['transitions'])}
- Estado inicial: {machine['states'][machine['initial_state']]['name']}
- Estados finais: {[machine['states'][s]['name'] for s in machine['final_states']]}

TESTES QUE FALHARAM:
{chr(10).join([f"- Input: '{t['input']}' | Esperado: {t['expected']} | Obtido: {t['actual']} | Erro: {t.get('error', 'N/A')}" for t in failed_info])}

TRANSIÇÕES ATUAIS:
{chr(10).join([f"- {machine['states'][t['from']]['name']} --({t['read']}/{t['write']},{t['move']})--> {machine['states'][t['to']]['name']}" for t in machine['transitions'][:20]])}

TAREFA:
1. Identifique quais transições estão faltando
2. Identifique transições duplicadas ou incorretas
3. Sugira as correções necessárias

Forneça a resposta em formato JSON:
{{
  "corrections": [
    {{
      "type": "ADD_TRANSITION" | "REMOVE_TRANSITION" | "MODIFY_TRANSITION",
      "from_state": "nome_estado",
      "to_state": "nome_estado",
      "read": "simbolo",
      "write": "simbolo",
      "move": "R|L|S",
      "reason": "explicação"
    }}
  ],
  "explanation": "explicação geral das correções"
}}
"""
    
    try:
        response = call_gemini(prompt, response_format="json")
        return response
    except Exception as e:
        print(f"Erro ao corrigir com IA: {e}")
        return None


def format_test_results(results: Dict[str, Any]) -> str:
    """
    Formata resultados de teste para exibição
    """
    lines = []
    lines.append("="*70)
    lines.append("RESULTADOS DOS TESTES")
    lines.append("="*70)
    lines.append(f"Total: {results['total_tests']}")
    lines.append(f"Passaram: {results['passed']}")
    lines.append(f"Falharam: {results['failed']}")
    lines.append(f"Status: {'VALIDA' if results['is_valid'] else 'INVALIDA'}")
    lines.append("")
    
    for i, result in enumerate(results['results'], 1):
        status_icon = "[+]" if result['status'] == 'PASS' else "[-]"
        lines.append(f"{status_icon} Teste {i}: '{result['input']}'")
        lines.append(f"    Esperado: {result['expected']}")
        lines.append(f"    Obtido: {result['actual']}")
        lines.append(f"    Status: {result['status']}")
        if result.get('error'):
            lines.append(f"    Erro: {result['error']}")
        lines.append("")
    
    lines.append("="*70)
    return "\n".join(lines)


if __name__ == '__main__':
    # Teste básico
    import sys
    
    if len(sys.argv) < 3:
        print("Uso: python turing_validator.py <arquivo.jff> <entrada>")
        sys.exit(1)
    
    jff_file = sys.argv[1]
    input_str = sys.argv[2]
    
    with open(jff_file, 'r', encoding='utf-8') as f:
        jff_content = f.read()
    
    result = simulate_turing(jff_content, input_str)
    
    print("Resultado:", "ACEITO" if result['accepted'] else "REJEITADO")
    print("Passos:", result['steps'])
    if result.get('error'):
        print("Erro:", result['error'])

