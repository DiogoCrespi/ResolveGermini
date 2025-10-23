"""
Script para testar automaticamente Máquinas de Turing no JFLAP
"""
import subprocess
import sys
import tempfile
from pathlib import Path
import os


def test_turing_machine(jff_file: str, input_string: str, jflap_jar: str = "JFLAP7.1.jar") -> dict:
    """
    Testa uma entrada em uma Máquina de Turing usando JFLAP
    
    Args:
        jff_file: Caminho para o arquivo .jff
        input_string: String de entrada para testar
        jflap_jar: Caminho para o arquivo JFLAP7.1.jar
    
    Returns:
        Dict com resultado: {'accepted': bool, 'output': str, 'error': str}
    """
    jff_path = Path(jff_file)
    jflap_path = Path(jflap_jar)
    
    # Verificar se os arquivos existem
    if not jff_path.exists():
        return {
            'accepted': None,
            'output': '',
            'error': f'Arquivo JFF não encontrado: {jff_file}'
        }
    
    if not jflap_path.exists():
        return {
            'accepted': None,
            'output': '',
            'error': f'JFLAP não encontrado: {jflap_jar}'
        }
    
    # Criar arquivo temporário com a entrada
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp:
        tmp.write(input_string)
        tmp_input_file = tmp.name
    
    try:
        # Executar JFLAP em modo batch
        # JFLAP suporta teste via linha de comando com a classe TestAction
        cmd = [
            'java',
            '-cp',
            str(jflap_path),
            'edu.duke.cs.jflap.gui.environment.AutomatonEnvironment',
            str(jff_path)
        ]
        
        # Tentar executar o JFLAP de várias formas
        # Método 1: Usar classe de teste do JFLAP (se disponível)
        try:
            # Este é um método experimental - JFLAP não tem CLI oficial muito robusto
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Como o JFLAP não tem CLI robusto, vamos usar uma abordagem alternativa
            # Vamos criar um script que rode o JFLAP de forma não-interativa
            return {
                'accepted': None,
                'output': result.stdout,
                'error': 'JFLAP não suporta testes automatizados via linha de comando de forma nativa. Considere usar uma simulação manual ou integração com biblioteca externa.'
            }
        except subprocess.TimeoutExpired:
            return {
                'accepted': None,
                'output': '',
                'error': 'Timeout ao executar JFLAP'
            }
        except Exception as e:
            return {
                'accepted': None,
                'output': '',
                'error': f'Erro ao executar JFLAP: {e}'
            }
    
    finally:
        # Limpar arquivo temporário
        if os.path.exists(tmp_input_file):
            os.unlink(tmp_input_file)


