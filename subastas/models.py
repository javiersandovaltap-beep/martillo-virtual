from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Subasta(models.Model):
    class Estado(models.TextChoices):
        ACTIVA   = "activa",   "Activa"
        CERRADA  = "cerrada",  "Cerrada"
        CANCELADA = "cancelada", "Cancelada"

    vendedor       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subastas_vendedor")
    titulo         = models.CharField(max_length=200)
    descripcion    = models.TextField()
    imagen         = models.ImageField(upload_to="subastas/", blank=True, null=True)
    precio_inicial = models.DecimalField(max_digits=12, decimal_places=2)
    estado         = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVA)
    fecha_cierre   = models.DateTimeField()
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    ganador        = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subastas_ganadas",
        verbose_name="Ganador",
    )

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "subasta"
        verbose_name_plural = "subastas"
        indexes = [
            models.Index(fields=["estado", "-creado_en"], name="subasta_estado_created_idx"),
            models.Index(fields=["fecha_cierre"], name="subasta_cierre_idx"),
        ]

    def __str__(self):
        return self.titulo

    @property
    def esta_activa(self):
        return self.estado == self.Estado.ACTIVA and timezone.now() < self.fecha_cierre

    @property
    def precio_actual(self):
        # If we have an annotated value, use it
        if hasattr(self, '_precio_actual'):
            return self._precio_actual
        mejor = self.ofertas.order_by("-monto").first()
        return mejor.monto if mejor else self.precio_inicial

    @property
    def total_ofertas(self):
        # If we have an annotated value, use it
        if hasattr(self, '_total_ofertas'):
            return self._total_ofertas
        return self.ofertas.count()

    @property
    def tiene_ganador(self):
        """True if subasta is cerrada AND has a ganador set."""
        return self.estado == self.Estado.CERRADA and self.ganador is not None

    @property
    def monto_ganador(self):
        """Returns the winning oferta monto, or None if no ganador."""
        if not self.tiene_ganador:
            return None
        mejor = self.ofertas.order_by("-monto", "creado_en").first()
        return mejor.monto if mejor else None


class Oferta(models.Model):
    subasta    = models.ForeignKey(Subasta, on_delete=models.CASCADE, related_name="ofertas")
    ofertante  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mis_ofertas")
    monto      = models.DecimalField(max_digits=12, decimal_places=2)
    creado_en  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-monto", "-creado_en"]
        verbose_name = "oferta"
        verbose_name_plural = "ofertas"
        indexes = [
            models.Index(fields=["-creado_en"], name="oferta_created_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["subasta", "ofertante", "monto"],
                name="unique_oferta_por_monto"
            )
        ]

    def __str__(self):
        return f"{self.ofertante.username} → ${self.monto} en {self.subasta}"
