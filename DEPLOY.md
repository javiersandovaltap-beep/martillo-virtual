# DEPLOY - MartilloVirtual

> Guia tecnica de despliegue en Render (Free Tier) + Supabase.

## Prerequisitos

- Cuenta GitHub con el repo `martillo-virtual` (o un fork)
- Cuenta Render (https://render.com)
- Cuenta Supabase (https://supabase.com)
- Python 3.14+ local

## Stack de Despliegue

| Componente | Servicio | Plan |
|---|---|---|
| App Web (Gunicorn) | Render Web Service | Free |
| Base de Datos | Supabase PostgreSQL | Free |
| Static Files | WhiteNoise | Integrado |
| Cierre Automatico (Cron) | Render Cron Job | Free |
| TLS/HTTPS | Render | Automatico |

---

## Pasos de Despliegue

### 1. Configuracion Local Inicial

```bash
git clone https://github.com/[tu-usuario]/martillo-virtual.git
cd martillo-virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Generar SECRET_KEY y pegarla en .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

python manage.py migrate
python manage.py seed_data
python manage.py runserver
```
Verificar en `http://127.0.0.1:8000/`.

### 2. Configuracion de Supabase

1. Crear proyecto en Supabase.
2. Ir a **Project Settings > Database**.
3. En **Connection String**, seleccionar **Transaction** o **Session** mode (Pooler).
   - *Nota tecnica:* Es obligatorio usar el Pooler URI (`aws-0-[region].pooler.supabase.com`) en lugar de la conexion directa para asegurar compatibilidad IPv4 en Render.
4. Copiar la **URI**. Formato: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`

### 3. Despliegue en Render

1. Push del repo a GitHub.
2. En Render Dashboard, click **New > Blueprint**.
3. Seleccionar el repo. Render detectara `render.yaml` y creara 2 servicios:
   - `martillo-virtual` (Web Service)
   - `martillo-cerrar-subastas` (Cron Job)
4. En la pantalla de configuracion, setear las variables de entorno para **ambos** servicios:
   - `DATABASE_URL`: Pegar la URI del Pooler de Supabase.
   - `SECRET_KEY`: Usar la misma generada localmente.
   - `ALLOWED_HOSTS`: `martillo-virtual.onrender.com` (o la URL final de Render).
5. Click **Apply**.

### 4. Build y Release

- Render ejecutara automaticamente el `buildCommand` definido en `render.yaml`.
- Los comandos (`pip install`, `collectstatic`, `migrate`) estan encadenados con `&&` para asegurar su ejecucion secuencial.
- *Nota tecnica:* El plan Free no soporta `releaseCommand` ni acceso Shell. Si se requiere poblar la DB, anadir temporalmente `python manage.py seed_data` al `buildCommand`.

### 5. Verificacion Post-Deploy

- [ ] La URL publica carga la homepage con subastas activas.
- [ ] El login funciona con usuarios demo (`don_roberto` / `Demo1234!`).
- [ ] `/mis-subastas/` muestra el dashboard con stats.
- [ ] El Cron Job aparece activo en el dashboard de Render.

---

## Troubleshooting Tecnico

| Error | Causa | Solucion |
|---|---|---|
| `Network is unreachable` en migrate/build | Render intenta conectar via IPv6 a Supabase. | Usar el Connection Pooler URI de Supabase (fuerza IPv4). |
| `DisallowedHost at /` | `ALLOWED_HOSTS` no incluye la URL de Render. | Actualizar la env var en Render con el dominio exacto (sin `https://`). |
| `migrate` falla en build | `DATABASE_URL` no configurada antes del build. | Setear la env var en Render antes del primer deploy. |
| 500 Error / Pagina vacia | DB sin datos seed. | Anadir `python manage.py seed_data` al `buildCommand` temporalmente, hacer deploy, y luego removerlo. |
| Static files 404 | `collectstatic` no corrio o `STATICFILES_STORAGE` mal configurado. | Verificar que `buildCommand` incluya `python manage.py collectstatic --noinput`. |

---

## URLs y Credenciales Demo

- **App URL:** `https://[tu-app].onrender.com/`
- **Admin URL:** `https://[tu-app].onrender.com/admin/` (requiere crear superuser)
- **Usuarios Demo:** `don_roberto`, `maria_coleccionista`, `pedro_antiguo`, `elena_arte`, `lucas_nuevo`
- **Password Demo:** `Demo1234!`
