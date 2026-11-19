# Manual de usuario resumido

## Acceso
Abra `http://127.0.0.1:8000`, ingrese correo y contraseña. El menú se adapta al rol. Use Cerrar sesión para invalidar la sesión.

## Dashboard
Consulte prácticas, datasets, ejecuciones y unidades revisadas. Los accesos rápidos llevan a aprendizaje, datos, laboratorio e historial.

## Aprendizaje IA
Abra una unidad, revise definición, ejemplo e idea clave y márquela como revisada. Incluye los fundamentos de HT-01, sin incorporar recursividad ni ID3.

## Centro de datos
Elija un dataset sintético o importe CSV. El sistema valida extensión, tamaño, encabezados y filas; después presenta estructura, tipos, valores faltantes, duplicados, distribución numérica y advertencias. Las advertencias no se corrigen silenciosamente.

## Laboratorio ML
Seleccione dataset y objetivo. Elija supervisado (clasificación o regresión) o no supervisado (agrupamiento). Seleccione variables numéricas de entrada. Guarde y ejecute.

## Resultados
Revise algoritmo, versión, métricas, explicación, pipeline y limitaciones. Clasificación presenta Accuracy y Macro F1; regresión presenta MAE, RMSE y R²; K-Means muestra número de grupos e inercia. Las métricas solo tienen sentido conociendo el dataset y el objetivo.

## Historial y reportes
Filtre por texto, estado y enfoque. Abra el detalle de una ejecución para recuperar su resultado persistido. Exporte el informe HTML y use Imprimir → Guardar como PDF.

## Perfiles
- Estudiante: aprende, importa datos, configura prácticas y consulta su historial.
- Instructor: consulta evidencias de aprendizaje autorizadas y auditoría.
- Administrador: gestiona usuarios y roles, además de las funciones de aprendizaje.

También puede importar los tres CSV sintéticos incluidos en `examples/` para repetir la práctica con archivos externos.
