"""
Tests for subastas.signals (email al ganador).

Covers:
- Subasta creation does NOT send email
- Saving without changing ganador does NOT send email
- Setting ganador (None -> user) DOES send email
- Changing ganador (user1 -> user2) does NOT send email (only first set)
- Ganador without email does NOT crash (fail_silently)
- Email content is correct
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone

from subastas.models import Subasta, Oferta


class TestNotifyGanadorSignal:
    def test_subasta_creation_does_not_send_email(self, db, vendedor):
        """Crear subasta nueva NO dispara email (no hay ganador)"""
        mail.outbox = []  # Clear
        Subasta.objects.create(
            vendedor=vendedor,
            titulo="Nueva",
            descripcion="d",
            precio_inicial=1000,
            fecha_cierre=timezone.now() + timedelta(days=1),
        )
        assert len(mail.outbox) == 0

    def test_save_without_changing_ganador_no_email(self, db, subasta_activa):
        """Save sin cambiar ganador NO dispara email"""
        mail.outbox = []
        subasta_activa.titulo = "Updated Title"
        subasta_activa.save()
        assert len(mail.outbox) == 0

    def test_setting_ganador_sends_email(self, db, vendedor, ofertante):
        """Setear ganador (None -> user) SI dispara email"""
        from datetime import timedelta
        from django.utils import timezone

        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo="Con Ganador",
            descripcion="d",
            precio_inicial=1000,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        # Crear oferta para que monto_ganador funcione
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=1500)

        mail.outbox = []
        s.ganador = ofertante
        s.save()

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert "Ganaste la subasta" in email.subject
        assert ofertante.email in email.to
        assert "Con Ganador" in email.body
        assert "1500" in email.body

    def test_changing_ganador_does_not_send_email(self, db, vendedor, ofertante):
        """Cambiar ganador (user1 -> user2) NO dispara email (solo primer set)"""
        from datetime import timedelta
        from django.utils import timezone

        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo="Cambio Ganador",
            descripcion="d",
            precio_inicial=1000,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=1500)

        # First set: sends email
        mail.outbox = []
        s.ganador = ofertante
        s.save()
        assert len(mail.outbox) == 1

        # Change to another user: should NOT send
        other_user = User.objects.create_user(
            username="other_winner", email="other@test.com", password="x"
        )
        mail.outbox = []
        s.ganador = other_user
        s.save()
        assert len(mail.outbox) == 0

    def test_ganador_without_email_does_not_crash(self, db, vendedor):
        """Ganador sin email NO crashea (fail_silently + guard)"""
        from datetime import timedelta
        from django.utils import timezone

        # User without email
        no_email_user = User.objects.create_user(
            username="no_email", password="x"  # No email set
        )
        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo="No Email Ganador",
            descripcion="d",
            precio_inicial=1000,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )

        mail.outbox = []
        s.ganador = no_email_user
        s.save()  # Should not raise
        assert len(mail.outbox) == 0

    def test_email_content_correct(self, db, vendedor, ofertante):
        """Email content: subject, body includes titulo, monto, username"""
        from datetime import timedelta
        from django.utils import timezone

        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo="Test Content Email",
            descripcion="d",
            precio_inicial=1000,
            estado=Subasta.Estado.CERRADA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=2500)

        mail.outbox = []
        s.ganador = ofertante
        s.save()

        email = mail.outbox[0]
        assert "Test Content Email" in email.subject
        assert "test_ofertante" in email.body  # username del ganador
        assert "2500" in email.body  # monto
        assert "MartilloVirtual" in email.body

    def test_cerrar_subastas_triggers_email_via_signal(self, db, vendedor, ofertante):
        """cerrar_subastas command setea ganador -> signal envia email automaticamente"""
        from datetime import timedelta
        from django.utils import timezone
        from io import StringIO
        from django.core.management import call_command

        s = Subasta.objects.create(
            vendedor=vendedor,
            titulo="Cerrar Con Email",
            descripcion="d",
            precio_inicial=1000,
            estado=Subasta.Estado.ACTIVA,
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        Oferta.objects.create(subasta=s, ofertante=ofertante, monto=1500)

        mail.outbox = []
        call_command("cerrar_subastas", stdout=StringIO())

        # Signal should have fired when cerrar_subastas set ganador
        assert len(mail.outbox) == 1
        assert "Cerrar Con Email" in mail.outbox[0].subject
