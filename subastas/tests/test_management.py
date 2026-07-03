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
from django.contrib.auth.models import User
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
        assert '1 subasta(s) cerrada(s)' in out.getvalue() and 'sin ofertas' in out.getvalue()

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
        assert '3 subasta(s) cerrada(s)' in output and 'sin ofertas' in output

        # Verify all 3 are now closed
        assert Subasta.objects.filter(estado=Subasta.Estado.CERRADA, titulo__startswith='Expirada').count() == 3

# ============================================================================
# cerrar_subastas sets ganador (Commit 4)
# ============================================================================

class TestCerrarSubastasGanador:
    def test_subasta_with_ofertas_sets_ganador(self, db, vendedor, ofertante):
        """Subasta with ofertas should set ganador to highest ofertante."""
        from datetime import timedelta
        from django.utils import timezone
        from subastas.models import Subasta, Oferta

        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Expirada Con Ofertas',
            descripcion='d',
            precio_inicial=1000,
            estado=Subasta.Estado.ACTIVA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        # 3 ofertas from different users, different montos
        other_user = User.objects.create_user(username='other_bidder', password='x')
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=1200)
        Oferta.objects.create(subasta=s, ofertante=other_user, monto=1500)
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=1300)

        from io import StringIO
        from django.core.management import call_command
        call_command('cerrar_subastas', stdout=StringIO())

        s.refresh_from_db()
        assert s.estado == Subasta.Estado.CERRADA
        assert s.ganador == other_user  # highest monto 1500

    def test_subasta_without_ofertas_no_ganador(self, db, vendedor):
        """Subasta without ofertas should close without ganador (ganador=None)."""
        from datetime import timedelta
        from django.utils import timezone
        from subastas.models import Subasta

        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Expirada Sin Ofertas',
            descripcion='d',
            precio_inicial=1000,
            estado=Subasta.Estado.ACTIVA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )

        from io import StringIO
        from django.core.management import call_command
        call_command('cerrar_subastas', stdout=StringIO())

        s.refresh_from_db()
        assert s.estado == Subasta.Estado.CERRADA
        assert s.ganador is None

    def test_ganador_desempate_by_creado_en(self, db, vendedor):
        """When 2 ofertas have same monto, earliest creado_en wins."""
        from datetime import timedelta
        from django.utils import timezone
        from subastas.models import Subasta, Oferta
        from django.contrib.auth.models import User

        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Empate',
            descripcion='d',
            precio_inicial=1000,
            estado=Subasta.Estado.ACTIVA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        user_a = User.objects.create_user(username='user_a', password='x')
        user_b = User.objects.create_user(username='user_b', password='x')
        # Both offer 1500
        Oferta.objects.create(subasta=s, ofertante=user_a, monto=1500)
        # Small delay to ensure different creado_en
        import time
        time.sleep(0.01)
        Oferta.objects.create(subasta=s, ofertante=user_b, monto=1500)

        from io import StringIO
        from django.core.management import call_command
        call_command('cerrar_subastas', stdout=StringIO())

        s.refresh_from_db()
        assert s.ganador == user_a  # earliest creado_en wins

    def test_dry_run_shows_ganador_info(self, db, vendedor, ofertante):
        """--dry-run output should show ganador info for subastas with ofertas."""
        from datetime import timedelta
        from django.utils import timezone
        from subastas.models import Subasta, Oferta
        from io import StringIO
        from django.core.management import call_command

        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Dry Run Test',
            descripcion='d',
            precio_inicial=1000,
            estado=Subasta.Estado.ACTIVA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=1500)

        out = StringIO()
        call_command('cerrar_subastas', '--dry-run', stdout=out)
        output = out.getvalue()
        assert 'ganador' in output.lower()
        assert 'test_ofertante' in output
        assert '$1500' in output or '1500' in output

    def test_audit_trail_shows_ganador(self, db, vendedor, ofertante):
        """Real run audit trail should show ganador info."""
        from datetime import timedelta
        from django.utils import timezone
        from subastas.models import Subasta, Oferta
        from io import StringIO
        from django.core.management import call_command

        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Audit Trail Test',
            descripcion='d',
            precio_inicial=1000,
            estado=Subasta.Estado.ACTIVA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=1500)

        out = StringIO()
        call_command('cerrar_subastas', stdout=out)
        output = out.getvalue()
        assert '1 con ganador' in output
        assert 'Audit Trail Test' in output
        assert 'test_ofertante' in output
