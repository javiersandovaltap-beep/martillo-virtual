"""
Signals for subastas app.

post_save on Subasta: cuando ganador pasa de None a un User,
envia email al ganador notificando que gano la subasta.

Solo dispara en el PRIMER seteo (None -> user).
Cambios user1 -> user2 no disparan (caso edge, no esperado en este flujo).
"""
import logging

from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Subasta

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Subasta)
def store_previous_ganador(sender, instance, **kwargs):
    """Captura el ganador_id actual de la DB antes del save.
    Necesario porque post_save no tiene acceso al valor anterior."""
    if instance.pk:
        try:
            instance._previous_ganador_id = (
                Subasta.objects.values_list("ganador_id", flat=True).get(pk=instance.pk)
            )
        except Subasta.DoesNotExist:
            instance._previous_ganador_id = None
    else:
        instance._previous_ganador_id = None


@receiver(post_save, sender=Subasta)
def notify_ganador(sender, instance, created, **kwargs):
    """Envia email al ganador cuando ganador pasa de None a un User.
    Solo dispara en el primer seteo (None -> user), no en cambios user1 -> user2."""
    if created:
        return  # Subasta recien creada, no tiene ganador

    previous_ganador_id = getattr(instance, "_previous_ganador_id", None)
    current_ganador_id = instance.ganador_id

    # Solo enviar si ganador paso de None a un User
    if previous_ganador_id is None and current_ganador_id is not None:
        if not instance.ganador or not instance.ganador.email:
            logger.warning(
                "Subasta %s tiene ganador sin email, no se envio notificacion",
                instance.pk,
            )
            return

        monto = instance.monto_ganador
        try:
            send_mail(
                subject=f"¡Ganaste la subasta: {instance.titulo}!",
                message=(
                    f"¡Felicitaciones {instance.ganador.username}!\n\n"
                    f"Ganaste la subasta '{instance.titulo}' "
                    f"con una oferta de ${monto}.\n\n"
                    f"El vendedor ({instance.vendedor.username}) se pondra en contacto "
                    f"para coordinar la entrega.\n\n"
                    f"-- MartilloVirtual"
                ),
                from_email="noreply@martillovirtual.cl",
                recipient_list=[instance.ganador.email],
                fail_silently=True,
            )
            logger.info(
                "Email enviado a ganador %s por subasta %s",
                instance.ganador.username,
                instance.pk,
            )
        except Exception as e:
            # fail_silently=True ya cubre SMTP errors, pero capturamos
            # cualquier otra excepcion para no romper cerrar_subastas
            logger.error("Error enviando email a ganador: %s", e)
