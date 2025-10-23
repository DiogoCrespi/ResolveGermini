#!/usr/bin/env python3
"""
Analisador da máquina de Turing para a linguagem H: {w | w ∈ {a, b}* e w contenha o dobro de símbolos "a" do que "b"}
"""

import xml.etree.ElementTree as ET

def analisar_maquina_turing(jff_file):
    """Analisa a máquina de Turing do arquivo JFLAP"""
    
    tree = ET.parse(jff_file)
    root = tree.getroot()
    
    # Extrair estados
    estados = {}
    estado_inicial = None
    estados_finais = []
    
    for state in root.findall('.//state'):
        state_id = state.get('id')
        state_name = state.get('name')
        x = float(state.find('x').text)
        y = float(state.find('y').text)
        
        estados[state_id] = {
            'name': state_name,
            'x': x,
            'y': y,
            'initial': state.find('initial') is not None,
            'final': state.find('final') is not None
        }
        
        if state.find('initial') is not None:
            estado_inicial = state_id
        if state.find('final') is not None:
            estados_finais.append(state_id)
    
    # Extrair transições
    transicoes = {}
    
    for transition in root.findall('.//transition'):
        from_state = transition.find('from').text
        to_state = transition.find('to').text
        read_symbol = transition.find('read').text if transition.find('read') is not None else ''
        write_symbol = transition.find('write').text if transition.find('write') is not None else ''
        move = transition.find('move').text if transition.find('move') is not None else ''
        
        if from_state not in transicoes:
            transicoes[from_state] = {}
        
        key = (read_symbol, write_symbol, move)
        transicoes[from_state][key] = to_state
    
    return estados, estado_inicial, estados_finais, transicoes

def simular_turing(entrada, estados, estado_inicial, estados_finais, transicoes, max_steps=1000):
    """Simula a execução da máquina de Turing"""
    
    # Estado atual
    estado_atual = estado_inicial
    posicao = 0
    fita = list(entrada)
    passos = 0
    historico = []
    
    while passos < max_steps:
        # Obter símbolo atual
        if posicao < 0:
            simbolo_atual = ''
        elif posicao >= len(fita):
            simbolo_atual = ''
        else:
            simbolo_atual = fita[posicao]
        
        # Registrar estado atual
        estado_info = estados[estado_atual]
        historico.append({
            'passo': passos,
            'estado': estado_atual,
            'nome_estado': estado_info['name'],
            'posicao': posicao,
            'simbolo_atual': simbolo_atual,
            'fita': ''.join(fita),
            'cursor_pos': posicao
        })
        
        # Verificar se está em estado final
        if estado_atual in estados_finais:
            return True, historico, f"ACEITA: Estado final {estado_info['name']} atingido"
        
        # Buscar transição
        transicoes_estado = transicoes.get(estado_atual, {})
        transicao_encontrada = None
        
        for (read, write, move), to_state in transicoes_estado.items():
            # Tratar None como string vazia para comparação
            read_compare = read if read is not None else ''
            if read_compare == simbolo_atual:
                transicao_encontrada = (read, write, move, to_state)
                break
        
        # Debug: mostrar transições disponíveis (comentado para saída limpa)
        # if not transicao_encontrada:
        #     print(f"    DEBUG: Estado {estado_atual}, símbolo '{simbolo_atual}', transições disponíveis: {list(transicoes_estado.keys())}")
        
        if not transicao_encontrada:
            return False, historico, f"REJEITA: Nenhuma transição encontrada no estado {estado_info['name']} para símbolo '{simbolo_atual}'"
        
        read, write, move, to_state = transicao_encontrada
        
        # Executar transição
        if write != '' and posicao >= 0 and posicao < len(fita):
            fita[posicao] = write
        
        # Mover cursor
        if move == 'R':
            posicao += 1
        elif move == 'L':
            posicao -= 1
        # move == 'S' significa ficar na mesma posição
        
        # Atualizar estado
        estado_atual = to_state
        passos += 1
    
    return False, historico, f"REJEITA: Máximo de passos ({max_steps}) atingido"

