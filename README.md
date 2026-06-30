# 🔨 MartilloVirtual

Casa de subastas en línea construida con **Django 6.0**. Proyecto de portafolio que demuestra arquitectura profesional, CRUD completo con CBVs, separación de entornos y deploy-ready con Supabase + Render.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | **Django 6.0.3**, Python 3.12+ |
| Base de datos | SQLite (dev) / PostgreSQL Supabase (prod) |
| Frontend | HTML5 + CSS custom (Design System OKLCH, dark mode, responsive) |
| Deploy | Render + Supabase + WhiteNoise + Gunicorn |
| Seguridad | HSTS, Secure Cookies, CSRF, CSP nativo Django 6.0, SSL redirect |

## Features Django 6.0 utilizadas

- **CSP nativo** (`django.middleware.csp.CSPMiddleware`) — sin librería externa `django-csp`
- **Template Partials** (`{% partialdef %}` / `{% partial %}`) — el navbar es un partial reutilizable
- **RETURNING clause** — `save()` obtiene `auto_now`/`auto_now_add` en una sola query (SQLite + PostgreSQL)
- **Background Tasks framework** — backend inmediato en dev, backend de BD en producción
- **Python 3.12+** — soporte para 3.10 y 3.11 fue eliminado en 6.0

## Características del proyecto

- ✅ CRUD completo de Subastas y Ofertas con Class-Based Views
- ✅ Autenticación nativa Django (registro, login, logout)
- ✅ Autorización por rol — solo el vendedor edita/elimina (`UserPassesTestMixin`)
- ✅ Validación de ofertas en servidor (superar precio actual)
- ✅ Countdown en tiempo real (JavaScript vanilla)
- ✅ Diseño responsive mobile-first con dark mode
- ✅ Panel admin personalizado con Inline de ofertas
- ✅ Settings multi-entorno: base / development / production
- ✅ Variables de entorno con python-dotenv
- ✅ Paginación en la grilla (9 subastas por página)
- ✅ Páginas de error 404 y 500 personalizadas
- ✅ `python manage.py seed_data` para datos demo

## Instalación local

```bash
# Requisito: Python 3.12 o superior (Django 6.0 no soporta 3.10/3.11)
python --version   # debe ser 3.12+

# 1. Clonar
git clone https://github.com/tu-usuario/martillo-virtual.git
cd martillo-virtual

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno
cp .env.example .env
# Editar .env y generar SECRET_KEY:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 5. Base de datos y datos demo
python manage.py migrate
python manage.py seed_data

# 6. Superusuario
python manage.py createsuperuser

# 7. Verificar seguridad
python manage.py check --deploy

# 8. Servidor
python manage.py runserver
```

Abre http://127.0.0.1:8000

**Usuario demo:** `don_roberto` / `Demo1234!`

## Deploy en Render + Supabase

### Variables de entorno en Render

```
DJANGO_ENV=production
SECRET_KEY=<clave-generada>
ALLOWED_HOSTS=tu-app.onrender.com
DATABASE_URL=<connection-string-supabase>
```

### Procfile

```
web: gunicorn config.wsgi --workers 2 --bind 0.0.0.0:$PORT
```

### Comandos post-deploy

```bash
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py seed_data
python manage.py check --deploy   # debe retornar System check identified no issues
```

## Estructura del proyecto

```
martillo_virtual/
├── config/
│   ├── settings/
│   │   ├── __init__.py       # Carga dev o prod según DJANGO_ENV
│   │   ├── base.py           # Común: CSP nativo, Background Tasks, template config
│   │   ├── development.py    # SQLite, DEBUG=True, sin HTTPS
│   │   └── production.py     # Supabase, DEBUG=False, todos los headers de seguridad
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── subastas/
│   ├── management/commands/
│   │   └── seed_data.py      # python manage.py seed_data
│   ├── templates/subastas/   # inicio, detalle, form, delete, dashboard, auth, errors
│   ├── models.py             # Subasta + Oferta (RETURNING clause automático)
│   ├── forms.py              # SubastaForm + OfertaForm con clean()
│   ├── views.py              # CBVs + LoginRequiredMixin + UserPassesTestMixin
│   ├── urls.py               # Namespaced URLs
│   └── admin.py              # ModelAdmin + OfertaInline
├── templates/
│   └── base.html             # Template partials ({% partialdef %}) + CSP nonce
├── static/css/
│   └── style.css             # Design system OKLCH, dark mode, responsive
├── .env.example
├── .gitignore
├── requirements.txt          # Django==6.0.3, Python 3.12+
└── README.md
```

---
Desarrollado como proyecto de portafolio — Django 6.0 Profesional.
