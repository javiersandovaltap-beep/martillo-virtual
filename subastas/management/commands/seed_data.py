"""
Comando personalizado para poblar la base de datos con datos de demo.
Uso:
  python manage.py seed_data           # idempotente (get_or_create)
  python manage.py seed_data --reset   # borra Subasta+Oferta, re-crea (mantiene users)

Datos demo:
- 5 usuarios (don_roberto, maria_coleccionista, pedro_antiguo, elena_arte, lucas_nuevo)
- 15 subastas (9 activas, 4 cerradas con ofertas, 2 canceladas)
- ~17 ofertas (competencia en cerradas, pujas en curso en activas)
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from subastas.models import Subasta, Oferta


# === USUARIOS DEMO ===
USUARIOS_DEMO = [
    {
        "username": "don_roberto",
        "email": "roberto@martillovirtual.cl",
        "password": "Demo1234!",
        "first_name": "Roberto",
        "last_name": "Donoso",
    },
    {
        "username": "maria_coleccionista",
        "email": "maria@martillovirtual.cl",
        "password": "Demo1234!",
        "first_name": "Maria",
        "last_name": "Fernandez",
    },
    {
        "username": "pedro_antiguo",
        "email": "pedro@martillovirtual.cl",
        "password": "Demo1234!",
        "first_name": "Pedro",
        "last_name": "Martinez",
    },
    {
        "username": "elena_arte",
        "email": "elena@martillovirtual.cl",
        "password": "Demo1234!",
        "first_name": "Elena",
        "last_name": "Vidal",
    },
    {
        "username": "lucas_nuevo",
        "email": "lucas@martillovirtual.cl",
        "password": "Demo1234!",
        "first_name": "Lucas",
        "last_name": "Rojas",
    },
]


# === SUBASTAS DEMO ===
# Formato: (titulo, descripcion, precio_inicial, dias_cierre, estado, vendedor_username)
# dias_cierre > 0 = futuro (activa), dias_cierre < 0 = pasado (cerrada)
SUBASTAS_DEMO = [
    # --- 9 ACTIVAS ---
    ("Reloj Omega Seamaster 1965",
     "Pieza original en excelente estado. Mecanismo revisado por relojero certificado. Incluye caja y documentacion original.",
     1200, 7, "activa", "don_roberto"),
    ("Pintura al Oleo - Paisaje Chileno S.XIX",
     "Obra de autor desconocido, posiblemente escuela costumbrista chilena. Marco original tallado en madera. Medidas: 60x80 cm.",
     850, 14, "activa", "don_roberto"),
    ("Monedas de Plata Coloniales (Lote x5)",
     "Cinco monedas de plata del periodo colonial americano, siglo XVIII. Certificadas por numismatico. Estado VF a XF.",
     3400, 10, "activa", "don_roberto"),
    ("Silla Estilo Chippendale - Caoba",
     "Silla original estilo Chippendale en madera de caoba tallada a mano. Tapizado en cuero natural. Circa 1890.",
     620, 5, "activa", "don_roberto"),
    ("Camara Leica M3 - Coleccionista",
     "Leica M3 doble avance, ano 1955. Optica Summicron 50mm f/2 original. Funcionamiento verificado. Estado estetico 8/10.",
     2100, 12, "activa", "don_roberto"),
    ("Libreria Victoriana - Roble Macizo",
     "Libreria de roble macizo estilo victoriano con vidrieras originales y herrajes de bronce. Alto 2.20m. Envio coordinado.",
     1800, 8, "activa", "don_roberto"),
    ("Jarron Ming Dinastia - Ceramica",
     "Jarron de ceramica de la dinastia Ming, periodo Xuande. Autenticado por experto en arte asiatico. Altura 28cm.",
     5000, 6, "activa", "maria_coleccionista"),
    ("Coleccion Filatelica - Sudamerica 1900-1950",
     "Album con 200+ estampillas sudamericanas, primera mitad siglo XX. Incluye piezas raras de Chile y Argentina.",
     1200, 9, "activa", "maria_coleccionista"),
    ("Oleo Original Firmado - Escuela Valenciana",
     "Oleo sobre tela firmado, escuela valenciana principios S.XX. Restauracion profesional reciente. 75x100 cm.",
     3500, 4, "activa", "elena_arte"),

    # --- 4 CERRADAS (con ofertas, para mostrar historial) ---
    ("Reloj de Bolsillo 1880 - Plata",
     "Reloj de bolsillo de plata, fabrica suiza, circa 1880. Cadena original. Funcionando. Estado de conservacion excelente.",
     900, -3, "cerrada", "don_roberto"),
    ("Escultura Bronce Art Deco",
     "Escultura de bronce estilo Art Deco, anos 1930. Figura femenina. Base de marfil. Altura 35cm. Firmada.",
     2800, -5, "cerrada", "maria_coleccionista"),
    ("Fotografia Ansel Adams - Edicion Limitada",
     "Print de coleccionista, fotografiado por Ansel Adams. Edicion limitada numerada. Certificado de autenticidad.",
     1800, -2, "cerrada", "elena_arte"),
    ("Tapiz Persa Antiguo - Kashan",
     "Tapiz persa Kashan, lana natural, circa 1920. Disenos florales tradicionales. 2x3 metros. Estado de conservacion muy bueno.",
     1500, -1, "cerrada", "elena_arte"),

    # --- 2 CANCELADAS ---
    ("Plataforma Vinyl 70s - Incompleta",
     "Plataforma de vinilo de los anos 70. Cancelada por vendedor (articulo dañado en almacen).",
     400, 7, "cancelada", "maria_coleccionista"),
    ("Grabado Goya - Caprichos",
     "Grabado de la serie Los Caprichos de Goya. Cancelada por falta de autenticacion.",
     2200, 10, "cancelada", "elena_arte"),
]


# === OFERTAS DEMO ===
# Formato: (subasta_titulo, ofertante_username, monto)
OFERTAS_DEMO = [
    # Subasta 1 (Reloj Omega, activa, don_roberto) - 1 oferta en curso
    ("Reloj Omega Seamaster 1965", "lucas_nuevo", 1300),

    # Subasta 7 (Reloj Bolsillo 1880, cerrada, don_roberto) - 4 ofertas, competencia
    ("Reloj de Bolsillo 1880 - Plata", "pedro_antiguo", 950),
    ("Reloj de Bolsillo 1880 - Plata", "maria_coleccionista", 1000),
    ("Reloj de Bolsillo 1880 - Plata", "pedro_antiguo", 1100),
    ("Reloj de Bolsillo 1880 - Plata", "elena_arte", 1150),

    # Subasta 8 (Escultura Bronce, cerrada, maria) - 4 ofertas, competencia
    ("Escultura Bronce Art Deco", "pedro_antiguo", 2900),
    ("Escultura Bronce Art Deco", "don_roberto", 3000),
    ("Escultura Bronce Art Deco", "lucas_nuevo", 3050),
    ("Escultura Bronce Art Deco", "don_roberto", 3300),

    # Subasta 9 (Oleo Original, activa, elena) - 2 ofertas en curso
    ("Oleo Original Firmado - Escuela Valenciana", "pedro_antiguo", 3600),
    ("Oleo Original Firmado - Escuela Valenciana", "maria_coleccionista", 3800),

    # Subasta 10 (Fotografia Ansel Adams, cerrada, elena) - 3 ofertas
    ("Fotografia Ansel Adams - Edicion Limitada", "don_roberto", 1900),
    ("Fotografia Ansel Adams - Edicion Limitada", "pedro_antiguo", 2000),
    ("Fotografia Ansel Adams - Edicion Limitada", "don_roberto", 2100),
]


class Command(BaseCommand):
    help = "Puebla la base de datos con subastas, usuarios y ofertas de demo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Borra Subasta y Oferta existentes antes de re-crear (mantiene usuarios)",
        )

    def handle(self, *args, **options):
        reset = options.get("reset", False)

        if reset:
            deleted_subastas, _ = Subasta.objects.all().delete()
            deleted_ofertas, _ = Oferta.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"Reset: eliminadas {deleted_subastas} subasta(s) y {deleted_ofertas} oferta(s)"
            ))

        # === Crear usuarios ===
        users = {}
        for data in USUARIOS_DEMO:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                },
            )
            if created:
                user.set_password(data["password"])
                user.save()
                self.stdout.write(f"  Usuario creado: {user.username}")
            users[data["username"]] = user

        # === Crear subastas ===
        now = timezone.now()
        subastas_by_titulo = {}
        creadas_subastas = 0
        for titulo, desc, precio, dias, estado, vendedor_username in SUBASTAS_DEMO:
            if dias > 0:
                fecha_cierre = now + timedelta(days=dias)
            else:
                fecha_cierre = now + timedelta(days=dias)  # dias negativo -> pasado

            _, created = Subasta.objects.get_or_create(
                titulo=titulo,
                defaults={
                    "vendedor": users[vendedor_username],
                    "descripcion": desc,
                    "precio_inicial": Decimal(str(precio)),
                    "estado": estado,
                    "fecha_cierre": fecha_cierre,
                },
            )
            if created:
                creadas_subastas += 1
            subastas_by_titulo[titulo] = Subasta.objects.get(titulo=titulo)

        self.stdout.write(self.style.SUCCESS(
            f"{creadas_subastas} subasta(s) de demo creada(s)."
        ))

        # === Crear ofertas ===
        creadas_ofertas = 0
        for subasta_titulo, ofertante_username, monto in OFERTAS_DEMO:
            subasta = subastas_by_titulo.get(subasta_titulo)
            if not subasta:
                self.stdout.write(self.style.WARNING(
                    f"  SKIP oferta: subasta '{subasta_titulo}' no encontrada"
                ))
                continue
            _, created = Oferta.objects.get_or_create(
                subasta=subasta,
                ofertante=users[ofertante_username],
                monto=Decimal(str(monto)),
            )
            if created:
                creadas_ofertas += 1

        self.stdout.write(self.style.SUCCESS(
            f"{creadas_ofertas} oferta(s) de demo creada(s)."
        ))

        # === Resumen final ===
        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS("RESUMEN DEMO DATA"))
        self.stdout.write("=" * 50)
        self.stdout.write(f"  Usuarios: {User.objects.count()}")
        self.stdout.write(f"  Subastas: {Subasta.objects.count()}")
        self.stdout.write(f"    - Activas: {Subasta.objects.filter(estado='activa').count()}")
        self.stdout.write(f"    - Cerradas: {Subasta.objects.filter(estado='cerrada').count()}")
        self.stdout.write(f"    - Canceladas: {Subasta.objects.filter(estado='cancelada').count()}")
        self.stdout.write(f"  Ofertas: {Oferta.objects.count()}")
        self.stdout.write("")
        self.stdout.write("Usuarios demo (password: Demo1234!):")
        for username in ["don_roberto", "maria_coleccionista", "pedro_antiguo", "elena_arte", "lucas_nuevo"]:
            self.stdout.write(f"  - {username}")
