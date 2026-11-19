# Análisis de integración de los documentos HT-01

## 1. Resultado del análisis

Los archivos `Documentacion_Enterprise_HT01_Uso_IA.pdf` y `Manual_Procedimiento_Funcionamiento_Enterprise_HT01_IA.pdf` describen una única solución: la **Plataforma Inteligente de Análisis y Explicación de IA HT-01**. No son dos productos que deban programarse por separado.

- La documentación técnica es la fuente de alcance, requerimientos, arquitectura, entidades, reglas, calidad y aceptación.
- El manual operativo traduce ese diseño a procedimientos, pantallas, responsabilidades por perfil, estados, recuperación de errores y guion de demostración.
- La integración correcta es un solo producto con módulos compartidos y dos perspectivas documentales.

## 2. Coincidencias y complementariedad

| Área | Documentación técnica | Manual de funcionamiento | Implementación integrada |
|---|---|---|---|
| Propósito | Plataforma para explicar y explorar IA/ML | Flujo de usuario de principio a fin | Un entorno web HT-01 |
| Roles | Estudiante, instructor, administrador | Permisos y restricciones por rol | Autorización backend por rol |
| Aprendizaje | Trazabilidad académica de semana 13 | Lecciones y secuencia recomendada | Biblioteca de 9 unidades y progreso |
| Datos | RF-03 a RF-06; validación y perfilado | Importar, inspeccionar y clasificar calidad | CSV, datasets sintéticos, perfilado y vista previa |
| Enfoques | RF-07 y RF-08 | Preguntas para elegir enfoque y tipo | Supervisado/no supervisado; clasificación/regresión |
| Pipeline | Capas y reglas de ejecución | Estados y procedimiento paso a paso | Ejecución con UUID, estados y etapas |
| Resultados | Métricas y explicación | Interpretación y limitaciones | Métricas adecuadas según problema |
| Evidencia | Historial y exportación | Filtros, reportes y auditoría | Historial, informe imprimible y eventos |
| Seguridad | RNF-03, RNF-06 y RNF-08 | Validación backend y recuperación | Sesiones, hash, roles, validación y auditoría |
| Aceptación | CP-01 a CP-10 y entregables | PA-01 a PA-13 y guion de demo | Matriz manual y pruebas automatizadas base |

## 3. Delimitación académica respetada

La semana 13 HT-01 contempla explicar el uso de IA, utilizar aprendizaje automático, diferenciar supervisado/no supervisado, datos/información y clasificación/regresión, además de introducir el flujo ML. Recursividad, estructuras de árbol y árboles de decisión/ID3 se reservan para semanas posteriores; por ello no se presentan como funcionalidades obligatorias de HT-01.

## 4. Decisiones técnicas tomadas para poder probarlo

Los documentos dejan framework, base de datos, hosting y lenguaje de motor como decisiones pendientes. Para entregar un sistema reproducible y sencillo de probar en un equipo Windows:

- Interfaz: HTML, CSS y JavaScript sin framework ni proceso de compilación.
- API: servidor HTTP Python modular, sin dependencias de terceros.
- Persistencia: SQLite local.
- Motor: algoritmos educativos implementados en Python puro, separados de la interfaz.
- Archivos: CSV en directorio privado local.
- Reporte: HTML imprimible/guardable como PDF desde el navegador.

Estas son decisiones de implementación de esta entrega, no tecnologías impuestas por los PDF. El nombre del módulo académico menciona Machine Learning in Java; la versión entregada usa Python puro para facilitar la ejecución local sin dependencias. Si el instructor exige Java, debe realizarse una adaptación del motor a Java manteniendo los contratos y el diseño.

## 5. Cobertura funcional entregada

| Requisito | Estado en esta entrega |
|---|---|
| Acceso, cierre de sesión y perfiles | Implementado |
| Dashboard e indicadores | Implementado |
| Contenidos HT-01 y progreso | Implementado |
| Dataset sintético y carga CSV | Implementado |
| Validación, perfilado y vista previa | Implementado; perfil estadístico básico |
| Comparación de enfoques | Implementado |
| Clasificación | Implementado con Gaussian Naive Bayes |
| Regresión | Implementado con regresión lineal multivariable |
| No supervisado | Implementado con K-Means |
| Pipeline y estado de ejecución | Implementado en flujo síncrono |
| Resultados y limitaciones | Implementado |
| Historial y filtros | Implementado |
| Informe de práctica | Implementado como HTML imprimible, no PDF binario |
| Auditoría | Implementado |
| Gestión de usuarios y roles | Implementado para administrador |
| Gestión de datasets | Consulta e importación; borrado de datasets sin prácticas solo admin |
| Cola de trabajos / procesamiento asíncrono | No incluido en la versión local |
| Despliegue productivo / HTTPS / MLOps | Fuera de esta entrega local |

## 6. Conclusión

El ZIP entrega una plataforma integrada para demostrar el recorrido operativo descrito por ambos PDF. No se limita a pantallas estáticas: conserva datos, valida permisos, ejecuta algoritmos y guarda resultados. La aceptación definitiva académica debe realizarse con las pruebas PA-01 a PA-13 en el equipo de demostración y confirmarse con el instructor.
