"""
Tests for backfill_ganadores command.
"""
from datetime import timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils import timezone

from subastas.models import Subasta, Oferta


class TestBackfillGanadores:
    def test_no_cerradas_sin_ganador_reports_consistent(self, db):
        """When no cerradas sin ganador, command reports DB consistente."""
        # Create a cerrada WITH ganador (already set)
        s = Subasta.objects.create(
            vendedor=__import__('django.contrib.auth.models', fromlist=['User']).User.objects.create_user('v', password='x'),
            titulo='Cerrada Con Ganador',
            descripcion='d',
            precio_inicial=100,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=1),
            ganador=__import__('django.contrib.auth.models', fromlist=['User']).User.objects.create_user('g', password='x'),
        )
        out = StringIO()
        call_command('backfill_ganadores', stdout=out)
        assert 'DB consistente' in out.getvalue()

    def test_dry_run_does_not_modify_db(self, db, vendedor, ofertante):
        """--dry-run should NOT modify DB."""
        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Cerrada Sin Ganador',
            descripcion='d',
            precio_inicial=100,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=150)

        out = StringIO()
        call_command('backfill_ganadores', '--dry-run', stdout=out)
        s.refresh_from_db()
        assert s.ganador is None  # Not modified
        assert '[DRY RUN]' in out.getvalue()

    def test_backfill_sets_ganador_for_cerrada_with_ofertas(self, db, vendedor, ofertante):
        """Backfill should set ganador for cerrada without ganador but with ofertas."""
        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Target',
            descripcion='d',
            precio_inicial=100,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=150)

        out = StringIO()
        call_command('backfill_ganadores', stdout=out)
        s.refresh_from_db()
        assert s.ganador == ofertante
        assert '1 subasta(s) actualizada(s)' in out.getvalue()

    def test_backfill_skips_cerrada_without_ofertas(self, db, vendedor):
        """Backfill should NOT set ganador for cerrada without ofertas (ganador stays None)."""
        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Sin Ofertas',
            descripcion='d',
            precio_inicial=100,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )

        out = StringIO()
        call_command('backfill_ganadores', stdout=out)
        s.refresh_from_db()
        assert s.ganador is None
        assert 'sin ofertas' in out.getvalue().lower()

    def test_backfill_idempotent(self, db, vendedor, ofertante):
        """Running backfill twice should be safe (second run reports consistente)."""
        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Idempotent',
            descripcion='d',
            precio_inicial=100,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=150)

        # First run: sets ganador
        call_command('backfill_ganadores', stdout=StringIO())
        s.refresh_from_db()
        assert s.ganador == ofertante

        # Second run: should report consistente (no changes)
        out2 = StringIO()
        call_command('backfill_ganadores', stdout=out2)
        assert 'DB consistente' in out2.getvalue()

    def test_backfill_uses_highest_monto_desempate_creado_en(self, db, vendedor):
        """Backfill uses same criteria as cerrar_subastas: -monto, creado_en asc."""
        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Desempate',
            descripcion='d',
            precio_inicial=100,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        user_a = User.objects.create_user(username='user_a', password='x')
        user_b = User.objects.create_user(username='user_b', password='x')
        # Both offer 200, user_a first (earlier creado_en)
        Oferta.objects.create(subasta=s, ofertante=user_a, monto=200)
        import time
        time.sleep(0.01)
        Oferta.objects.create(subasta=s, ofertante=user_b, monto=200)

        call_command('backfill_ganadores', stdout=StringIO())
        s.refresh_from_db()
        assert s.ganador == user_a  # earliest creado_en wins on tie
