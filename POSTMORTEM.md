# POSTMORTEM - MartilloVirtual

> Reflexion final del proyecto. Experimento 3 modelos re-escoped por L29 (rate limits).

## Resumen del proyecto

**MartilloVirtual** -- casa de subastas online construida con Django 6.0. Proyecto de portafolio que evoluciono desde un zip inconcluso hasta una app deploy-ready con 125 tests, 97% coverage, protocolo de ganador, notificaciones email, y deploy en Render + Supabase.

### Metricas finales

| Metrica | Valor |
|---|---|
| Fases completadas | 5 (de 6 planeadas) + Phase 4.5 (pre-deploy polish) |
| Commits totales | ~60 |
| Tests automatizados | 125 pasando |
| Coverage total | 97% (views 99%, models 100%) |
| Bugs cerrados | 30+ |
| Lessons documentadas | 9 (L21-L29) |
| Decisiones de diseño | 34 (D01-D34) |
| Tags estables | 7 (v0.1 a v0.6 + v1.0) |
| Modelos LLM usados | 3 (Minimax M2.7, Nemotron, GLM-5.1) |

---

## Fase por fase: que funciono, que no

### Phase 0 - Recovery + Migrations Audit (v0.1-stable)

**Funciono:**
- Baseline limpio: venv, git init, .gitignore, SECRET_KEY rotada
- Fix de seed_data.py (Subasta.ESTADO_ACTIVA bug)
- Eliminacion de martillo_v3/ (snapshot stale)

**No funciono:**
- L21: git show --stat mostro archivos duplicados (artefacto de presentacion, no bug real)
- Claude Code corrompio UTF-8 en .md con non-ASCII (L08 confirmada)

### Phase 1 - Critical blockers + Security audit (v0.2-stable)

**Funciono:**
- 8 bugs cerrados: S02-S10, B07-B02
- Open redirect fixeado con `url_has_allowed_host_and_scheme` (5/5 attack vector tests)
- Race condition fixeado con `transaction.atomic + select_for_update` (2/2 race tests)
- Method validation (`@require_POST`) en ofertar y logout

**No funciono:**
- L23: Layer 1 (`python manage.py check`) NO valida logica de seguridad. Un fix incorrecto (`allowed_hosts=None`) pasaba Layer 1. Atrapado por test empírico.
- L25: Django test client usa `testserver` como HTTP_HOST default, causando DisallowedHost 400. Falso positivo en tests de B07.
- NIM timeout de 10 minutos durante B02 (L22 confirmada)

### Phase 2 - Workflow discipline + Config split (v0.3-stable)

**Funciono:**
- STATICFILES_STORAGE condicional (dev vs prod)
- crispy_forms eliminado (deps + INSTALLED_APPS + settings)
- .env.example completo con comentarios
- Cleanup de imports muertos + trailing newline

**No funciono:**
- Fase mecanica, sin sorpresas. 0 lessons nuevas.

### Phase 3 - Estabilizacion (v0.4-stable)

**Funciono:**
- N+1 eliminados: InicioView 20→2 queries, MisSubastasView ~12→4 queries
- Indexes en Subasta.estado, fecha_cierre, Oferta.creado_en
- fecha_inicio eliminado (redundante con creado_en)
- Management command `cerrar_subastas`
- UX fixes: badge "En vivo" condicional, stats consistentes, divider por field name

**No funciono:**
- L27: `@property` es data descriptor, annotations con mismo nombre NO la sombrean. Atrapado por test de query count.
- L28: Filtrar queries por substring da false positives cuando hay COUNT embebidos.
- L29: Rate limits de LLM free tier se agotaron. Switch a 100% bash scripts.

### Phase 4 - Hardening (v0.5-stable)

**Funciono:**
- 94 tests escritos (models + forms + views + management + ratelimit)
- Coverage 97% (objetivo 80% superado)
- django-ratelimit: login 5/m, registro 3/h
- Bug real atrapado por tests: cerrar_subastas audit trail vacio despues de `.update()` (queryset re-evaluaba con filtro original)

**No funciono:**
- django-ratelimit E003: LocMemCache no es compartido entre workers. Silenciado con SILENCED_SYSTEM_CHECKS (aceptable para dev/portfolio).

### Phase 4.5 - Pre-deploy polish (v0.6-stable)

**Funciono:**
- Seed expandido: 15 subastas, 5 usuarios, ~14 ofertas
- Protocolo de ganador completo: FK + cerrar_subastas + backfill + signal email
- InicioView ?estado= filter con tabs (activas/cerradas/todas)
- Dashboard "Mis ofertas recientes"
- Dark mode persiste via localStorage
- 3-tier finalizada logic (ganador > con ofertas > sin ofertas)

