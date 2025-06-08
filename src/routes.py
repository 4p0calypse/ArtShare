from flask import Blueprint, render_template, current_app
from flask_login import current_user
from .services.sirope_service import SiropeService
from .artwork.model import Artwork

bp = Blueprint('main', __name__)
sirope = SiropeService()

@bp.route('/')
def index():
    # Obtener los artworks más recientes
    artworks = sirope.find_all(Artwork)
    # Ordenar por fecha de creación (más recientes primero)
    artworks = sorted(artworks, key=lambda x: x.created_at, reverse=True)
    # Limitar a los 12 más recientes
    artworks = artworks[:12]
    
    return render_template('index.html',
                         title='Inicio',
                         artworks=artworks)

@bp.route('/explore')
def explore():
    # Obtener todos los artworks
    artworks = sirope.find_all(Artwork)
    # Ordenar por puntos recibidos (más populares primero)
    artworks = sorted(artworks, key=lambda x: x.points_received, reverse=True)
    
    return render_template('explore.html',
                         title='Explorar',
                         artworks=artworks)

@bp.route('/about')
def about():
    return render_template('about.html', title='Acerca de') 