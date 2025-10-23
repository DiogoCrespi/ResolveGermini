#!/usr/bin/env python3
"""
Máquina de Turing corrigida para a linguagem H: {w | w ∈ {a, b}* e w contenha o dobro de símbolos "a" do que "b"}
"""

import xml.etree.ElementTree as ET

def criar_turing_corrigida():
    """Cria uma máquina de Turing corrigida para a linguagem H"""
    
    # Estrutura XML da máquina corrigida
    turing_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<structure>
    <type>turing</type>
    <automaton>
        <!-- Estados -->
        <state id="0" name="q0">
            <x>200.0</x>
            <y>200.0</y>
            <initial/>
        </state>
        <state id="1" name="q1">
            <x>400.0</x>
            <y>200.0</y>
        </state>
        <state id="2" name="q2">
            <x>600.0</x>
            <y>200.0</y>
        </state>
        <state id="3" name="q3">
            <x>800.0</x>
            <y>200.0</y>
        </state>
        <state id="4" name="q4">
            <x>1000.0</x>
            <y>200.0</y>
        </state>
        <state id="5" name="q5">
            <x>1200.0</x>
            <y>200.0</y>
        </state>
        <state id="6" name="q6">
            <x>1400.0</x>
            <y>200.0</y>
            <final/>
        </state>
        <state id="7" name="q7">
            <x>800.0</x>
            <y>400.0</y>
        </state>
        <state id="8" name="q8">
            <x>600.0</x>
            <y>400.0</y>
        </state>
        <state id="9" name="q9">
            <x>400.0</x>
            <y>400.0</y>
        </state>
        <state id="10" name="q10">
            <x>200.0</x>
            <y>400.0</y>
        </state>
        
        <!-- Transições -->
        <!-- q0: estado inicial - percorre a fita procurando por 'b' -->
        <transition>
            <from>0</from>
            <to>0</to>
            <read>a</read>
            <write>a</write>
            <move>R</move>
        </transition>
        <transition>
            <from>0</from>
            <to>1</to>
            <read>b</read>
            <write>X</write>
            <move>R</move>
        </transition>
        <transition>
            <from>0</from>
            <to>6</to>
            <read></read>
            <write></write>
            <move>S</move>
        </transition>
        
        <!-- q1: encontrou um 'b', marcou como 'X', agora procura o primeiro 'a' -->
        <transition>
            <from>1</from>
            <to>1</to>
            <read>a</read>
            <write>a</write>
            <move>R</move>
        </transition>
        <transition>
            <from>1</from>
            <to>1</to>
            <read>b</read>
            <write>b</write>
            <move>R</move>
        </transition>
        <transition>
            <from>1</from>
            <to>1</to>
            <read>X</read>
            <write>X</write>
            <move>R</move>
        </transition>
        <transition>
            <from>1</from>
            <to>2</to>
            <read></read>
            <write></write>
            <move>L</move>
        </transition>
        
        <!-- q2: voltando para procurar o primeiro 'a' para marcar -->
        <transition>
            <from>2</from>
            <to>2</to>
            <read>a</read>
            <write>a</write>
            <move>L</move>
        </transition>
        <transition>
            <from>2</from>
            <to>2</to>
            <read>b</read>
            <write>b</write>
            <move>L</move>
        </transition>
        <transition>
            <from>2</from>
            <to>2</to>
            <read>X</read>
            <write>X</write>
            <move>L</move>
        </transition>
        <transition>
            <from>2</from>
            <to>3</to>
            <read></read>
            <write></write>
            <move>R</move>
        </transition>
        
        <!-- q3: procurando o primeiro 'a' para marcar -->
        <transition>
            <from>3</from>
            <to>3</to>
            <read>a</read>
            <write>a</write>
            <move>R</move>
        </transition>
        <transition>
            <from>3</from>
            <to>4</to>
            <read>a</read>
            <write>Y</write>
            <move>R</move>
        </transition>
        <transition>
            <from>3</from>
            <to>7</to>
            <read>b</read>
            <write>b</write>
            <move>S</move>
        </transition>
        <transition>
            <from>3</from>
            <to>7</to>
            <read>X</read>
            <write>X</write>
            <move>S</move>
        </transition>
        <transition>
            <from>3</from>
            <to>7</to>
            <read></read>
            <write></write>
            <move>S</move>
        </transition>
        
        <!-- q4: marcou o primeiro 'a' como 'Y', agora procura o segundo 'a' -->
        <transition>
            <from>4</from>
            <to>4</to>
            <read>a</read>
            <write>a</write>
            <move>R</move>
        </transition>
        <transition>
            <from>4</from>
            <to>4</to>
            <read>b</read>
            <write>b</write>
            <move>R</move>
        </transition>
        <transition>
            <from>4</from>
            <to>4</to>
            <read>X</read>
            <write>X</write>
            <move>R</move>
        </transition>
        <transition>
            <from>4</from>
            <to>5</to>
            <read>a</read>
            <write>Z</write>
            <move>R</move>
        </transition>
        <transition>
            <from>4</from>
            <to>7</to>
            <read></read>
            <write></write>
            <move>S</move>
        </transition>
        
        <!-- q5: marcou o segundo 'a' como 'Z', volta para o início -->
        <transition>
            <from>5</from>
            <to>5</to>
            <read>a</read>
            <write>a</write>
            <move>R</move>
        </transition>
        <transition>
            <from>5</from>
            <to>5</to>
            <read>b</read>
            <write>b</write>
            <move>R</move>
        </transition>
        <transition>
            <from>5</from>
            <to>5</to>
            <read>X</read>
            <write>X</write>
            <move>R</move>
        </transition>
        <transition>
            <from>5</from>
            <to>5</to>
            <read>Y</read>
            <write>Y</write>
            <move>R</move>
        </transition>
        <transition>
            <from>5</from>
            <to>5</to>
            <read>Z</read>
            <write>Z</write>
            <move>R</move>
        </transition>
        <transition>
            <from>5</from>
            <to>0</to>
            <read></read>
            <write></write>
            <move>L</move>
        </transition>
        
        <!-- q7: estado de rejeição -->
        <transition>
            <from>7</from>
            <to>7</to>
            <read>a</read>
            <write>a</write>
            <move>S</move>
        </transition>
        
        <!-- q8, q9, q10: estados auxiliares para limpeza -->
        <transition>
            <from>8</from>
            <to>8</to>
            <read>Y</read>
            <write>a</write>
            <move>L</move>
        </transition>
        <transition>
            <from>8</from>
            <to>8</to>
            <read>Z</read>
            <write>a</write>
            <move>L</move>
        </transition>
        <transition>
            <from>8</from>
            <to>9</to>
            <read></read>
            <write></write>
            <move>R</move>
        </transition>
        
        <transition>
            <from>9</from>
            <to>9</to>
            <read>Y</read>
            <write>a</write>
            <move>R</move>
        </transition>
        <transition>
            <from>9</from>
            <to>9</to>
            <read>Z</read>
            <write>a</write>
            <move>R</move>
        </transition>
        <transition>
            <from>9</from>
            <to>10</to>
            <read></read>
            <write></write>
            <move>L</move>
        </transition>
        
        <transition>
            <from>10</from>
            <to>10</to>
            <read>Y</read>
            <write>a</write>
            <move>L</move>
        </transition>
        <transition>
            <from>10</from>
            <to>10</to>
            <read>Z</read>
            <write>a</write>
            <move>L</move>
        </transition>
        <transition>
            <from>10</from>
            <to>6</to>
            <read></read>
            <write></write>
            <move>S</move>
        </transition>
    </automaton>
