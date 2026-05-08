---
name: testing-password-metrics
description: Probar end-to-end los flujos de Métricas de Contraseñas (creación, edición desde admin, reset por token) y validar que el dashboard /admin/password-metrics y la exportación a Excel se actualizan correctamente. Úsalo cuando se modifique cualquier código en `MetricasContrasena`, `PasswordMetricRepository`, `editar_usuario`, `reset_password` o el botón "Exportar Excel".
---

# Testing — Métricas Password

## Resumen rápido

- App: Flask + pyodbc + SQL Server. Puerto 5000.
- Tabla clave: `MetricasContrasena` (registra cada vez que se genera/cambia una contraseña).
- Rutas clave:
  - `/admin/usuarios` — crear/editar usuarios (admin)
  - `/admin/password-metrics` — dashboard
  - `/admin/password-metrics/export` — Excel
  - `/password/reset/<token>` — reset por enlace

## Setup local mínimo

La env-config (`update_environment_config`) ya cubre la instalación de ODBC Driver 18 y crea el venv. Para el SQL Server local, usa el snippet de la knowledge `local-db` (referencia `$MSSQL_TEST_SA_PASSWORD`, no embebas el valor literal).

`.env` apuntando al SQL Server local:
```
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_SERVER=localhost
DB_NAME=HistoriasClinicas
DB_USER=sa
DB_PASSWORD=<valor de $MSSQL_TEST_SA_PASSWORD>
DB_TRUST_SERVER_CERT=yes
FLASK_SECRET_KEY=devsecret
FLASK_DEBUG=true
EMAIL_DELIVERY_ENABLED=false
```
Luego: `source .venv/bin/activate && python app.py`.

## Credenciales

- Admin seed: `admin` / `admin123` (definido en `config/init_database.sql`).
- No hay credenciales reales que solicitar al usuario para pruebas locales.
- Gmail (`SMTP_*`) y Solana (`ALCHEMY_SOLANA_RPC_URL`) **pueden quedarse sin configurar**. Los warnings son tolerados — el alta y los cambios de contraseña funcionan igual.

## Devin Secrets Needed

Ninguno para pruebas locales contra SQL Server en Docker (la contraseña de `sa` la elige Devin como `$MSSQL_TEST_SA_PASSWORD` y no es un secreto real). Para probar el envío real del enlace de reset por correo se necesitarían `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` (no probado en estas sesiones; pedirlos como `should_save=true` con `save_scope=org` si se requieren).

## Smoke tests recomendados (en este orden)

1. **Login admin** en `/login/admin` con `admin` / `admin123`. Debe redirigir a `/admin/dashboard`.
2. **Crear usuario** en `/admin/usuarios` → "Nuevo Usuario". El modal pre-rellena 12 chars en el campo de password — si quieres una longitud específica, **`triple_click` + `type`** (no basta con `click + type`, queda concatenado).
3. **Editar usuario** en `/admin/usuarios` → "Editar". El campo "Contraseña nueva (opcional)" empieza vacío; si lo dejas así, la BD NO debe registrar una nueva métrica (verifica con `SELECT COUNT(*) FROM MetricasContrasena`). Esta es la regresión más fácil de romper.
4. **Reset password sin Gmail**: como `forgot_password` necesita SMTP, inserta un token directamente:
   ```sql
   INSERT INTO TokensRecuperacionContrasena (IdUsuario, Token, FechaExpiracion, Usado)
   VALUES (<id_usuario>, '<token_aleatorio>', DATEADD(HOUR, 1, GETDATE()), 0);
   ```
   Y navega a `http://localhost:5000/password/reset/<token>`.
5. **Exportar Excel** desde `/admin/password-metrics`. Para verificar contenido sin abrir Office, descárgalo con `curl -b <cookiejar> .../export -o m.xlsx` y léelo con `openpyxl`. Compara contra los valores del dashboard.

## Qué mirar si el dashboard / Excel no refleja un cambio de contraseña

Checkpoints en orden de probabilidad:

1. ¿Se insertó la fila en `MetricasContrasena`?
   ```sql
   SELECT TOP 5 IdUsuario, LongitudContrasena, NivelFortaleza, FechaCreacion
   FROM MetricasContrasena ORDER BY FechaCreacion DESC;
   ```
2. Si NO hay fila nueva: el bug está en el handler que cambia la password. Revisa que llame a `password_metric_repo.create(...)` después de `usuario_repo.update(...)` o `auth_service.change_password(...)`. Es la pieza que se omitió en el bug original (PR #6).
3. Si SÍ hay fila pero el dashboard no la muestra: revisa `PasswordMetricRepository.get_per_user()` — usa subquery con `MAX(FechaCreacion)` para sacar la última longitud por usuario.
4. Si el Excel muestra valores distintos al dashboard: ambos llaman `_build_password_metrics_xlsx()` con `password_metric_repo.get_per_user()` y `get_summary()`. Si difieren, alguien rompió el repositorio.
5. El campo `generation_time_ms` viene de un hidden en el formulario; si es 0 quiere decir que el JS de tracking no cargó (revisar `static/js/admin-management.js` y `static/js/password-security.js`, y los `script` tags en los templates).

## Política de contraseñas (para que los formularios no rechacen)

Min 8 caracteres, al menos 1 mayúscula, 1 minúscula, 1 número, 1 carácter especial. Ej: `Aa1!aaaa1` (9), `Aa1!aaaaaaaaa1` (14), `Reset!Pwd123` (12).

## Trampas conocidas

- **`source .env` falla** porque `DB_DRIVER=ODBC Driver 18 for SQL Server` tiene espacios y bash no parsea bien. No lo necesitas: `app.py` ya llama a `load_dotenv()`.
- El binario `google-chrome` en VMs Devin es un wrapper a CDP en `:29229`. Si el navegador real no está corriendo, lanza Chromium directamente:
  ```
  nohup env DISPLAY=:0 /opt/.devin/playwright_browsers/chromium-1097/chrome-linux/chrome \
    --user-data-dir=/home/ubuntu/.browser_data_dir --no-first-run --start-maximized \
    "<URL>" >/tmp/chrome.log 2>&1 &
  ```
  Si reusas el `user-data-dir`, borra `SingletonLock`/`SingletonCookie`/`SingletonSocket` antes de arrancar para evitar el lock stale.
- El campo de password del modal "Nuevo usuario" pre-rellena 12 chars. **`triple_click` antes de tipear** o quedará concatenado.
- Solana puede emitir warnings al alta (`ALCHEMY_SOLANA_RPC_URL` no configurado). Es esperado y no bloquea.
