"""
Schema para rastreamento de pagamentos de operadores em partidas
Permite validar se um operador já pagou antes de agendar a partida
"""

# Adicionar ao models.py após a classe Partida

class PagamentoOperador(db.Model):
    __tablename__ = 'pagamento_operador'
    
    id = db.Column(db.Integer, primary_key=True)
    operador_id = db.Column(db.Integer, db.ForeignKey('operadores.id'), nullable=False)
    partida_id = db.Column(db.Integer, db.ForeignKey('partidas.id'), nullable=True)  # NULL = pagamento geral
    
    valor = db.Column(db.Float, nullable=False)  # Valor esperado
    valor_pago = db.Column(db.Float, default=0)  # Valor realmente pago
    status = db.Column(db.String(20), default='Pendente')  # Pendente, Parcial, Pago, Cancelado
    
    # Rastreamento
    data_vencimento = db.Column(db.DateTime, nullable=True)
    data_pagamento = db.Column(db.DateTime, nullable=True)
    metodo_pagamento = db.Column(db.String(50), nullable=True)  # PIX, Dinheiro, Débito, Crédito
    registrado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Quem registrou
    observacoes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    operador = db.relationship('Operador', backref='pagamentos')
    partida = db.relationship('Partida', backref='pagamentos_operadores')
    registrador = db.relationship('User', backref='pagamentos_registrados')
    
    def marcar_pago(self, valor=None, metodo=None, usuario=None):
        """Marca o pagamento como realizado"""
        if valor is None:
            valor = self.valor
        
        self.status = 'Pago' if valor >= self.valor else 'Parcial'
        self.valor_pago = valor
        self.data_pagamento = datetime.utcnow()
        self.metodo_pagamento = metodo
        self.registrado_por = usuario
        db.session.commit()
    
    def pendente(self):
        """Retorna quanto ainda está pendente"""
        return max(0, self.valor - self.valor_pago)
    
    def __repr__(self):
        return f"<PagamentoOperador {self.operador.warname} - {self.status}>"


# Adicionar esta função utilitária após os modelos ou em um novo arquivo utils

def validar_pagamentos_partida(operador_ids: list, valor_por_pessoa: float) -> dict:
    """
    Valida se todos os operadores têm pagamento registrado e não vencido
    
    Args:
        operador_ids: Lista de IDs dos operadores
        valor_por_pessoa: Valor esperado de pagamento
    
    Returns:
        {
            'valido': bool,
            'operadores_ok': list,
            'operadores_sem_pagamento': list,
            'operadores_pagamento_incompleto': list,
            'detalhes': str
        }
    """
    from datetime import datetime, timedelta
    
    operadores_ok = []
    operadores_sem_pagamento = []
    operadores_pagamento_incompleto = []
    
    for op_id in operador_ids:
        # Buscar último pagamento registrado
        pagamento = PagamentoOperador.query.filter_by(
            operador_id=op_id,
            partida_id=None  # Pagamento geral, não específico de partida
        ).order_by(PagamentoOperador.created_at.desc()).first()
        
        operador = Operador.query.get(op_id)
        warname = operador.warname if operador else f"ID {op_id}"
        
        if not pagamento:
            operadores_sem_pagamento.append({
                'id': op_id,
                'warname': warname,
                'motivo': 'Sem registro de pagamento'
            })
        elif pagamento.status == 'Pendente' or pagamento.pendente() > 0:
            operadores_pagamento_incompleto.append({
                'id': op_id,
                'warname': warname,
                'pendente': pagamento.pendente()
            })
        elif pagamento.status == 'Pago':
            # Verificar se venceu (considera válido por 30 dias)
            dias_desde_pagamento = (datetime.utcnow() - pagamento.data_pagamento).days
            if dias_desde_pagamento <= 30:
                operadores_ok.append(op_id)
            else:
                operadores_sem_pagamento.append({
                    'id': op_id,
                    'warname': warname,
                    'motivo': 'Pagamento vencido (> 30 dias)'
                })
        else:
            operadores_sem_pagamento.append({
                'id': op_id,
                'warname': warname,
                'motivo': f'Status: {pagamento.status}'
            })
    
    # Compilar resultado
    tem_problemas = bool(operadores_sem_pagamento or operadores_pagamento_incompleto)
    
    if tem_problemas:
        detalhes = "Operadores com problema de pagamento:\n"
        if operadores_sem_pagamento:
            detalhes += "\n❌ Sem Pagamento:\n"
            for op in operadores_sem_pagamento:
                detalhes += f"  • {op['warname']}: {op['motivo']}\n"
        if operadores_pagamento_incompleto:
            detalhes += "\n⚠️ Pagamento Incompleto:\n"
            for op in operadores_pagamento_incompleto:
                detalhes += f"  • {op['warname']}: Faltam R$ {op['pendente']:.2f}\n"
    else:
        detalhes = "✅ Todos os operadores com pagamento em dia!"
    
    return {
        'valido': not tem_problemas,
        'operadores_ok': operadores_ok,
        'operadores_sem_pagamento': operadores_sem_pagamento,
        'operadores_pagamento_incompleto': operadores_pagamento_incompleto,
        'detalhes': detalhes
    }