</structure>'''
    
    return turing_xml

def criar_turing_simples():
    """Cria uma versão mais simples da máquina de Turing"""
    
    turing_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<structure>
    <type>turing</type>
    <automaton>
        <!-- Estados -->
        <state id="0" name="q0">
            <x>200.0</x>
            <y>200.0</y>
            <initial/>
        </state>
        <state id="1" name="q1">
            <x>400.0</x>
            <y>200.0</y>
        </state>
        <state id="2" name="q2">
            <x>600.0</x>
            <y>200.0</y>
        </state>
        <state id="3" name="q3">
            <x>800.0</x>
            <y>200.0</y>
            <final/>
        </state>
        <state id="4" name="q4">
            <x>600.0</x>
            <y>400.0</y>
        </state>
        
        <!-- Transições -->
        <!-- q0: conta 'a's e 'b's -->
        <transition>
            <from>0</from>
            <to>0</to>
            <read>a</read>
            <write>a</write>
            <move>R</move>
        </transition>
        <transition>
            <from>0</from>
            <to>0</to>
            <read>b</read>
            <write>b</write>
            <move>R</move>
        </transition>
        <transition>
            <from>0</from>
            <to>1</to>
            <read></read>
            <write></write>
            <move>L</move>
        </transition>
        
        <!-- q1: verifica se há pelo menos um 'b' -->
        <transition>
            <from>1</from>
            <to>1</to>
            <read>a</read>
            <write>a</write>
            <move>L</move>
        </transition>
        <transition>
            <from>1</from>
            <to>2</to>
            <read>b</read>
            <write>X</write>
            <move>L</move>
        </transition>
        <transition>
            <from>1</from>
            <to>4</to>
            <read></read>
            <write></write>
            <move>R</move>
        </transition>
        
        <!-- q2: procura por dois 'a's para marcar -->
        <transition>
            <from>2</from>
            <to>2</to>
            <read>a</read>
            <write>a</write>
            <move>L</move>
        </transition>
        <transition>
            <from>2</from>
            <to>2</to>
            <read>b</read>
            <write>b</write>
            <move>L</move>
        </transition>
        <transition>
            <from>2</from>
            <to>2</to>
            <read>X</read>
            <write>X</write>
            <move>L</move>
        </transition>
        <transition>
            <from>2</from>
            <to>3</to>
            <read></read>
            <write></write>
            <move>R</move>
        </transition>
        
        <!-- q4: estado de rejeição -->
        <transition>
            <from>4</from>
            <to>4</to>
            <read>a</read>
            <write>a</write>
            <move>S</move>
        </transition>
    </automaton>
</structure>'''
    
    return turing_xml

