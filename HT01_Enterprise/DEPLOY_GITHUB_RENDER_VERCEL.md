# HT-01 Enterprise — GitHub + Render + Vercel (SIN PostgreSQL)

## Arquitectura
- **GitHub:** repositorio del código fuente.
- **Render:** API Python y archivos persistentes.
- **Vercel:** frontend estático.
- **SQLite:** base de datos local del backend, ubicada en `/var/data/ht01.sqlite3` en Render.
- **CSV:** archivos privados en `/var/data/private_uploads/`.

No se utiliza PostgreSQL, MySQL, ORM ni un servicio de base de datos externo. SQLite forma parte de Python mediante `sqlite3`.

## 1. Subir a GitHub
1. Descomprime el ZIP.
2. Crea un repositorio `ht01-enterprise`.
3. Sube el contenido de esta carpeta, manteniendo `app/`, `static/`, `docs/`, `examples/`, `render.yaml` y `vercel.json` en la raíz.
4. No subas bases de datos locales, CSV privados, claves ni contraseñas.

```bash
git init
git add .
git commit -m "HT01 Enterprise inicial"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/ht01-enterprise.git
git push -u origin main
```

## 2. Desplegar backend en Render
1. En Render elige **New > Blueprint** y conecta el repositorio.
2. Render leerá `render.yaml` y creará el servicio con un disco persistente de 1 GB.
3. En variables de entorno configura `HT01_CORS_ORIGINS` con el dominio de Vercel, por ejemplo `https://ht01-enterprise.vercel.app` (sin `/` final).
4. Espera el despliegue y abre `https://TU-SERVICIO.onrender.com/api/health`. Debe devolver `status: ok`.

**Persistencia:** la base SQLite y los CSV se guardan en `/var/data`, que debe estar montado como disco persistente. No cambies `HT01_DATA_DIR` a una ruta efímera. El plan definido en el Blueprint es `starter` porque el servicio necesita disco persistente; revisa el costo vigente en Render antes de confirmar. En un plan sin disco persistente los datos locales podrían perderse al reiniciar o desplegar.

## 3. Desplegar frontend en Vercel
1. Abre `static/config.js`.
2. Reemplaza `https://TU-SERVICIO.onrender.com` por la URL real del backend Render, conservando `https://`.
3. Guarda y sube el cambio a GitHub.
4. En Vercel importa el mismo repositorio. Framework Preset: **Other**; Root Directory: `.`.
5. Despliega y copia el dominio asignado.
6. Vuelve a Render y verifica que `HT01_CORS_ORIGINS` contenga exactamente ese dominio. Si cambias el dominio, actualiza la variable y vuelve a desplegar.

## 4. Cuentas de prueba
Consulta `docs/INSTALACION_Y_CREDENCIALES.md`. Cambia las contraseñas de demostración antes de compartir el sistema.

## 5. Desarrollo local
Deja `API_URL` vacío en `static/config.js` y ejecuta `INICIAR_HT01.bat` en Windows. La base se crea en `data/ht01.sqlite3` automáticamente.

## 6. Consideraciones
- No subir `data/*.sqlite3`, archivos privados ni secretos a GitHub.
- No usar `*` como origen CORS cuando se usan cookies.
- El backend es una implementación de demostración con servidor HTTP integrado de Python. Antes de un uso productivo real se requiere endurecimiento de seguridad, protección CSRF, rate limiting, copias de seguridad y pruebas de carga/seguridad.
- SQLite es apropiado para desarrollo, demostraciones y concurrencia moderada de una sola instancia. No está pensado para múltiples instancias de escritura simultánea.
- No cargar datos personales, sensibles o confidenciales en la demostración.
