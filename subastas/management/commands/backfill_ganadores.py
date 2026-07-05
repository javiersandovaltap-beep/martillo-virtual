"""
Comando para backfill ganador en subastas cerradas que no tienen ganador seteado.

Contexto: el campo Subasta.ganador se añadió en migracion 0005 (Phase 4.5 Commit 3).
Las subastas cerradas ANTES de esa migracion quedaron con ganador=None, incluso
si tienen ofertas. Este command las arregla seteando el ganador correctamente
(ofertante de la oferta mas alta, desempate por creado_en mas temprano).

Uso:
  python manage.py backfill_ganadores           # aplica cambios
  python manage.py backfill_ganadores --dry-run # preview sin aplicar

Seguro de correr multiples veces (idempotente: solo afecta cerradas sin ganador).
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from subastas.models import Subasta


class Command(BaseCommand):
    help = "Backfill ganador en subastas cerradas sin ganador (data consistency)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué subastas se actualizarian sin aplicar cambios",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        # Subastas cerradas sin ganador
        cerradas_sin_ganador = Subasta.objects.filter(
            estado=Subasta.Estado.CERRADA,
            ganador__isnull=True,
        )

        count = cerradas_sin_ganador.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "No hay subastas cerradas sin ganador. DB consistente."
                )
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] {count} subasta(s) cerrada(s) sin ganador serian actualizadas:"
                )
            )
            for s in cerradas_sin_ganador:
                oferta_count = s.ofertas.count()
                ganador_info = ""
                if oferta_count > 0:
                    mejor = s.ofertas.order_by("-monto", "creado_en").first()
                    ganador_info = f" [nuevo ganador: {mejor.ofertante.username} ${mejor.monto}]"
                else:
                    ganador_info = " (sin ofertas, ganador queda None)"
                self.stdout.write(
                    f"  - pk={s.pk} titulo='{s.titulo}' ofertas={oferta_count}{ganador_info}"
                )
            return

        # Capture pks before update (audit trail pattern from cerrar_subastas)
        target_info = list(cerradas_sin_ganador.values_list("pk", "titulo"))
        audit_trail = []
        actualizadas = 0

        with transaction.atomic():
            for pk, titulo in target_info:
                subasta = Subasta.objects.select_for_update().get(pk=pk)
                mejor_oferta = subasta.ofertas.order_by("-monto", "creado_en").first()

                if mejor_oferta:
                    subasta.ganador = mejor_oferta.ofertante
                    subasta.save()
                    actualizadas += 1
                    audit_trail.append(
                        (pk, titulo, mejor_oferta.ofertante.username, mejor_oferta.monto)
                    )
                else:
                    # Sin ofertas, ganador queda None (correcto)
                    audit_trail.append((pk, titulo, None, None))

        self.stdout.write(
            self.style.SUCCESS(
                f"{actualizadas} subasta(s) actualizada(s) con ganador. "
                f"{count - actualizadas} sin ofertas (ganador None, correcto)."
            )
        )

        self.stdout.write("Audit trail:")
        for pk, titulo, ganador_username, ganador_monto in audit_trail:
            if ganador_username:
                self.stdout.write(
                    f"  - pk={pk} titulo='{titulo}' ganador='{ganador_username}' monto=${ganador_monto}"
                )
            else:
                self.stdout.write(
                    f"  - pk={pk} titulo='{titulo}' (sin ofertas, ganador None)"
                )
