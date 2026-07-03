"""
Tests for subastas.views (all views).

Covers:
- InicioView: GET 200, only active subastas, pagination, context
- DetalleView: GET 200, 404, context
- CrearSubastaView: auth required, GET, POST
- EditarSubastaView: owner permission, GET, POST
- EliminarSubastaView: owner permission, POST
- ofertar: POST, invalid monto, closed subasta, owner, GET 405 (B08)
- MisSubastasView: GET 200, only own subastas, stats
- login_view: GET, POST auth, next redirect (safe + open redirect blocked B07)
- logout_view: POST, GET 405 (B09)
- registro: GET, POST create user

Uses Django test Client with HTTP_HOST='localhost' (L25).
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from subastas.models import Subasta, Oferta


# ============================================================================
# Helper: client with HTTP_HOST='localhost' (L25)
# ============================================================================

def get_client(authenticated_user=None):
    """Returns a Client with HTTP_HOST='localhost'. If user provided, logs in."""
    c = Client(HTTP_HOST='localhost')
    if authenticated_user:
        c.force_login(authenticated_user)
    return c


# ============================================================================
# InicioView
# ============================================================================

class TestInicioView:
    def test_get_200(self, db, subasta_activa):
        c = get_client()
        response = c.get(reverse('subastas:inicio'))
        assert response.status_code == 200

    def test_only_active_subastas_shown(self, db, subasta_activa, subasta_cerrada):
        """Subastas with estado=cerrada should NOT appear in inicio"""
        c = get_client()
        response = c.get(reverse('subastas:inicio'))
        content = response.content.decode('utf-8')
        assert 'Test Subasta Activa' in content
        assert 'Test Subasta Cerrada' not in content

    def test_context_total_subastas(self, db, subasta_activa):
        c = get_client()
        response = c.get(reverse('subastas:inicio'))
        assert 'total_subastas' in response.context
        assert response.context['total_subastas'] == 1

    def test_expired_subasta_not_shown_as_active(self, db, subasta_expirada):
        """Subasta with estado=activa but fecha_cierre in past should NOT show 'En vivo' badge"""
        c = get_client()
        response = c.get(reverse('subastas:inicio'))
        # Note: InicioView filters by estado='activa', so expired-but-activa WILL appear
        # in queryset. But F01 fix means badge 'En vivo' should NOT render if not esta_activa.
        content = response.content.decode('utf-8')
        # The subasta appears (because estado=activa) but badge doesn't (because esta_activa=False)
        assert 'Test Subasta Expirada' in content
        # Count 'En vivo' badges: should be 0 (no active subastas in this test)
        assert content.count('En vivo') == 0


# ============================================================================
# DetalleView
# ============================================================================

class TestDetalleView:
    def test_get_200(self, db, subasta_activa):
        c = get_client()
        response = c.get(reverse('subastas:detalle', kwargs={'pk': subasta_activa.pk}))
        assert response.status_code == 200

    def test_404_invalid_pk(self, db):
        c = get_client()
        response = c.get(reverse('subastas:detalle', kwargs={'pk': 99999}))
        assert response.status_code == 404

    def test_context_ofertas(self, db, subasta_activa, oferta):
        c = get_client()
        response = c.get(reverse('subastas:detalle', kwargs={'pk': subasta_activa.pk}))
        assert 'ofertas' in response.context
        # oferta fixture creates 1 oferta with monto=1500
        assert len(response.context['ofertas']) == 1

    def test_form_oferta_not_in_context(self, db, subasta_activa):
        """B06 fix: form_oferta was removed from context"""
        c = get_client()
        response = c.get(reverse('subastas:detalle', kwargs={'pk': subasta_activa.pk}))
        assert 'form_oferta' not in response.context


# ============================================================================
# CrearSubastaView
# ============================================================================

class TestCrearSubastaView:
    def test_anonymous_redirected_to_login(self, db):
        c = get_client()
        response = c.get(reverse('subastas:crear'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_authenticated_get_200(self, db, vendedor):
        c = get_client(vendedor)
        response = c.get(reverse('subastas:crear'))
        assert response.status_code == 200

    def test_post_creates_subasta(self, db, vendedor):
        c = get_client(vendedor)
        data = {
            'titulo': 'Nueva Subasta',
            'descripcion': 'Desc',
            'precio_inicial': '1000',
            'fecha_cierre': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
        }
        response = c.post(reverse('subastas:crear'), data)
        assert response.status_code == 302  # Redirect to detalle
        assert Subasta.objects.filter(titulo='Nueva Subasta').exists()
        s = Subasta.objects.get(titulo='Nueva Subasta')
        assert s.vendedor == vendedor


# ============================================================================
# EditarSubastaView
# ============================================================================

class TestEditarSubastaView:
    def test_anonymous_redirected_to_login(self, db, subasta_activa):
        c = get_client()
        response = c.get(reverse('subastas:editar', kwargs={'pk': subasta_activa.pk}))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_owner_get_200(self, db, subasta_activa, vendedor):
        c = get_client(vendedor)
        response = c.get(reverse('subastas:editar', kwargs={'pk': subasta_activa.pk}))
        assert response.status_code == 200

    def test_non_owner_get_403(self, db, subasta_activa, ofertante):
        """UserPassesTestMixin: non-owner gets 403"""
        c = get_client(ofertante)
        response = c.get(reverse('subastas:editar', kwargs={'pk': subasta_activa.pk}))
        assert response.status_code == 403

    def test_owner_post_updates(self, db, subasta_activa, vendedor):
        c = get_client(vendedor)
        data = {
            'titulo': 'Updated Title',
            'descripcion': 'Updated desc',
            'precio_inicial': '2000',
            'fecha_cierre': (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M'),
        }
        response = c.post(reverse('subastas:editar', kwargs={'pk': subasta_activa.pk}), data)
        assert response.status_code == 302
        subasta_activa.refresh_from_db()
        assert subasta_activa.titulo == 'Updated Title'
        assert subasta_activa.precio_inicial == Decimal('2000')


# ============================================================================
# EliminarSubastaView
# ============================================================================

class TestEliminarSubastaView:
    def test_anonymous_redirected_to_login(self, db, subasta_activa):
        c = get_client()
        response = c.get(reverse('subastas:eliminar', kwargs={'pk': subasta_activa.pk}))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_owner_get_200(self, db, subasta_activa, vendedor):
        c = get_client(vendedor)
        response = c.get(reverse('subastas:eliminar', kwargs={'pk': subasta_activa.pk}))
        assert response.status_code == 200

    def test_non_owner_get_403(self, db, subasta_activa, ofertante):
        c = get_client(ofertante)
        response = c.get(reverse('subastas:eliminar', kwargs={'pk': subasta_activa.pk}))
        assert response.status_code == 403

    def test_owner_post_deletes(self, db, subasta_activa, vendedor):
        pk = subasta_activa.pk
        c = get_client(vendedor)
        response = c.post(reverse('subastas:eliminar', kwargs={'pk': pk}))
        assert response.status_code == 302
        assert not Subasta.objects.filter(pk=pk).exists()


# ============================================================================
# ofertar
# ============================================================================

class TestOfertarView:
    def test_get_returns_405(self, db, subasta_activa, ofertante):
        """B08 fix: GET should return 405 Method Not Allowed"""
        c = get_client(ofertante)
        response = c.get(reverse('subastas:ofertar', kwargs={'pk': subasta_activa.pk}))
        assert response.status_code == 405

    def test_post_valid_oferta_creates(self, db, subasta_activa, ofertante):
        c = get_client(ofertante)
        response = c.post(
            reverse('subastas:ofertar', kwargs={'pk': subasta_activa.pk}),
            {'monto': '1500'}
        )
        assert response.status_code == 302  # Redirect to detalle
        assert Oferta.objects.filter(subasta=subasta_activa, ofertante=ofertante).exists()

    def test_post_invalid_monto_low(self, db, subasta_activa, ofertante):
        """monto <= precio_actual -> rejected, redirect back"""
        c = get_client(ofertante)
        response = c.post(
            reverse('subastas:ofertar', kwargs={'pk': subasta_activa.pk}),
            {'monto': '500'}  # < precio_inicial 1000
        )
        assert response.status_code == 302  # Redirect back to detalle with error message
        assert not Oferta.objects.filter(subasta=subasta_activa, ofertante=ofertante).exists()

    def test_post_on_closed_subasta_rejected(self, db, subasta_cerrada, ofertante):
        c = get_client(ofertante)
        response = c.post(
            reverse('subastas:ofertar', kwargs={'pk': subasta_cerrada.pk}),
            {'monto': '1500'}
        )
        assert response.status_code == 302
        assert not Oferta.objects.filter(subasta=subasta_cerrada, ofertante=ofertante).exists()

    def test_post_by_owner_rejected(self, db, subasta_activa, vendedor):
        """Owner cannot ofer on own subasta"""
        c = get_client(vendedor)
        response = c.post(
            reverse('subastas:ofertar', kwargs={'pk': subasta_activa.pk}),
            {'monto': '1500'}
        )
        assert response.status_code == 302
        assert not Oferta.objects.filter(subasta=subasta_activa, ofertante=vendedor).exists()

    def test_anonymous_redirected_to_login(self, db, subasta_activa):
        c = get_client()
        response = c.post(
            reverse('subastas:ofertar', kwargs={'pk': subasta_activa.pk}),
            {'monto': '1500'}
        )
        assert response.status_code == 302
        assert '/login/' in response.url


# ============================================================================
# MisSubastasView
# ============================================================================

class TestMisSubastasView:
    def test_anonymous_redirected_to_login(self, db):
        c = get_client()
        response = c.get(reverse('subastas:mis_subastas'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_authenticated_get_200(self, db, vendedor, subasta_activa):
        c = get_client(vendedor)
        response = c.get(reverse('subastas:mis_subastas'))
        assert response.status_code == 200

    def test_only_own_subastas(self, db, vendedor, ofertante):
        """User should see only their own subastas"""
        # Create subasta owned by ofertante (not vendedor)
        from subastas.models import Subasta
        other_subasta = Subasta.objects.create(
            vendedor=ofertante,
            titulo='Other User Subasta',
            descripcion='desc',
            precio_inicial=500,
            fecha_cierre=timezone.now() + timedelta(days=1),
        )
        # Create subasta owned by vendedor
        my_subasta = Subasta.objects.create(
            vendedor=vendedor,
            titulo='My Subasta',
            descripcion='desc',
            precio_inicial=800,
            fecha_cierre=timezone.now() + timedelta(days=1),
        )
        c = get_client(vendedor)
        response = c.get(reverse('subastas:mis_subastas'))
        content = response.content.decode('utf-8')
        assert 'My Subasta' in content
        assert 'Other User Subasta' not in content

    def test_context_stats(self, db, vendedor, subasta_activa, subasta_cerrada):
        """Stats should be in context (total, activas, cerradas, total_ofertas_recibidas)"""
        # Note: subasta_cerrada fixture is owned by vendedor too
        c = get_client(vendedor)
        response = c.get(reverse('subastas:mis_subastas'))
        assert 'total' in response.context
        assert 'activas' in response.context
        assert 'cerradas' in response.context
        assert 'total_ofertas_recibidas' in response.context
        # 2 subastas: 1 activa, 1 cerrada
        assert response.context['total'] == 2
        assert response.context['activas'] == 1
        assert response.context['cerradas'] == 1


# ============================================================================
# login_view
# ============================================================================

class TestLoginView:
    def test_get_200(self, db):
        c = get_client()
        response = c.get(reverse('subastas:login'))
        assert response.status_code == 200

    def test_post_valid_credentials(self, db, vendedor):
        c = get_client()
        response = c.post(reverse('subastas:login'), {
            'username': 'test_vendedor',
            'password': 'TestPass123!',
        })
        assert response.status_code == 302  # Redirect after login

    def test_post_invalid_credentials(self, db, vendedor):
        c = get_client()
        response = c.post(reverse('subastas:login'), {
            'username': 'test_vendedor',
            'password': 'wrongpass',
        })
        assert response.status_code == 200  # Stays on form

    def test_open_redirect_blocked(self, db, vendedor):
        """B07 fix: next=https://evil.com/ should NOT redirect to evil.com"""
        c = get_client()
        response = c.post(
            reverse('subastas:login') + '?next=https://evil.com/',
            {'username': 'test_vendedor', 'password': 'TestPass123!'}
        )
        assert response.status_code == 302
        location = response.url
        assert 'evil.com' not in location

    def test_safe_next_redirect(self, db, vendedor):
        """Legitimate relative next should work"""
        c = get_client()
        response = c.post(
            reverse('subastas:login') + '?next=/crear/',
            {'username': 'test_vendedor', 'password': 'TestPass123!'}
        )
        assert response.status_code == 302
        assert response.url == '/crear/'

    def test_no_next_redirects_to_inicio(self, db, vendedor):
        """Without next param, redirect to inicio (/)"""
        c = get_client()
        response = c.post(reverse('subastas:login'), {
            'username': 'test_vendedor',
            'password': 'TestPass123!',
        })
        assert response.status_code == 302
        assert response.url == '/'


