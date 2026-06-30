#!/usr/bin/env bash
# phase0_main.sh - Fase 0: Recovery + Migrations Audit
# Proyecto: MartilloVirtual (Django 6.0.3)
# Ejecutar desde la raiz del proyecto (donde esta manage.py)
# Shell: Git Bash en Windows, bash en Linux/Mac

set -e

# === Colores ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Fase 0: Recovery + Migrations Audit${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# === Verificar raiz del proyecto ===
if [ ! -f manage.py ]; then
    echo -e "${RED}ERROR: No se encontro manage.py${NC}"
    echo "Ejecuta este script desde la raiz del proyecto."
    exit 1
fi

PROJECT_ROOT=$(pwd)
echo -e "${BLUE}Project root: ${PROJECT_ROOT}${NC}"
echo ""

# === Paso 1: Limpieza ===
echo -e "${YELLOW}--- Paso 1: Limpieza de archivos stale ---${NC}"

if [ -d martillo_v3 ]; then
    echo "Eliminando martillo_v3/..."
    rm -rf martillo_v3
    echo -e "${GREEN}[OK] martillo_v3/ eliminado${NC}"
else
    echo -e "${GREEN}[OK] martillo_v3/ no existe${NC}"
fi

if [ -d venv ]; then
    echo "Eliminando venv/ viejo..."
    rm -rf venv
    echo -e "${GREEN}[OK] venv/ eliminado${NC}"
else
    echo -e "${GREEN}[OK] venv/ no existe${NC}"
fi

if [ -f db.sqlite3 ]; then
    echo "Eliminando db.sqlite3 viejo..."
    rm -f db.sqlite3
    echo -e "${GREEN}[OK] db.sqlite3 eliminado${NC}"
else
    echo -e "${GREEN}[OK] db.sqlite3 no existe${NC}"
fi

echo ""

# === Paso 2: Fix requirements.txt ===
echo -e "${YELLOW}--- Paso 2: Fix requirements.txt ---${NC}"

if grep -q "psycopg\[binary\]==3.2.4" requirements.txt; then
    echo "Actualizando psycopg 3.2.4 -> 3.3.3..."
    sed -i 's/psycopg\[binary\]==3.2.4/psycopg[binary]==3.3.3/' requirements.txt
    echo -e "${GREEN}[OK] requirements.txt actualizado${NC}"
else
    echo -e "${GREEN}[OK] requirements.txt no necesita fix${NC}"
fi

echo ""

# === Paso 3: Fix seed_data.py ===
echo -e "${YELLOW}--- Paso 3: Fix seed_data.py ---${NC}"

if grep -q "Subasta.ESTADO_ACTIVA" subastas/management/commands/seed_data.py; then
    echo "Fix Subasta.ESTADO_ACTIVA -> Subasta.Estado.ACTIVA..."
    sed -i 's/Subasta.ESTADO_ACTIVA/Subasta.Estado.ACTIVA/' subastas/management/commands/seed_data.py
    echo -e "${GREEN}[OK] seed_data.py fixeado${NC}"
else
    echo -e "${GREEN}[OK] seed_data.py no tiene el bug${NC}"
fi

echo ""

# === Paso 4: Crear venv ===
echo -e "${YELLOW}--- Paso 4: Crear venv ---${NC}"

PYTHON_BIN=""
for cmd in python python3 python3.14 python3.13 python3.12; do
    if command -v "$cmd" &> /dev/null; then
        PYTHON_BIN=$cmd
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}ERROR: Python no encontrado. Instala Python 3.12+${NC}"
    exit 1
fi

echo "Usando: $($PYTHON_BIN --version)"
$PYTHON_BIN -m venv venv
echo -e "${GREEN}[OK] venv creado${NC}"

# Activar venv
if [ -f venv/Scripts/activate ]; then
    source venv/Scripts/activate
elif [ -f venv/bin/activate ]; then
    source venv/bin/activate
else
    echo -e "${RED}ERROR: activate script no encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] venv activado: $(python --version)${NC}"
echo ""

