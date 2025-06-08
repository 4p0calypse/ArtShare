import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .forms import ArtworkForm, EditArtworkForm, GivePointsForm
from .model import Artwork
from ..points.model import PointsTransaction
from ..services.sirope_service import SiropeService
from ..utils.helpers import save_image, get_artwork, sync_user_artworks, sync_user_points
from ..auth.user_model import User
from ..comment.model import Comment
from ..comment.forms import CommentForm
import logging
from datetime import datetime

bp = Blueprint('artwork', __name__)
sirope = SiropeService()
logger = logging.getLogger(__name__)

# Registrar funciones de ayuda para las plantillas
@bp.app_template_global()
def get_user(user_id):
    """
    Función de ayuda para obtener un usuario por su ID desde las plantillas
    
    Args:
        user_id (str): ID del usuario a buscar
        
    Returns:
        User|None: Instancia del usuario o None si no se encuentra
        
    Note:
        Maneja errores silenciosamente para evitar interrupciones en las plantillas
    """
    if not user_id:
        return None
    try:
        user = sirope.find_by_id(user_id, User)
        return user
    except Exception as e:
        logger.error(f"Error al obtener usuario {user_id}: {e}")
        return None

@bp.app_template_global()
def format_points(points):
    """
    Función de ayuda para formatear puntos con separadores de miles
    
    Args:
        points (int|str): Cantidad de puntos a formatear
        
    Returns:
        str: Puntos formateados con separadores de miles
        
    Note:
        Retorna "0" si el valor no es válido
    """
    try:
        return f"{int(points):,}"
    except (ValueError, TypeError):
        return "0"

# Registrar get_artwork como función global de plantilla
bp.add_app_template_global(get_artwork, 'get_artwork')

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """
    Vista para crear un nuevo artwork
    
    Esta vista maneja tanto el formulario de creación como el procesamiento
    de la imagen y la sincronización con el usuario autor.
    
    Returns:
        str: Plantilla renderizada con el formulario o redirección
        
    Note:
        Requiere autenticación
        Maneja la subida de imágenes y la sincronización de artworks
    """
    # Validar que el usuario actual es válido
    if not current_user.is_authenticated or not current_user.id:
        logger.error(f"Usuario inválido en create artwork: {current_user}")
        flash('Error de sesión. Por favor, inicia sesión nuevamente.')
        return redirect(url_for('auth.login'))

    form = ArtworkForm()
    if form.validate_on_submit():
        try:
            # Intentar recargar el usuario actual
            user = sirope.find_by_id(current_user.id, User)
            if not user:
                logger.error(f"No se pudo encontrar el usuario {current_user.id}")
                flash('Error de sesión. Por favor, inicia sesión nuevamente.')
                return redirect(url_for('auth.login'))

            logger.info(f"Creando artwork para usuario {user.username} (ID: {user.id})")

            # Crear y guardar el artwork
            filename = save_image(form.image.data, current_app.config['ARTWORK_IMAGES_FOLDER'])
            if not filename:
                raise Exception("Error al guardar la imagen")

            # Limpiar el ID del usuario para el artwork
            clean_user_id = str(user.id).split('@')[-1] if '@' in str(user.id) else str(user.id)
            
            artwork = Artwork(
                title=form.title.data,
                description=form.description.data,
                image_path=filename,
                author_id=clean_user_id,
                tags=form.tags.data
            )
            
            logger.info(f"Guardando artwork con autor_id: {clean_user_id}")
            
            # Guardar el artwork
            artwork = sirope.save(artwork)
            if not artwork or not artwork.id:
                raise Exception("Error al guardar el artwork")
            
            logger.info(f"Artwork guardado con ID: {artwork.id}")
            
            # Sincronizar los artworks del usuario
            if not hasattr(user, 'artworks'):
                user.artworks = []
            
            # Asegurarse de que el ID del artwork esté en formato correcto
            artwork_id = str(artwork.id).split('@')[-1] if '@' in str(artwork.id) else str(artwork.id)
            if artwork_id not in user.artworks:
                user.artworks.append(artwork_id)
                user = sirope.save(user)
                logger.info(f"Usuario actualizado con nuevo artwork. Total artworks: {len(user.artworks)}")
            
            flash('¡Tu artwork ha sido publicado!')
            return redirect(url_for('artwork.view', artwork_id=artwork.id))
                
        except Exception as e:
            logger.error(f"Error al crear artwork: {str(e)}")
            # Si ya se creó el artwork pero falló la actualización del usuario,
            # intentar eliminarlo para mantener consistencia
            if 'artwork' in locals() and artwork and artwork.id:
                try:
                    sirope.force_delete(artwork)
                except Exception as del_e:
                    logger.error(f"Error al eliminar artwork inconsistente: {del_e}")
            flash('Error al crear el artwork. Por favor, inténtalo de nuevo.')
            return redirect(url_for('artwork.create'))
            
    return render_template('artwork/create.html', title='Crear Artwork', form=form)