def analisar_lógica_maquina(estados, transicoes):
    """Analisa a lógica da máquina de Turing"""
    
    print("=== ANÁLISE DA MÁQUINA DE TURING ===")
    print()
    
    print("ESTADOS:")
    for state_id, info in estados.items():
        tipo = ""
        if info['initial']:
            tipo += " [INICIAL]"
        if info['final']:
            tipo += " [FINAL]"
        print(f"  {state_id}: {info['name']}{tipo}")
    
    print()
    print("TRANSIZÕES:")
    for from_state, trans_list in transicoes.items():
        print(f"  Estado {from_state} ({estados[from_state]['name']}):")
        for (read, write, move), to_state in trans_list.items():
            read_str = f"'{read}'" if read else "ε"
            write_str = f"'{write}'" if write else "ε"
            print(f"    {read_str} -> {write_str}, {move} -> {to_state} ({estados[to_state]['name']})")
    
    print()
    print("ANÁLISE DA LÓGICA:")
    
    # Analisar q0
    q0_trans = transicoes.get('0', {})
    print("  q0 (estado inicial):")
    print("    - Move para direita lendo 'a', 'b' ou 'X'")
    print("    - Quando encontra ε (fim da fita), vai para q1")
    
    # Analisar q1
    q1_trans = transicoes.get('1', {})
    print("  q1:")
    print("    - Se lê 'b', marca como 'X' e vai para q3")
    print("    - Se lê ε, aceita (vai para q6)")
    print("    - Move para esquerda lendo 'X'")
    
    # Analisar q3
    q3_trans = transicoes.get('3', {})
    print("  q3:")
    print("    - Move para esquerda lendo 'b' ou 'X'")
    print("    - Se lê 'a', marca como 'X' e vai para q4")
    
    # Analisar q4
    q4_trans = transicoes.get('4', {})
    print("  q4:")
    print("    - Se lê 'b', rejeita (vai para 'falha')")
    print("    - Se lê 'a', marca como 'X' e vai para q5")
    
    # Analisar q5
    q5_trans = transicoes.get('5', {})
    print("  q5:")
    print("    - Move para esquerda lendo 'a'")
    print("    - Se lê ε, volta para q0")
    
    print()
    print("ESTRATÉGIA IDENTIFICADA:")
    print("  1. q0: Percorre a fita da esquerda para direita")
    print("  2. q1: Quando chega ao fim, procura por 'b' para marcar")
    print("  3. q3: Move para esquerda procurando por 'a' correspondente")
    print("  4. q4: Marca o 'a' encontrado e verifica se há 'b' sem par")
    print("  5. q5: Volta ao início para repetir o processo")
    print("  6. A máquina aceita quando não há mais 'b's para processar")
    
    print()
    print("LÓGICA DA LINGUAGEM:")
    print("  - A máquina parece implementar uma estratégia de pareamento:")
    print("  - Para cada 'b', procura 2 'a's para marcar")
    print("  - Se consegue marcar todos os símbolos, aceita")
    print("  - Se sobra algum símbolo sem par, rejeita")

def main():
    jff_file = "atividade turing/H linguagem_w_ab_estrela_dobro_a_que_b.jff"
    
    try:
        estados, estado_inicial, estados_finais, transicoes = analisar_maquina_turing(jff_file)
        
        print("=== ANÁLISE DA MÁQUINA DE TURING H ===")
        print(f"Arquivo: {jff_file}")
        print()
        
        analisar_lógica_maquina(estados, transicoes)
        
        print()
        print("=== TESTES DE SIMULAÇÃO ===")
        
        # Casos de teste
        casos_teste = [
            ("", "String vazia"),
            ("aab", "2 a's, 1 b - deve aceitar"),
            ("aba", "2 a's, 1 b - deve aceitar"),
            ("baa", "2 a's, 1 b - deve aceitar"),
            ("aabb", "2 a's, 2 b's - deve rejeitar"),
            ("ab", "1 a, 1 b - deve rejeitar"),
            ("aa", "2 a's, 0 b's - deve rejeitar"),
            ("bb", "0 a's, 2 b's - deve rejeitar"),
            ("aaaabb", "4 a's, 2 b's - deve aceitar"),
            ("aabbaa", "4 a's, 2 b's - deve aceitar"),
        ]
        
        for entrada, descricao in casos_teste:
            print(f"\nTestando: '{entrada}' - {descricao}")
            resultado, historico, motivo = simular_turing(entrada, estados, estado_inicial, estados_finais, transicoes)
            
            print(f"  Resultado: {'ACEITA' if resultado else 'REJEITA'}")
            print(f"  Motivo: {motivo}")
            print(f"  Passos: {len(historico)}")
            
            # Mostrar últimos passos se necessário
            if len(historico) > 5:
                print("  Últimos passos:")
                for h in historico[-3:]:
                    fita_vis = h['fita'][:h['cursor_pos']] + '|' + h['fita'][h['cursor_pos']:]
                    print(f"    {h['passo']}: {h['nome_estado']} - {fita_vis}")
            else:
                print("  Passos completos:")
                for h in historico:
                    fita_vis = h['fita'][:h['cursor_pos']] + '|' + h['fita'][h['cursor_pos']:]
                    print(f"    {h['passo']}: {h['nome_estado']} - {fita_vis}")
    
    except Exception as e:
        print(f"Erro ao analisar a máquina: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
