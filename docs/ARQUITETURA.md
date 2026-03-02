# 📐 Arquitetura - BattleZone

## Padrão MVC + S

**M**odel → **V**iew → **C**ontroller + **S**ervice

```
app.py              # Ponto de entrada, inicializar app
├── models.py       # Modelos ORM (User, Operador, Equipe, Partida, etc)
├── auth.py         # Rotas de autenticação
├── routes/         # Rotas por módulo (equipes, partidas, etc)
├── forms.py        # Validação de formulários
├── templates/      # HTML (Jinja2)
├── static/         # CSS, JS, imagens
├── utils.py        # Funções auxiliares
├── validators.py   # Validadores customizados
├── security_utils  # Segurança e sanitização
├── auth_security   # 2FA e autenticação avançada
├── cloud_manager   # Integração com Google Drive
└── decorators.py   # Decoradores customizados
```

## Camadas de Aplicação

### 1. Presentation (Templates)
- `templates/base.html` - Layout base
- `templates/auth/` - Login, registrar
- `templates/equipes/` - Gestão de equipes
- `templates/partidas/` - Gestão de partidas
- `templates/admin/` - Portal administrativo

### 2. Application (Routes)
- `app.py` - Rotas principais
- `auth.py` - Rotas de autenticação
- Decoradores: `@admin_required`, `@requer_permissao`

### 3. Business Logic (Services)
- `utils.py` - Lógica de negócio
- `cloud_manager.py` - Backup na nuvem
- `auth_security.py` - Lógica de 2FA

### 4. Data Access (Models)
- `models.py` - ORM SQLAlchemy
- `forms.py` - Validação de dados
- `validators.py` - Validadores customizados

### 5. Infrastructure
- `config.py` - Configuração centralizada
- `security_utils.py` - Segurança e sanitização
- `seguranca.env` - Variáveis secretas

## Fluxo de Requisição

```
1. Request chega em app.py
2. Flask roteia para rota apropriada
3. Se precisa auth: decorador valida
4. Form é instanciado e validado
5. Models retornam dados do banco
6. Template renderiza com dados
7. Response retorna ao cliente
```

## Banco de Dados (SQLite)

### Tabelas Principais
- `users` - Usuários do sistema
- `operadores` - Operadores/jogadores
- `equipes` - Times
- `partidas` - Partidas disputadas
- `partida_participantes` - Relação partida ↔ operador
- `vendas` - Histórico de vendas
- `estoque` - Gestão de inventário
- `logs` - Auditoria

### Relacionamentos
```
User 1 ← N Operador
Operador N ← M Equipe
Equipe 1 ← N Partida
Partida N ← M PartidaParticipante
```

## Configuração

### Ambiente
```
FLASK_ENV=development (local) ou production (Railway)
DEBUG=True (dev) ou False (prod)
SECRET_KEY=<gerado automaticamente>
```

### Variáveis em seguranca.env
```
SECRET_KEY
FLASK_ENV
LOG_LEVEL
```

## Deploy

### Local
```bash
python run.py
```

### Production (Railway)
1. Conecta GitHub
2. Detecta `Procfile`
3. Instala dependências
4. Roda: `gunicorn --bind 0.0.0.0:$PORT app:app`

## Segurança de Arquivos

### Protegidos (não commitar)
- `seguranca.env` - Variáveis secretas
- `/instance/*` - Banco de dados
- `/logs/*` - Arquivos de log
- `.venv/` - Virtual environment

### Ignorados no Git (.gitignore)
- `__pycache__/`
- `*.pyc`
- `.venv/`
- `instance/`
- `seguranca.env`

