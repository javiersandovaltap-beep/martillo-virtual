from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import Subasta, Oferta
from .forms import SubastaForm, OfertaForm, RegistroForm, LoginForm


# ─── Listado público ─────────────────────────────────────────────────────────
class InicioView(ListView):
    model = Subasta
    template_name = "subastas/inicio.html"
    context_object_name = "subastas"
    paginate_by = 9

    def get_queryset(self):
        return Subasta.objects.filter(estado="activa").order_by("-creado_en")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Use paginator.count (already calculated by ListView) instead of
        # running a separate COUNT query via self.get_queryset().count()
        paginator = ctx.get("paginator")
        if paginator:
            ctx["total_subastas"] = paginator.count
        else:
            ctx["total_subastas"] = self.object_list.count()
        return ctx


# ─── Detalle ─────────────────────────────────────────────────────────────────
class DetalleView(DetailView):
    model = Subasta
    template_name = "subastas/subasta_detail.html"
    context_object_name = "subasta"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["ofertas"] = self.object.ofertas.order_by("-monto")[:20]
        ctx["form_oferta"] = OfertaForm(subasta=self.object)
        return ctx


# ─── CRUD ─────────────────────────────────────────────────────────────────────
class CrearSubastaView(LoginRequiredMixin, CreateView):
    model = Subasta
    form_class = SubastaForm
    template_name = "subastas/subasta_form.html"
    login_url = "subastas:login"

    def form_valid(self, form):
        form.instance.vendedor = self.request.user
        messages.success(self.request, "✅ Subasta publicada exitosamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("subastas:detalle", kwargs={"pk": self.object.pk})


class EditarSubastaView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Subasta
    form_class = SubastaForm
    template_name = "subastas/subasta_form.html"
    login_url = "subastas:login"

    def test_func(self):
        return self.get_object().vendedor == self.request.user

    def form_valid(self, form):
        messages.success(self.request, "✅ Cambios guardados.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("subastas:detalle", kwargs={"pk": self.object.pk})


class EliminarSubastaView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Subasta
    template_name = "subastas/subasta_confirm_delete.html"
    success_url = reverse_lazy("subastas:mis_subastas")
    login_url = "subastas:login"

    def test_func(self):
        return self.get_object().vendedor == self.request.user

    def form_valid(self, form):
        messages.success(self.request, "🗑 Subasta eliminada.")
        return super().form_valid(form)


# ─── Ofertar ─────────────────────────────────────────────────────────────────
@login_required(login_url="subastas:login")
@require_POST
def ofertar(request, pk):
    # Use atomic + select_for_update to prevent race conditions:
    # two users offering the same amount simultaneously would both pass
    # validation without the row lock.
    with transaction.atomic():
        # select_for_update locks the Subasta row until transaction commits.
        # Concurrent transactions block here until the first one finishes.
        subasta = get_object_or_404(
            Subasta.objects.select_for_update(),
            pk=pk,
        )

        if not subasta.esta_activa:
            messages.error(request, "Esta subasta ya no está activa.")
            # Redirect happens AFTER the transaction commits (context manager exit)
            # to avoid side effects inside atomic block.
            # But we can return inside the with block safely -- Django will commit
            # on context exit if no exception was raised.
            return redirect("subastas:detalle", pk=pk)

        if subasta.vendedor == request.user:
            messages.warning(request, "No puedes ofertar en tu propia subasta.")
            return redirect("subastas:detalle", pk=pk)

        form = OfertaForm(subasta=subasta, data=request.POST)
        if form.is_valid():
            oferta = form.save(commit=False)
            oferta.subasta = subasta
            oferta.ofertante = request.user
            oferta.save()
            messages.success(request, f"🔨 ¡Oferta de ${oferta.monto} registrada!")
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())

    return redirect("subastas:detalle", pk=pk)


# ─── Mis subastas ─────────────────────────────────────────────────────────────
class MisSubastasView(LoginRequiredMixin, ListView):
    model = Subasta
    template_name = "subastas/mis_subastas.html"
    context_object_name = "subastas"
    login_url = "subastas:login"

    def get_queryset(self):
        return Subasta.objects.filter(vendedor=self.request.user).order_by("-creado_en")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx["total"]   = qs.count()
        ctx["activas"] = qs.filter(estado="activa").count()
        ctx["cerradas"] = qs.filter(estado="cerrada").count()
        ctx["total_ofertas_recibidas"] = sum(s.total_ofertas for s in qs)
        return ctx


# ─── Auth ─────────────────────────────────────────────────────────────────────
def registro(request):
    form = RegistroForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"¡Bienvenido, {user.username}!")
        return redirect("subastas:inicio")
    return render(request, "subastas/registro.html", {"form": form})


def login_view(request):
    form = LoginForm(request=request, data=request.POST or None)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        next_url = request.GET.get("next", "")
        if not (
            next_url
            and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
            )
        ):
            next_url = "subastas:inicio"
        return redirect(next_url)
    return render(request, "subastas/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect("subastas:inicio")


# ─── Error handlers ───────────────────────────────────────────────────────────
def handler404(request, exception=None):
    return render(request, "subastas/404.html", status=404)

def handler500(request):
    return render(request, "subastas/500.html", status=500)