# ============================================================================
# logout_view
# ============================================================================

class TestLogoutView:
    def test_get_returns_405(self, db, vendedor):
        """B09 fix: GET should return 405"""
        c = get_client(vendedor)
        response = c.get(reverse('subastas:logout'))
        assert response.status_code == 405

    def test_post_logs_out(self, db, vendedor):
        c = get_client(vendedor)
        response = c.post(reverse('subastas:logout'))
        assert response.status_code == 302
        # Verify session is anonymous by accessing login-required view
        response2 = c.get(reverse('subastas:crear'))
        assert response2.status_code == 302
        assert '/login/' in response2.url


# ============================================================================
# registro
# ============================================================================

class TestRegistroView:
    def test_get_200(self, db):
        c = get_client()
        response = c.get(reverse('subastas:registro'))
        assert response.status_code == 200

    def test_post_creates_user(self, db):
        c = get_client()
        response = c.post(reverse('subastas:registro'), {
            'username': 'brand_new_user',
            'email': 'brand@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        assert response.status_code == 302  # Redirect after register + login
        assert User.objects.filter(username='brand_new_user').exists()

    def test_post_invalid_data_stays_on_form(self, db):
        c = get_client()
        response = c.post(reverse('subastas:registro'), {
            'username': '',  # Missing
            'email': 'invalid',
            'password1': 'x',
            'password2': 'y',
        })
        assert response.status_code == 200  # Stays on form

# ============================================================================
# InicioView ?estado= filter (Commit 6)
# ============================================================================

class TestInicioViewEstadoFilter:
    def test_default_filter_activas(self, db, subasta_activa, subasta_cerrada):
        """Default (no ?estado=) shows only activas"""
        c = Client(HTTP_HOST='localhost')
        response = c.get(reverse('subastas:inicio'))
        content = response.content.decode('utf-8')
        assert 'Test Subasta Activa' in content
        assert 'Test Subasta Cerrada' not in content
        assert response.context['estado_filter'] == 'activas'

    def test_filter_activas_explicit(self, db, subasta_activa, subasta_cerrada):
        c = Client(HTTP_HOST='localhost')
        response = c.get(reverse('subastas:inicio') + '?estado=activas')
        content = response.content.decode('utf-8')
        assert 'Test Subasta Activa' in content
        assert 'Test Subasta Cerrada' not in content
        assert response.context['estado_filter'] == 'activas'

    def test_filter_cerradas(self, db, subasta_activa, subasta_cerrada):
        c = Client(HTTP_HOST='localhost')
        response = c.get(reverse('subastas:inicio') + '?estado=cerradas')
        content = response.content.decode('utf-8')
        assert 'Test Subasta Cerrada' in content
        assert 'Test Subasta Activa' not in content
        assert response.context['estado_filter'] == 'cerradas'

    def test_filter_todas(self, db, subasta_activa, subasta_cerrada):
        c = Client(HTTP_HOST='localhost')
        response = c.get(reverse('subastas:inicio') + '?estado=todas')
        content = response.content.decode('utf-8')
        assert 'Test Subasta Activa' in content
        assert 'Test Subasta Cerrada' in content
        assert response.context['estado_filter'] == 'todas'

    def test_invalid_filter_defaults_to_activas(self, db, subasta_activa):
        """Invalid ?estado= value falls back to activas queryset (default branch)"""
        c = Client(HTTP_HOST='localhost')
        response = c.get(reverse('subastas:inicio') + '?estado=invalid_xyz')
        assert response.context['estado_filter'] == 'invalid_xyz'
        # But queryset still filters by activa (default branch)
        assert 'Test Subasta Activa' in response.content.decode('utf-8')

    def test_tabs_render_in_template(self, db, subasta_activa):
        """Template should render 3 tab links"""
        c = Client(HTTP_HOST='localhost')
        response = c.get(reverse('subastas:inicio'))
        content = response.content.decode('utf-8')
        assert '?estado=activas' in content
        assert '?estado=cerradas' in content
        assert '?estado=todas' in content


# ============================================================================
# DetalleView shows ganador (Commit 6)
# ============================================================================

class TestDetalleViewGanador:
    def test_cerrada_con_ganador_shows_ganador(self, db, vendedor, ofertante):
        """Detalle of cerrada subasta with ganador shows ganador info"""
        from datetime import timedelta
        from django.utils import timezone
        from subastas.models import Subasta, Oferta

        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Cerrada Con Ganador Test',
            descripcion='d',
            precio_inicial=1000,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=1),
            ganador=ofertante,
        )
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=1500)

        c = Client(HTTP_HOST='localhost')
        response = c.get(reverse('subastas:detalle', kwargs={'pk': s.pk}))
        content = response.content.decode('utf-8')
        assert 'Ganador' in content
        assert 'test_ofertante' in content
        assert '1500' in content

    def test_cerrada_sin_ganador_shows_sin_ofertas(self, db, vendedor):
        """Detalle of cerrada subasta without ganador shows 'sin ofertas' message"""
        from datetime import timedelta
        from django.utils import timezone
        from subastas.models import Subasta

        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo='Cerrada Sin Ganador Test',
            descripcion='d',
            precio_inicial=1000,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )

        c = Client(HTTP_HOST='localhost')
        response = c.get(reverse('subastas:detalle', kwargs={'pk': s.pk}))
        content = response.content.decode('utf-8')
        assert 'finalizado sin ofertas' in content.lower()
