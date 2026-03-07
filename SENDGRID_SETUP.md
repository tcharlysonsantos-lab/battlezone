# SendGrid Setup - Instruções Completas

## Por que migrar de SMTP para SendGrid?

**Problema Encontrado:**
- Railway planos Free/Hobby **bloqueiam conexões SMTP externas**
- Erro: `OSError: [Errno 101] Rede inacessível` (Network unreachable)
- Não é possível enviar emails via SMTP do Gmail/Outlook

**Solução:**
- Usar **SendGrid Email API** ao invés de SMTP
- SendGrid usa HTTP (não SMTP) - funciona em qualquer plano do Railway
- SendGrid é **GRÁTIS** até 100 emails/dia (plano muito suficiente)
- Recomendação oficial de: Railway, Render, Heroku, Fly.io, Vercel

---

## Passo 1: Criar Conta SendGrid (Grátis)

1. Acesse: https://sendgrid.com/free
2. Clique em **"Sign Up Free"**
3. Preencha o formulário:
   - **Email**: Use seu email pessoal
   - **Password**: Crie uma senha forte
   - **Company Name**: "BattleZone" ou seu nome
4. Clique em **"Create Account"**
5. Confirme seu email (SendGrid enviará um link de confirmação)

---

## Passo 2: Verificar Email (Sender Verification)

Para poder enviar emails, você precisa verificar seu email no SendGrid:

1. **Acesse:** https://app.sendgrid.com/settings/sender_auth/single_senders
2. Clique em **"Create New Sender"** (botão azul)
3. Preencha os dados:
   - **Name:** "BattleZone"
   - **Email Address:** O email que você usa (ex: seu-email@gmail.com)
   - **Company Name:** "Seu Nome da Empresa"
   - **Website:** "https://battlezone-production.up.railway.app" (sua app no Railway)
4. Clique em **"Create"**
5. SendGrid enviará um email para confirmar
6. **Abra seu email** e clique no link de confirmação SendGrid

**Aguarde 1-2 minutos** para o email chegar, depois confirme.

---

## Passo 3: Gerar API Key

1. **Acesse:** https://app.sendgrid.com/settings/api_keys
2. Clique em **"Create API Key"** (botão azul no topo direito)
3. Preencha:
   - **API Key Name:** "BattleZone Production" (ou outro nome descritivo)
   - **API Key Permissions:** Selecione apenas **"Mail Send"**
4. Clique em **"Create & View"** ou **"Create"**
5. **COPIE A CHAVE** que aparece (é mostrada apenas UMA VEZ!)

Formato da chave: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**⚠️ IMPORTANTE:** Salve essa chave em um lugar seguro (bloco de notas, 1Password, etc)

---

## Passo 4: Adicionar Variáveis de Ambiente no Railway

1. **Acesse seu projeto no Railway:** https://railway.app/project/YOUR_PROJECT_ID
2. Vá para **Settings** (engrenagem no topo)
3. Clique em **"Environment"** no menu lateral
4. **Adicione as variáveis:**

```
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MAIL_USERNAME=seu-email@gmail.com
```

5. Clique em **"Save"** (botão verde)

### Onde encontrar as informações:

- **SENDGRID_API_KEY**: A chave que você copiou no Passo 3
- **MAIL_USERNAME**: O email que você verificou no Passo 2

---

## Passo 5: Deploy (Automático)

Como você fez push do código, o Railway **redeploy automaticamente**:

1. Vá para **Deployments** no Railway
2. Você verá um novo deploy começando
3. **Aguarde** ~2-3 minutos para completar
4. Verifique o status: **ONLINE** (verde)

---

## Testando

Após o deploy:

1. **Acesse sua app:** https://battlezone-production.up.railway.app
2. Vá para **"Esqueci a Senha"**
3. Digite seu email (ex: seu-email@gmail.com)
4. Clique em **"Enviar"**
5. **NOVO:** Página redirecionará em < 1 segundo ✅
6. Verifique seu email (~30 segundos geralmente)
7. Clique no link de reset

---

## Monitorando Envios

### Ver logs de envio no SendGrid:

1. Acesse: https://app.sendgrid.com/email_activity
2. Você verá todos os emails enviados com status:
   - **Processed** ✅
   - **Delivered** ✅
   - **Opened** (se o usuário abrir)
   - **Bounced** ❌ (email inválido)
   - **Blocked** ❌ (problema de entrega)

### Ver logs no Railway:

1. Railway > Project > Deployments > Logs
2. Procure por:
   ```
   [OK] Email agendado para envio (async) via SendGrid
   [OK] Email enviado com sucesso! (Status: 202)
   ```

---

## Troubleshooting

### ❌ "Email service not initialized"
- Verifique se SENDGRID_API_KEY está em Railway > Settings > Environment
- Verifique se não tem espaços extras
- Re-deploy: `git push origin main`

### ❌ "SENDGRID_API_KEY inválida"
- Confirme a chave está correta (copie novamente)
- Confirme não tem espaços extras
- Gere uma nova chave se necessário

### ❌ "MAIL_USERNAME não verificado no SendGrid"
- Verifique o email em: https://app.sendgrid.com/settings/sender_auth/single_senders
- Confirme o email de verificação que SendGrid enviou
- Pode levar 5-10 minutos para propagar

### ❌ Email não chega na caixa de entrada (vai para Spam)
- Comum com NOVO domínio/email
- Configure SPF e DKIM (SendGrid oferece guia)
- Adicione sua app à lista de remetentes confiável do Gmail
- Teste novamente após 24 horas

### Aceite ser lido as respostas de email em logs:
```
[STDERR] Email enviado com sucesso! (Status: 202)
```

Status 202 = aceito para entrega (SendGrid vai entregar)

---

## Limites Free (SendGrid)

- **100 emails/dia** (suficiente!)
- **Sem limite de contatos**
- **APIs completas**
- Upgrade automático conforme necessário

---

## Links Rápidos

- **SendGrid Dashboard:** https://app.sendgrid.com
- **API Documentation:** https://docs.sendgrid.com/api-reference
- **Email Activity:** https://app.sendgrid.com/email_activity
- **Settings:** https://app.sendgrid.com/settings/api_keys

---

## Próximos Passos

Após setup do SendGrid, teste completo do "Esqueci a Senha":

1. ✅ Validação de email funciona (verde/vermelho)
2. ✅ Página não congela ao clicar "Enviar"
3. ✅ Email chega em ~30 segundos
4. ✅ Link no email funciona
5. ✅ Nova senha é aceita
6. ✅ Login com nova senha funciona

Se tudo passar, feature "Esqueci a Senha" está 100% operacional!

---

**Data:** Februar 26, 2026
**Por:** GitHub Copilot
**Status:** Produção Pronta
