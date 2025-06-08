from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app, send_from_directory
from flask_login import login_required, current_user
from .models import Message
from ..services.sirope_service import SiropeService
from ..auth.user_model import User
import logging
import os
from datetime import datetime
from ..utils.helpers import get_user

bp = Blueprint('social', __name__)
sirope = SiropeService()
logger = logging.getLogger(__name__)

@bp.route('/')
@login_required
def index():
    try:
        # Obtener ID del usuario actual
        current_user_id = sirope._extract_numeric_id(current_user.id)
        logger.info(f"Cargando página social para el usuario {current_user_id}")
        
        # Obtener una copia fresca del usuario actual
        current_user_fresh = sirope.find_by_id(current_user_id, User)
        if not current_user_fresh:
            logger.error(f"Usuario actual no encontrado en BD: {current_user_id}")
            flash('Ha ocurrido un error al cargar la página social.')
            return render_template('social/index.html', friends=[], users=[], recent_followers=[], conversations=[])

        # Asegurar que el usuario tenga todos los atributos necesarios
        current_user_fresh.ensure_attributes()
        sirope.save(current_user_fresh)
        
        logger.info(f"Usuario actual - Following: {current_user_fresh.following}")
        logger.info(f"Usuario actual - Followers: {current_user_fresh.followers}")

        # Obtener todos los usuarios
        all_users = sirope.find_all(User)
        users = []
        friends = []  # Usuarios que se siguen mutuamente
        processed_ids = set()

        for user in all_users:
            try:
                if not user or not user.id:
                    continue

                numeric_id = sirope._extract_numeric_id(user.id)
                str_numeric_id = str(numeric_id)
                
                # Evitar duplicados y el usuario actual
                if numeric_id == current_user_id or numeric_id in processed_ids:
                    continue
                
                processed_ids.add(numeric_id)

                # Asegurar que el usuario tenga todos los atributos necesarios
                user.ensure_attributes()
                sirope.save(user)

                # Verificar si hay seguimiento mutuo (amistad)
                str_current_id = str(current_user_id)
                current_follows_user = str_numeric_id in current_user_fresh.following
                user_follows_current = str_current_id in user.following

                if current_follows_user and user_follows_current:
                    friends.append(user)
                    logger.info(f"Usuario {user.username} añadido a amigos")
                else:
                    users.append(user)
                    logger.info(f"Usuario {user.username} añadido a usuarios")

            except Exception as user_error:
                logger.error(f"Error procesando usuario: {str(user_error)}")
                continue
        
        # Ordenar las listas por nombre de usuario
        friends.sort(key=lambda x: x.username.lower())
        users.sort(key=lambda x: x.username.lower())
        
        # Obtener seguidores recientes (últimos 5)
        recent_followers = []
        if current_user_fresh.followers:
            for follower_id in current_user_fresh.followers[-5:]:
                follower = sirope.find_by_id(follower_id, User)
                if follower:
                    follower.ensure_attributes()
                    sirope.save(follower)
                    recent_followers.append(follower)
        recent_followers.reverse()
        
        # Obtener conversaciones recientes
        conversations = get_recent_conversations(current_user_id)
        
        return render_template('social/index.html',
                             friends=friends,
                             users=users,
                             recent_followers=recent_followers,
                             conversations=conversations)

    except Exception as e:
        logger.error(f"Error en la página social: {str(e)}")
        flash('Ha ocurrido un error al cargar la página social.')
        return render_template('social/index.html', friends=[], users=[], recent_followers=[], conversations=[])

