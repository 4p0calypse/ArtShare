from flask import Flask, send_from_directory
from flask_login import LoginManager
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from .config import Config
from .services.sirope_service import SiropeService
from .auth.user_model import User
from .utils.filters import format_date, format_datetime
from .utils.helpers import get_user, format_points, format_currency
import logging
import os
import tempfile
from datetime import datetime
import redis

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

login_manager = LoginManager()
sirope_service = SiropeService()
sess = Session()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_SECRET_KEY'] = app.config['SECRET_KEY']
    
    # Ruta para servir archivos estáticos
    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory(app.static_folder, filename)
    
    # Inicializar Redis y Flask-Session
    try:
        # Crear el cliente Redis
        redis_client = redis.from_url(app.config['SESSION_REDIS'])
        redis_client.ping()  # Verificar conexión
        app.config['SESSION_REDIS'] = redis_client
        logger.info("Conexión exitosa con Redis")
        
        # Inicializar Flask-Session
        sess.init_app(app)
        logger.info("Flask-Session inicializado correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar Redis o Flask-Session: {str(e)}")
        raise

    # Asegurar que existe la carpeta de uploads
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Inicializar extensiones
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    login_manager.session_protection = 'strong'
    csrf.init_app(app)

    # Registrar filtros personalizados
    app.jinja_env.filters['date'] = format_date
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['format_points'] = format_points
    app.jinja_env.filters['format_currency'] = format_currency
    app.jinja_env.globals['get_user'] = get_user
    app.jinja_env.globals['format_points'] = format_points
    app.jinja_env.globals['format_currency'] = format_currency
    app.jinja_env.globals['now'] = datetime.utcnow
    app.jinja_env.globals['csrf_token'] = lambda: csrf._get_token()

    # Registrar blueprints
    from .auth.routes import bp as auth_bp
    app.register_blueprint(auth_bp)

    from .main.routes import bp as main_bp
    app.register_blueprint(main_bp)

    from .artwork.routes import bp as artwork_bp
    app.register_blueprint(artwork_bp, url_prefix='/artwork')

    from .comment.routes import bp as comment_bp
    app.register_blueprint(comment_bp, url_prefix='/comment')

    from .points.routes import bp as points_bp
    app.register_blueprint(points_bp, url_prefix='/points')

    from .social.routes import bp as social_bp
    app.register_blueprint(social_bp, url_prefix='/social')

    # Ruta para servir archivos subidos
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @login_manager.user_loader
    def load_user(user_id):
        logger.info(f"Intentando cargar usuario con ID: {user_id}")
        try:
            if not user_id:
                logger.warning("ID de usuario vacío")
                return None
                
            # Intentar cargar el usuario directamente
            user = sirope_service.find_by_id(user_id, User)
            
            if user:
                # Asegurar que el usuario tenga todos los atributos necesarios
                if not hasattr(user, 'artworks'):
                    user.artworks = []
                if not hasattr(user, 'followers'):
                    user.followers = []
                if not hasattr(user, 'following'):
                    user.following = []
                if not hasattr(user, 'points'):
                    user.points = 0
                if not hasattr(user, 'created_at'):
                    user.created_at = datetime.utcnow()
                
                # Verificar que el usuario tenga un ID válido
                if not user.id:
                    logger.error(f"Usuario sin ID válido después de cargar: {user.username}")
                    return None
                
                logger.info(f"Usuario cargado exitosamente: {user.username} (ID: {user.id})")
                return user
            else:
                logger.warning(f"No se encontró usuario con ID: {user_id}")
                return None
        except Exception as e:
            logger.error(f"Error al cargar usuario: {str(e)}")
            return None

    return app 