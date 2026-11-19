# Arquitectura y modelo lógico HT-01

## Arquitectura por capas

1. **Presentación:** HTML, CSS y JavaScript responsive; navegación, formularios, estados y resultados.
2. **Aplicación/API:** servidor HTTP y endpoints REST; autenticación, autorización, validación y orquestación.
3. **Dominio:** conceptos Dataset, perfilado, práctica, enfoque, tipo de problema, ejecución y reglas de compatibilidad.
4. **Servicio ML desacoplado:** contrato interno `run_model`; implementaciones Gaussian Naive Bayes, regresión lineal y K-Means.
5. **Infraestructura:** SQLite, almacenamiento privado de CSV, sesiones, reportes descargables y auditoría.

La interfaz no contiene reglas de entrenamiento. El backend vuelve a validar los datos y permisos. La separación permite reemplazar el motor por un servicio independiente en una siguiente versión.

## Flujo de ejecución

Navegador → API autenticada → autorización del dataset → registro de ejecución con UUID → preparación de variables → motor ML → métricas y advertencias → persistencia → historial/reporte → evento de auditoría.

## Entidades persistidas

- **User:** id, nombre, correo, hash de contraseña, rol, estado y fecha.
- **Dataset:** id, nombre, origen, archivo privado, filas, perfil, conteos, estado, propietario y fecha.
- **DatasetColumn (perfil embebido):** nombre, tipo inferido, faltantes, porcentaje, valores distintos y estadísticos numéricos.
- **MLPractice:** id, título, dataset, enfoque, tipo de problema, objetivo, variables, descripción y creador.
- **Execution:** id, práctica, estado, inicio/fin, motor/versión, resultado y error seguro.
- **AuditEvent:** actor, acción, tipo/ID de recurso, resultado, metadatos y fecha.
- **LearningProgress:** usuario, unidad y fecha de finalización.
- **Session:** hash del token, usuario, expiración y creación.

## Reglas principales

- Clasificación exige variable objetivo discreta con al menos dos clases.
- Regresión exige variable objetivo numérica.
- No supervisado no utiliza objetivo y ejecuta agrupamiento K-Means.
- Las variables de entrada deben ser numéricas en el motor de esta versión; la interfaz explica esta limitación.
- Se excluyen filas incompletas en las variables elegidas y se informa cuántas.
- Clasificación/regresión usan partición determinista 80/20. Las métricas se calculan sobre la partición de prueba.
- La ejecución guarda el resultado y metadatos del motor; el historial no recalcula resultados a partir de datos actuales.
- Ninguna métrica demostrativa se presenta como resultado de un motor externo.

## Seguridad implementada y pendiente

Implementado: hash PBKDF2, token aleatorio en cookie HttpOnly/SameSite, roles validados en backend, sesión con expiración, CSV limitado a 5 MB/10 000 filas, validación de extensión/encabezados, archivos privados, errores sin stack trace, eventos de auditoría.

Pendiente para producción: HTTPS, protección CSRF explícita, rate limiting, análisis antimalware, política de retención, cifrado de backups, rotación de sesiones, base de datos administrada, servidor de aplicación de producción, monitorización y pruebas de penetración.
