# 🚀 GUIA DE INICIALIZAÇÃO - BATTLEZONE SEGURO

## 1️⃣ Primeira Vez? Execute:

```bash
# Ativar ambiente virtual
.\.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# IMPORTANTE: Criar/atualizar seguranca.env
# (O arquivo já foi criado com SECRET_KEY gerada)

# Iniciar servidor
python run.py
```

## 2️⃣ O que vai acontecer na primeira execução:

```
✅ Banco de dados criado
✅ Admin criado com senha aleatória
✅ ADMIN_CREDENTIALS.json gerado (GUARDE ESSA SENHA!)
✅ Servidor started em http://localhost:5000
```

## 3️⃣ Acessar o sistema:

```
URL: http://localhost:5000
Usuário: admin
Senha: (verifique em ADMIN_CREDENTIALS.json)
```

## 4️⃣ IMPORTANTE: Deletar ADMIN_CREDENTIALS.json

**Após confirmar que conseguiu logar com sucesso:**
```bash
del ADMIN_CREDENTIALS.json
```

ou no PowerShell:
```powershell
Remove-Item ADMIN_CREDENTIALS.json
```

## 5️⃣ Customizações Necessárias

Edite `seguranca.env`:

```env
# Seu email real (para notificações)
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=senha-especifica-do-app

# Logo que for produção (com domínio + HTTPS)
FLASK_ENV=production
DEBUG=false
```

## ⚠️ SEGREDOS DO ARQUIVO seguranca.env

- ✅ **NUNCA** commit no Git
- ✅ **NUNCA** compartilhe com ninguém
- ✅ **NUNCA** deixe em repositórios públicos
- ✅ **NUNCA** hardcode em código
- ✅ **Sempre** use variáveis de ambiente

---

## 🔍 VERIFICAR SE ESTÁ FUNCIONANDO

### 1. Headers de Segurança
```bash
curl -I http://localhost:5000
```
Você deve ver:
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Content-Security-Policy: ...
```

### 2. Rate Limiting
Acesse `/test-upload` 6 vezes em menos de 1 minuto:
```
5ª vez: ✅ Funciona
6ª vez: ❌ "429 Too Many Requests"
```

### 3. Validação de Upload
Tente fazer upload de arquivo suspeito:
```
fake.exe.png → ❌ Rejeitado
foto.jpg → ✅ Aceito
```

---

## 📊 ESTRUTURA DE ARQUIVOS IMPORTANTES

```
battlezone_flask/
├── app.py                # App principal (AGORA SEGURO)
├── config.py             # ✨ NOVO - Configuração centralizada
├── security_utils.py     # ✨ NOVO - Funções de segurança
├── run.py               # ✨ ATUALIZADO - Sem senha hardcoded
├── seguranca.env        # ✨ ATUALIZADO - Com SECRET_KEY real
├── seguranca.env.example # ✨ NOVO - Template
├── .gitignore           # ✨ NOVO - Proteção de Git
├── SECURITY.md          # ✨ NOVO - Documentação
├── DEPLOYMENT.md        # ✨ NOVO - Este arquivo
└── requirements.txt     # ✨ ATUALIZADO - Novas dependências
```

---

## 🆘 PROBLEMAS COMUNS

### ❌ "SECRET_KEY não configurada"
**Solução**: Copie seguranca.env.example para seguranca.env

### ❌ "ModuleNotFoundError: No module named 'flask_talisman'"  
**Solução**: Execute `pip install -r requirements.txt`

### ❌ "Port 5000 already in use"
**Solução**: Feche outro Flask rodando, ou mude a porta em run.py

### ❌ "Database locked"
**Solução**: Feche outros processos Python, ou delete `instance/database.db` e recrie

---

## 🎯 PRÓXIMAS ETAPAS (Depois de testar)

1. **Adicionar 2FA** (autenticação de dois fatores)
2. **Configurar Fail2ban** (bloquear IPs agressivos)
3. **Setup HTTPS** (quando tiver domínio)
4. **Monitoramento Sentry** (alertas de erro)

---

## ✅ CHECKLIST PRÉ-PRODUÇÃO

- [ ] Todos os testes passaram?
- [ ] Tentou fazer upload de arquivo malicioso?
- [ ] Rate limiting está funcionando?
- [ ] ADMIN_CREDENTIALS.json foi deletado?
- [ ] Email está configurado em seguranca.env?
- [ ] Fez backup do banco de dados?

---

**Tudo pronto para rodar!** 🚀