# === Paso 5: pip install ===
echo -e "${YELLOW}--- Paso 5: pip install ---${NC}"

python -m pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}[OK] dependencias instaladas${NC}"

python -c "import django; print(f'Django {django.get_version()}')"
echo ""

# === Paso 6: Generar .env ===
echo -e "${YELLOW}--- Paso 6: Generar .env ---${NC}"

SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

cat > .env << EOF
DJANGO_ENV=development
SECRET_KEY=${SECRET_KEY}
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
EOF

echo -e "${GREEN}[OK] .env creado${NC}"
echo "SECRET_KEY = ${SECRET_KEY:0:10}... (truncada por seguridad)"
echo ""

# === Paso 7: Layer 1 ===
echo -e "${YELLOW}--- Paso 7: Layer 1 (check) ---${NC}"

python manage.py check
echo -e "${GREEN}[OK] Layer 1 pasado${NC}"
echo ""

# === Paso 8: Auditoria migraciones ===
echo -e "${YELLOW}--- Paso 8: Auditoria de migraciones ---${NC}"

echo "=== showmigrations ==="
python manage.py showmigrations
echo ""
echo "=== migrate --plan ==="
python manage.py migrate --plan
echo ""

# === Paso 9: Aplicar migraciones ===
echo -e "${YELLOW}--- Paso 9: Aplicar migraciones ---${NC}"

python manage.py migrate
echo -e "${GREEN}[OK] migraciones aplicadas${NC}"
echo ""

# === Paso 10: Seed data ===
echo -e "${YELLOW}--- Paso 10: Seed data ---${NC}"

python manage.py seed_data
echo -e "${GREEN}[OK] seed data creado${NC}"
echo ""

# === Paso 11: Git init + commit + tag ===
echo -e "${YELLOW}--- Paso 11: Git init + commit + tag ---${NC}"

if [ ! -d .git ]; then
    git init
    echo -e "${GREEN}[OK] git init${NC}"
else
    echo -e "${GREEN}[OK] .git ya existe${NC}"
fi

# Configurar user si no esta (para que commit funcione)
if ! git config user.email > /dev/null; then
    git config user.email "dev@martillovirtual.local"
    echo -e "${YELLOW}[WARN] git user.email no configurado, usando default${NC}"
fi
if ! git config user.name > /dev/null; then
    git config user.name "MartilloVirtual Dev"
    echo -e "${YELLOW}[WARN] git user.name no configurado, usando default${NC}"
fi

git add .
git commit -m "chore: Fase 0 baseline

- Eliminado martillo_v3/ (snapshot stale)
- Eliminado venv/ viejo (paths Windows)
- Fix requirements.txt: psycopg 3.2.4 -> 3.3.3
- Fix seed_data.py: Subasta.ESTADO_ACTIVA -> Subasta.Estado.ACTIVA
- Creado venv nuevo
- Generada nueva SECRET_KEY en .env
- Reset db.sqlite3, aplicadas migraciones
- Seed data (6 subastas, 1 user don_roberto)
- Archivos operacionales: SESSION_STATE.md, CLAUDE.md, AGENTS.md, ALTERNATIVES.md
- Subagents: .claude/agents/*.md (6 agents)

Tag: v0.1-stable" || echo -e "${YELLOW}[WARN] commit fallo (posiblemente sin cambios)${NC}"

git tag -f v0.1-stable
echo -e "${GREEN}[OK] tag v0.1-stable${NC}"
echo ""

# === Resumen ===
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Fase 0 completada${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Proximos pasos MANUALES:"
echo ""
echo "1. Crear superuser (interactivo):"
echo "   python manage.py createsuperuser"
echo "   (anotar username/password)"
echo ""
echo "2. Validar Layer 3 (opcional pero recomendado):"
echo "   python manage.py runserver"
echo "   (abrir http://127.0.0.1:8000/ en browser)"
echo "   (Ctrl+C para parar)"
echo ""
echo "3. Ejecutar script de validacion:"
echo "   bash scripts/phase0_validate.sh"
echo "   (pegar output al chat senior)"
