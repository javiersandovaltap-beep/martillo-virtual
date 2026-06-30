from django.contrib import admin
from .models import Subasta, Oferta


class OfertaInline(admin.TabularInline):
    model = Oferta
    extra = 0
    readonly_fields = ("ofertante", "monto", "creado_en")
    can_delete = False


@admin.register(Subasta)
class SubastaAdmin(admin.ModelAdmin):
    list_display  = ("titulo", "vendedor", "precio_actual", "total_ofertas", "estado", "fecha_cierre")
    list_filter   = ("estado", "fecha_cierre")
    search_fields = ("titulo", "vendedor__username")
    readonly_fields = ("creado_en", "actualizado_en")
    inlines = [OfertaInline]


@admin.register(Oferta)
class OfertaAdmin(admin.ModelAdmin):
    list_display  = ("subasta", "ofertante", "monto", "creado_en")
    list_filter   = ("creado_en",)
    search_fields = ("subasta__titulo", "ofertante__username")
    readonly_fields = ("creado_en",)
