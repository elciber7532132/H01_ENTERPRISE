# Pruebas y aceptación

## Matriz funcional alineada a los documentos HT-01

| ID | Escenario | Resultado esperado |
|---|---|---|
| PA-01 | Login válido por rol | Acceso al dashboard con opciones según rol. |
| PA-02 | Login inválido | Denegación con mensaje genérico. |
| PA-03 | Fundamentos IA | Unidades de IA, ML, datos/información, supervisado/no supervisado, clasificación/regresión y flujo. |
| PA-04 | CSV válido | Importación, vista previa y perfilado. |
| PA-05 | Archivo inválido/no CSV | Rechazo y explicación. |
| PA-06 | Clasificación | Exige objetivo discreto válido. |
| PA-07 | Regresión | Exige objetivo numérico. |
| PA-08 | No supervisado | Permite agrupamiento sin etiqueta objetivo. |
| PA-09 | Pipeline | Guarda ejecución, muestra etapas y métricas. |
| PA-10 | Error de configuración | No se informa éxito; el mensaje permite corregir. |
| PA-11 | Resultados | Identifica algoritmo, versión, métricas y limitaciones. |
| PA-12 | Historial/reporte | Recupera resultado persistido por ID y exporta informe. |
| PA-13 | Auditoría | Registra actor, acción, recurso, resultado y fecha. |
| CP-08 | Doble clic | El formulario deshabilita el botón mientras espera la respuesta; la idempotencia robusta del backend queda como mejora pendiente. |
| CP-09 | Estudiante administra usuarios | API deniega con HTTP 403. |
| CP-10 | Transparencia | Etiqueta motor y algoritmo real usados; no se inventan métricas. |

## Prueba manual recomendada

1. Inicie como estudiante (`estudiante@ht01.local`).
2. Revise 2 unidades en Aprendizaje IA.
3. Abra Centro de datos y consulte los 3 datasets sintéticos.
4. Seleccione “Solicitudes de crédito (sintético)”, cree clasificación con `aprobada` como objetivo y use variables numéricas.
5. Ejecute. Revise Accuracy, Macro F1, partición, algoritmo y advertencias.
6. Repita con “Ventas mensuales (sintético)”, regresión y objetivo `ventas`.
7. Repita con “Comportamiento de clientes (sintético)” y enfoque no supervisado.
8. Consulte historial y genere el informe HTML (desde el navegador puede imprimirlo o guardarlo como PDF).
9. Cierre sesión e ingrese como instructor: revise historial y auditoría.
10. Ingrese como administrador: cree una cuenta y pruebe activar/desactivar.
11. Intente entrar a `/api/users` con estudiante: el backend debe responder 403.

## Límites conocidos

- El motor ML es educativo y está implementado en Python puro; no equivale a scikit-learn, TensorFlow ni a un servicio MLOps.
- Las variables predictoras admitidas son numéricas. No se codifican automáticamente categorías de entrada en esta primera versión.
- El CSV se analiza en memoria y el tamaño está limitado para demostración.
- La exportación genera HTML autocontenido imprimible; no genera un XLSX ni un PDF binario directamente.
- No incluye cola de trabajos ni notificaciones push; la ejecución se procesa en la solicitud HTTP.
- La seguridad es adecuada para pruebas locales controladas, no para exponer directamente en internet.
