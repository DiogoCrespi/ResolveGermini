"""
Factory para escolher entre diferentes clientes de IA (Gemini ou GPT)
"""

from typing import Dict, Any, List
from .config import AI_MODEL


def get_ai_functions():
    """
    Retorna as funções apropriadas baseadas no modelo de IA configurado
    """
    if AI_MODEL == "gpt":
        try:
            from .gpt_client import (
                extract_with_gpt as extract_with_ai,
                segment_text_into_questions_gpt as segment_text_into_questions,
                validate_grammars_gpt as validate_grammars,
                generate_turing_tests_gpt as generate_turing_tests,
                merge_blocks
            )
            print(f"✅ Usando modelo GPT: {AI_MODEL}")
            return extract_with_ai, segment_text_into_questions, validate_grammars, generate_turing_tests, merge_blocks
        except ImportError as e:
            print(f"❌ Erro ao importar cliente GPT: {e}")
            print("Verifique se a biblioteca 'openai' está instalada: pip install openai")
            raise
    elif AI_MODEL == "deepseek":
        try:
            from .deepseek_client import (
                extract_with_deepseek as extract_with_ai,
                segment_text_into_questions_deepseek as segment_text_into_questions,
                validate_grammars_deepseek as validate_grammars,
                generate_turing_tests_deepseek as generate_turing_tests,
                merge_blocks
            )
            print(f"✅ Usando modelo DeepSeek: {AI_MODEL}")
            return extract_with_ai, segment_text_into_questions, validate_grammars, generate_turing_tests, merge_blocks
        except ImportError as e:
            print(f"❌ Erro ao importar cliente DeepSeek: {e}")
            print("Verifique se a biblioteca 'requests' está instalada: pip install requests")
            raise
    elif AI_MODEL == "gemini":
        try:
            from .gemini_client import (
                extract_with_gemini as extract_with_ai,
                segment_text_into_questions,
                validate_grammars,
                generate_turing_tests,
                merge_blocks
            )
            print(f"✅ Usando modelo Gemini: {AI_MODEL}")
            return extract_with_ai, segment_text_into_questions, validate_grammars, generate_turing_tests, merge_blocks
        except ImportError as e:
            print(f"❌ Erro ao importar cliente Gemini: {e}")
            raise
    else:
        raise ValueError(f"Modelo de IA não suportado: {AI_MODEL}. Use 'gemini', 'gpt' ou 'deepseek'")


# Inicializar as funções baseadas na configuração
try:
    extract_with_ai, segment_text_into_questions, validate_grammars, generate_turing_tests, merge_blocks = get_ai_functions()
except Exception as e:
    print(f"❌ Erro ao inicializar cliente de IA: {e}")
    raise
