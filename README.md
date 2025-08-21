<img src="https://via.placeholder.com/100" alt="HobbyPicker icon" align="right" />

# HobbyPicker 🎯

Aplicación de escritorio escrita en **Python** que te sugiere actividades o hobbies de forma aleatoria según tus preferencias. Todo el proyecto sigue una aproximación de **Clean Architecture**, separando responsabilidades por capas.

## Características

- Interfaz gráfica con **Tkinter**.
- Persistencia ligera usando **SQLite**.
- Instalación automática de dependencias al ejecutar la aplicación.
- Comprobación opcional de actualizaciones desde `origin/main` antes de abrir la interfaz.

## Estructura del proyecto

```
main.pyw           # Punto de entrada
presentation/      # Interfaz Tkinter
domain/            # Lógica de negocio y modelos
data/              # Acceso a datos (DAO SQLite)
infrastructure/    # Conexión y utilidades de base de datos
reset_db.py        # Script auxiliar para reiniciar la base de datos
```

## Instalación y uso

1. Clona el repositorio.
2. (Opcional) crea y activa un entorno virtual.
3. Ejecuta la aplicación:

```bash
python main.pyw
```

El script instalará los requisitos necesarios (excepto Tkinter, que viene incluido en la distribución estándar de Python) y lanzará la interfaz.

## Requisitos

- Python 3.10 o superior.
- Tkinter y SQLite3 (incluidos de serie con Python).

## Licencia

Este proyecto se distribuye bajo la licencia MIT.
