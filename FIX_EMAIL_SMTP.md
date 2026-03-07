# INSTRUÇÕES PARA FIXA EMAIL NO RAILWAY

## 1. ATIVAR 2FA NO GMAIL
Acesse: https://myaccount.google.com/security/signinoptions/two-step-verification
- Clique em "Iniciar verificação em 2 etapas"
- Siga as instruções

## 2. GERAR APP PASSWORD (não é a senha normal!)
Acesse: https://myaccount.google.com/apppasswords
- Selecione: "Mail" e "Windows Computer"
- Clique: "Gerar"
- COPIE a senha que aparecer (formato: 16 caracteres com espaços)

## 3. ATUALIZAR RAILWAY
Dashboard: https://dashboard.railway.app/
1. Clique no projeto "battlezone"
2. Clique em "Variables"
3. Procure por "MAIL_PASSWORD"
4. Cole a senha gerada do passo 2 (remova os espaços se tiver)

## VARIÁVEIS ESPERADAS EM RAILWAY:
- MAIL_SERVER: smtp.gmail.com
- MAIL_PORT: 587
- MAIL_USE_TLS: true
- MAIL_USERNAME: campobattlezoneairsoft@gmail.com
- MAIL_PASSWORD: (16 caracteres - App Password, NÃO a senha do Gmail!)

## VERIFICAÇÃO RÁPIDA:
Depois de atualizar MAIL_PASSWORD em Railway:
1. Aguarde 2-3 minutos
2. Abra: https://battlezone-production.up.railway.app/auth/esqueci-senha
3. Digite: tcharlysonf.f@gmail.com
4. Clique: "Enviar Link de Recuperação"
5. Verifique seu email em ~10 segundos
