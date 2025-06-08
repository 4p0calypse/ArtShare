import os
from datetime import timedelta

class Config:
    # Ruta base del proyecto
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-desarrollo'
    
    # Configuración de uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'src', 'static', 'uploads')
    PROFILE_PICTURES_FOLDER = os.path.join(UPLOAD_FOLDER, 'profile_pictures')
    ARTWORK_IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, 'artworks')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB tamaño máximo de archivo
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Configuración de la sesión con Redis
    SESSION_TYPE = 'redis'
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    SESSION_REDIS = REDIS_URL
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = True
    
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