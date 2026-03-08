# 🚀 RAILWAY DEPLOYMENT - QUICK VERIFICATION CHECKLIST

## POST-DEPLOY (After ~2 minutes)

### ✅ Step 1: Check Build Status
```
Railway Dashboard → Your App → Deployments
Should show: ✅ Success (green)
```

### ✅ Step 2: Check Logs for Database Initialization
```
Railway Dashboard → Logs (filter to latest)

Look for these messages in order:
1. [BATTLEZONE] Sistema de Gerenciamento de Airsoft
2. [DB] Inicializando banco de dados...
3. ➜ Chamando init_database() para validar...
4. [DB] ✓ Conexão estabelecida. Tabelas existentes: XX
5. [DB] ✅ Todas as 13 tabelas necessárias existem!

If you see message #5 → SUCCESS! ✅
```

### ✅ Step 3: Test Dashboard Loads
```bash
Open in browser:
https://your-railway-app-url/

If shows login page → Database working! ✅
If shows error → See troubleshooting below
```

### ✅ Step 4: Verify Database Tables
```bash
# If you can login to Railway SSH console:
railway run bash

# Inside console:
python

# Python shell:
from backend.models import db, Evento, Sorteio, Battlepass
result = db.session.execute("SELECT COUNT(*) FROM evento").fetchone()
print(f"Eventos table has: {result[0]} records")  # Should not error

# Type: exit() to exit Python
```

---

## 🔴 TROUBLESHOOTING

### Problem: Build fails immediately
**Solution:**
- Syntax error in Python files
- Check recent commits: `git log --oneline -5`
- Verify files weren't corrupted

### Problem: "Table doesn't exist" errors
**Solution:**
- Run: `git push origin main` (force redeploy)
- Wait 2 minutes for new build
- Check logs again for initialization messages

### Problem: App starts but won't respond
**Solution:**
- PostgreSQL service may be down
- Restart database from Railway dashboard
- Wait 1 minute then try again

### Problem: Connection refused / Database unreachable
**Solution:**
- Verify `DATABASE_URL` env var is set:
  - Railway Dashboard → Settings → Environment
  - Should contain: `postgresql://user:pass@host/dbname`
- If missing or wrong:
  - Delete current PostgreSQL service
  - Create new PostgreSQL service
  - Wait 5 minutes for service to start

---

## ⚡ QUICK FIXES

### Force rebuild if stuck:
```bash
git commit --allow-empty -m "chore: force redeploy"
git push origin main
```

### View detailed logs:
```bash
Railway Dashboard → Logs → Expand all → Search for "[DB]"
```

### Reset database (DELETES ALL DATA):
```
Railway Dashboard → Database → Settings → Delete Volume
Then: git push origin main
Railway will create new database from scratch
```

---

## 📊 SUCCESS CRITERIA

All of these should be TRUE:

- [ ] Build completes with ✅ Success
- [ ] Logs show: "[DB] ✅ Todas as 13 tabelas..."
- [ ] App URL responds (shows login page)
- [ ] No "table not found" errors
- [ ] Can login with admin credentials
- [ ] Dashboard shows Eventos section
- [ ] Dashboard shows Sorteios Realizados section
- [ ] Can create operador and user

---

## 📞 IF ALL ELSE FAILS

Last resort (will reset database):

1. Go to Railway Dashboard
2. Settings → Database service → Delete Volume
3. Wait 5 minutes
4. In terminal: `git commit --allow-empty -m "chore: full redeploy"`
5. Then: `git push origin main`
6. Railway will recreate everything from scratch

**This will delete all data**, but should fix initialization issues.

---

**Status:** All fixes deployed ✅
**Next Action:** Monitor Railway logs for ~2 minutes
**Expected Time to Fix:** 30-120 seconds after git push