@bp.route('/search')
@login_required
def search():
    try:
        query = request.args.get('q', '').strip().lower()
        logger.info(f"Búsqueda de usuarios con query: '{query}'")
        
        if not query:
            return render_template('social/search.html', users=[], query='')
        
        # Obtener una copia fresca del usuario actual
        current_numeric_id = sirope._extract_numeric_id(current_user.id)
        current_user_fresh = sirope.find_by_id(current_numeric_id, User)
        
        if not current_user_fresh:
            logger.error(f"Usuario actual no encontrado en BD: {current_numeric_id}")
            flash('Ha ocurrido un error al buscar usuarios.')
            return render_template('social/search.html', users=[], query=query)
        
        # Asegurarse de que el usuario actual tenga las listas necesarias
        if not hasattr(current_user_fresh, 'following'):
            current_user_fresh.following = []
        if not hasattr(current_user_fresh, 'followers'):
            current_user_fresh.followers = []
        
        # Buscar usuarios que coincidan con la query
        all_users = sirope.find_all(User)
        users = []
        
        for user in all_users:
            try:
                if not user or not user.id or not user.username:
                    continue
                
                numeric_id = sirope._extract_numeric_id(user.id)
                str_numeric_id = str(numeric_id)
                
                # Evitar mostrar al usuario actual
                if str_numeric_id == str(current_numeric_id):
                    continue
            
                # Buscar coincidencia en username
                if query in user.username.lower():
                    # Asegurar atributos necesarios
                    if not hasattr(user, 'following'):
                        user.following = []
                        sirope.save(user)
                    if not hasattr(user, 'followers'):
                        user.followers = []
                        sirope.save(user)
                    if not hasattr(user, 'bio'):
                        user.bio = ""
                    if not hasattr(user, 'artworks'):
                        user.artworks = []
                    
                    users.append(user)
                    logger.info(f"Usuario {user.username} añadido a resultados")
            
            except Exception as user_error:
                logger.error(f"Error procesando usuario durante búsqueda: {str(user_error)}")
                continue
        
        # Ordenar por nombre de usuario
        users.sort(key=lambda x: x.username.lower())
        
        return render_template('social/search.html',
                             users=users,
                             query=query,
                             current_user_fresh=current_user_fresh)
    
    except Exception as e:
        logger.error(f"Error en la búsqueda de usuarios: {str(e)}")
        flash('Ha ocurrido un error al buscar usuarios.')
        return render_template('social/search.html', users=[], query=query)

@bp.route('/chat/<user_id>')
@login_required
def chat(user_id):
    try:
        # Extraer IDs numéricos
        numeric_id = sirope._extract_numeric_id(user_id)
        current_numeric_id = sirope._extract_numeric_id(current_user.id)
        
        # Obtener el otro usuario
        other_user = sirope.find_by_id(numeric_id, User)
        if not other_user:
            flash('Usuario no encontrado.')
            return redirect(url_for('social.index'))
        
        # Obtener una copia fresca del usuario actual
        current_user_fresh = sirope.find_by_id(current_numeric_id, User)
        if not current_user_fresh:
            flash('Error al cargar la información del usuario.')
            return redirect(url_for('social.index'))
        
        # Verificar si hay seguimiento mutuo (amistad)
        user_follows_current = str(current_numeric_id) in other_user.following
        current_follows_user = str(numeric_id) in current_user_fresh.following
        is_friend = user_follows_current and current_follows_user
        
        # Obtener mensajes si son amigos
        messages = []
        if is_friend:
            messages = sirope.find_all(
                Message,
                lambda m: (
                    (sirope._extract_numeric_id(m.sender_id) == current_numeric_id and 
                      sirope._extract_numeric_id(m.receiver_id) == numeric_id) or
                     (sirope._extract_numeric_id(m.sender_id) == numeric_id and 
                     sirope._extract_numeric_id(m.receiver_id) == current_numeric_id)
                )
            )
            messages = sorted(messages, key=lambda m: m.created_at)
        
        return render_template('social/chat.html', 
                             other_user=other_user,
                             messages=messages, 
                             is_friend=is_friend,
                             is_following=current_follows_user,
                             is_followed_by=user_follows_current)
    
    except Exception as e:
        logger.error(f"Error en la página de chat: {str(e)}")
        flash('Ha ocurrido un error al cargar el chat.')
        return redirect(url_for('social.index'))

