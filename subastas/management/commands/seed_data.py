"""
Comando personalizado para poblar la base de datos con datos iniciales.
Uso: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from subastas.models import Subasta


SUBASTAS_DEMO = [
    {
        "titulo": "Reloj Omega Seamaster 1965",
        "descripcion": "Pieza original en excelente estado de conservación. Mecanismo revisado por relojero certificado. Incluye caja y documentación original.",
        "precio_inicial": 1200.00,
        "dias": 7,
    },
    {
        "titulo": "Pintura al Óleo — Paisaje Chileno S.XIX",
        "descripcion": "Obra de autor desconocido, posiblemente escuela costumbrista chilena. Marco original tallado en madera. Medidas: 60x80 cm.",
        "precio_inicial": 850.00,
        "dias": 14,
    },
    {
        "titulo": "Monedas de Plata Coloniales (Lote x5)",
        "descripcion": "Cinco monedas de plata del período colonial americano, siglo XVIII. Certificadas por numismático. Estado VF a XF.",
        "precio_inicial": 3400.00,
        "dias": 10,
    },
    {
        "titulo": "Silla Estilo Chippendale — Caoba",
        "descripcion": "Silla original estilo Chippendale en madera de caoba tallada a mano. Tapizado en cuero natural. Circa 1890.",
        "precio_inicial": 620.00,
        "dias": 5,
    },
    {
        "titulo": "Cámara Leica M3 — Coleccionista",
        "descripcion": "Leica M3 doble avance, año 1955. Óptica Summicron 50mm f/2 original. Funcionamiento verificado. Estado estético 8/10.",
        "precio_inicial": 2100.00,
        "dias": 12,
    },
    {
        "titulo": "Librería Victoriana — Roble Macizo",
        "descripcion": "Librería de roble macizo estilo victoriano con vidrieras originales y herrajes de bronce. Alto 2.20m. Envío coordinado.",
        "precio_inicial": 1800.00,
        "dias": 8,
    },
]


class Command(BaseCommand):
    help = "Puebla la base de datos con subastas y usuario demo."

    def handle(self, *args, **kwargs):
        # Crear usuario demo si no existe
        user, created = User.objects.get_or_create(
            username="don_roberto",
            defaults={
                "email": "roberto@martillovirtual.cl",
                "first_name": "Roberto",
                "last_name": "Donoso",
            },
        )
        if created:
            user.set_password("Demo1234!")
            user.save()
            self.stdout.write(self.style.SUCCESS("Usuario 'don_roberto' creado (pass: Demo1234!)"))
        else:
            self.stdout.write(self.style.WARNING("Usuario 'don_roberto' ya existe."))

        # Crear subastas demo
        creadas = 0
        for data in SUBASTAS_DEMO:
            _, created = Subasta.objects.get_or_create(
                titulo=data["titulo"],
                defaults={
                    "descripcion": data["descripcion"],
                    "precio_inicial": data["precio_inicial"],
                    "vendedor": user,
                    "estado": Subasta.Estado.ACTIVA,
                    "fecha_cierre": timezone.now() + timedelta(days=data["dias"]),
                },
            )
            if created:
                creadas += 1

        self.stdout.write(
            self.style.SUCCESS(f"{creadas} subasta(s) de demo creada(s).")
        )
        if creadas == 0:
            self.stdout.write(self.style.WARNING("Las subastas ya existían."))
