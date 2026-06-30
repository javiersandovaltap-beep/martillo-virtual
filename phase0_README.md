# Phase 0 - Recovery + Migrations Audit

> Archivos para ejecutar Fase 0 del flujo senior con 3 modelos.
> Proyecto: MartilloVirtual (Django 6.0.3)

## Que contiene este zip

```
phase0/
├── scripts/
│   ├── phase0_main.sh          # Script principal de Fase 0
│   └── phase0_validate.sh      # Script de validacion (output para pegar)
├── SESSION_STATE.md            # Source of truth (ASCII puro)
├── CLAUDE.md                   # Reglas operativas para Claude Code (ASCII puro)
├── AGENTS.md                   # Arquitectura de agents 3 capas (ASCII puro)
├── ALTERNATIVES.md             # Decisiones de diseno (ASCII puro)
├── .claude/
│   └── agents/
│       ├── django-backend.md   # Subagent backend
│       ├── django-frontend.md  # Subagent frontend
│       ├── django-test.md      # Subagent tests
│       ├── django-security.md  # Subagent security
│       ├── django-devops.md    # Subagent devops
│       └── django-docs.md      # Subagent docs
└── phase0_README.md            # Este archivo
```

## Como ejecutar Fase 0

### Pre-requisitos

1. Tener el proyecto martillo_virtual extraido en una carpeta (donde esta manage.py)
2. Tener Python 3.12+ instalado (verificar con `python --version`)
3. Tener Git instalado (`git --version`)
4. Tener Git Bash instalado (si estas en Windows)

### Paso 1: Extraer este zip en la raiz del proyecto

Extrae el contenido de este zip DIRECTAMENTE en la raiz del proyecto (donde esta manage.py).

La estructura debe quedar asi:

```
martillo_virtual/
├── manage.py
├── requirements.txt
├── .env                    # existe, sera regenerado
├── db.sqlite3              # existe, sera eliminado
├── martillo_v3/            # existe, sera eliminado
├── venv/                   # existe, sera eliminado y recreado
├── config/
├── subastas/
├── static/
├── templates/
├── scripts/                # NUEVO (de este zip)
│   ├── phase0_main.sh
│   └── phase0_validate.sh
├── SESSION_STATE.md        # NUEVO (de este zip)
├── CLAUDE.md               # NUEVO (de este zip)
├── AGENTS.md               # NUEVO (de este zip)
├── ALTERNATIVES.md         # NUEVO (de este zip)
└── .claude/                # NUEVO (de este zip)
    └── agents/
        └── *.md
```

### Paso 2: Abrir Git Bash en la carpeta del proyecto

En Windows: click derecho en la carpeta > "Git Bash Here"

### Paso 3: Ejecutar script principal

```bash
bash scripts/phase0_main.sh
```

El script hara automaticamente:
1. Eliminar martillo_v3/ (snapshot stale)
2. Eliminar venv/ viejo y db.sqlite3 viejo
3. Fix requirements.txt (psycopg 3.2.4 -> 3.3.3)
4. Fix seed_data.py (Subasta.ESTADO_ACTIVA -> Subasta.Estado.ACTIVA)
5. Crear venv nuevo con Python detectado
6. pip install -r requirements.txt
7. Generar nueva SECRET_KEY y crear .env
8. python manage.py check (Layer 1)
9. python manage.py showmigrations + migrate --plan (auditoria)
10. python manage.py migrate (aplicar a DB fresca)
11. python manage.py seed_data (6 subastas + user don_roberto)
12. git init + commit baseline + tag v0.1-stable

Si algo falla, el script se detiene (set -e). Lee el error, corrigelo, y vuelve a ejecutar el script (es idempotente).

### Paso 4: Crear superuser (manual, interactivo)

```bash
source venv/Scripts/activate    # Windows Git Bash
# o: source venv/bin/activate   # Linux/Mac

python manage.py createsuperuser
```

Te pedira username, email, password. Anota estos datos.

### Paso 5: Validar Layer 3 (opcional pero recomendado)

```bash
python manage.py runserver
```

Abre http://127.0.0.1:8000/ en tu browser. Verifica:
- Pagina de inicio carga con 6 subastas
- Click en una subasta -> detalle carga
- Click en "Ingresar" -> login form carga
- Login con don_roberto / Demo1234! -> funciona
- http://127.0.0.1:8000/admin/ -> redirect a login admin
- Login con tu superuser -> admin panel carga

Ctrl+C para parar el servidor.

### Paso 6: Ejecutar script de validacion

```bash
bash scripts/phase0_validate.sh
```

Este script genera un output completo que debes PEGAR al chat senior.

El output incluye:
- Python version
- Django version
- Layer 1 (check)
- showmigrations
- DB tablas y counts
- Git log + tag
- Archivos operacionales (ls)
- .claude/agents/ (ls)
- SESSION_STATE.md (primeras 40 lineas)
- .env (sin SECRET_KEY)
- requirements.txt
- seed_data.py fix verificado

## Que hacer despues

1. Copia TODO el output de `phase0_validate.sh`
2. Pegalo en el chat senior
3. Espera aprobacion de Fase 0
4. Si aprobado, arrancamos Fase 1 (Critical blockers + Security audit)

## Troubleshooting

### Error: python no encontrado
Instala Python 3.12+ desde https://www.python.org/downloads/
Verifica: `python --version` debe mostrar 3.12 o superior

### Error: pip install falla
- Verifica conexion a internet
- Prueba: `python -m pip install --upgrade pip`
- Si psycopg falla: en Windows puede faltar Microsoft Visual C++ Build Tools

### Error: git commit falla "Author identity unknown"
El script configura user.email y user.name por defecto, pero si falla:
```bash
git config user.email "tu@email.com"
git config user.name "Tu Nombre"
```
Y vuelve a correr el script.

### Error: secret_key en .env no funciona
Verifica que el .env este en la raiz del proyecto (no en subcarpeta).
Verifica permisos: el archivo debe ser legible por el usuario que corre Python.

### Error: migrate falla
Posible migracion corrupta. Prueba:
```bash
rm db.sqlite3
python manage.py migrate
```

### Error: seed_data falla con AttributeError
El fix deberia haberse aplicado. Verifica:
```bash
grep "ESTADO_ACTIVA" subastas/management/commands/seed_data.py
```
Si muestra algo, el fix no se aplico. Ejecuta manualmente:
```bash
sed -i 's/Subasta.ESTADO_ACTIVA/Subasta.Estado.ACTIVA/' subastas/management/commands/seed_data.py
```

## Notas

- El script es idempotente: puedes ejecutarlo multiples veces sin romper nada
- Si algo falla a mitad, corrige el problema y vuelve a ejecutar
- El tag v0.1-stable se fuerza (-f) cada vez, asi que no se acumulan tags
- El commit baseline se hace una sola vez (si ya existe, git commit falla sin romper nada)