**No funciono:**
- Script v1 de Commit 6 fallo silenciosamente (string matching rigido). Fix con markers flexibles.
- Data inconsistency: subastas cerradas tenian creado_en > fecha_cierre. Fix: backdate creado_en.

### Phase 5 - Deploy + Reflection (v1.0-stable)

**Funciono:**
- Dockerfile (ejercicio aprendizaje, multi-stage build)
- Procfile + runtime.txt + .python-version
- render.yaml (Blueprint IaC con web + cron services)
- DEPLOY.md dual (personal + repo)
- README reescrito sin claims falsos (S08 cerrado)
- backfill_ganadores command para data consistency

**No funciono:**
- No se probo deploy real en Render (requiere cuentas cloud manuales)

---

## Experimento 3 modelos (re-escoped por L29)

### Plan original

Comparar 3 modelos (Minimax M2.7, Nemotron, GLM-5.1) en 5 tipos de tareas:
1. Docs operacionales
2. Tests Django
3. Templates HTML
4. Migraciones DB
5. Refactor de views

### Realidad (L29 impact)

**L29:** Free tier LLM APIs tienen rate limits duro (32 req/worker en NIM). En un proyecto de ~60 commits con multiples rondas de validacion, los rate limits se agotaron antes de completar el trabajo.

### Lo que si pudimos comparar

| Tipo de tarea | Modelo usado | Resultado |
|---|---|---|
| Settings fixes (mecanica) | Nemotron | Correcto, sin issues |
| Open redirect fix (security) | Minimax M2.7 | Intento fix incorrecto primero (`allowed_hosts=None`), se autocorrigio |
| Race condition (complex) | Minimax M2.7 | Correcto, pero timeout de 10min (L22) |
| Method validation (mecanica) | Nemotron | Correcto |
| Templates fixes (4 en batch) | GLM-5.1 | Intento creatividad primero (cambio no pedido), se autocorrigio |
| N+1 fixes con annotate (ORM complejo) | Minimax M2.7 | 4 iteraciones, eventualmente correcto con Subqueries |
| Migrations (schema) | Minimax M2.7 | Correcto |
| Tests de models/forms/views | bash scripts (L29) | N/A -- no se uso LLM |

### Observaciones por modelo

**Minimax M2.7 (opus slot):**
- Mejor para: razonamiento complejo (race conditions, ORM annotate, security)
- Debilidad: timeouts bajo load (L22), rate limits (L29)
- Tendencia: sobre-pensa, genera multiples iteraciones

**Nemotron (sonnet slot):**
- Mejor para: tareas mecanicas (settings, imports, cleanup)
- Debilidad: menos razonamiento para security fixes
- Tendencia: directo al grano, menos iteraciones

**GLM-5.1 (haiku slot):**
- Mejor para: templates HTML, ediciones mecanicas
- Debilidad: "mejora" mas alla del spec (añade cambios no pedidos)
- Tendencia: creativo pero requiere validacion empirica (L23)

### Conclusion del experimento

**L29 cambio el scope:** en lugar de "comparar 3 modelos en 5 tipos de tareas", el experimento real fue "comparar modelos donde disponible, documentar rate limit impact, y confiar en scripts bash para el resto".

**Patron observado:** para proyectos de este tamaño (~60 commits), los rate limits del free tier se agotan alrededor del commit 30-40. A partir de ahi, scripts bash deterministicos son mas confiables que LLMs.

**Recomendacion para proyectos pagos:** con Claude Code + Claude real (sin proxy free tier), el flujo seria viable end-to-end. El bottleneck fue el proxy free tier, no el flujo en si.

---

## Lessons learned (L21-L29)

| Lesson | Fase | Descripcion |
|---|---|---|
| L21 | Phase 0 | git show --stat puede mostrar duplicados (artefacto) |
| L22 | Phase 1 | NIM timeouts transitorios, no descartan modelo |
| L23 | Phase 1 | Layer 1 NO valida logica de seguridad |
| L24 | Phase 1 | Git Bash + Windows native commands (taskkill) |
| L25 | Phase 1 | Django test client HTTP_HOST=testserver false positive |
| L27 | Phase 3 | @property es data descriptor, annotations no la sombrean |
| L28 | Phase 3 | Query filter por substring da false positives |
| L29 | Phase 3 | Free tier LLM rate limits se agotan en proyectos medianos |

(L26 fue excluida por ser meta del hilo de orquestacion, no del proyecto)

## Decisiones de diseño (D01-D34)

34 decisiones documentadas en SESSION_STATE.md y ALTERNATIVES.md. Highlights:

