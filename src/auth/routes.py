from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
import os
import time
from .forms import LoginForm, RegistrationForm, ProfileForm, RequestPasswordResetForm, DirectPasswordResetForm
from .user_model import User
from ..services.sirope_service import SiropeService
from ..artwork.model import Artwork
from ..comment.model import Comment
from ..social.models import Message
from ..points.model import PointsTransaction
from ..utils.helpers import get_artwork, sync_user_artworks, sync_user_points
import logging
from werkzeug.security import generate_password_hash
from datetime import datetime
from PIL import Image

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__)
sirope = SiropeService()

# Configuración para subida de imágenes
UPLOAD_FOLDER = os.path.join('src', 'static', 'uploads', 'profile_pictures')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Registrar funciones de ayuda para las plantillas
@bp.app_template_global()
def now():
    """Función de ayuda para obtener la fecha y hora actual"""
    return datetime.now()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_picture(file):
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            # Crear un nombre único para el archivo
            base, ext = os.path.splitext(filename)
            unique_filename = f"{base}_{str(int(time.time()))}{ext}"
            
            # Usar la ruta correcta para las imágenes de perfil
            profile_pictures_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pictures')
            os.makedirs(profile_pictures_folder, exist_ok=True)
            
            # Asegurarse de que el archivo se guarde con la extensión correcta
            if ext.lower() not in ['.jpg', '.jpeg', '.png']:
                logger.error(f"Extensión de archivo no permitida: {ext}")
                return None
            
            # Guardar temporalmente el archivo
            temp_path = os.path.join(profile_pictures_folder, 'temp_' + unique_filename)
            file.save(temp_path)
            
            try:
                # Abrir y procesar la imagen con Pillow
                with Image.open(temp_path) as img:
                    # Convertir a RGB si es necesario
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Obtener dimensiones
                    width, height = img.size
                    
                    # Determinar el tamaño del cuadrado
                    size = min(width, height)
                    
                    # Calcular coordenadas para el recorte
                    left = (width - size) // 2
                    top = (height - size) // 2
                    right = left + size
                    bottom = top + size
                    
                    # Recortar la imagen en un cuadrado
                    img = img.crop((left, top, right, bottom))
                    
                    # Redimensionar a un tamaño estándar (400x400)
                    img = img.resize((400, 400), Image.Resampling.LANCZOS)
                    
                    # Guardar la imagen procesada
                    file_path = os.path.join(profile_pictures_folder, unique_filename)
                    img.save(file_path, 'JPEG', quality=85)
                
                # Eliminar el archivo temporal
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                logger.info(f"Imagen de perfil guardada y procesada en: {file_path}")
                
                # Devolver la ruta relativa para acceder desde la web
                return unique_filename
                
            finally:
                # Asegurarse de que el archivo temporal se elimine incluso si hay errores
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            logger.error(f"Error al guardar la imagen: {e}")
            return None
            
    return None

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        logger.info(f"Intento de login para email: {form.email.data}")
        
        try:
            def match_email(user):
                return user.email == form.email.data
            
            user = sirope.find_first(User, match_email)
            
            if user and user.check_password(form.password.data):
                # Asegurarse de que el usuario tenga todos los campos necesarios
                if not user.id or not user.username or not user.email:
                    logger.info("Usuario incompleto, guardando en Sirope")
                    user = sirope.save(user)
                
                # Verificar que el usuario tiene todos los campos requeridos
                if not user.id or not user.username or not user.email:
                    logger.error(f"Usuario inválido después de guardar: {user}")
                    flash('Error al iniciar sesión. Por favor, contacta al administrador.')
                    return redirect(url_for('auth.login'))
                
                # Sincronizar puntos del usuario
                if not sync_user_points(user, sirope):
                    logger.warning(f"No se pudieron sincronizar los puntos para {user.username}")
                
                logger.info(f"Login exitoso para usuario: {user.username} (ID: {user.id})")
                login_user(user, remember=form.remember_me.data)
                
                # Verificar que la sesión se estableció correctamente
                if not current_user.is_authenticated or not current_user.id:
                    logger.error("Error al establecer la sesión")
                    flash('Error al iniciar sesión. Por favor, inténtalo de nuevo.')
                    return redirect(url_for('auth.login'))
                
                logger.info(f"Sesión establecida correctamente para {user.username}")
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('main.index')
                return redirect(next_page)
            else:
                logger.warning(f"Login fallido para email: {form.email.data}")
                flash('Email o contraseña incorrectos.')
        except Exception as e:
            logger.error(f"Error durante el login: {str(e)}")
            flash('Error al iniciar sesión. Por favor, inténtalo de nuevo.')
            
    return render_template('auth/login.html', title='Iniciar Sesión', form=form)

@bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        logger.info(f"Logout para usuario: {current_user.username}")
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Crear nuevo usuario
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            
            # Inicializar listas
            user.following = []
            user.followers = []
            user.artworks = []
            
            # Manejar la imagen de perfil si se proporcionó una
            if form.profile_picture.data:
                profile_picture_path = save_profile_picture(form.profile_picture.data)
                if profile_picture_path:
                    user.profile_picture = profile_picture_path
            
            # Guardar usuario
            user = sirope.save(user)
            if not user.id:
                logger.error("Error: Usuario guardado sin ID")
                flash('Error al crear el usuario. Por favor, inténtalo de nuevo.')
                return render_template('auth/register.html', title='Registro', form=form)
            
            # Verificar que las listas se guardaron correctamente
            user = sirope.find_by_id(user.id, User)
            if not hasattr(user, 'following') or not hasattr(user, 'followers'):
                logger.error(f"Error: Usuario {user.id} guardado sin listas de following/followers")
                flash('Error al crear el usuario. Por favor, inténtalo de nuevo.')
                return render_template('auth/register.html', title='Registro', form=form)
            
            logger.info(f"Nuevo usuario registrado: {user.username} (ID: {user.id})")
            logger.info(f"Estado de following: {user.following}")
            logger.info(f"Estado de followers: {user.followers}")
            
            flash('¡Registro completado con éxito!')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            logger.error(f"Error al registrar usuario: {str(e)}")
            flash('Error al crear el usuario. Por favor, inténtalo de nuevo.')
            return render_template('auth/register.html', title='Registro', form=form)
            
    return render_template('auth/register.html', title='Registro', form=form)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    
    try:
        if form.validate_on_submit():
            # Obtener una copia fresca del usuario
            user = sirope.find_by_id(current_user.id, User)
            if not user:
                raise ValueError("Usuario no encontrado en la base de datos")
            
            # Asegurar que el usuario tenga todos los atributos necesarios
            user.ensure_attributes()
            
            # Actualizar datos del perfil
            user.username = form.username.data
            user.bio = form.bio.data
            
            # Manejar la imagen de perfil
            if form.profile_picture.data:
                try:
                    # Procesar y guardar la nueva imagen
                    new_filename = save_profile_picture(form.profile_picture.data)
                    if new_filename:
                        # Eliminar la imagen anterior si existe
                        if user.profile_picture:
                            old_file = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pictures', user.profile_picture)
                            try:
                                if os.path.exists(old_file):
                                    os.remove(old_file)
                                    logger.info(f"Imagen anterior eliminada: {old_file}")
                            except Exception as e:
                                logger.warning(f"No se pudo eliminar la imagen anterior: {str(e)}")
                        
                        user.profile_picture = new_filename
                        logger.info(f"Nueva imagen de perfil guardada: {new_filename}")
                    else:
                        raise Exception("Error al procesar la imagen de perfil")
                        
                except Exception as e:
                    logger.error(f"Error al procesar la imagen de perfil: {str(e)}")
                    flash('Error al guardar la imagen de perfil.', 'danger')
                    return redirect(url_for('auth.profile'))
            
            # Guardar el usuario actualizado
            user = sirope.save(user)
            
            # Actualizar la sesión con el usuario actualizado
            login_user(user)
            
            flash('Tu perfil ha sido actualizado correctamente.', 'success')
            return redirect(url_for('auth.profile'))
            
        elif request.method == 'GET':
            # Obtener datos actuales del usuario
            user = sirope.find_by_id(current_user.id, User)
            if user:
                user.ensure_attributes()
                form.username.data = user.username
                form.bio.data = user.bio
        
        # Obtener artworks del usuario actualizados
        artworks = []
        user = sirope.find_by_id(current_user.id, User)
        if user:
            for art_id in user.artworks:
                artwork = get_artwork(art_id)
                if artwork:
                    artworks.append(artwork)
            
            # Ordenar artworks por fecha de creación (más recientes primero)
            artworks.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') else datetime.now(), reverse=True)
        
        return render_template('auth/profile.html', 
                             title='Perfil',
                             form=form,
                             artworks=artworks)
                             
    except Exception as e:
        logger.error(f"Error al actualizar perfil: {str(e)}")
        flash('Error al actualizar el perfil. Por favor, inténtalo de nuevo.', 'danger')
        return redirect(url_for('auth.profile'))

