# Instalación y cuentas de prueba

## Requisitos
- Windows 10/11, macOS o Linux.
- Python 3.10 o superior.
- Navegador actualizado.
- No requiere Node, PostgreSQL ni paquetes externos.

## Inicio
- Windows: doble clic en `INICIAR_HT01.bat`.
- macOS/Linux: `python3 app/server.py` desde la raíz del proyecto.
- URL local: `http://127.0.0.1:8000`.
- Para detener: Ctrl+C en la terminal.

## Credenciales iniciales de demostración

| Perfil | Usuario | Contraseña |
|---|---|---|
| Administrador | admin@ht01.local | AdminHT01!2026 |
| Instructor | instructor@ht01.local | DocenteHT01!2026 |
| Estudiante | estudiante@ht01.local | AlumnoHT01!2026 |

Las cuentas se crean automáticamente en el primer inicio. Las contraseñas se almacenan con PBKDF2-HMAC-SHA256 y salt aleatorio; nunca en texto plano. Cambie las credenciales si el entorno se comparte. La pantalla de acceso identifica estas cuentas como datos de demostración.

## Reinicio del entorno
Detenga el servidor. Para restablecer el entorno de demostración, elimine `data/ht01.sqlite3` y el contenido de `data/private_uploads/`. Al reiniciar se crean de nuevo usuarios y datasets sintéticos.

## Configuración
- `HT01_HOST`: interfaz de escucha; por defecto `127.0.0.1` (solo equipo local).
- `HT01_PORT`: puerto; por defecto `8000`.
- `HT01_SECRET`: reservado para endurecimiento futuro; defina un secreto largo y persistente al desplegar.

No cambie `HT01_HOST` a `0.0.0.0` para exponerlo en una red sin configurar primero HTTPS, firewall, credenciales nuevas y controles de producción.