- D08: pytest-django (mejor output, fixtures, parametrize)
- D10: cerrar_subastas via management command + cron (no celery)
- D25-D28: testing stack (pytest-django, tests/ folder, N+1 regression, rate limiting)
- D29-D34: protocolo de ganador, email signal, InicioView filter, dark mode localStorage

---

## Lo que fue bien

1. **Flujo senior con 3 capas:** orquestacion (chat) + ejecucion (Claude Code/scripts) + revision (chat + tests empiricos). Funciono.
2. **Tests como red de seguridad:** atraparon bug real en cerrar_subastas audit trail. Sin tests, hubiera llegado a produccion.
3. **SESSION_STATE.md como source of truth:** mantener estado sincronizado entre sesiones fue clave.
4. **Switch a scripts bash cuando LLM se agoto (L29):** permitio terminar el proyecto sin depender de disponibilidad de API.
5. **Evidence before hypothesis:** cada fix se valido empiricamente (attack vector tests, query count, etc.), no solo con Layer 1.

## Lo que no fue bien

1. **Rate limits del free tier (L29):** proyecto de este tamaño excede los 32 req/worker de NIM. Hubo que switchear a scripts bash a mitad de Phase 3.
2. **Scripts con string matching rigido:** multiples veces fallen silenciosamente cuando el formato real differia del esperado (Commits 3, 6, 7 de Phase 4.5). Fix: markers flexibles.
3. **Timeouts de Minimax (L22):** 10 minutos frozen, requirio nudge del usuario.
4. **False positives en tests (L25, L28):** tests mal formulados daban PASS cuando el fix no funcionaba. Atrapado por validacion visual del usuario.
5. **Data inconsistency detectada tarde:** subastas cerradas con creado_en > fecha_cierre. No era bug de codigo, era bug de data. Atrapado por inspeccion visual del usuario.

---

## Future enhancements

Documentado en README "Lo que NO esta incluido":

1. **Payment gateway:** no integrado (decision de scope). Para produccion real: MercadoPago/Stripe con webhooks.
2. **Real-time notifications:** solo email. Para subastas en tiempo real: Django Channels + WebSocket.
3. **Image upload con storage cloud:** imagenes locales. Para produccion: S3/Cloudinary + django-storages.
4. **CSP nativo Django 6.0:** no configurado. Requiere mover JS inline a external files o usar nonces.
5. **Template partials:** no usados. Podrian usarse para navbar reutilizable.
6. **Background tasks framework:** no configurado. Para envio async de emails: Django 6.0 tasks o celery.
7. **Admin customization:** default Django admin. Para portafolio avanzado: override base_site.html con branding.
8. **Redis cache:** LocMemCache en dev. Para prod multi-worker: Redis o DatabaseCache.

---

## Conclusion

**MartilloVirtual paso de un zip inconcluso a una app deploy-ready en 5 fases + 1 fase de polish.**

El flujo senior con 3 modelos valido el patron: planificar (chat) + ejecutar (Claude Code/scripts) + revisar (tests empiricos). L29 (rate limits) forzo una pivote a scripts bash a mitad de camino, pero el resultado final cumple el objetivo: portafolio profesional, testeado, deployable, escalable.

**Para el siguiente proyecto:** si se usa Claude Code con Claude real (paid), el flujo es viable end-to-end. Si se mantiene free tier, planificar budget de LLM requests y tener scripts bash como fallback desde el inicio.

---

*Documento generado en Phase 5, Commit 7. Tag final: v1.0-stable.*

---

## UPDATE: Deploy Exitoso (Post-Project)

El deploy en Render + Supabase se completó exitosamente.

**URL pública:** https://martillo-virtual.onrender.com

**Lecciones del deploy real:**
1. **IPv6 vs IPv4 en Render Free Tier:** Render intentó conectar a Supabase via IPv6 por defecto, fallando con "Network is unreachable". Fix: usar el Connection Pooler de Supabase (host `.pooler.supabase.com`) que fuerza IPv4.
2. **`releaseCommand` en Free Tier:** aunque la documentación de Render lo soporta, en la práctica el plan Free no lo ejecutó de forma fiable.
3. **`buildCommand` chaining:** para correr comandos de DB (migrate, seed) en el build de Render Free, fue necesario encadenarlos con `&&` en una sola línea en lugar de multiline (`|`).
4. **Render Shell es de pago:** para poblar la DB sin acceso SSH, movimos `seed_data` al `buildCommand` temporalmente, luego lo removimos una vez poblada.

El proyecto está oficialmente EN PRODUCCIÓN y listo para ser añadido al portafolio profesional.
