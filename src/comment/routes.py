from flask import Blueprint, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from .model import Comment
from ..artwork.model import Artwork
from ..services.sirope_service import SiropeService
from ..auth.user_model import User

bp = Blueprint('comment', __name__)
sirope = SiropeService()

@bp.route('/create/<artwork_id>', methods=['POST'])
@login_required
def create(artwork_id):
    artwork = sirope.find_by_id(artwork_id, Artwork)
    if artwork is None:
        return jsonify({'error': 'Artwork no encontrado'}), 404
    
    content = request.form.get('content')
    if not content:
        return jsonify({'error': 'El comentario no puede estar vacío'}), 400
    
    comment = Comment(content=content, author_id=current_user.id, artwork_id=artwork_id)
    comment_id = sirope.save(comment)
    
    artwork.add_comment(comment_id)
    sirope.save(artwork)
    
    author = sirope.find_by_id(comment.author_id, User)
    
    return jsonify({
        'id': comment_id,
        'content': comment.content,
        'author': author.username,
        'created_at': comment.created_at.isoformat()
    })

@bp.route('/<comment_id>/edit', methods=['POST'])
@login_required
def edit(comment_id):
    comment = sirope.find_by_id(comment_id, Comment)
    if comment is None:
        return jsonify({'error': 'Comentario no encontrado'}), 404
    if comment.author_id != current_user.id:
        return jsonify({'error': 'No tienes permiso para editar este comentario'}), 403
    
    content = request.form.get('content')
    if not content:
        return jsonify({'error': 'El comentario no puede estar vacío'}), 400
    
    comment.edit_content(content)
    sirope.save(comment)
    
    return jsonify({
        'content': comment.content,
        'updated_at': comment.updated_at.isoformat()
    })

@bp.route('/<comment_id>/delete', methods=['POST'])
@login_required
def delete(comment_id):
    comment = sirope.find_by_id(comment_id, Comment)
    if comment is None:
        return jsonify({'error': 'Comentario no encontrado'}), 404
    
    # Obtener el artwork para verificar si el usuario actual es el autor
    artwork = sirope.find_by_id(comment.artwork_id, Artwork)
    if artwork is None:
        return jsonify({'error': 'Artwork no encontrado'}), 404
    
    # Verificar si el usuario actual es el autor del comentario o del artwork
    if comment.author_id != current_user.id and artwork.author_id != current_user.id:
        return jsonify({'error': 'No tienes permiso para eliminar este comentario'}), 403
    
    # Eliminar el comentario del artwork silenciosamente
    artwork.remove_comment(comment_id)
    sirope.save(artwork)
    
    # Eliminar el comentario
    sirope.delete(comment)
    
    return jsonify({'message': 'Comentario eliminado'}) 