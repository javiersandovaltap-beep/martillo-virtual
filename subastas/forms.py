from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Subasta, Oferta

User = get_user_model()


class SubastaForm(forms.ModelForm):
    fecha_cierre = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Fecha de cierre",
        help_text="La subasta cerrará automáticamente en esta fecha.",
    )

    class Meta:
        model = Subasta
        fields = ["titulo", "descripcion", "imagen", "precio_inicial", "fecha_cierre"]
        widgets = {
            "titulo":         forms.TextInput(attrs={"placeholder": "Ej: Reloj de bolsillo 1920"}),
            "descripcion":    forms.Textarea(attrs={"placeholder": "Describe el estado, historia, materiales…", "rows": 4}),
            "precio_inicial": forms.NumberInput(attrs={"placeholder": "0.00", "min": "0"}),
        }
        labels = {
            "titulo":         "Título de la pieza",
            "descripcion":    "Descripción",
            "imagen":         "Imagen del producto",
            "precio_inicial": "Precio base ($)",
        }

    def clean_fecha_cierre(self):
        fecha = self.cleaned_data["fecha_cierre"]
        if fecha <= timezone.now():
            raise forms.ValidationError("La fecha de cierre debe ser en el futuro.")
        return fecha


class OfertaForm(forms.ModelForm):
    class Meta:
        model = Oferta
        fields = ["monto"]
        widgets = {"monto": forms.NumberInput(attrs={"min": "0", "step": "1"})}
        labels = {"monto": "Tu oferta"}

    def __init__(self, subasta=None, *args, **kwargs):
        self._subasta = subasta
        super().__init__(*args, **kwargs)

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if self._subasta and monto <= self._subasta.precio_actual:
            raise forms.ValidationError(
                f"Tu oferta debe superar el precio actual de ${self._subasta.precio_actual}."
            )
        return monto


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo electrónico")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            "username":  "Nombre de usuario",
            "password1": "Contraseña",
            "password2": "Confirmar contraseña",
        }
        help_texts = {"username": None}


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuario"
        self.fields["password"].label = "Contraseña"
        self.fields["username"].widget.attrs.update({"autofocus": True, "placeholder": "tu_usuario"})
        self.fields["password"].widget.attrs.update({"placeholder": "••••••••"})
