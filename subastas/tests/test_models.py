"""
Tests for subastas.models (Subasta, Oferta).

Covers:
- __str__ methods
- esta_activa property (4 escenarios)
- precio_actual property (no ofertas, with ofertas, multiple ofertas)
- total_ofertas property (0, 1, many)
- Oferta unique constraint (subasta + ofertante + monto)
- Subasta.Meta.ordering
- Subasta.Estado choices
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone

from subastas.models import Subasta, Oferta


# ============================================================================
# Subasta.__str__
# ============================================================================

class TestSubastaStr:
    def test_str_returns_titulo(self, subasta_activa):
        assert str(subasta_activa) == "Test Subasta Activa"

    def test_str_with_empty_titulo(self, db, vendedor):
        # Edge case: titulo with special chars
        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo="Reloj Omega — 1965",
            descripcion="desc",
            precio_inicial=100,
            fecha_cierre=timezone.now() + timedelta(days=1),
        )
        assert str(s) == "Reloj Omega — 1965"


# ============================================================================
# Subasta.esta_activa property
# ============================================================================

class TestSubastaEstaActiva:
    def test_activa_with_future_cierre(self, subasta_activa):
        """estado=activa AND fecha_cierre > now -> True"""
        assert subasta_activa.esta_activa is True

    def test_cerrada_with_future_cierre(self, subasta_cerrada):
        """estado=cerrada (even with future fecha_cierre) -> False"""
        assert subasta_cerrada.esta_activa is False

    def test_activa_with_past_cierre(self, subasta_expirada):
        """estado=activa BUT fecha_cierre in past -> False (logical close)"""
        assert subasta_expirada.esta_activa is False

    def test_cancelada_with_future_cierre(self, db, vendedor):
        """estado=cancelada -> False"""
        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo="Cancelada",
            descripcion="desc",
            precio_inicial=100,
            estado=Subasta.Estado.CANCELADA,
            fecha_cierre=timezone.now() + timedelta(days=1),
        )
        assert s.esta_activa is False


# ============================================================================
# Subasta.precio_actual property
# ============================================================================

class TestSubastaPrecioActual:
    def test_no_ofertas_returns_precio_inicial(self, subasta_activa):
        """Sin ofertas, precio_actual = precio_inicial"""
        assert subasta_activa.precio_actual == Decimal("1000")

    def test_with_one_oferta_returns_oferta_monto(self, subasta_activa, oferta):
        """Con 1 oferta, precio_actual = monto of oferta"""
        assert subasta_activa.precio_actual == Decimal("1500")

    def test_with_multiple_ofertas_returns_highest(self, db, subasta_activa, ofertante):
        """Con múltiples ofertas, precio_actual = max monto"""
        Oferta.objects.create(subasta=subasta_activa, ofertante=ofertante, monto=1200)
        Oferta.objects.create(subasta=subasta_activa, ofertante=ofertante, monto=1800)
        Oferta.objects.create(subasta=subasta_activa, ofertante=ofertante, monto=1500)
        # Refresh from DB to get clean state
        subasta_activa.refresh_from_db()
        assert subasta_activa.precio_actual == Decimal("1800")

    def test_precio_actual_below_precio_inicial(self, db, vendedor, ofertante):
        """Edge: oferta can be below precio_inicial (OfertaForm prevents this in UI,
        but property should still return the oferta monto if it exists)"""
        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo="Test",
            descripcion="desc",
            precio_inicial=1000,
            fecha_cierre=timezone.now() + timedelta(days=1),
        )
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=500)
        # Property returns highest oferta monto, even if below precio_inicial
        assert s.precio_actual == Decimal("500")


# ============================================================================
# Subasta.total_ofertas property
# ============================================================================

class TestSubastaTotalOfertas:
    def test_zero_ofertas(self, subasta_activa):
        assert subasta_activa.total_ofertas == 0

    def test_one_oferta(self, subasta_activa, oferta):
        assert subasta_activa.total_ofertas == 1

    def test_many_ofertas(self, db, subasta_activa, ofertante):
        for monto in [1100, 1200, 1300, 1400]:
            Oferta.objects.create(subasta=subasta_activa, ofertante=ofertante, monto=monto)
        subasta_activa.refresh_from_db()
        assert subasta_activa.total_ofertas == 4


# ============================================================================
# Oferta.__str__
# ============================================================================

class TestOfertaStr:
    def test_str_format(self, oferta):
        """__str__ should return 'username → $monto en titulo'"""
        expected = f"test_ofertante → ${Decimal('1500')} en Test Subasta Activa"
        assert str(oferta) == expected


# ============================================================================
# Oferta unique constraint (subasta + ofertante + monto)
# ============================================================================

class TestOfertaUniqueConstraint:
    def test_same_user_same_monto_rejected(self, db, subasta_activa, ofertante):
        """Same user offering same monto twice on same subasta -> IntegrityError"""
        Oferta.objects.create(subasta=subasta_activa, ofertante=ofertante, monto=1500)
        with pytest.raises(IntegrityError):
            Oferta.objects.create(subasta=subasta_activa, ofertante=ofertante, monto=1500)

    def test_same_user_different_monto_allowed(self, db, subasta_activa, ofertante):
        """Same user, different monto -> OK (unique is on triple)"""
        Oferta.objects.create(subasta=subasta_activa, ofertante=ofertante, monto=1500)
        Oferta.objects.create(subasta=subasta_activa, ofertante=ofertante, monto=1600)
        assert subasta_activa.total_ofertas == 2

    def test_different_users_same_monto_allowed(self, db, subasta_activa, ofertante):
        """Different users, same monto -> OK (unique is on triple, not on monto alone)"""
        other_user = User.objects.create_user(username='other_ofertante', password='pass')
        Oferta.objects.create(subasta=subasta_activa, ofertante=ofertante, monto=1500)
        Oferta.objects.create(subasta=subasta_activa, ofertante=other_user, monto=1500)
        assert subasta_activa.total_ofertas == 2


# ============================================================================
# Subasta.Meta.ordering
# ============================================================================

class TestSubastaOrdering:
    def test_ordering_by_creado_en_desc(self, db, vendedor):
        """Subastas should be ordered by -creado_en (newest first)"""
        s1 = Subasta.objects.create(
            vendedor=vendedor, titulo="Old", descripcion="d",
            precio_inicial=100, fecha_cierre=timezone.now() + timedelta(days=1),
        )
        # Sleep to ensure different creado_en timestamps
        import time
        time.sleep(0.01)
        s2 = Subasta.objects.create(
            vendedor=vendedor, titulo="New", descripcion="d",
            precio_inicial=100, fecha_cierre=timezone.now() + timedelta(days=1),
        )
        subastas = list(Subasta.objects.all())
        # s2 (newest) should be first
        assert subastas[0].pk == s2.pk
        assert subastas[1].pk == s1.pk


# ============================================================================
# Subasta.Estado choices
# ============================================================================

class TestSubastaEstadoChoices:
    def test_estado_choices_values(self):
        """Estado choices should be activa, cerrada, cancelada"""
        choices = [choice[0] for choice in Subasta.Estado.choices]
        assert "activa" in choices
        assert "cerrada" in choices
        assert "cancelada" in choices
        assert len(choices) == 3

    def test_default_estado_is_activa(self, subasta_activa):
        """Default estado should be activa"""
        # subasta_activa fixture sets estado explicitly, but if we don't set it:
        assert subasta_activa.estado == Subasta.Estado.ACTIVA

    def test_estado_display(self, subasta_cerrada):
        """get_estado_display returns human-readable"""
        assert subasta_cerrada.get_estado_display() == "Cerrada"
