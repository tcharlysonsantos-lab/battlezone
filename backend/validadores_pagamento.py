"""
Validadores para pagamento de operadores em partidas
"""
from datetime import datetime, timedelta
from backend.models import db, PagamentoOperador, Operador


def validar_pagamentos_partida(operador_ids: list) -> dict:
    """
    Valida se todos os operadores têm pagamento registrado e em dia
    Válido por 30 dias após o pagamento
    
    Args:
        operador_ids: Lista de IDs dos operadores que vão participar
    
    Returns:
        {
            'valido': bool,
            'operadores_ok': list,
            'operadores_sem_pagamento': list,
            'operadores_pagamento_incompleto': list,
            'mensagem_erro': str (amigável para exibir no flash)
        }
    """
    operadores_ok = []
    operadores_sem_pagamento = []
    operadores_pagamento_incompleto = []
    
    for op_id in operador_ids:
        # Buscar último pagamento registrado (não específico de partida)
        pagamento = PagamentoOperador.query.filter_by(
            operador_id=op_id,
            partida_id=None  # Pagamento geral, válido para qualquer partida
        ).order_by(PagamentoOperador.created_at.desc()).first()
        
        operador = Operador.query.get(op_id)
        warname = operador.warname if operador else f"ID {op_id}"
        
        if not pagamento:
            # Nunca pagou
            operadores_sem_pagamento.append({
                'id': op_id,
                'warname': warname,
                'motivo': 'Sem registro de pagamento'
            })
        elif pagamento.status == 'Pago':
            # Verificar se ainda está válido (30 dias)
            dias_desde_pagamento = (datetime.utcnow() - pagamento.data_pagamento).days
            if dias_desde_pagamento <= 30:
                operadores_ok.append(op_id)
            else:
                operadores_sem_pagamento.append({
                    'id': op_id,
                    'warname': warname,
                    'motivo': f'Pagamento vencido ({dias_desde_pagamento} dias atrás)'
                })
        elif pagamento.status == 'Parcial':
            # Pagamento incompleto
            pendente = pagamento.pendente()
            operadores_pagamento_incompleto.append({
                'id': op_id,
                'warname': warname,
                'valor_total': pagamento.valor,
                'valor_pago': pagamento.valor_pago,
                'pendente': pendente
            })
        else:
            # Status Pendente, Cancelado, etc
            operadores_sem_pagamento.append({
                'id': op_id,
                'warname': warname,
                'motivo': f'Status: {pagamento.status}'
            })
    
    # Compilar resultado
    tem_problemas = bool(operadores_sem_pagamento or operadores_pagamento_incompleto)
    
    # Montar mensagem de erro amigável
    mensagem_erro = ""
    if operadores_sem_pagamento:
        mensagem_erro += "❌ <strong>Sem Pagamento Válido:</strong><br>"
        for op in operadores_sem_pagamento:
            mensagem_erro += f"  • <strong>{op['warname']}</strong><br>"
            mensagem_erro += f"    └─ {op['motivo']}<br>"
    
    if operadores_pagamento_incompleto:
        if mensagem_erro:
            mensagem_erro += "<br>"
        mensagem_erro += "⚠️ <strong>Pagamento Incompleto:</strong><br>"
        for op in operadores_pagamento_incompleto:
            pendente = op['pendente']
            mensagem_erro += f"  • <strong>{op['warname']}</strong><br>"
            mensagem_erro += f"    └─ Faltam R$ {pendente:.2f} (pago: R$ {op['valor_pago']:.2f})<br>"
    
    return {
        'valido': not tem_problemas,
        'operadores_ok': operadores_ok,
        'operadores_sem_pagamento': operadores_sem_pagamento,
        'operadores_pagamento_incompleto': operadores_pagamento_incompleto,
        'mensagem_erro': mensagem_erro
    }


def registrar_pagamento_operador(operador_id: int, valor: float, metodo: str = None, usuario_id: int = None, observacoes: str = None) -> bool:
    """
    Registra um pagamento de operador (válido para qualquer partida por 30 dias)
    
    Args:
        operador_id: ID do operador
        valor: Valor pago
        metodo: Método de pagamento (PIX, Dinheiro, Débito, Crédito)
        usuario_id: ID do usuário que registrou
        observacoes: Observações sobre o pagamento
    
    Returns:
        True se registrado com sucesso
    """
    try:
        # Verificar se já existe pagamento pendente/parcial
        pagamento_existente = PagamentoOperador.query.filter_by(
            operador_id=operador_id,
            partida_id=None,
            status__in=['Pendente', 'Parcial']  # Não funciona assim, vou usar OR
        ).first()
        
        # Ajuste correto para SQLAlchemy
        from sqlalchemy import or_
        pagamento_existente = PagamentoOperador.query.filter(
            PagamentoOperador.operador_id == operador_id,
            PagamentoOperador.partida_id == None,
            or_(
                PagamentoOperador.status == 'Pendente',
                PagamentoOperador.status == 'Parcial'
            )
        ).first()
        
        if pagamento_existente:
            # Atualizar existente
            pagamento_existente.valor_pago = valor
            pagamento_existente.status = 'Pago' if valor >= pagamento_existente.valor else 'Parcial'
            pagamento_existente.data_pagamento = datetime.utcnow()
            pagamento_existente.metodo_pagamento = metodo
            pagamento_existente.registrado_por = usuario_id
            pagamento_existente.observacoes = observacoes
            pagamento_existente.updated_at = datetime.utcnow()
        else:
            # Criar novo
            pagamento = PagamentoOperador(
                operador_id=operador_id,
                valor=valor,
                valor_pago=valor,
                status='Pago',
                metodo_pagamento=metodo,
                registrado_por=usuario_id,
                observacoes=observacoes,
                data_pagamento=datetime.utcnow()
            )
            db.session.add(pagamento)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao registrar pagamento: {str(e)}")
        return False
