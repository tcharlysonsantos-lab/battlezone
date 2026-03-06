# ✉️ GUIA DE CORREÇÃO: Email Não Funciona no Railway

## 🎯 PROBLEMA IDENTIFICADO

- ✅ Funciona localmente (localhost)
- ❌ Não funciona no Railway em produção

**Causa raiz:** Variáveis de ambiente de email NÃO foram configuradas no dashboard do Railway.

---

## 🔧 SOLUÇÃO PASSO A PASSO

### **PASSO 1: Gerar Senha de Aplicativo do Gmail**

O Gmail NÃO aceita sua senha real. Você precisa de uma "Senha de Aplicativo":

1. ✅ Acesse: **https://myaccount.google.com**
2. ✅ Ative **"Verificação em duas etapas"** (se não estiver ativada)
3. ✅ Vá para: **"Segurança"** → **"Senhas de aplicativos"**
4. ✅ Selecione: **App = Mail**, **Device = Windows** (ou seu OS)
5. ✅ Google gerará uma senha de 16 caracteres (ex: `abcd efgh ijkl mnop`)
6. ✅ **COPIE A SENHA** (sem os espaços): `abcdefghijklmnop`

### **PASSO 2: Configurar Variáveis no Dashboard Railway**

1. ✅ Acesse seu projeto no **Railway.app**
2. ✅ Vá para: **Settings** → **Environment**
3. ✅ Clique em **"New Variable"** e adicione:

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app-16-chars
```

**IMPORTANTE:**
- `MAIL_USERNAME`: Use seu email COMPLETO do Gmail
- `MAIL_PASSWORD`: Cole a senha de 16 caracteres SEM ESPAÇOS
- Não use aspas nas variáveis

### **PASSO 3: Fazer Deploy**

1. ✅ No Railway, clique em **"Deploy"** para redeployar a aplicação
2. ✅ Ou faça um push no Git para triggerar build automático:
   ```bash
   git add .
   git commit -m "Fix: Email configuration for Railway"
   git push
   ```

---

## ✅ VALIDAÇÃO

### **Testar Email em Produção**

Após deploy, teste se está funcionando:

1. **Endpoint de Health Check:**
   ```
   https://seu-app.railway.app/auth/health/email
   ```
   
   Deve retornar:
   ```json
   {
     "status": "healthy",
     "service": "email",
     "is_initialized": true,
     "config_valid": true,
     "message": "✅ Configuração de email válida"
   }
   ```

2. **Teste Real - Reset de Senha:**
   - Acesse: `https://seu-app.railway.app/auth/esqueci-senha`
   - Digite um email cadastrado
   - Verifique se o email chega (pode levar até 2 minutos)

### **Se ainda não funcionar:**

#### 🔍 Debug 1: Verificar Logs no Railway
```bash
# No terminal do Railway ou via dashboard
# Procurar por mensagens como:
# [🔍] Saúde Email: 
# [✅] Email service initialized successfully
# [🚨] Configuração de email inválida
```

#### 🔍 Debug 2: Verificar Credenciais
```bash
# Teste fora do Railway com Python:
import smtplib
from email.mime.text import MIMEText

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('seu-email@gmail.com', 'sua-senha-de-app-16-chars')
    print("✅ Autenticação bem-sucedida!")
    server.quit()
except Exception as e:
    print(f"❌ Erro: {e}")
```

#### 🔍 Debug 3: Logs da Aplicação
No Railway, vá para **"Logs"** e procure por:
- `[🚨 ERRO]` - Erro ao enviar email
- `[⚠️]` - Aviso de configuração
- `[✅]` - Email enviado com sucesso

---

## 🚨 PROBLEMAS COMUNS

### ❌ "MAIL_USERNAME inválido ou não configurado"
**Solução:** Certifique-se que preencheu `MAIL_USERNAME` no Railway com seu email real

### ❌ "SMTPAuthenticationError"
**Solução:** 
- [ ] Verifique se a "Senha de Aplicativo" está correta (sem espaços)
- [ ] Verifique se 2FA está ativado na conta Gmail
- [ ] Tente regenerar a "Senha de Aplicativo"

### ❌ "Connection refused" ou "Connection timeout"
**Solução:**
- [ ] Verifique se `MAIL_SERVER=smtp.gmail.com` está correto
- [ ] Verifique se `MAIL_PORT=587` está correto
- [ ] Verifique se `MAIL_USE_TLS=true` está correto
- [ ] Railway pode estar bloqueando porta 587 (contate suporte)

### ❌ Email "não iniciado" no health check
**Solução:**
- [ ] Variáveis `MAIL_*` podem estar vazias no Railway
- [ ] Redeploy a aplicação após adicionar as variáveis

---

## 📋 CHECKLIST FINAL

- [ ] Senha de Aplicativo gerada no Gmail
- [ ] Variáveis adicionadas no Railway
- [ ] Aplicação feita deploy
- [ ] Health check retorna `status: "healthy"`
- [ ] Email de reset de senha é recebido em até 2 minutos
- [ ] Usuário consegue resetar senha com sucesso

---

## 🔒 SEGURANÇA

⚠️ **NUNCA** commit `seguranca.env` com credenciais reais no Git!

```bash
# Gitignore (já deve estar configurado)
seguranca.env      # Arquivo local com credenciais
RAILWAY_DEPLOYMENT.env  # Template para produção
```

Se as credenciais forem expostas acidentalmente:

1. ✅ Regenere a "Senha de Aplicativo" no Gmail
2. ✅ Atualize a variável `MAIL_PASSWORD` no Railway
3. ✅ Redeploy
4. ✅ Revogue acesso se necessário

---

## 📞 SUPORTE

Se continuar com problemas:

1. Verifique os logs no Railway
2. Teste com `MAIL_DEBUG=true` em desenvolvimento
3. Contate suporte do Gmail ou Railway

---

**✅ Última atualização:** Março 2026