def simulate_turing_machine(jff_file: str, input_string: str) -> dict:
    """
    Simulação básica de Máquina de Turing baseada no arquivo JFF
    
    Esta é uma implementação alternativa que lê o JFF e simula a execução
    sem depender do JFLAP.
    """
    import xml.etree.ElementTree as ET
    
    try:
        tree = ET.parse(jff_file)
        root = tree.getroot()
        
        # Verificar se é uma Máquina de Turing
        type_elem = root.find('type')
        if type_elem is None or type_elem.text != 'turing':
            return {
                'accepted': None,
                'output': '',
                'error': 'Arquivo não é uma Máquina de Turing'
            }
        
        automaton = root.find('automaton')
        if automaton is None:
            return {
                'accepted': None,
                'output': '',
                'error': 'Estrutura de autômato não encontrada'
            }
        
        # Extrair estados
        states = {}
        initial_state = None
        final_states = set()
        
        for state in automaton.findall('state'):
            state_id = state.get('id')
            state_name = state.get('name', f'q{state_id}')
            states[state_id] = state_name
            
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
        
        # Simular execução
        tape = list(input_string) if input_string else []
        head_pos = 0
        current_state = initial_state
        steps = 0
        max_steps = 10000  # Limite para evitar loop infinito
        
        execution_log = []
        execution_log.append(f"Estado inicial: {states.get(current_state, current_state)}")
        execution_log.append(f"Entrada: {input_string}")
        execution_log.append("")
        
        while steps < max_steps:
            # Verificar se atingiu estado final
            if current_state in final_states:
                execution_log.append(f"\n[ACEITO] - Estado final: {states.get(current_state, current_state)}")
                execution_log.append(f"Total de passos: {steps}")
                return {
                    'accepted': True,
                    'output': '\n'.join(execution_log),
                    'error': ''
                }
            
            # Ler caractere atual da fita
            if head_pos < 0:
                execution_log.append(f"\n[ERRO] - Cabecote saiu da fita pela esquerda")
                return {
                    'accepted': False,
                    'output': '\n'.join(execution_log),
                    'error': 'Cabecote saiu da fita'
                }
            
            # Expandir fita se necessário
            while head_pos >= len(tape):
                tape.append('')  # Blank symbol
            
            current_char = tape[head_pos] if tape[head_pos] else ''
            
            # Buscar transição aplicável
            applicable_trans = None
            for trans in transitions:
                if trans['from'] == current_state:
                    # Transição vazia (blank) casa com string vazia
                    if trans['read'] == current_char:
                        applicable_trans = trans
                        break
                    # Permitir transição com read vazio para blank
                    elif trans['read'] == '' and current_char == '':
                        applicable_trans = trans
                        break
            
            if applicable_trans is None:
                execution_log.append(f"\n[REJEITADO] - Nenhuma transicao aplicavel")
                execution_log.append(f"Estado: {states.get(current_state, current_state)}")
                execution_log.append(f"Caractere lido: '{current_char}' (posicao {head_pos})")
                execution_log.append(f"Fita: {''.join(tape)}")
                execution_log.append(f"Total de passos: {steps}")
                return {
                    'accepted': False,
                    'output': '\n'.join(execution_log),
                    'error': 'Sem transicao aplicavel'
                }
            
            # Aplicar transição
            old_state = current_state
            old_char = current_char
            
            tape[head_pos] = applicable_trans['write']
            current_state = applicable_trans['to']
            
            # Log da transição
            if steps < 50:  # Limitar log para não ficar muito grande
                execution_log.append(
                    f"Passo {steps + 1}: {states.get(old_state, old_state)} "
                    f"-> {states.get(current_state, current_state)} | "
                    f"Leu: '{old_char}' -> Escreveu: '{applicable_trans['write']}' | "
                    f"Move: {applicable_trans['move']}"
                )
            elif steps == 50:
                execution_log.append("... (mostrando apenas primeiros 50 passos)")
            
            # Mover cabeçote
            if applicable_trans['move'] == 'R':
                head_pos += 1
            elif applicable_trans['move'] == 'L':
                head_pos -= 1
            # 'S' mantém posição
            
            steps += 1
        
        # Se atingiu limite de passos
        execution_log.append(f"\n[TIMEOUT] - Limite de {max_steps} passos atingido")
        execution_log.append(f"Estado atual: {states.get(current_state, current_state)}")
        return {
            'accepted': False,
            'output': '\n'.join(execution_log),
            'error': 'Limite de passos atingido (possivel loop)'
        }
    
    except Exception as e:
        return {
            'accepted': None,
            'output': '',
            'error': f'Erro ao simular máquina: {e}'
        }


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Testa entrada em Máquina de Turing (arquivo JFF)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python test_turing.py 1.jff abccdd
  python test_turing.py "atividade turing/1.jff" "aabbccdd"
  python test_turing.py out/resolvidas/Q1a.jff "aaccdd" --jflap JFLAP7.1.jar
        """
    )
    
    parser.add_argument('jff_file', help='Arquivo JFF da Máquina de Turing')
    parser.add_argument('input_string', help='String de entrada para testar')
    parser.add_argument('--jflap', default='JFLAP7.1.jar', help='Caminho para JFLAP7.1.jar (padrão: JFLAP7.1.jar)')
    parser.add_argument('--mode', choices=['simulate', 'jflap'], default='simulate',
                       help='Modo de teste: simulate (simulação interna) ou jflap (usar JFLAP) (padrão: simulate)')
    
    args = parser.parse_args()
    
    print(f"{'='*70}")
    print(f"TESTE DE MAQUINA DE TURING")
    print(f"{'='*70}")
    print(f"Arquivo JFF: {args.jff_file}")
    print(f"Entrada: {args.input_string}")
    print(f"Modo: {args.mode}")
    print(f"{'='*70}\n")
    
    if args.mode == 'simulate':
        result = simulate_turing_machine(args.jff_file, args.input_string)
    else:
        result = test_turing_machine(args.jff_file, args.input_string, args.jflap)
    
    # Exibir resultado
    if result['output']:
        print(result['output'])
    
    if result['error']:
        print(f"\n[!] ERRO: {result['error']}")
    
    print(f"\n{'='*70}")
    if result['accepted'] is True:
        print("[+] RESULTADO: ACEITO")
        sys.exit(0)
    elif result['accepted'] is False:
        print("[-] RESULTADO: REJEITADO")
        sys.exit(1)
    else:
        print("[!] RESULTADO: INDETERMINADO (erro na execucao)")
        sys.exit(2)


if __name__ == '__main__':
    main()

