# API REST resumida

Todas las rutas `/api/*` salvo `/api/login` y `/api/health` requieren sesión.

| Método | Ruta | Acceso | Función |
|---|---|---|---|
| GET | `/api/health` | Público | Estado del servicio |
| POST | `/api/login` | Público | Crear sesión |
| POST | `/api/logout` | Sesión | Invalidar sesión |
| GET | `/api/me` | Sesión | Usuario actual |
| GET | `/api/dashboard` | Sesión | Indicadores y actividad |
| GET | `/api/learning` | Sesión | Unidades y progreso |
| POST | `/api/learning/{unit_id}` | Sesión | Marcar unidad revisada |
| GET/POST | `/api/datasets` | Sesión | Catálogo / importar CSV |
| GET | `/api/datasets/{id}` | Sesión | Perfil y vista previa |
| DELETE | `/api/datasets/{id}` | Admin | Eliminar si no tiene prácticas asociadas |
| GET/POST | `/api/practices` | Sesión | Listar / crear práctica |
| POST | `/api/practices/{id}/execute` | Propietario o rol autorizado | Ejecutar pipeline |
| GET | `/api/executions` | Sesión | Historial filtrable |
| GET | `/api/executions/{id}` | Propietario o rol autorizado | Detalle persistido |
| POST | `/api/executions/{id}/report` | Propietario o rol autorizado | Auditar exportación de informe |
| GET | `/api/audit` | Instructor/Admin | Eventos recientes |
| GET/POST | `/api/users` | Admin | Listar / crear usuarios |
| PATCH | `/api/users/{id}` | Admin | Activar/desactivar cuenta |

Las respuestas de error utilizan JSON con propiedad `error`. Las rutas sensibles vuelven a validar el rol en backend.
