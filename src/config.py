import os
from datetime import timedelta

class Config:
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    
    # Configuración de archivos
    STATIC_FOLDER = os.path.join('src', 'static')
    UPLOAD_FOLDER = os.path.join('src', 'static', 'uploads')
    ARTWORK_IMAGES_FOLDER = os.path.join('src', 'static', 'uploads', 'artworks')
    PROFILE_PICTURES_FOLDER = os.path.join('src', 'static', 'uploads', 'profile_pictures')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit
    
    # Configuración de sesión
    SESSION_TYPE = 'redis'
    SESSION_REDIS = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Configuración de puntos
    POINTS_PER_ARTWORK = 100
    MIN_WITHDRAWAL_POINTS = 1000
    POINTS_TO_CURRENCY_RATE = 0.01  # 1 punto = 0.01€
    
    # Configuración de archivos permitidos
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Ruta base del proyecto
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Crear directorios de uploads si no existen
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PROFILE_PICTURES_FOLDER, exist_ok=True)
    os.makedirs(ARTWORK_IMAGES_FOLDER, exist_ok=True)
    print(f"Directorio de uploads configurado en: {UPLOAD_FOLDER}")
    print(f"Directorio de imágenes de perfil configurado en: {PROFILE_PICTURES_FOLDER}")
    print(f"Directorio de imágenes de artworks configurado en: {ARTWORK_IMAGES_FOLDER}")
    
    # Configuración de Sirope
    SIROPE_PATH = os.path.abspath(os.path.join(BASE_DIR, 'data', 'sirope'))
    os.makedirs(SIROPE_PATH, exist_ok=True)  # Crear el directorio si no existe
    print(f"Directorio Sirope configurado en: {SIROPE_PATH}")
    
    # Configuración de Redis
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    
    # Configuración de puntos y conversión
    POINTS_TO_CURRENCY_RATE = 0.01  # 1 punto = 0.01€
    MIN_WITHDRAWAL_POINTS = 1000  # Mínimo de puntos para retirar (10€) 