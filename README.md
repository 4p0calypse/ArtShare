# ArtShare - Plataforma de Compartición de Arte

ArtShare es una plataforma web que permite a los artistas compartir sus obras, recibir comentarios y puntos que pueden ser canjeados por dinero real.

## Características

- Registro y autenticación de usuarios
- Subida y gestión de obras de arte
- Sistema de comentarios y respuestas
- Sistema de reacciones (likes)
- Sistema de puntos canjeables por dinero real
- Perfiles de usuario personalizables
- Sistema de se guidores

## Requisitos

- Python 3.8 o superior
- Redis
- Sirope
- Dependencias listadas en requirements.txt

## Instalación

1. Clonar el repositorio:
```bash
git clone [url-del-repositorio]
cd ArtShare
```

2. Crear un entorno virtual:
```bash
python -m venv venv
```

3. Activar el entorno virtual:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Instalar dependencias:
```bash
pip install -r requirements.txt
```

5. Configurar variables de entorno (opcional):
Crear un archivo `.env` en la raíz del proyecto:
```
SECRET_KEY=tu-clave-secreta
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Ejecución

1. Asegurarse de que Redis está en ejecución

2. Ejecutar la aplicación:
```bash
python run.py
```

3. Abrir el navegador en `http://localhost:5000`

## Estructura del Proyecto

```
src/
├── __init__.py          # Configuración principal de la aplicación
├── config.py            # Configuración y variables de entorno
├── auth/               # Módulo de autenticación
├── artwork/            # Módulo de obras de arte
├── comment/            # Módulo de comentarios
├── points/             # Módulo de puntos y transacciones
├── services/           # Servicios compartidos
├── templates/          # Plantillas Jinja2
├── static/            # Archivos estáticos
└── utils/             # Utilidades generales
```

## Uso

1. Registro/Inicio de sesión
2. Completar perfil
3. Subir obras de arte
4. Interactuar con otras obras (comentarios, likes, puntos)
5. Gestionar puntos y retiros

## Contribución

1. Fork del repositorio
2. Crear rama de feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit de cambios (`git commit -am 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crear Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles. 
