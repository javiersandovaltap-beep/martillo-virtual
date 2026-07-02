"""
Tests for subastas.management.commands.cerrar_subastas.

Covers:
- --dry-run flag (no changes applied)
- Real run closes expired subastas
- Audit trail output
- No-op when no expired subastas
"""
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from subastas.models import Subasta


class TestCerrarSubastasCommand:
    def test_dry_run_does_not_modify_db(self, db, subasta_expirada):
        """--dry-run should NOT close subastas"""
        out = StringIO()
        call_command('cerrar_subastas', '--dry-run', stdout=out)
        subasta_expirada.refresh_from_db()
        assert subasta_expirada.estado == Subasta.Estado.ACTIVA  # Still active
        assert '[DRY RUN]' in out.getvalue()

    def test_dry_run_lists_expiradas(self, db, subasta_expirada):
        """--dry-run should list which subastas would be closed"""
        out = StringIO()
        call_command('cerrar_subastas', '--dry-run', stdout=out)
        output = out.getvalue()
        assert 'Test Subasta Expirada' in output
        assert '1 subasta(s) expirada(s) se cerrarian' in output

    def test_real_run_closes_expiradas(self, db, subasta_expirada):
        """Real run should close expired subastas"""
        out = StringIO()
        call_command('cerrar_subastas', stdout=out)
        subasta_expirada.refresh_from_db()
        assert subasta_expirada.estado == Subasta.Estado.CERRADA
        assert '1 subasta(s) cerrada(s) correctamente' in out.getvalue()

    def test_real_run_lists_closed_subastas(self, db, subasta_expirada):
        """Real run should list closed subastas (audit trail)"""
        out = StringIO()
        call_command('cerrar_subastas', stdout=out)
        output = out.getvalue()
        assert 'Subastas cerradas:' in output
        assert 'Test Subasta Expirada' in output

    def test_no_expiradas_reports_nothing_to_close(self, db, subasta_activa):
        """When no expired subastas, command reports it"""
        out = StringIO()
        call_command('cerrar_subastas', stdout=out)
        output = out.getvalue()
        assert 'No hay subastas expiradas que cerrar' in output

    def test_only_activa_expiradas_closed(self, db, vendedor):
        """Only estado=activa with fecha_cierre past should be closed.
        estado=cerrada subastas should NOT be touched (already closed)."""
        # Already closed subasta with past fecha_cierre
        s_closed = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Already Closed',
            descripcion='d',
            precio_inicial=100,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=5),
        )
        # Active subasta with past fecha_cierre (should be closed)
        s_expirada = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Expirada Active',
            descripcion='d',
            precio_inicial=100,
            estado=Subasta.Estado.ACTIVA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        # Active subasta with future fecha_cierre (should NOT be closed)
        s_active = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Still Active',
            descripcion='d',
            precio_inicial=100,
            estado=Subasta.Estado.ACTIVA,
            fecha_cierre=timezone.now() + timedelta(days=5),
        )

        out = StringIO()
        call_command('cerrar_subastas', stdout=out)

        s_closed.refresh_from_db()
        s_expirada.refresh_from_db()
        s_active.refresh_from_db()

        assert s_closed.estado == Subasta.Estado.CERRADA  # Unchanged
        assert s_expirada.estado == Subasta.Estado.CERRADA  # Closed
        assert s_active.estado == Subasta.Estado.ACTIVA  # Unchanged

    def test_multiple_expiradas_closed_in_batch(self, db, vendedor):
        """Multiple expired subastas closed in 1 query (.update())"""
        # Create 3 expired subastas
        for i in range(3):
            Subasta.objects.create(
                vendedor=vendedor,
                titulo=f'Expirada {i}',
                descripcion='d',
                precio_inicial=100,
                estado=Subasta.Estado.ACTIVA,
                fecha_cierre=timezone.now() - timedelta(days=i+1),
            )

        out = StringIO()
        call_command('cerrar_subastas', stdout=out)
        output = out.getvalue()
        assert '3 subasta(s) cerrada(s) correctamente' in output

        # Verify all 3 are now closed
        assert Subasta.objects.filter(estado=Subasta.Estado.CERRADA, titulo__startswith='Expirada').count() == 3
