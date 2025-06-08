import os
import uuid
from PIL import Image
from flask import current_app, send_from_directory
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Verifica si la extensión del archivo está permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_image(file, upload_folder='uploads'):
    """Guarda una imagen en el sistema de archivos"""
    if file:
        try:
            filename = secure_filename(file.filename)
            # Crear un nombre único para el archivo
            base, ext = os.path.splitext(filename)
            unique_filename = f"{base}_{str(int(time.time()))}{ext}"
            
            # Asegurarse de que el directorio existe
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            
            return unique_filename
        except Exception as e:
            logger.error(f"Error al guardar la imagen: {e}")
            return None
    return None

def get_uploaded_file(filename):
    """Obtiene un archivo subido desde la carpeta de uploads"""
    try:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Error al obtener el archivo {filename}: {str(e)}")
        return None

def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """Formatea una fecha y hora"""
    if value is None:
        return ""
    return value.strftime(format)

def format_currency(amount):
    """Formatea un valor monetario"""
    try:
        return "{:.2f}€".format(float(amount))
    except:
        return "0.00€"

def format_points(points):
    """Formatea un número de puntos para mostrar"""
    try:
        return "{:,}".format(int(points)).replace(',', '.')
    except:
        return "0"

def get_user(user_id):
    """Obtiene un usuario por su ID"""
    try:
        from ..services.sirope_service import SiropeService
        from ..auth.user_model import User
        
        sirope = SiropeService()
        numeric_id = sirope._extract_numeric_id(user_id) if user_id else None
        
        if numeric_id:
            return sirope.find_by_id(numeric_id, User)
        else:
            return None
    except Exception as e:
        logger.error(f"Error al obtener usuario: {e}")
        return None

def get_artwork(artwork_id, sirope=None):
    """Obtiene una obra de arte por su ID"""
    try:
        if not sirope:
            from ..services.sirope_service import SiropeService
            sirope = SiropeService()
        
        from ..artwork.model import Artwork
        
        if not artwork_id:
            return None
            
        return sirope.find_by_id(artwork_id, Artwork)
    except Exception as e:
        logger.error(f"Error al obtener artwork: {e}")
        return None

def sync_user_artworks(user, sirope):
    """Sincroniza la lista de artworks del usuario"""
    try:
        if not hasattr(user, 'artworks'):
            user.artworks = []
            return True
            
        # Filtrar artworks que ya no existen
        valid_artworks = []
        for artwork_id in user.artworks:
            if sirope.find_by_id(artwork_id, Artwork):
                valid_artworks.append(artwork_id)
                
        user.artworks = valid_artworks
        return True
    except Exception as e:
        logger.error(f"Error al sincronizar artworks: {e}")
        return False

def sync_user_points(user, sirope):
    """Sincroniza los puntos del usuario"""
    try:
        if not hasattr(user, 'points'):
            user.points = 0
            return True
            
        # Aquí podrías agregar lógica adicional para sincronizar puntos
        return True
    except Exception as e:
        logger.error(f"Error al sincronizar puntos: {e}")
        return False