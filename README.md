# HobbyPicker 🎯

App de escritorio en Python (Tkinter + SQLite) para sugerirte actividades/hobbies aleatorios según tus gustos. Sigue el patrón Clean Architecture.

## Uso rápido

1. Instala las dependencias (solo `tk` es necesaria).
2. Ejecuta `python reset_db.py` para inicializar la base de datos.
3. Lanza la aplicación con `python main.pyw`.

## Estructura
- `main.py`: punto de entrada
- `presentation/`: interfaz con Tkinter
- `domain/`: lógica y modelos de negocio
- `data/`: acceso a datos (DAO SQLite)
- `infrastructure/`: conexión base de datos

## Requisitos
- Python 3.10+
- Tkinter (viene por defecto con Python)
- SQLite3 (viene integrado)

## Licencia
MIT
