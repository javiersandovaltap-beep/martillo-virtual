"""
Comando personalizado para cerrar subastas expiradas.
Uso:
  python manage.py cerrar_subastas           # cierra expiradas
  python manage.py cerrar_subastas --dry-run # preview sin aplicar

Cuando cierra una subasta:
- Si tiene ofertas: setea ganador al ofertante de la oferta más alta
  (desempate por creado_en más temprano, mismo criterio que precio_actual)
- Si no tiene ofertas: cierra sin ganador (ganador queda None)
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from subastas.models import Subasta, Oferta


class Command(BaseCommand):
    help = "Cierra subastas expiradas (estado='activa' con fecha_cierre en el pasado). Setea ganador si hay ofertas."

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
                oferta_count = s.ofertas.count()
                ganador_info = ""
                if oferta_count > 0:
                    mejor = s.ofertas.order_by("-monto", "creado_en").first()
                    ganador_info = f" [ganador: {mejor.ofertante.username} ${mejor.monto}]"
                self.stdout.write(
                    f"  - pk={s.pk} titulo='{s.titulo}' "
                    f"ofertas={oferta_count}{ganador_info}"
                )
            return

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS("No hay subastas expiradas que cerrar.")
            )
            return

        # Capture pks BEFORE update (audit trail fix from R4.1)
        expiradas_info = list(expiradas.values_list("pk", "titulo", "fecha_cierre"))

        cerradas_con_ganador = 0
        cerradas_sin_ofertas = 0
        audit_trail = []

        # Per-row close with ganador assignment (transactional)
        with transaction.atomic():
            for pk, titulo, fecha_cierre in expiradas_info:
                # select_for_update prevents race with ofertar() view
                subasta = Subasta.objects.select_for_update().get(pk=pk)

                # Find highest oferta (desempate por creado_en más temprano)
                mejor_oferta = subasta.ofertas.order_by("-monto", "creado_en").first()

                if mejor_oferta:
                    subasta.ganador = mejor_oferta.ofertante
                    cerradas_con_ganador += 1
                    audit_trail.append(
                        (pk, titulo, fecha_cierre, mejor_oferta.ofertante.username, mejor_oferta.monto)
                    )
                else:
                    cerradas_sin_ofertas += 1
                    audit_trail.append(
                        (pk, titulo, fecha_cierre, None, None)
                    )

                subasta.estado = Subasta.Estado.CERRADA
                subasta.save()

        # Report
        self.stdout.write(
            self.style.SUCCESS(
                f"{count} subasta(s) cerrada(s): "
                f"{cerradas_con_ganador} con ganador, "
                f"{cerradas_sin_ofertas} sin ofertas."
            )
        )

        # Audit trail
        self.stdout.write("Subastas cerradas:")
        for pk, titulo, fecha_cierre, ganador_username, ganador_monto in audit_trail:
            if ganador_username:
                self.stdout.write(
                    f"  - pk={pk} titulo='{titulo}' fecha_cierre={fecha_cierre.isoformat()} "
                    f"ganador='{ganador_username}' monto=${ganador_monto}"
                )
            else:
                self.stdout.write(
                    f"  - pk={pk} titulo='{titulo}' fecha_cierre={fecha_cierre.isoformat()} "
                    f"(sin ofertas, sin ganador)"
                )
