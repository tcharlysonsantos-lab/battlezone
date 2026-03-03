"""
Rotas para gerenciar pagamentos de operadores
Permite visualizar e registrar pagamentos
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from backend.models import db, PagamentoOperador, Operador, User
from backend.validadores_pagamento import registrar_pagamento_operador
from datetime import datetime
from functools import wraps

pagamento_bp = Blueprint('pagamentos', __name__, url_prefix='/pagamentos')


def requer_permissao_financeiro(f):
    """Decorator para verificar se usuário tem permissão de financeiro/admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.nivel not in ['admin', 'gerente', 'financeiro']:
            flash('❌ Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@pagamento_bp.route('/')
@login_required
@requer_permissao_financeiro
def listar_pagamentos():
    """Lista todos os pagamentos registrados com filtros"""
    
    # Filtros
    status = request.args.get('status', 'todos')
    operador_id = request.args.get('operador_id')
    
    # Query base
    query = PagamentoOperador.query.filter_by(partida_id=None)  # Apenas pagamentos gerais
    
    # Aplicar filtros
    if status != 'todos':
        query = query.filter_by(status=status)
    
    if operador_id:
        query = query.filter_by(operador_id=operador_id)
    
    # Ordenar por data (maior primeiro)
    pagamentos = query.order_by(PagamentoOperador.created_at.desc()).all()
    
    # Listar operadores para select
    operadores = Operador.query.order_by(Operador.nome).all()
    
    stats = {
        'total_operadores': Operador.query.count(),
        'com_pagamento_ativo': PagamentoOperador.query.filter_by(status='Pago').count(),
        'com_pagamento_vencido': len([p for p in PagamentoOperador.query.filter_by(status='Pago').all() 
                                       if (datetime.utcnow() - p.data_pagamento).days > 30]),
        'com_pendencia': PagamentoOperador.query.filter(
            PagamentoOperador.status.in_(['Pendente', 'Parcial'])
        ).count(),
    }
    
    return render_template('pagamentos/listar.html', 
                         pagamentos=pagamentos, 
                         operadores=operadores,
                         status_filtro=status,
                         operador_id_filtro=operador_id,
                         stats=stats)


@pagamento_bp.route('/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao_financeiro
def registrar_pagamento():
    """Registra um novo pagamento de operador"""
    
    operadores = Operador.query.order_by(Operador.nome).all()
    
    if request.method == 'POST':
        try:
            operador_id = request.form.get('operador_id')
            valor = request.form.get('valor')
            metodo = request.form.get('metodo')
            observacoes = request.form.get('observacoes')
            
            # Validações
            if not operador_id:
                flash('❌ Selecione um operador.', 'danger')
                return render_template('pagamentos/form.html', operadores=operadores)
            
            if not valor:
                flash('❌ Digite o valor do pagamento.', 'danger')
                return render_template('pagamentos/form.html', operadores=operadores)
            
            try:
                valor = float(valor)
                if valor <= 0:
                    raise ValueError
            except ValueError:
                flash('❌ Valor deve ser um número positivo.', 'danger')
                return render_template('pagamentos/form.html', operadores=operadores)
            
            # Verificar se operador existe
            operador = Operador.query.get(operador_id)
            if not operador:
                flash('❌ Operador não encontrado.', 'danger')
                return render_template('pagamentos/form.html', operadores=operadores)
            
            # Registrar pagamento
            pagamento = PagamentoOperador(
                operador_id=operador_id,
                valor=valor,
                valor_pago=valor,
                status='Pago',
                metodo_pagamento=metodo,
                registrado_por=current_user.id,
                observacoes=observacoes,
                data_pagamento=datetime.utcnow()
            )
            
            db.session.add(pagamento)
            db.session.commit()
            
            flash(f'✅ Pagamento registrado para {operador.warname}: R$ {valor:.2f}', 'success')
            return redirect(url_for('pagamentos.listar_pagamentos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro ao registrar pagamento: {str(e)}', 'danger')
    
    return render_template('pagamentos/form.html', operadores=operadores)


@pagamento_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@requer_permissao_financeiro
def editar_pagamento(id):
    """Edita um pagamento existente"""
    
    pagamento = PagamentoOperador.query.get_or_404(id)
    operadores = Operador.query.order_by(Operador.nome).all()
    
    if request.method == 'POST':
        try:
            operador_id = request.form.get('operador_id')
            valor = request.form.get('valor')
            metodo = request.form.get('metodo')
            observacoes = request.form.get('observacoes')
            
            # Validações
            try:
                valor = float(valor)
                if valor <= 0:
                    raise ValueError
            except ValueError:
                flash('❌ Valor deve ser um número positivo.', 'danger')
                return render_template('pagamentos/editar.html', pagamento=pagamento, operadores=operadores)
            
            # Atualizar
            pagamento.operador_id = operador_id
            pagamento.valor = valor
            pagamento.valor_pago = valor
            pagamento.status = 'Pago'
            pagamento.metodo_pagamento = metodo
            pagamento.observacoes = observacoes
            pagamento.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'✅ Pagamento atualizado com sucesso!', 'success')
            return redirect(url_for('pagamentos.listar_pagamentos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro ao atualizar pagamento: {str(e)}', 'danger')
    
    return render_template('pagamentos/editar.html', pagamento=pagamento, operadores=operadores)


@pagamento_bp.route('/<int:id>/deletar', methods=['POST'])
@login_required
@requer_permissao_financeiro
def deletar_pagamento(id):
    """Deleta um pagamento"""
    
    pagamento = PagamentoOperador.query.get_or_404(id)
    operador_warname = pagamento.operador.warname
    
    try:
        db.session.delete(pagamento)
        db.session.commit()
        flash(f'✅ Pagamento de {operador_warname} deletado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro ao deletar pagamento: {str(e)}', 'danger')
    
    return redirect(url_for('pagamentos.listar_pagamentos'))


@pagamento_bp.route('/api/status-operador/<int:operador_id>')
@login_required
@requer_permissao_financeiro
def api_status_operador(operador_id):
    """API para verificar status de pagamento de um operador"""
    
    from backend.validadores_pagamento import validar_pagamentos_partida
    
    resultado = validar_pagamentos_partida([operador_id])
    
    if resultado['valido']:
        return jsonify({
            'status': 'ok',
            'operador_id': operador_id,
            'mensagem': '✅ Pagamento em dia'
        })
    else:
        problemas = resultado['operadores_sem_pagamento'] + resultado['operadores_pagamento_incompleto']
        return jsonify({
            'status': 'erro',
            'operador_id': operador_id,
            'mensagem': f"❌ Operador com problema de pagamento",
            'detalhes': resultado['mensagem_erro']
        })
