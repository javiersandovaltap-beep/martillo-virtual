#!/usr/bin/env bash
# fase1.5_fix_f841_retry.sh - Revierte test_backfill.py (fix anterior incorrecto)
# y aplica el fix F841 SOLO a la primera ocurrencia real (linea ~18).
# test_views.py NO se toca: ya quedo bien en el intento anterior.

echo "=== Fase 1.5: Retry fix F841 (test_backfill.py unicamente) ==="
echo ""

echo "--- Revirtiendo test_backfill.py al estado del ultimo commit ---"
git checkout -- subastas/tests/test_backfill.py
echo "[OK] revertido"
echo ""

echo "--- Aplicando fix SOLO a la primera ocurrencia en el archivo ---"
# El rango 0,/patron/ hace que sed reemplace unicamente la PRIMERA
# coincidencia en todo el archivo, no todas.
sed -i '0,/        s = Subasta.objects.create(/{s/        s = Subasta.objects.create(/        Subasta.objects.create(/}' subastas/tests/test_backfill.py

echo ""
echo "=== Diff generado (test_backfill.py) ==="
git diff subastas/tests/test_backfill.py

echo ""
echo "=== ruff check sobre test_backfill.py y test_views.py ==="
ruff check subastas/tests/test_backfill.py subastas/tests/test_views.py

echo ""
echo "=== pytest completo (Layer 2b) ==="
pytest --cov=subastas --cov-report=term-missing

echo ""
echo "=== Script terminado. Si todo OK arriba (0 F821, 125 passed), corre: ==="
echo "  git add -A"
echo "  git commit -m \"fix: remove unused local variables flagged by ruff (F841)\""
