#!/usr/bin/env python3
"""
Simulador de Máquina de Turing para testar a linguagem {wwR | w ∈ {a,b}*}
Versão corrigida
"""

import json
import xml.etree.ElementTree as ET

class TuringMachine:
    def __init__(self, jff_file):
        self.states = {}
        self.transitions = {}
        self.initial_state = None
        self.final_states = set()
        self.load_from_jff(jff_file)
    
    def load_from_jff(self, jff_file):
        """Carrega a máquina de Turing do arquivo JFLAP"""
        tree = ET.parse(jff_file)
        root = tree.getroot()
        
        # Carregar estados
        for state in root.findall('.//state'):
            state_id = state.get('id')
            state_name = state.get('name', f'q{state_id}')
            self.states[state_id] = state_name
            
            # Verificar se é estado inicial (geralmente q0)
            if state_name == 'q0':
                self.initial_state = state_id
        
        # Carregar transições
        for transition in root.findall('.//transition'):
            from_state = transition.find('from').text
            to_state = transition.find('to').text
            read_symbol = transition.find('read').text or ''  # Símbolo vazio
            write_symbol = transition.find('write').text or ''  # Símbolo vazio
            move = transition.find('move').text
            
            if from_state not in self.transitions:
                self.transitions[from_state] = {}
            
            self.transitions[from_state][read_symbol] = {
                'to': to_state,
                'write': write_symbol,
                'move': move
            }
    
    def simulate(self, input_string, max_steps=1000, verbose=False):
        """Simula a execução da máquina de Turing"""
        tape = list(input_string)
        head_position = 0
        current_state = self.initial_state
        steps = 0
        
        # Adicionar símbolos de branco nas bordas se necessário
        if head_position < 0:
            tape = ['_'] + tape
            head_position = 0
        elif head_position >= len(tape):
            tape.append('_')
        
        if verbose:
            print(f"Entrada: '{input_string}'")
            print(f"Fita inicial: {tape}")
            print(f"Posição inicial: {head_position}")
            print(f"Estado inicial: {self.states[current_state]}")
            print("-" * 50)
        
        while steps < max_steps:
            steps += 1
            
            # Ler símbolo atual
            current_symbol = tape[head_position] if head_position < len(tape) else '_'
            
            if verbose:
                print(f"Passo {steps}: Estado {self.states[current_state]}, Símbolo '{current_symbol}', Posição {head_position}")
            
            # Verificar se há transição para o símbolo atual
            if current_state not in self.transitions:
                if verbose:
                    print(f"❌ Sem transições do estado {self.states[current_state]}")
                return False, f"Sem transições do estado {self.states[current_state]}"
            
            if current_symbol not in self.transitions[current_state]:
                if verbose:
                    print(f"❌ Sem transição para símbolo '{current_symbol}' no estado {self.states[current_state]}")
                return False, f"Sem transição para símbolo '{current_symbol}' no estado {self.states[current_state]}"
            
            # Executar transição
            transition = self.transitions[current_state][current_symbol]
            next_state = transition['to']
            write_symbol = transition['write']
            move = transition['move']
            
            # Escrever símbolo
            if head_position < len(tape):
                tape[head_position] = write_symbol
            else:
                tape.append(write_symbol)
            
            # Mover cabeça
            if move == 'L':
                head_position -= 1
            elif move == 'R':
                head_position += 1
            # Se move == 'S', não move
            
            # Atualizar estado
            current_state = next_state
            
            if verbose:
                print(f"  → Escreve '{write_symbol}', Move {move}, Novo estado {self.states[current_state]}")
                print(f"  → Fita: {tape}, Nova posição: {head_position}")
            
            # Verificar se chegou a um estado final (assumindo que q6 é final)
            if current_state == '6':  # q6 parece ser o estado final
                if verbose:
                    print(f"✅ Aceita! Chegou ao estado final {self.states[current_state]}")
                return True, f"Aceita após {steps} passos"
            
            if verbose:
                print()
        
        if verbose:
            print(f"❌ Timeout após {max_steps} passos")
        return False, f"Timeout após {max_steps} passos"

def test_machine_with_cases():
    """Testa a máquina de Turing com os casos de teste gerados"""
    
    # Carregar casos de teste
    with open('test_cases_G_correto.json', 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    # Carregar máquina de Turing corrigida
    machine = TuringMachine('atividade turing/G linguagem_wwr_w_em_ab_estrela_CORRIGIDA.jff')
    
    print("="*70)
    print("TESTANDO MÁQUINA DE TURING CORRIGIDA PARA LINGUAGEM {wwR | w ∈ {a,b}*}")
    print("="*70)
    
    correct_predictions = 0
    total_tests = len(test_data['test_cases'])
    
    # Testar apenas alguns casos primeiro
    test_cases_to_run = test_data['test_cases'][:10]  # Primeiros 10 casos
    
    for i, test_case in enumerate(test_cases_to_run):
        input_string = test_case['input']
        expected = test_case['expected']
        
        print(f"\n{'='*70}")
        print(f"TESTE {i+1}/10: '{input_string}'")
        print(f"Esperado: {'ACEITA' if expected else 'REJEITA'}")
        print(f"{'='*70}")
        
        accepted, reason = machine.simulate(input_string, verbose=True)
        
        if accepted == expected:
            print(f"✅ CORRETO: {reason}")
            correct_predictions += 1
        else:
            print(f"❌ INCORRETO: Esperado {'ACEITA' if expected else 'REJEITA'}, mas {'ACEITA' if accepted else 'REJEITA'}")
        
        print(f"{'='*70}")
    
    print(f"\n{'='*70}")
    print(f"RESULTADO FINAL: {correct_predictions}/10 testes corretos")
    print(f"Taxa de acerto: {correct_predictions/10*100:.1f}%")
    print(f"{'='*70}")
    
    return correct_predictions, 10

if __name__ == "__main__":
    test_machine_with_cases()

