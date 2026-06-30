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
    fecha_inicio   = models.DateTimeField(auto_now_add=True)
    fecha_cierre   = models.DateTimeField()
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "subasta"
        verbose_name_plural = "subastas"

    def __str__(self):
        return self.titulo

    @property
    def esta_activa(self):
        return self.estado == self.Estado.ACTIVA and timezone.now() < self.fecha_cierre

    @property
    def precio_actual(self):
        mejor = self.ofertas.order_by("-monto").first()
        return mejor.monto if mejor else self.precio_inicial

    @property
    def total_ofertas(self):
        return self.ofertas.count()


class Oferta(models.Model):
    subasta    = models.ForeignKey(Subasta, on_delete=models.CASCADE, related_name="ofertas")
    ofertante  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mis_ofertas")
    monto      = models.DecimalField(max_digits=12, decimal_places=2)
    creado_en  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-monto", "-creado_en"]
        verbose_name = "oferta"
        verbose_name_plural = "ofertas"
        constraints = [
            models.UniqueConstraint(
                fields=["subasta", "ofertante", "monto"],
                name="unique_oferta_por_monto"
            )
        ]

    def __str__(self):
        return f"{self.ofertante.username} → ${self.monto} en {self.subasta}"
