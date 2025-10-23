#!/usr/bin/env python3
"""
Simulador simples de Máquina de Turing para linguagem {wwR | w ∈ {a,b}*}
"""

import json
import xml.etree.ElementTree as ET

class SimpleTuringMachine:
    def __init__(self, jff_file):
        self.states = {}
        self.transitions = {}
        self.initial_state = None
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
            
            if state_name == 'q0':
                self.initial_state = state_id
        
        # Carregar transições
        for transition in root.findall('.//transition'):
            from_state = transition.find('from').text
            to_state = transition.find('to').text
            read_symbol = transition.find('read').text or ''
            write_symbol = transition.find('write').text or ''
            move = transition.find('move').text
            
            if from_state not in self.transitions:
                self.transitions[from_state] = {}
            
            self.transitions[from_state][read_symbol] = {
                'to': to_state,
                'write': write_symbol,
                'move': move
            }
    
    def simulate(self, input_string, max_steps=1000):
        """Simula a execução da máquina de Turing"""
        tape = list(input_string)
        head_position = 0
        current_state = self.initial_state
        steps = 0
        
        while steps < max_steps:
            steps += 1
            
            # Ler símbolo atual
            current_symbol = tape[head_position] if head_position < len(tape) else '_'
            
            # Verificar se há transição
            if current_state not in self.transitions:
                return False, f"Sem transições do estado {self.states[current_state]}"
            
            if current_symbol not in self.transitions[current_state]:
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
            
            # Atualizar estado
            current_state = next_state
            
            # Verificar se chegou ao estado final (q6)
            if current_state == '6':
                return True, f"Aceita após {steps} passos"
        
        return False, f"Timeout após {max_steps} passos"

def test_simple_cases():
    """Testa casos simples primeiro"""
    
    machine = SimpleTuringMachine('atividade turing/G linguagem_wwr_w_em_ab_estrela_FINAL.jff')
    
    test_cases = [
        ("", True, "String vazia"),
        ("aa", True, "w=a, wR=a"),
        ("bb", True, "w=b, wR=b"),
        ("abba", True, "w=ab, wR=ba"),
        ("baab", True, "w=ba, wR=ab"),
        ("a", False, "Tamanho ímpar"),
        ("ab", False, "Não é wwR"),
        ("abc", False, "Caractere inválido"),
    ]
    
    print("="*70)
    print("TESTANDO CASOS SIMPLES")
    print("="*70)
    
    correct = 0
    total = len(test_cases)
    
    for input_str, expected, description in test_cases:
        accepted, reason = machine.simulate(input_str)
        
        status = "✅" if accepted == expected else "❌"
        result = "ACEITA" if accepted else "REJEITA"
        expected_result = "ACEITA" if expected else "REJEITA"
        
        print(f"{status} '{input_str}' ({description})")
        print(f"   Esperado: {expected_result}, Obtido: {result}")
        print(f"   Motivo: {reason}")
        print()
        
        if accepted == expected:
            correct += 1
    
    print(f"Resultado: {correct}/{total} corretos ({correct/total*100:.1f}%)")
    return correct, total

if __name__ == "__main__":
    test_simple_cases()

