# HT-01 Enterprise — GitHub + Render + Vercel (persistencia JSON, sin PostgreSQL/SQLite en disco)

## Arquitectura
- **GitHub:** repositorio del proyecto.
- **Vercel:** frontend estático y enlace público.
- **Render:** API Python.
- **Persistencia:** archivo temporal `/tmp/ht01_data/ht01_store.json` y archivos CSV en `/tmp/ht01_data/private_uploads/`.
- No se crea un servicio PostgreSQL ni un archivo SQLite persistente. El backend utiliza un espacio SQL temporal en memoria para ejecutar las operaciones existentes; los datos durables se escriben en JSON. Si el requisito es no utilizar ni siquiera el motor SQLite en memoria, el backend tendría que reescribirse por completo con operaciones JSON nativas.

## 1. GitHub
1. Descomprime el ZIP.
2. Sube TODO el contenido de `HT01_Enterprise` a la raíz de un repositorio.
3. Verifica que `app/`, `static/`, `docs/`, `examples/`, `render.yaml` y `vercel.json` queden en la raíz.

## 2. Render — solo un Web Service
1. Render → **New + → Web Service** (no PostgreSQL).
2. Conecta el repositorio.
3. Configura:
   - Runtime: Python 3
   - Branch: `main`
   - Root Directory: vacío
   - Build Command: `python -m compileall -q app`
   - Start Command: `python app/server.py`
   - Instance: Starter
4. **No agregues Persistent Disk**: para mantener el despliegue gratuito, esta configuración usa almacenamiento temporal.
5. Variables:
   - `PYTHON_VERSION` = `3.12.7`
   - `HT01_SECRET` = secreto largo y aleatorio
   - `HT01_DATA_DIR` = `/tmp/ht01_data`
   - `HT01_CROSS_SITE_COOKIE` = `1`
   - `HT01_CORS_ORIGINS` = dominio Vercel exacto, por ejemplo `https://ht01-enterprise.vercel.app`
6. Despliega. Verifica `https://TU-SERVICIO.onrender.com/api/health`.

## 3. Vercel — frontend
1. Abre `static/config.js` y reemplaza `https://TU-SERVICIO.onrender.com` por la URL real de Render.
2. Guarda y sube el cambio a GitHub.
3. Vercel → Add New → Project → importa el mismo repositorio.
4. Framework Preset: **Other**.
5. Build Command: vacío.
6. Output Directory: `static`.
7. Deploy.
8. Copia el dominio Vercel y confirma que `HT01_CORS_ORIGINS` en Render contiene ese dominio exacto. Si lo agregas o cambias, vuelve a desplegar Render.

## 4. Cuentas iniciales
Consulta `docs/INSTALACION_Y_CREDENCIALES.md`. Cambia las contraseñas de demostración antes de compartir el enlace.

## 5. Persistencia y límites
En el plan Free, `/tmp/ht01_data` es almacenamiento efímero. Los registros JSON y CSV pueden perderse al reiniciar, volver a desplegar o reciclar la instancia; no uses esta modalidad para información importante o confidencial. No agregues un Persistent Disk ni cambies al plan Starter si no quieres pagar. Esta modalidad es solo para pruebas/demostración.

## 6. Importante sobre “sin base de datos”
No se instala PostgreSQL ni se guarda un archivo SQLite. Para conservar la lógica actual del proyecto, se usa SQLite solo como motor temporal en memoria, mientras que la persistencia real se escribe en JSON. Una versión que no importe ni use SQLite requeriría reemplazar toda la capa de consultas SQL por una implementación JSON nativa.
