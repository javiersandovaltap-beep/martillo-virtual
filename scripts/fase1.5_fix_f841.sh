#!/usr/bin/env bash
# fase1.5_fix_f841.sh - Elimina 3 asignaciones a variables locales sin usar (F841)

echo "=== Fase 1.5: Fix F841 (3 unused local variables) ==="
echo ""

DIRTY=$(git status --porcelain --untracked-files=no)

if [ -n "$DIRTY" ]; then
    echo "AVISO: hay cambios sin commitear en archivos ya trackeados:"
    echo "$DIRTY"
    echo "Revisa antes de continuar. El script NO va a aplicar cambios."
else
    echo "[OK] no hay cambios pendientes en archivos trackeados, aplicando fixes"

    sed -i "s/        s = Subasta.objects.create(/        Subasta.objects.create(/" subastas/tests/test_backfill.py
    sed -i "s/        other_subasta = Subasta.objects.create(/        Subasta.objects.create(/" subastas/tests/test_views.py
    sed -i "s/        my_subasta = Subasta.objects.create(/        Subasta.objects.create(/" subastas/tests/test_views.py

    echo ""
    echo "=== Diff generado ==="
    git diff subastas/tests/test_backfill.py subastas/tests/test_views.py

    echo ""
    echo "=== ruff check sobre los 2 archivos ==="
    ruff check subastas/tests/test_backfill.py subastas/tests/test_views.py

    echo ""
    echo "=== pytest completo (Layer 2b) ==="
    pytest --cov=subastas --cov-report=term-missing
fi

echo ""
echo "=== Script terminado. Si todo OK arriba, corre manualmente: ==="
echo "  git add -A"
echo "  git commit -m \"fix: remove unused local variables flagged by ruff (F841)\""
