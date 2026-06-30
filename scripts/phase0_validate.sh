#!/usr/bin/env bash
# phase0_validate.sh - Valida Fase 0 y genera output para pegar al chat senior
# Ejecutar DESPUES de phase0_main.sh + createsuperuser
# Asegurate de tener venv activado: source venv/Scripts/activate (Windows) o source venv/bin/activate (Linux)

echo "=== VALIDACION FASE 0 ==="
echo ""

echo "--- Python version ---"
python --version
echo ""

echo "--- Django version ---"
python -c "import django; print(django.get_version())"
echo ""

echo "--- venv activado? ---"
which python
echo ""

echo "--- Layer 1: check ---"
python manage.py check 2>&1
echo ""

echo "--- showmigrations ---"
python manage.py showmigrations 2>&1
echo ""

echo "--- DB tablas y counts ---"
python -c "
import sqlite3, os
db_path = 'db.sqlite3'
if not os.path.exists(db_path):
    print('  db.sqlite3 NO EXISTE')
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT name FROM sqlite_master WHERE type=\"table\" ORDER BY name')
    tables = [r[0] for r in cur.fetchall()]
    print(f'  Tablas ({len(tables)}):')
    for t in tables:
        cur.execute(f'SELECT COUNT(*) FROM \"{t}\"')
        n = cur.fetchone()[0]
        print(f'    {t}: {n} rows')
    print()
    print('  Usuarios:')
    cur.execute('SELECT id, username, email, is_staff, is_superuser FROM auth_user')
    for r in cur.fetchall():
        print(f'    {r}')
    print()
    print('  Subastas (titulo, estado, fecha_cierre):')
    cur.execute('SELECT titulo, estado, fecha_cierre FROM subastas_subasta ORDER BY creado_en')
    for r in cur.fetchall():
        print(f'    {r}')
    conn.close()
" 2>&1
echo ""

echo "--- Git log ---"
git log --oneline 2>&1
echo ""

echo "--- Git tag ---"
git tag 2>&1
echo ""

echo "--- Archivos operacionales ---"
ls -la SESSION_STATE.md CLAUDE.md AGENTS.md ALTERNATIVES.md 2>&1
echo ""

echo "--- .claude/agents/ ---"
ls -la .claude/agents/ 2>&1
echo ""

echo "--- SESSION_STATE.md (primeras 40 lineas) ---"
head -40 SESSION_STATE.md 2>&1
echo ""

echo "--- .env (sin SECRET_KEY) ---"
grep -v SECRET_KEY .env 2>&1
echo ""

echo "--- requirements.txt ---"
cat requirements.txt 2>&1
echo ""

echo "--- seed_data.py fix verificado ---"
grep -n "Estado.ACTIVA\|ESTADO_ACTIVA" subastas/management/commands/seed_data.py 2>&1
echo ""

echo "=== FIN VALIDACION ==="
