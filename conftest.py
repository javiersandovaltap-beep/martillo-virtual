import pytest
from django.contrib.auth.models import User
from subastas.models import Subasta, Oferta

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear Django cache before and after each test.
    Prevents rate limit counters from persisting between tests (D09)."""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()



@pytest.fixture
def vendedor(db):
    """User that creates subastas."""
    user = User.objects.create_user(
        username='test_vendedor',
        email='vendedor@test.com',
        password='TestPass123!'
    )
    return user


@pytest.fixture
def ofertante(db):
    """User that makes ofertas."""
    user = User.objects.create_user(
        username='test_ofertante',
        email='ofertante@test.com',
        password='TestPass123!'
    )
    return user


@pytest.fixture
def subasta_activa(db, vendedor):
    """Active subasta with future fecha_cierre."""
    from datetime import timedelta
    from django.utils import timezone
    return Subasta.objects.create(
        vendedor=vendedor,
        titulo='Test Subasta Activa',
        descripcion='Descripcion de test',
        precio_inicial=1000,
        estado=Subasta.Estado.ACTIVA,
        fecha_cierre=timezone.now() + timedelta(days=7),
    )


@pytest.fixture
def subasta_cerrada(db, vendedor):
    """Closed subasta (estado=cerrada)."""
    from datetime import timedelta
    from django.utils import timezone
    return Subasta.objects.create(
        vendedor=vendedor,
        titulo='Test Subasta Cerrada',
        descripcion='Descripcion de test',
        precio_inicial=1000,
        estado=Subasta.Estado.CERRADA,
        fecha_cierre=timezone.now() - timedelta(days=1),
    )


@pytest.fixture
def subasta_expirada(db, vendedor):
    """Subasta with estado=activa but fecha_cierre in the past (logical bug)."""
    from datetime import timedelta
    from django.utils import timezone
    return Subasta.objects.create(
        vendedor=vendedor,
        titulo='Test Subasta Expirada',
        descripcion='Descripcion de test',
        precio_inicial=1000,
        estado=Subasta.Estado.ACTIVA,
        fecha_cierre=timezone.now() - timedelta(days=1),
    )


@pytest.fixture
def oferta(db, subasta_activa, ofertante):
    """Oferta on subasta_activa."""
    return Oferta.objects.create(
        subasta=subasta_activa,
        ofertante=ofertante,
        monto=1500,
    )
