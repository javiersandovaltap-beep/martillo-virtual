#!/usr/bin/env bash
# fase1.5_fix_f403_f405.sh - Marca F403/F405 intencionales con noqa explicito
# (star imports del split de settings, D01-D04 en ALTERNATIVES.md)

echo "=== Fase 1.5: Fix F403/F405 (noqa explicito, sin refactor) ==="
echo ""

DIRTY=$(git status --porcelain --untracked-files=no)

if [ -n "$DIRTY" ]; then
    echo "AVISO: hay cambios sin commitear en archivos ya trackeados:"
    echo "$DIRTY"
    echo "Revisa antes de continuar. El script NO va a aplicar cambios."
else
    echo "[OK] no hay cambios pendientes en archivos trackeados, aplicando fixes"

    sed -i 's/    from \.production import \*$/    from .production import *  # noqa: F403/' config/settings/__init__.py
    sed -i 's/    from \.development import \*$/    from .development import *  # noqa: F403/' config/settings/__init__.py
    sed -i 's/"NAME": BASE_DIR \/ "db\.sqlite3",$/"NAME": BASE_DIR \/ "db.sqlite3",  # noqa: F405/' config/settings/development.py

    echo ""
    echo "=== Diff generado ==="
    git diff config/settings/__init__.py config/settings/development.py

    echo ""
    echo "=== ruff check completo (debe dar 0 hallazgos) ==="
    ruff check .

    echo ""
    echo "=== pytest completo (Layer 2b) ==="
    pytest --cov=subastas --cov-report=term-missing
fi

echo ""
echo "=== Script terminado. Si todo OK arriba (0 findings, 125 passed), corre: ==="
echo "  git add -A"
echo "  git commit -m \"chore: mark intentional settings star imports with explicit noqa\""