@bp.route('/follow_user/<user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    try:
        # Extraer IDs numéricos
        numeric_id = sirope._extract_numeric_id(user_id)
        current_numeric_id = sirope._extract_numeric_id(current_user.id)
        
        logger.info(f"Intento de follow: usuario {current_numeric_id} -> {numeric_id}")
        
        # Verificar que no se intente seguir a sí mismo
        if str(numeric_id) == str(current_numeric_id):
            logger.warning(f"Usuario {current_numeric_id} intentó seguirse a sí mismo")
            return jsonify({'error': 'No puedes seguirte a ti mismo'}), 400
        
        # Obtener el usuario a seguir y el usuario actual
        user_to_follow = sirope.find_by_id(numeric_id, User)
        current_user_fresh = sirope.find_by_id(current_numeric_id, User)
        
        if not user_to_follow:
            logger.error(f"Usuario a seguir no encontrado: {numeric_id}")
            return jsonify({'error': 'Usuario no encontrado'}), 404
            
        if not current_user_fresh:
            logger.error(f"Usuario actual no encontrado: {current_numeric_id}")
            return jsonify({'error': 'Error al actualizar la relación'}), 500
            
        # Asegurar que ambos usuarios tengan todos los atributos necesarios
        current_user_fresh.ensure_attributes()
        user_to_follow.ensure_attributes()
            
        str_numeric_id = str(numeric_id)
        str_current_id = str(current_numeric_id)
        
        # Verificar si ya lo sigue
        if str_numeric_id in current_user_fresh.following:
            logger.warning(f"Usuario {current_numeric_id} ya sigue a {numeric_id}")
            return jsonify({'error': 'Ya sigues a este usuario'}), 400
            
        # Seguir al usuario
        current_user_fresh.following.append(str_numeric_id)
        user_to_follow.followers.append(str_current_id)
        
        # Guardar ambos usuarios
        sirope.save(current_user_fresh)
        sirope.save(user_to_follow)
        
        # Verificar que los cambios se guardaron correctamente
        current_user_fresh = sirope.find_by_id(current_numeric_id, User)
        user_to_follow = sirope.find_by_id(numeric_id, User)
        
        if str_numeric_id not in current_user_fresh.following:
            logger.error("Los cambios en following no se guardaron correctamente")
            return jsonify({'error': 'Error al actualizar la relación'}), 500
            
        if str_current_id not in user_to_follow.followers:
            logger.error("Los cambios en followers no se guardaron correctamente")
            return jsonify({'error': 'Error al actualizar la relación'}), 500
        
        # Verificar si hay seguimiento mutuo
        is_mutual = str_current_id in user_to_follow.following
        
        logger.info(f"Follow exitoso: {current_numeric_id} -> {numeric_id} (mutual: {is_mutual})")
        
        return jsonify({
            'success': True,
            'message': 'Usuario seguido correctamente',
            'is_mutual': is_mutual
        })
            
    except Exception as e:
        logger.error(f"Error al seguir usuario: {str(e)}")
        return jsonify({'error': 'Error al seguir al usuario'}), 500

@bp.route('/unfollow_user/<user_id>', methods=['POST'])
@login_required
def unfollow_user(user_id):
    try:
        # Extraer IDs numéricos
        numeric_id = sirope._extract_numeric_id(user_id)
        current_numeric_id = sirope._extract_numeric_id(current_user.id)
        
        logger.info(f"Intento de unfollow: usuario {current_numeric_id} -> {numeric_id}")
        
        # Obtener el usuario a dejar de seguir y el usuario actual
        user_to_unfollow = sirope.find_by_id(numeric_id, User)
        current_user_fresh = sirope.find_by_id(current_numeric_id, User)
        
        if not user_to_unfollow:
            logger.error(f"Usuario a dejar de seguir no encontrado: {numeric_id}")
            return jsonify({'error': 'Usuario no encontrado'}), 404
            
        if not current_user_fresh:
            logger.error(f"Usuario actual no encontrado: {current_numeric_id}")
            return jsonify({'error': 'Error al actualizar la relación'}), 500
            
        # Asegurar que ambos usuarios tengan todos los atributos necesarios
        current_user_fresh.ensure_attributes()
        user_to_unfollow.ensure_attributes()
            
        str_numeric_id = str(numeric_id)
        str_current_id = str(current_numeric_id)
        
        # Verificar si lo sigue
        if str_numeric_id not in current_user_fresh.following:
            logger.warning(f"Usuario {current_numeric_id} no sigue a {numeric_id}")
            return jsonify({'error': 'No sigues a este usuario'}), 400
            
        # Dejar de seguir al usuario
        current_user_fresh.following.remove(str_numeric_id)
        if str_current_id in user_to_unfollow.followers:
            user_to_unfollow.followers.remove(str_current_id)
        
        # Guardar ambos usuarios
        sirope.save(current_user_fresh)
        sirope.save(user_to_unfollow)
        
        # Verificar que los cambios se guardaron correctamente
        current_user_fresh = sirope.find_by_id(current_numeric_id, User)
        user_to_unfollow = sirope.find_by_id(numeric_id, User)
        
        if str_numeric_id in current_user_fresh.following:
            logger.error("Los cambios en following no se eliminaron correctamente")
            return jsonify({'error': 'Error al actualizar la relación'}), 500
            
        if str_current_id in user_to_unfollow.followers:
            logger.error("Los cambios en followers no se eliminaron correctamente")
            return jsonify({'error': 'Error al actualizar la relación'}), 500
        
        logger.info(f"Unfollow exitoso: {current_numeric_id} -> {numeric_id}")
        
        return jsonify({
            'success': True,
            'message': 'Usuario dejado de seguir correctamente'
        })
            
    except Exception as e:
        logger.error(f"Error al dejar de seguir usuario: {str(e)}")
        return jsonify({'error': 'Error al dejar de seguir al usuario'}), 500

@bp.route('/send_message/<user_id>', methods=['POST'])
@login_required
def send_message(user_id):
    try:
        # Intentar obtener el contenido del mensaje de JSON o form-data
        if request.is_json:
            data = request.get_json()
            content = data.get('content', '').strip() if data else ''
        else:
            content = request.form.get('content', '').strip()

        if not content:
            return jsonify({'error': 'El mensaje no puede estar vacío'}), 400
        
        # Extraer IDs numéricos
        numeric_id = sirope._extract_numeric_id(user_id)
        current_numeric_id = sirope._extract_numeric_id(current_user.id)
        
        # Verificar que el usuario existe
        other_user = sirope.find_by_id(numeric_id, User)
        if not other_user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Verificar que son amigos
        current_user_fresh = sirope.find_by_id(current_numeric_id, User)
        if not current_user_fresh:
            return jsonify({'error': 'Error al verificar la relación de amistad'}), 500
        
        user_follows_current = str(current_numeric_id) in other_user.following
        current_follows_user = str(numeric_id) in current_user_fresh.following
        
        if not (user_follows_current and current_follows_user):
            return jsonify({'error': 'No puedes enviar mensajes a este usuario'}), 403
        
        # Crear y guardar el mensaje
        now = datetime.now()
        message = Message(
            sender_id=current_user.id,
            receiver_id=other_user.id,
            content=content
        )
        message.created_at = now
        message.read = False
        sirope.save(message)
        
        return jsonify({
            'success': True,
            'message': {
                'content': message.content,
                'created_at': now.strftime('%Y-%m-%d %H:%M:%S'),
                'sender_id': message.sender_id,
                'receiver_id': message.receiver_id
            }
        })
    
    except Exception as e:
        logger.error(f"Error al enviar mensaje: {str(e)}")
        return jsonify({'error': 'Error al enviar el mensaje'}), 500

def get_recent_conversations(user_id):
    try:
        # Obtener todos los mensajes donde el usuario es sender o receiver
        all_messages = sirope.find_all(
            Message,
            lambda m: (
                sirope._extract_numeric_id(m.sender_id) == user_id or
                sirope._extract_numeric_id(m.receiver_id) == user_id
            )
        )
        
        # Agrupar por conversación
        conversations = {}
        for message in all_messages:
            other_id = (sirope._extract_numeric_id(message.receiver_id) 
                       if sirope._extract_numeric_id(message.sender_id) == user_id 
                       else sirope._extract_numeric_id(message.sender_id))
            
            if other_id not in conversations:
                other_user = sirope.find_by_id(other_id, User)
                if other_user:
                    conversations[other_id] = {
                        'user': other_user,
                        'last_message': message
                    }
            else:
                if message.created_at > conversations[other_id]['last_message'].created_at:
                    conversations[other_id]['last_message'] = message
        
        # Convertir a lista y ordenar por fecha del último mensaje
        conv_list = list(conversations.values())
        conv_list.sort(key=lambda x: x['last_message'].created_at, reverse=True)
        
        return conv_list
    
    except Exception as e:
        logger.error(f"Error al obtener conversaciones recientes: {str(e)}")
        return []

def mark_messages_as_read(messages, user_id):
    try:
        for message in messages:
            if (sirope._extract_numeric_id(message.receiver_id) == user_id and 
                not message.read):
                message.read = True
                sirope.save(message)
    except Exception as e:
        logger.error(f"Error al marcar mensajes como leídos: {str(e)}") 