@bp.route('/<artwork_id>', methods=['GET', 'POST'])
def view(artwork_id):
    """
    Vista para visualizar un artwork específico
    
    Esta vista maneja la visualización detallada de un artwork, incluyendo:
    - Información del artwork y autor
    - Sistema de likes
    - Comentarios
    - Donación de puntos
    - Artworks similares
    
    Args:
        artwork_id (str): ID del artwork a visualizar
        
    Returns:
        str: Plantilla renderizada con los detalles del artwork
        
    Note:
        Accesible sin autenticación pero con funcionalidad limitada
        Incrementa el contador de vistas
    """
    logger.info(f"Intentando cargar artwork con ID: {artwork_id}")
    
    # Intentar cargar el artwork
    artwork = get_artwork(artwork_id)
    
    # Si no se encuentra, redirigir al inicio
    if artwork is None:
        logger.warning(f"No se encontró el artwork con ID: {artwork_id}")
        flash('Artwork no encontrado o ha sido eliminado.')
        return redirect(url_for('main.index'))
    
    # Verificar que el autor existe
    author = sirope.find_by_id(artwork.author_id, User)
    if author is None:
        logger.warning(f"No se encontró el autor con ID: {artwork.author_id}")
        flash('Error al cargar el autor del artwork.')
        return redirect(url_for('main.index'))

    # Limpiar ID del autor para comparaciones consistentes
    clean_author_id = str(artwork.author_id).split('@')[-1] if '@' in str(artwork.author_id) else str(artwork.author_id)
    
    # Obtener todos los artworks para buscar similares
    all_artworks = sirope.find_all(Artwork)
    artworks = []
    for art in all_artworks:
        if art and art.id and art.id != artwork_id:  # Excluir la obra actual
            verified_art = get_artwork(art.id)
            if verified_art and hasattr(verified_art, 'tags') and verified_art.tags:
                # Verificar si tiene etiquetas en común
                if any(tag.strip() in artwork.tags for tag in verified_art.tags):
                    artworks.append(verified_art)
    
    # Ordenar por número de likes sin limitar la cantidad
    artworks = sorted(artworks, key=lambda x: len(x.likes) if hasattr(x, 'likes') else 0, reverse=True)

    # Inicializar variables para usuario autenticado
    comment_form = None
    points_form = None
    has_donated = False
    clean_user_id = None

    # Manejar funcionalidades que requieren autenticación
    if current_user.is_authenticated:
        clean_user_id = str(current_user.id).split('@')[-1] if '@' in str(current_user.id) else str(current_user.id)
        
        # Formulario de comentarios
        comment_form = CommentForm()
        if comment_form.validate_on_submit():
            try:
                comment = Comment(
                    content=comment_form.content.data,
                    author_id=current_user.id,
                    artwork_id=artwork_id
                )
                comment = sirope.save(comment)
                
                # Añadir el ID del comentario al artwork
                if not hasattr(artwork, 'comments'):
                    artwork.comments = []
                artwork.comments.append(comment.id)
                sirope.save(artwork)
                
                flash('Comentario añadido correctamente.')
                return redirect(url_for('artwork.view', artwork_id=artwork_id))
            except Exception as e:
                logger.error(f"Error al guardar el comentario: {str(e)}")
                flash('Error al publicar el comentario.')
        
        # Formulario de puntos (solo si no es el autor)
        if clean_user_id != clean_author_id:
            if not hasattr(artwork, 'donors'):
                artwork.donors = []
                sirope.save(artwork)
            
            has_donated = clean_user_id in artwork.donors
            if not has_donated:
                points_form = GivePointsForm()

    # Cargar comentarios
    comments = []
    if hasattr(artwork, 'comments'):
        comments = sirope.find_many_by_ids(artwork.comments, Comment)
        comments = sorted(comments, key=lambda x: x.created_at, reverse=True)

    return render_template('artwork/view.html',
                         artwork=artwork,
                         author=author,
                         similar_artworks=artworks,
                         comment_form=comment_form,
                         comments=comments,
                         points_form=points_form,
                         has_donated=has_donated)

