# Martillo Virtual — Roadmap de Mejoras y Testing Manual

> **Estado actual:** v3 corriendo localmente ✅  
> **Objetivo:** Escalar a producción con UX profesional, seguridad y robustez

---

## 🗂️ Índice de Prioridades

| Prioridad | Área | Esfuerzo | Impacto |
|-----------|------|----------|---------|
| 🔴 Alta | Seguridad y autenticación | Medio | Crítico |
| 🔴 Alta | Lógica de pujas (race conditions) | Alto | Crítico |
| 🟡 Media | UX / UI — formularios y feedback | Medio | Alto |
| 🟡 Media | Imágenes y media | Bajo | Alto |
| 🟢 Baja | Notificaciones en tiempo real | Alto | Medio |
| 🟢 Baja | Panel de administración avanzado | Medio | Medio |

---

## 🔴 FASE 1 — Seguridad y Autenticación (Retomar primero)

### 1.1 Proteger todas las vistas con login

**Qué hacer:**

Agregar `@login_required` a cada vista que manipule datos:

```python
# subastas/views.py
from django.contrib.auth.decorators import login_required

@login_required
def crear_subasta(request):
    ...

@login_required
def hacer_puja(request, pk):
    ...
```

**Test manual:**
1. Cerrar sesión
2. Intentar acceder a `/subasta/crear/` directamente en la URL
3. ✅ Debe redirigir a `/login/?next=/subasta/crear/`
4. ✅ Después de loguearse, debe volver a la página original

---

### 1.2 Proteger vistas de propietario

Solo el creador de la subasta debe poder editarla o eliminarla.

```python
@login_required
def editar_subasta(request, pk):
    subasta = get_object_or_404(Subasta, pk=pk)
    if subasta.creador != request.user:
        raise PermissionDenied
    ...
```

**Test manual:**
1. Crear una subasta con Usuario A
2. Loguearse como Usuario B
3. Intentar acceder a `/subasta/1/editar/`
4. ✅ Debe mostrar error 403

---

### 1.3 Validar CSRF en formularios AJAX

Si usas JavaScript para enviar pujas, verificar que el token CSRF se incluya:

```javascript
// En el template, obtener el token
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

fetch('/puja/', {
    method: 'POST',
    headers: {'X-CSRFToken': csrfToken, 'Content-Type': 'application/json'},
    body: JSON.stringify({monto: monto})
})
```

**Test manual:**
1. Abrir DevTools → Network
2. Hacer una puja
3. ✅ La request POST debe incluir `X-CSRFToken` en los headers

---

## 🔴 FASE 2 — Lógica de Pujas (Race Conditions)

### 2.1 Usar select_for_update() para evitar pujas duplicadas

**Problema:** Dos usuarios pueden hacer la misma puja simultáneamente y ambas se guardan.

```python
# subastas/views.py
from django.db import transaction

@login_required
@transaction.atomic
def hacer_puja(request, pk):
    subasta = Subasta.objects.select_for_update().get(pk=pk)
    
    monto = Decimal(request.POST.get('monto'))
    
    if monto <= subasta.precio_actual:
        messages.error(request, 'Tu puja debe superar el precio actual.')
        return redirect('subasta_detail', pk=pk)
    
    if subasta.ha_terminado():
        messages.error(request, 'Esta subasta ya terminó.')
        return redirect('subasta_detail', pk=pk)
    
    Puja.objects.create(subasta=subasta, usuario=request.user, monto=monto)
    subasta.precio_actual = monto
    subasta.save()
    
    messages.success(request, f'¡Puja de ${monto} registrada!')
    return redirect('subasta_detail', pk=pk)
```

**Test manual:**
1. Abrir dos pestañas distintas con dos usuarios diferentes
2. Ambos intentan hacer una puja menor o igual a la actual al mismo tiempo
3. ✅ Solo una puja debe guardarse, la otra debe mostrar error

---

### 2.2 Verificar cierre automático de subastas

```python
# subastas/models.py
from django.utils import timezone

class Subasta(models.Model):
    ...
    fecha_fin = models.DateTimeField()
    
    def ha_terminado(self):
        return timezone.now() >= self.fecha_fin
    
    @property
    def tiempo_restante(self):
        delta = self.fecha_fin - timezone.now()
        if delta.total_seconds() <= 0:
            return "Finalizada"
        horas = int(delta.total_seconds() // 3600)
        minutos = int((delta.total_seconds() % 3600) // 60)
        return f"{horas}h {minutos}m"
```

**Test manual:**
1. Crear una subasta con `fecha_fin` 2 minutos en el futuro
2. Esperar que expire
3. Intentar hacer una puja
4. ✅ Debe mostrar "Esta subasta ya terminó"

---

## 🟡 FASE 3 — UX y Feedback al Usuario

### 3.1 Mensajes flash correctamente estilizados

Verificar que `base.html` muestra los mensajes de Django con colores apropiados:

```html
<!-- templates/base.html — dentro de <body> -->
{% if messages %}
<div class="messages-container">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
    {% endfor %}
</div>
{% endif %}
```

**Test manual:**
1. Hacer una puja exitosa → ✅ mensaje verde "¡Puja registrada!"
2. Hacer puja con monto menor → ✅ mensaje rojo con el error
3. Crear subasta → ✅ mensaje de confirmación
4. Eliminar subasta → ✅ mensaje de confirmación

---

### 3.2 Validación del lado del cliente en formularios

Agregar validación HTML5 básica:

