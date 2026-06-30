from django.urls import path
from . import views

app_name = "subastas"

urlpatterns = [
    path("",               views.InicioView.as_view(),          name="inicio"),
    path("subasta/<int:pk>/",   views.DetalleView.as_view(),    name="detalle"),
    path("crear/",         views.CrearSubastaView.as_view(),     name="crear"),
    path("editar/<int:pk>/",    views.EditarSubastaView.as_view(), name="editar"),
    path("eliminar/<int:pk>/",  views.EliminarSubastaView.as_view(), name="eliminar"),
    path("ofertar/<int:pk>/",   views.ofertar,                  name="ofertar"),
    path("mis-subastas/",  views.MisSubastasView.as_view(),      name="mis_subastas"),
    path("registro/",      views.registro,                       name="registro"),
    path("login/",         views.login_view,                     name="login"),
    path("logout/",        views.logout_view,                    name="logout"),
]