@bp.route('/<artwork_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(artwork_id):
    artwork = sirope.find_by_id(artwork_id, Artwork)
    if artwork is None:
        flash('Artwork no encontrado.')
        return redirect(url_for('main.index'))
    if artwork.author_id != current_user.id:
        flash('No tienes permiso para editar este artwork.')
        return redirect(url_for('artwork.view', artwork_id=artwork_id))
    
    form = EditArtworkForm()
    if form.validate_on_submit():
        artwork.title = form.title.data
        artwork.description = form.description.data
        # Actualizar etiquetas
        artwork.tags = form.tags.data.split(',') if form.tags.data else []
        if form.image.data:
            if artwork.image_path:
                old_image_path = os.path.join(current_app.config['ARTWORK_IMAGES_FOLDER'], artwork.image_path)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            filename = save_image(form.image.data, current_app.config['ARTWORK_IMAGES_FOLDER'])
            artwork.image_path = filename
        sirope.save(artwork)
        flash('Tu artwork ha sido actualizado.')
        return redirect(url_for('artwork.view', artwork_id=artwork_id))
    elif request.method == 'GET':
        form.title.data = artwork.title
        form.description.data = artwork.description
        form.tags.data = ', '.join(artwork.tags) if artwork.tags else ''
    return render_template('artwork/edit.html', title='Editar Artwork', form=form, artwork=artwork)

@bp.route('/<artwork_id>/delete', methods=['GET'])
@login_required
def delete(artwork_id):
    """
    Vista para eliminar un artwork
    
    Esta vista maneja el proceso completo de eliminación:
    - Verificación de permisos
    - Eliminación de la imagen del sistema de archivos
    - Eliminación de comentarios asociados
    - Actualización de referencias en el autor
    
    Args:
        artwork_id (str): ID del artwork a eliminar
        
    Returns:
        str: Redirección a la página principal o al artwork
        
    Note:
        Requiere autenticación
        Solo el autor puede eliminar su artwork
    """
    try:
        artwork = get_artwork(artwork_id)
        if not artwork:
            flash('Artwork no encontrado.')
            return redirect(url_for('main.index'))
            
        # Verificar que el usuario actual es el autor
        if artwork.author_id != current_user.id:
            flash('No tienes permiso para eliminar este artwork.')
            return redirect(url_for('artwork.view', artwork_id=artwork_id))
            
        # Obtener el autor
        author = sirope.find_by_id(artwork.author_id, User)
        if not author:
            flash('Error: No se pudo encontrar el autor del artwork.')
            return redirect(url_for('main.index'))
            
        # 1. Eliminar la imagen del sistema de archivos
        if artwork.image_path:
            try:
                image_path = os.path.join(current_app.config['ARTWORK_IMAGES_FOLDER'], artwork.image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                logger.error(f"Error al eliminar imagen del artwork: {e}")
                
        # 2. Eliminar comentarios asociados silenciosamente
        if hasattr(artwork, 'comments'):
            for comment_id in artwork.comments:
                try:
                    comment = sirope.find_by_id(comment_id, Comment)
                    if comment:
                        sirope.delete(comment)
                except Exception as e:
                    logger.error(f"Error al eliminar comentario {comment_id}: {e}")

        # 3. Eliminar el artwork de la lista de artworks del autor
        if hasattr(author, 'artworks'):
            try:
                author.artworks.remove(artwork_id)
                sirope.save(author)
            except Exception as e:
                logger.error(f"Error al eliminar artwork de la lista del autor: {e}")

        # 4. Eliminar el artwork
        sirope.delete(artwork)
        
        flash('Artwork eliminado correctamente.')
        return redirect(url_for('main.index'))
        
    except Exception as e:
        logger.error(f"Error al eliminar artwork: {e}")
        flash('Error al eliminar el artwork.')
        return redirect(url_for('artwork.view', artwork_id=artwork_id))

@bp.route('/<artwork_id>/give_points', methods=['POST'])
@login_required
def give_points(artwork_id):
    """
    Vista para donar puntos a un artwork
    
    Esta vista maneja el proceso de donación de puntos:
    - Validación de puntos disponibles
    - Creación de transacciones
    - Actualización de balances
    - Sincronización de usuarios
    
    Args:
        artwork_id (str): ID del artwork receptor
        
    Returns:
        str: Redirección a la vista del artwork
        
    Note:
        Requiere autenticación
        Verifica saldo suficiente
        Crea transacciones para donante y receptor
    """
    try:
        # Obtener el artwork
        artwork = sirope.find_by_id(artwork_id, Artwork)
        if artwork is None:
            flash('Artwork no encontrado.')
            return redirect(url_for('main.index'))
        
        # Verificar que el usuario no es el autor
        clean_author_id = str(artwork.author_id).split('@')[-1] if '@' in str(artwork.author_id) else str(artwork.author_id)
        clean_user_id = str(current_user.id).split('@')[-1] if '@' in str(current_user.id) else str(current_user.id)
        
        if clean_author_id == clean_user_id:
            flash('No puedes donar puntos a tu propio artwork.')
            return redirect(url_for('artwork.view', artwork_id=artwork_id))
        
        # Verificar que el usuario no ha donado antes
        if not hasattr(artwork, 'donors'):
            artwork.donors = []
            
        if clean_user_id in artwork.donors:
            flash('Ya has donado puntos a este artwork.')
            return redirect(url_for('artwork.view', artwork_id=artwork_id))
        
        form = GivePointsForm()
        if form.validate_on_submit():
            points = form.points.data
            
            # Obtener instancias frescas de los usuarios
            donor = sirope.find_by_id(current_user.id, User)
            if not donor:
                raise Exception("No se pudo encontrar el usuario donante")
                
            artwork_author = sirope.find_by_id(artwork.author_id, User)
            if not artwork_author:
                raise Exception("No se pudo encontrar el autor del artwork")
            
            # Sincronizar puntos de ambos usuarios
            if not sync_user_points(donor, sirope):
                logger.warning(f"No se pudieron sincronizar los puntos del donante {donor.username}")
            if not sync_user_points(artwork_author, sirope):
                logger.warning(f"No se pudieron sincronizar los puntos del autor {artwork_author.username}")
            
            if donor.points >= points:
                try:
                    # Crear transacciones
                    give_tx = PointsTransaction.create_give_transaction(
                        donor.id, artwork_id, points)
                    receive_tx = PointsTransaction.create_receive_transaction(
                        artwork_author.id, artwork_id, points)
                    
                    # Guardar transacciones
                    give_tx_id = sirope.save(give_tx)
                    receive_tx_id = sirope.save(receive_tx)
                    if not give_tx_id or not receive_tx_id:
                        raise Exception("Error al guardar las transacciones")
                    
                    # Actualizar puntos de los usuarios
                    donor.remove_points(points)
                    artwork_author.add_points(points)
                    
                    # Actualizar artwork
                    artwork.add_points(points, donor.id)
                    
                    # Guardar todos los cambios
                    saved_donor = sirope.save(donor)
                    saved_author = sirope.save(artwork_author)
                    saved_artwork = sirope.save(artwork)
                    
                    if not all([saved_donor, saved_author, saved_artwork]):
                        raise Exception("Error al guardar los cambios")
                    
                    # Actualizar la sesión del usuario actual
                    from flask_login import login_user
                    login_user(donor)  # Esto actualiza la sesión con los nuevos puntos
                    
                    flash(f'¡Has donado {format_points(points)} puntos al artwork!')
                except Exception as e:
                    # Si algo falla, intentar revertir las transacciones
                    logger.error(f"Error al procesar la donación: {str(e)}")
                    if 'give_tx_id' in locals():
                        try:
                            sirope.force_delete(give_tx_id)
                        except:
                            logger.error("No se pudo revertir la transacción de donación")
                    if 'receive_tx_id' in locals():
                        try:
                            sirope.force_delete(receive_tx_id)
                        except:
                            logger.error("No se pudo revertir la transacción de recepción")
                    raise e
            else:
                flash('No tienes suficientes puntos.')
    except Exception as e:
        logger.error(f"Error al procesar la donación: {str(e)}")
        flash('Error al procesar la donación. Por favor, inténtalo de nuevo.')
    
    return redirect(url_for('artwork.view', artwork_id=artwork_id))

@bp.route('/<artwork_id>/like', methods=['POST'])
@login_required
def toggle_like(artwork_id):
    try:
        artwork = sirope.find_by_id(artwork_id, Artwork)
        if not artwork:
            return jsonify({'error': 'Artwork no encontrado'}), 404

        if not hasattr(artwork, 'likes'):
            artwork.likes = []

        # Toggle like
        if current_user.id in artwork.likes:
            artwork.likes.remove(current_user.id)
            liked = False
        else:
            artwork.likes.append(current_user.id)
            liked = True

        sirope.save(artwork)
        return jsonify({
            'success': True,
            'liked': liked,
            'likes_count': len(artwork.likes)
        })
    except Exception as e:
        logger.error(f"Error al procesar like: {str(e)}")
        return jsonify({'error': 'Error al procesar la acción'}), 500 