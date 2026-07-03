from django.apps import AppConfig


class SubastasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "subastas"
    verbose_name = "Casa de Subastas"

    def ready(self):
        # Importar signals para que se conecten
        # Import implicito: los @receiver decorators se registran al importar
        from . import signals  # noqa: F401
