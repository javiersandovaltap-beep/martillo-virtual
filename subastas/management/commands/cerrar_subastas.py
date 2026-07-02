"""
Comando personalizado para cerrar subastas expiradas.
Uso: python manage.py cerrar_subastas

Busca subastas con estado='activa' AND fecha_cierre <= now
y las actualiza a estado='cerrada'.

Diseñado para correr via cron en Render (Fase 5).
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from subastas.models import Subasta


class Command(BaseCommand):
    help = "Cierra subastas expiradas (estado='activa' con fecha_cierre en el pasado)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué subastas se cerrarian sin aplicar cambios",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        now = timezone.now()

        # Subastas activas con fecha_cierre en el pasado
        expiradas = Subasta.objects.filter(
            estado=Subasta.Estado.ACTIVA,
            fecha_cierre__lte=now,
        )

        count = expiradas.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] {count} subasta(s) expirada(s) se cerrarian:"
                )
            )
            for s in expiradas:
                self.stdout.write(
                    f"  - pk={s.pk} titulo='{s.titulo}' "
                    f"fecha_cierre={s.fecha_cierre.isoformat()}"
                )
            return

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS("No hay subastas expiradas que cerrar.")
            )
            return

        # Capture pks/titulos BEFORE update.
        # After .update(estado=CERRADA), the queryset re-evaluates with the
        # original filter (estado=ACTIVA), which no longer matches the updated
        # rows. So we must capture the audit data before the update.
        expiradas_info = list(expiradas.values_list("pk", "titulo", "fecha_cierre"))

        # Cerrar (update batch, 1 query)
        actualizadas = expiradas.update(estado=Subasta.Estado.CERRADA)

        self.stdout.write(
            self.style.SUCCESS(
                f"{actualizadas} subasta(s) cerrada(s) correctamente."
            )
        )

        # Listar las cerradas (audit trail) using captured data
        self.stdout.write("Subastas cerradas:")
        for pk, titulo, fecha_cierre in expiradas_info:
            self.stdout.write(
                f"  - pk={pk} titulo='{titulo}' fecha_cierre={fecha_cierre.isoformat()}"
            )
