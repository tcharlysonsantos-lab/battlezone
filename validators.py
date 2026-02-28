# validators.py
import re
from wtforms import ValidationError

def validar_email(email):
    """Valida se o email tem formato correto"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_telefone(telefone):
    """Valida se o telefone tem formato correto (XX 99999-9999 ou XX 99999 9999 ou 99999-9999)"""
    # Remove espaços, hífens e parênteses para validação
    digits_only = re.sub(r'[^\d]', '', telefone)
    
    # Deve ter 10 ou 11 dígitos (com ou sem área)
    if len(digits_only) < 10 or len(digits_only) > 11:
        return False
    
    return True

def validar_cpf(cpf):
    """Valida CPF usando o algoritmo do dígito verificador"""
    # Remove caracteres não-numéricos
    cpf = re.sub(r'[^\d]', '', str(cpf))
    
    # CPF deve ter 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Rejeita CPFs com todos os dígitos iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = 11 - (soma % 11)
    digito1 = 0 if digito1 > 9 else digito1
    
    # Calcula segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = 11 - (soma % 11)
    digito2 = 0 if digito2 > 9 else digito2
    
    # Verifica se os dígitos calculados correspondem aos informados
    return int(cpf[9]) == digito1 and int(cpf[10]) == digito2
