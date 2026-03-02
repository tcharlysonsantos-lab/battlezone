# 📚 Documentação - BattleZone Flask

Guias completos e referência técnica.

---

## 📖 Índice

### 🏗️ **[Infrastructure Guide](../infrastructure/README.md)**
**[LEIA PRIMEIRO]** - Deploy, NGROK, Railway, Database  
→ [NGROK Setup](../infrastructure/ngrok/README.md)  
→ [Railway Deploy](../infrastructure/railway/README.md)  
→ [Database Management](../infrastructure/database/README.md)

---

## 🔧 **[ARQUITETURA.md](ARQUITETURA.md)**
Visão técnica completa do sistema:
- Estrutura de pastas
- MVC pattern
- Models e relacionamentos
- Fluxo de autenticação
- Rotas e endpoints
- Database schema

---

## 🔒 **[SEGURANCA.md](SEGURANCA.md)**
Implementação de segurança:
- CSRF Protection
- 2FA com TOTP
- Rate Limiting
- Password hashing (bcrypt)
- Security Headers (Talisman)
- SQL Injection Prevention
- Access Control (RBAC)
- Tokens e sessões

---

## 📊 **[SINCRONIZACAO_STATS.md](SINCRONIZACAO_STATS.md)**
Sistema de sincronização de estatísticas:
- Arquitetura de sync
- Eventos e listeners
- Atualização de placar
- Histórico de partidas
- Reports de desempenho

---

## 🚀 Quick Links

| Documento | Propósito | Tempo de leitura |
|-----------|----------|-----------------|
| [Infrastructure](../infrastructure/README.md) | Deploy & sistema | 10 min |
| [ARQUITETURA.md](ARQUITETURA.md) | Código da aplicação | 20 min |
| [SEGURANCA.md](SEGURANCA.md) | Implementação segura | 15 min |
| [SINCRONIZACAO_STATS.md](SINCRONIZACAO_STATS.md) | Sync de dados | 10 min |

---

## 📂 Estrutura de Documentação

```
docs/
├── README.md                  ← Você está aqui
├── ARQUITETURA.md            ← Design técnico
├── SEGURANCA.md              ← Segurança
├── SINCRONIZACAO_STATS.md    ← Sync de dados
```

---

## 🎯 Por Onde Começar?

### 👤 **Eu sou usuário final**
→ Leia [Infrastructure Guide](../infrastructure/README.md)

### 👨‍💻 **Eu sou desenvolvedor**
→ Leia [ARQUITETURA.md](ARQUITETURA.md) depois [SEGURANCA.md](SEGURANCA.md)

### 🔐 **Eu preciso de segurança**
→ Leia [SEGURANCA.md](SEGURANCA.md)

### 🚀 **Eu quero fazer deploy**
→ Leia [Infrastructure Guide](../infrastructure/README.md)

### 📊 **Eu preciso sincronizar dados**
→ Leia [SINCRONIZACAO_STATS.md](SINCRONIZACAO_STATS.md)

---

## 🔗 Sistema de Cross-Links

Todos os documentos têm links entre si. Você pode:
- Ler de forma linear
- Pular para seções específicas
- Voltar ao índice usando breadcrumbs

---

## 📝 Convenções

- 🚀 = Início rápido
- ⚠️ = Aviso importante
- 💡 = Dica
- ❌ = Problema comum
- ✅ = Confirmação de sucesso
- 🔗 = Link externo

---

## 🆘 Troubleshooting

Se você tem um problema:

1. **Erro durante deploy?** → [Infrastructure](../infrastructure/README.md)
2. **Erro de código?** → [ARQUITETURA.md](ARQUITETURA.md)
3. **Erro de segurança?** → [SEGURANCA.md](SEGURANCA.md)
4. **Erro de dados?** → [SINCRONIZACAO_STATS.md](SINCRONIZACAO_STATS.md)

---

## 💬 Perguntas Frequentes

**P: Onde começo?**  
R: Se é primeira vez, leia [Infrastructure](../infrastructure/README.md).

**P: Como fazer deploy?**  
R: [infrastructure/railway/README.md](../infrastructure/railway/README.md)

**P: Qual é a estrutura do código?**  
R: [ARQUITETURA.md](ARQUITETURA.md)

**P: Como funciona a autenticação?**  
R: [SEGURANCA.md](SEGURANCA.md) - seção "Authentication Flow"

**P: Como sincronizar estatísticas?**  
R: [SINCRONIZACAO_STATS.md](SINCRONIZACAO_STATS.md)

---

## 📚 Recursos Externos

- [Flask Documentation](https://flask.palletsprojects.com)
- [SQLAlchemy ORM](https://www.sqlalchemy.org)
- [WTForms](https://wtforms.readthedocs.io)
- [Flask-Login](https://flask-login.readthedocs.io)
- [Werkzeug Security](https://werkzeug.palletsprojects.com/security/)

---

## 🔄 Atualização de Documentação

Esta documentação foi atualizada em **2026-03-02**

**Próximas atualizações:**
- [ ] Guia de testes unitários
- [ ] Guia de API REST
- [ ] Performance optimization guide
- [ ] Migration guide de SQLite para PostgreSQL

---

**Versão**: 3.1.3  
**Status**: Production Ready ✅