def main():
    """Cria as versões corrigidas da máquina de Turing"""
    
    print("=== CRIANDO MÁQUINAS DE TURING CORRIGIDAS ===")
    
    # Salvar versão corrigida
    turing_corrigida = criar_turing_corrigida()
    with open("H_linguagem_corrigida.jff", "w", encoding="utf-8") as f:
        f.write(turing_corrigida)
    
    print("✅ Máquina corrigida salva em: H_linguagem_corrigida.jff")
    
    # Salvar versão simples
    turing_simples = criar_turing_simples()
    with open("H_linguagem_simples.jff", "w", encoding="utf-8") as f:
        f.write(turing_simples)
    
    print("✅ Máquina simples salva em: H_linguagem_simples.jff")
    
    print("\n=== ESTRATÉGIA DA MÁQUINA CORRIGIDA ===")
    print("1. q0: Percorre a fita procurando por 'b'")
    print("2. q1: Quando encontra 'b', marca como 'X' e continua")
    print("3. q2: Volta para o início procurando o primeiro 'a'")
    print("4. q3: Marca o primeiro 'a' como 'Y'")
    print("5. q4: Marca o segundo 'a' como 'Z'")
    print("6. q5: Volta para o início e repete")
    print("7. q6: Aceita quando não há mais 'b's para processar")
    print("8. q7: Rejeita se não consegue encontrar 'a's suficientes")

if __name__ == "__main__":
    main()