@bp.route('/user/<username>')
def user_profile(username):
    logger.info(f"Accediendo al perfil de usuario: {username}")
    
    # Obtener el usuario por nombre de usuario
    user = sirope.find_first(User, lambda u: u.username == username)
    if user is None:
        logger.warning(f"Usuario no encontrado: {username}")
        flash('Usuario no encontrado.')
        return redirect(url_for('main.index'))
    
    logger.info(f"Usuario encontrado: {user.username} (ID: {user.id})")
    
    # Asegurar que el usuario tenga todos los atributos necesarios
    user.ensure_attributes()
    sirope.save(user)
    
    # Si el usuario está autenticado, obtener una copia fresca del usuario actual
    current_user_fresh = None
    if current_user.is_authenticated:
        current_user_fresh = sirope.find_by_id(current_user.id, User)
        if current_user_fresh:
            current_user_fresh.ensure_attributes()
            sirope.save(current_user_fresh)
    
    # Obtener artworks del usuario
    artworks = []
    for art_id in user.artworks:
        artwork = get_artwork(art_id)
        if artwork:
            artworks.append(artwork)
    
    # Ordenar artworks por fecha de creación (más recientes primero)
    artworks.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') else datetime.now(), reverse=True)
    
    # Obtener seguidores y seguidos
    followers = []
    following = []
    
    for follower_id in user.followers:
        follower = sirope.find_by_id(follower_id, User)
        if follower:
            follower.ensure_attributes()
            sirope.save(follower)
            followers.append(follower)
    
    for following_id in user.following:
        followed = sirope.find_by_id(following_id, User)
        if followed:
            followed.ensure_attributes()
            sirope.save(followed)
            following.append(followed)
    
    # Ordenar seguidores y seguidos por nombre de usuario
    followers.sort(key=lambda x: x.username.lower())
    following.sort(key=lambda x: x.username.lower())
    
    return render_template('auth/user_profile.html',
                         user=user,
                         artworks=artworks,
                         followers=followers,
                         following=following)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = RequestPasswordResetForm()
    direct_form = DirectPasswordResetForm()
    
    if form.validate_on_submit():
        try:
            user = sirope.find_first(User, lambda u: u.email == form.email.data)
            if user:
                # Por ahora, solo mostraremos un mensaje de éxito
                # En una implementación real, aquí enviaríamos un email
                flash('Se han enviado instrucciones a tu correo electrónico.')
                logger.info(f"Solicitud de recuperación de contraseña para {user.email}")
                return redirect(url_for('auth.login'))
        except Exception as e:
            logger.error(f"Error en solicitud de recuperación de contraseña: {e}")
            flash('Ha ocurrido un error. Por favor, inténtalo de nuevo más tarde.')
            
    return render_template('auth/reset_password_request.html', 
                         title='Recuperar Contraseña', 
                         form=form,
                         direct_form=direct_form)

@bp.route('/direct_reset', methods=['POST'])
def direct_reset():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = DirectPasswordResetForm()
    if form.validate_on_submit():
        try:
            user = sirope.find_first(
                User, 
                lambda u: u.email == form.email.data and u.username == form.username.data
            )
            
            if user:
                # Actualizar la contraseña
                user.password_hash = generate_password_hash(form.new_password.data)
                sirope.save(user)
                
                flash('Tu contraseña ha sido actualizada. Ya puedes iniciar sesión.')
                logger.info(f"Contraseña actualizada directamente para {user.email}")
                return redirect(url_for('auth.login'))
                
        except Exception as e:
            logger.error(f"Error en cambio directo de contraseña: {e}")
            flash('Ha ocurrido un error. Por favor, inténtalo de nuevo más tarde.')
    
    # Si hay errores, volver al formulario
    return render_template('auth/reset_password_request.html', 
                         title='Recuperar Contraseña',
                         form=RequestPasswordResetForm(),
                         direct_form=form) 