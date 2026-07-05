# DEPLOY - MartilloVirtual

> Guia de deploy en Render + Supabase.
> 2 secciones: personal (testing) y repo (production-ready).

## Prerequisitos (comun a ambas secciones)

- Cuenta GitHub con el repo `martillo_virtual` pusheado
- Cuenta Render (https://render.com, free tier OK)
- Cuenta Supabase (https://supabase.com, free tier OK)
- Python 3.14+ local (para debugging si algo falla)

## Stack de deploy

| Componente | Servicio | Plan |
|---|---|---|
| App web (gunicorn) | Render Web Service | Free |
| DB PostgreSQL | Supabase | Free (500MB, 5 conexiones) |
| Static files | WhiteNoise (served by gunicorn) | -- |
| Cron (cerrar_subastas) | Render Cron Job | Free |
| TLS/HTTPS | Render (auto) | -- |

---

## Seccion A: Deploy personal (testing)

> Para probar el deploy por primera vez, con tu cuenta personal.

### Paso A1: Crear proyecto Supabase

1. Ir a https://supabase.com/dashboard
2. Click "New Project"
3. Nombre: `martillo-virtual`
4. Database password: generar fuerte, guardarla en password manager
5. Region: elegir la mas cercana (ej: US East para Render Oregon)
6. Plan: Free
7. Esperar ~2 minutos a que provisione

### Paso A2: Obtener DATABASE_URL

1. En Supabase dashboard: Settings > Database
2. Buscar "Connection string" > "URI"
3. Formato: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
4. Guardar este string (lo usaremos en Render)

### Paso A3: Push a GitHub

```bash
git remote add origin https://github.com/[tu-usuario]/martillo_virtual.git
git push -u origin master
# Si prefieres main: git branch -M main && git push -u origin main
```

### Paso A4: Conectar Render

1. Ir a https://dashboard.render.com
2. Click "New +" > "Blueprint"
3. Seleccionar el repo `martillo_virtual`
4. Render detecta `render.yaml` automaticamente
5. Mostrara 2 servicios: `martillo-virtual` (web) + `martillo-cerrar-subastas` (cron)
6. Click "Apply"

### Paso A5: Configurar env vars en Render

En el dashboard de Render, para el servicio `martillo-virtual`:

1. Ir a "Environment" tab
2. Setear manualmente:
   - `DATABASE_URL` = el string de Supabase (Paso A2)
3. Render ya genero `SECRET_KEY` automaticamente (generateValue: true)
4. `ALLOWED_HOSTS` ya tiene placeholder `martillo-virtual.onrender.com` -- actualizar despues del primer deploy con la URL real
5. Guardar cambios

Hacer lo mismo para el servicio cron `martillo-cerrar-subastas`:
- `DATABASE_URL` (mismo valor)
- `SECRET_KEY` (mismo valor que el web service)

### Paso A6: Primer deploy

1. Render hara build automaticamente:
   - `pip install -r requirements.txt`
   - `python manage.py collectstatic --noinput`
   - `python manage.py migrate`
2. Si todo OK, status cambia a "Live"
3. Visitar la URL (ej: `https://martillo-virtual.onrender.com`)

### Paso A7: Post-deploy (datos demo)

En Render dashboard, ir a "Shell" del web service y ejecutar:

```bash
python manage.py seed_data --reset
python manage.py backfill_ganadores
python manage.py createsuperuser  # opcional, para admin
```

Esto poblara la DB de produccion con datos demo + seteara ganadores en cerradas.

### Paso A8: Verificacion

- [ ] `https://[tu-url].onrender.com/` carga (homepage con 9 subastas activas)
- [ ] Click en una subasta -> detalle carga
- [ ] Login como `don_roberto` / `Demo1234!` -> funciona
- [ ] `/mis-subastas/` muestra stats [7, 6, 1, 0] para don_roberto
- [ ] `/admin/` redirige a login admin
- [ ] Cron job aparece en Render dashboard (corre cada hora)

### Paso A9: Actualizar ALLOWED_HOSTS

Despues del primer deploy, tomar la URL real de Render y actualizar:

1. En `render.yaml`: cambiar `martillo-virtual.onrender.com` por tu URL real
2. Commit + push -> Render auto-deploya
3. O en Render dashboard > Environment > editar `ALLOWED_HOSTS`

---

## Seccion B: Deploy del repo (production-ready)

> Para que un reviewer del repo lo deploye desde cero.

### Paso B1: Fork + clone

```bash
git clone https://github.com/[tu-usuario]/martillo_virtual.git
cd martillo_virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Paso B2: Configurar .env local

```bash
cp .env.example .env
# Editar .env y setear SECRET_KEY generada con:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Paso B3: Setup DB local

```bash
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
# Verificar en http://127.0.0.1:8000/
```

### Paso B4: Crear cuentas cloud

1. Supabase: crear project, obtener `DATABASE_URL` (ver Seccion A pasos A1-A2)
2. Render: crear cuenta, conectar GitHub

### Paso B5: Deploy en Render via Blueprint

1. Push a tu GitHub fork
2. Render dashboard > New > Blueprint > seleccionar repo
3. Render lee `render.yaml`, crea web + cron services
4. Setear `DATABASE_URL` en env vars de ambos servicios
5. Deploy automatico

### Paso B6: Verificacion post-deploy

Same checklist que Paso A8.

---

## Troubleshooting

### Error: `DisallowedHost at /`
- Causa: `ALLOWED_HOSTS` no incluye la URL de Render
- Fix: actualizar `ALLOWED_HOSTS` env var en Render con la URL correcta (sin https://)

### Error: `migrate` falla en build
- Causa: `DATABASE_URL` no configurado antes del build
- Fix: setear `DATABASE_URL` en Render env vars ANTES del primer deploy, o hacer manual `python manage.py migrate` via Shell

### Error: 500 en homepage
- Causa probable: `seed_data` no corrio
- Fix: Render Shell > `python manage.py seed_data --reset`

### Error: static files 404
- Causa: `collectstatic` no corrio en build
- Fix: verificar que `buildCommand` en render.yaml incluye `python manage.py collectstatic --noinput`

### Cron no corre
- Verificar en Render dashboard > Cron Jobs > logs
- El schedule `0 * * * *` corre al minuto 0 de cada hora
- Para testing: cambiar a `*/5 * * * *` (cada 5 min)

### Supabase connection limit
- Free tier: 5 conexiones simultaneas
- `conn_max_age=600` en settings (10 min) reusa conexiones
- Si tienes error "too many connections": considerar pooler mode (pgBouncer) en Supabase

---

## URLs importantes (post-deploy)

- App: `https://[tu-url].onrender.com/`
- Admin: `https://[tu-url].onrender.com/admin/`
- Render dashboard: `https://dashboard.render.com`
- Supabase dashboard: `https://supabase.com/dashboard`
- GitHub repo: `https://github.com/[tu-usuario]/martillo_virtual`

## Usuarios demo (post seed_data)

| Username | Password | Rol |
|---|---|---|
| don_roberto | Demo1234! | Vendedor + ofertante |
| maria_coleccionista | Demo1234! | Vendedora + ofertante |
| pedro_antiguo | Demo1234! | Ofertante |
| elena_arte | Demo1234! | Vendedora + ofertante |
| lucas_nuevo | Demo1234! | Ofertante |
| [tu superuser] | [tu password] | Admin |
