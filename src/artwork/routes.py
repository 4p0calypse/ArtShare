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
    """Función de ayuda para obtener un usuario por su ID"""
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
    """Función de ayuda para formatear puntos"""
    try:
        return f"{int(points):,}"
    except (ValueError, TypeError):
        return "0"

# Registrar get_artwork como función global de plantilla
bp.add_app_template_global(get_artwork, 'get_artwork')

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
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

    # Limpiar IDs para comparaciones consistentes
    clean_author_id = str(artwork.author_id).split('@')[-1] if '@' in str(artwork.author_id) else str(artwork.author_id)
    clean_user_id = str(current_user.id).split('@')[-1] if '@' in str(current_user.id) else str(current_user.id) if current_user.is_authenticated else None
    
    logger.info(f"IDs limpios - Autor: {clean_author_id}, Usuario: {clean_user_id}")
    
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

    # Inicializar el formulario de comentarios
    comment_form = None
    if current_user.is_authenticated:
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
        
    comments = []
    if hasattr(artwork, 'comments'):
        comments = sirope.find_many_by_ids(artwork.comments, Comment)
        comments = sorted(comments, key=lambda x: x.created_at, reverse=True)
        
    # Solo mostrar el formulario de puntos si el usuario está autenticado y no es el autor
    points_form = None
    has_donated = False
    if current_user.is_authenticated:
        logger.info(f"Usuario autenticado: {current_user.username}")
        if clean_user_id != clean_author_id:
            logger.info("Usuario no es el autor")
            if not hasattr(artwork, 'donors'):
                logger.info("Artwork no tiene lista de donors, inicializando")
                artwork.donors = []
                sirope.save(artwork)
            
            # Limpiar los IDs de los donantes para comparación
            donors_clean = [str(d).split('@')[-1] if '@' in str(d) else str(d) for d in artwork.donors]
            logger.info(f"Donantes limpios: {donors_clean}")
            logger.info(f"Usuario actual (limpio): {clean_user_id}")
            
            has_donated = clean_user_id in donors_clean
            points_form = GivePointsForm()
            
            if has_donated:
                logger.info("Usuario ya ha donado a este artwork")
            else:
                logger.info("Usuario no ha donado antes")
        else:
            logger.info("Usuario es el autor del artwork")
    else:
        logger.info("Usuario no está autenticado")
    
    artwork.increment_views()
    artwork = sirope.save(artwork)
    
    return render_template('artwork/view.html',
                         artwork=artwork,
                         author=author,
                         comments=comments,
                         points_form=points_form,
                         has_donated=has_donated,
                         comment_form=comment_form,
                         artworks=artworks,
                         clean_user_id=clean_user_id,
                         clean_author_id=clean_author_id)

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
    """Elimina un artwork y todas sus referencias"""
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