```html
<!-- subastas/templates/subastas/subasta_form.html -->
<input type="number" 
       name="precio_inicial" 
       min="1" 
       step="0.01"
       required
       class="form-control">

<input type="datetime-local" 
       name="fecha_fin"
       min="{{ now_iso }}"
       required
       class="form-control">
```

**Test manual:**
1. Intentar enviar formulario vacío
2. ✅ El browser debe bloquear y mostrar "Este campo es requerido"
3. Intentar fecha de fin en el pasado
4. ✅ Debe mostrar error de validación

---

### 3.3 Paginación en listados

Si hay más de 10 subastas, agregar paginación:

```python
# subastas/views.py
from django.core.paginator import Paginator

def inicio(request):
    subastas_list = Subasta.objects.filter(activa=True).order_by('-fecha_creacion')
    paginator = Paginator(subastas_list, 9)  # 9 por página
    page = request.GET.get('page')
    subastas = paginator.get_page(page)
    return render(request, 'subastas/inicio.html', {'subastas': subastas})
```

**Test manual:**
1. Crear más de 9 subastas
2. ✅ Debe aparecer paginación al final
3. Navegar a página 2
4. ✅ URL debe ser `/?page=2`

---

## 🟡 FASE 4 — Imágenes y Media

### 4.1 Verificar subida de imágenes

```python
# config/settings/base.py — verificar que existan
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

```python
# config/urls.py — verificar en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Test manual:**
1. Crear subasta con imagen
2. ✅ La imagen debe aparecer en el detalle
3. Revisar que la carpeta `media/` se haya creado en el proyecto
4. ✅ El archivo debe estar en `media/subastas/nombre_imagen.jpg`

---

### 4.2 Imagen por defecto cuando no hay imagen

```html
<!-- subasta_detail.html -->
{% if subasta.imagen %}
    <img src="{{ subasta.imagen.url }}" alt="{{ subasta.titulo }}" class="img-fluid">
{% else %}
    <img src="{% static 'img/no-imagen.png' %}" alt="Sin imagen" class="img-fluid">
{% endif %}
```

**Test manual:**
1. Crear subasta sin imagen
2. ✅ Debe mostrar imagen placeholder, no un espacio vacío ni error

---

## 🟢 FASE 5 — Notificaciones (Opcional, más avanzado)

### 5.1 Email al ganador de la subasta

```python
# subastas/signals.py — crear este archivo
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Subasta

@receiver(post_save, sender=Subasta)
def notificar_ganador(sender, instance, **kwargs):
    if instance.ha_terminado() and instance.ganador:
        send_mail(
            subject=f'¡Ganaste la subasta: {instance.titulo}!',
            message=f'Felicidades, ganaste con una puja de ${instance.precio_actual}.',
            from_email='noreply@martillovirtual.com',
            recipient_list=[instance.ganador.email],
        )
```

**Test manual (con consola):**

En `settings/development.py`, usar backend de email a consola:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
1. Dejar expirar una subasta con pujas
2. ✅ El email debe aparecer impreso en la consola del servidor

---

## 🟢 FASE 6 — Panel de Admin Mejorado

### 6.1 Registrar modelos con configuración avanzada

```python
# subastas/admin.py
from django.contrib import admin
from .models import Subasta, Puja

@admin.register(Subasta)
class SubastaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'creador', 'precio_actual', 'fecha_fin', 'ha_terminado']
    list_filter = ['fecha_fin', 'creador']
    search_fields = ['titulo', 'descripcion']
    readonly_fields = ['fecha_creacion']
    ordering = ['-fecha_creacion']

@admin.register(Puja)
class PujaAdmin(admin.ModelAdmin):
    list_display = ['subasta', 'usuario', 'monto', 'fecha']
    list_filter = ['subasta', 'usuario']
    ordering = ['-fecha']
```

**Test manual:**
1. Ir a `http://127.0.0.1:8000/admin/`
2. ✅ Las subastas deben tener filtros y búsqueda
3. ✅ Las pujas deben mostrar todas las columnas
4. Usar la búsqueda para encontrar una subasta por título

---

## 📋 Checklist de Regresión (Ejecutar antes de cada sesión)

Correr esto cada vez que retomes el proyecto para asegurarte de que nada se rompió:

```
□ python manage.py check              → Sin errores de sistema
□ python manage.py migrate            → Sin migraciones pendientes  
□ python manage.py runserver          → Servidor corre sin errores
□ Abrir http://127.0.0.1:8000/        → Página de inicio carga
□ Registrar usuario nuevo             → Formulario funciona
□ Login / Logout                      → Funciona correctamente
□ Crear subasta                       → Se guarda y aparece en inicio
□ Hacer puja                          → Precio se actualiza
□ Ver mis subastas                    → Lista correcta
□ Editar subasta propia               → Cambios se guardan
□ Eliminar subasta propia             → Se elimina con confirmación
□ Intentar editar subasta ajena       → Error 403 o redirección
```

---

## 🚀 Comandos para Retomar el Proyecto

```cmd
cd C:\Users\HP\Desktop\martillo_virtual
venv\Scripts\activate
python manage.py runserver
```

Luego abrir: `http://127.0.0.1:8000/`

---

## 📌 Orden Recomendado de Implementación

1. **Hoy (30 min):** Fase 1.1 — `@login_required` en todas las vistas
2. **Próxima sesión (1 hora):** Fase 1.2 + Fase 2.1 — Permisos de propietario + select_for_update
3. **Siguiente sesión (1 hora):** Fase 3 completa — Mensajes flash + validación + paginación
4. **Sesión avanzada:** Fase 4 — Media e imágenes
5. **Cuando quieras escalar:** Fases 5 y 6

