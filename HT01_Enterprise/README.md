# HT-01 Enterprise — Plataforma Inteligente de Análisis y Explicación de IA

Aplicación web local, modular y funcional que integra los dos documentos HT-01: documentación técnica y manual de procedimiento. Implementa autenticación por roles, aprendizaje, importación y perfilado CSV, configuración de prácticas, ejecución de algoritmos ML, resultados, historial, reportes y auditoría.

## Publicación en GitHub, Render y Vercel

Consulta `DEPLOY_GITHUB_RENDER_VERCEL_JSON.md`. Render Free aloja la API Python con almacenamiento temporal; Vercel Free sirve el frontend estático. En Render Free los datos locales pueden perderse al reiniciar o desplegar. El proyecto funciona sin PostgreSQL ni servicios externos de base de datos.

## Inicio rápido (Windows 10/11)

1. Extraiga `HT01_Enterprise.zip` en una carpeta, por ejemplo `C:\HT01_Enterprise`.
2. Instale Python 3.10 o superior desde <https://www.python.org/downloads/> y active **Add Python to PATH**.
3. Abra la carpeta extraída y ejecute `INICIAR_HT01.bat`.
4. Se abrirá el navegador en `http://127.0.0.1:8000` (si no se abre, copie esa dirección manualmente).
5. Inicie sesión con una de las cuentas de prueba descritas en `docs/INSTALACION_Y_CREDENCIALES.md`.

No necesita Node.js, internet ni instalar paquetes Python: el backend usa la biblioteca estándar de Python y SQLite. La tipografía remota puede usar Google Fonts cuando exista conexión; la interfaz sigue funcionando sin ella.

## Módulos incluidos

- Dashboard e indicadores de actividad.
- Fundamentos IA: IA, ML, datos/información, supervisado/no supervisado, clasificación/regresión y flujo ML; progreso por unidad.
- Centro de datos: datasets sintéticos, importación CSV, validación, vista previa, tipos, nulos, duplicados y perfilado.
- Laboratorio ML: configuración supervisada/no supervisada, objetivo, variables numéricas y validación de compatibilidad.
- Pipeline y resultados: Gaussian Naive Bayes (clasificación), regresión lineal multivariable (regresión) y K-Means (agrupamiento), con división 80/20 cuando aplica.
- Historial con filtros y detalle persistido por identificador.
- Informe HTML imprimible/guardable como PDF.
- Auditoría de operaciones relevantes.
- Administración de cuentas y roles (solo administrador).

## Cuentas iniciales

Ver `docs/INSTALACION_Y_CREDENCIALES.md`. Cambie las contraseñas iniciales antes de cualquier despliegue compartido.

## Persistencia y archivos

La base SQLite se crea en `data/ht01.sqlite3`; los CSV importados se conservan bajo `data/private_uploads/` con nombres internos aleatorios. Para reiniciar todos los datos de prueba, cierre el servidor y elimine ambos elementos; al volver a iniciar se recrearán las cuentas y datasets sintéticos.

## Pruebas

Ejecute `python tests/test_core.py` desde la carpeta del proyecto. Para probar el flujo completo, consulte `docs/PRUEBAS_Y_ACEPTACION.md`.

## Importante: alcance y uso responsable

Esta es una versión funcional de demostración académica/local, no un despliegue productivo certificado. Los algoritmos incluidos son implementaciones educativas reales en Python puro; no son un motor industrial ni sustituyen validación experta. Las entradas numéricas incompletas se excluyen de la ejecución y se informan. El CSV no debe contener datos personales, sensibles ni información real confidencial.

En Render Free el almacenamiento local es temporal y no garantiza conservar datos tras reinicios o despliegues. Para datos duraderos se necesitaría almacenamiento externo; no se incluye uno de pago en esta configuración. También se requieren endurecimiento de sesiones/CSRF, límites y antivirus de archivos, política de retención y pruebas de seguridad. El servidor integrado de Python de esta versión es una base de demostración y debe endurecerse antes de uso productivo.

## CSV de práctica

En `examples/` se incluyen tres archivos para probar la importación: clasificación (`solicitudes_clasificacion.csv`), regresión (`ventas_regresion.csv`) y agrupamiento (`clientes_agrupamiento.csv`). Todos contienen datos sintéticos.
