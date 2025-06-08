from flask import Blueprint, render_template, send_from_directory, current_app, abort, request
from flask_login import current_user
from ..artwork.model import Artwork
from ..services.sirope_service import SiropeService
from ..utils.helpers import get_artwork, get_user, sync_user_artworks
from ..auth.user_model import User
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)
bp = Blueprint('main', __name__)
sirope = SiropeService()

@bp.route('/')
def index():
    # Obtener artworks recientes
    all_artworks = sirope.find_all(Artwork)
    # Filtrar artworks usando get_artwork para verificar que realmente existen
    artworks = []
    processed_authors = set()
    valid_users = set()  # Conjunto para almacenar usuarios únicos válidos
    
    for art in all_artworks:
        if art and art.id:
            verified_art = get_artwork(art.id, sirope)
            if verified_art:
                # Sincronizar artworks con el autor si aún no lo hemos hecho
                author = get_user(verified_art.author_id)
                if author and hasattr(author, 'id') and author.id and author.id not in processed_authors:
                    sync_user_artworks(author, sirope)
                    processed_authors.add(author.id)
                    # Añadir autor válido al conjunto de usuarios
                    if author.username:
                        valid_users.add(author.id)
                artworks.append(verified_art)
    
    # Ordenar por fecha de creación (más recientes primero)
    artworks = sorted(artworks, key=lambda x: x.created_at if hasattr(x, 'created_at') else datetime.now(), reverse=True)
    
    # Limitar a 9 artworks (3 filas de 3)
    artworks = artworks[:9]
    
    # Obtener el total de artworks válidos
    total_artworks = len([art for art in all_artworks if get_artwork(art.id, sirope)])
    remaining_artworks = total_artworks - 9 if total_artworks > 9 else 0
    
    # Obtener el total de usuarios activos
    all_users = sirope.find_all(User)
    for user in all_users:
        if (user and 
            hasattr(user, 'id') and user.id and 
            hasattr(user, 'username') and user.username and
            hasattr(user, 'email') and user.email):
            # Solo contar usuarios que tengan ID, username y email
            valid_users.add(user.id)
    
    total_users = len(valid_users)
    
    return render_template('index.html', 
                         artworks=artworks,
                         total_artworks=total_artworks,
                         remaining_artworks=remaining_artworks,
                         total_users=total_users)

def clean_duplicate_users(users):
    """Limpia usuarios duplicados basándose en el username"""
    seen_usernames = {}
    cleaned_users = []
    
    for user in users:
        if user and user.username:
            if user.username not in seen_usernames:
                seen_usernames[user.username] = user
                cleaned_users.append(user)
            else:
                # Si el usuario actual tiene ID y el anterior no, usamos el actual
                existing_user = seen_usernames[user.username]
                if not existing_user.id and user.id:
                    seen_usernames[user.username] = user
                    cleaned_users.remove(existing_user)
                    cleaned_users.append(user)
    
    return cleaned_users

@bp.route('/explore')
def explore():
    search_type = request.args.get('search_type', 'all')
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort_by', 'recent')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Obtener todos los artworks
    all_artworks = sirope.find_all(Artwork)
    artworks = []
    
    # Filtrar artworks según el tipo de búsqueda
    for art in all_artworks:
        if art and art.id:
            # Verificar que el artwork existe y es válido
            verified_art = get_artwork(art.id)
            if verified_art and verified_art.author_id:
                # Verificar que el autor existe
                author = get_user(verified_art.author_id)
                if author:
                    if search_query:
                        if search_type == 'title' and search_query.lower() in verified_art.title.lower():
                            artworks.append(verified_art)
                        elif search_type == 'tags' and any(search_query.lower() in tag.lower() for tag in verified_art.tags):
                            artworks.append(verified_art)
                        elif search_type == 'all' and (
                            search_query.lower() in verified_art.title.lower() or
                            any(search_query.lower() in tag.lower() for tag in verified_art.tags)
                        ):
                            artworks.append(verified_art)
                    else:
                        artworks.append(verified_art)
    
    # Ordenar artworks según los parámetros
    if sort_by == 'title':
        artworks.sort(key=lambda x: x.title.lower(), reverse=(sort_order == 'desc'))
    elif sort_by == 'likes':
        artworks.sort(key=lambda x: len(x.likes), reverse=(sort_order == 'desc'))
    elif sort_by == 'views':
        artworks.sort(key=lambda x: x.views, reverse=(sort_order == 'desc'))
    elif sort_by == 'points':
        artworks.sort(key=lambda x: x.points_received, reverse=(sort_order == 'desc'))
    else:  # 'recent' por defecto
        artworks.sort(key=lambda x: x.created_at, reverse=(sort_order == 'desc'))
    
    search_performed = bool(search_query)
    return render_template('explore.html', 
                         title='Explorar', 
                         artworks=artworks,
                         search_type=search_type,
                         search_performed=search_performed,
                         sort_by=sort_by,
                         sort_order=sort_order)

@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    """Sirve archivos subidos de forma segura"""
    try:
        # Primero intentar en la carpeta de artworks
        return send_from_directory(current_app.config['ARTWORK_IMAGES_FOLDER'], filename)
    except FileNotFoundError:
        try:
            # Si no se encuentra, intentar en la carpeta de uploads general
            return send_from_directory(os.path.join(current_app.root_path, '..', 'uploads'), filename)
        except FileNotFoundError:
            logger.error(f"Archivo no encontrado: {filename}")
            abort(404)

@bp.route('/profile_pictures/<filename>')
def profile_picture(filename):
    """Sirve imágenes de perfil de forma segura"""
    try:
        # Definir la ruta correcta para las imágenes de perfil
        profile_pictures_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pictures')
        
        # Verificar si el archivo existe
        if filename and os.path.exists(os.path.join(profile_pictures_folder, filename)):
            logger.info(f"Sirviendo imagen de perfil: {filename}")
            return send_from_directory(profile_pictures_folder, filename)
        else:
            logger.warning(f"Imagen de perfil no encontrada: {filename}, usando imagen por defecto")
            # Asegurarse de que la ruta al archivo por defecto es correcta
            default_image_path = os.path.join(current_app.root_path, 'static', 'img', 'default.jpg')
            if os.path.exists(default_image_path):
                return send_from_directory(os.path.join(current_app.root_path, 'static', 'img'), 'default.jpg')
            else:
                logger.error("Imagen por defecto no encontrada")
                abort(404)
    except Exception as e:
        logger.error(f"Error al servir imagen de perfil {filename}: {str(e)}")
        # Intentar servir la imagen por defecto
        try:
            return send_from_directory(os.path.join(current_app.root_path, 'static', 'img'), 'default.jpg')
        except:
            abort(404) 