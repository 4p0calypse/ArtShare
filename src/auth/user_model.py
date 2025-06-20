from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class User(UserMixin):
    """
    Modelo que representa un usuario en la aplicación ArtShare.
    
    Esta clase maneja toda la información y funcionalidad relacionada con los usuarios,
    incluyendo autenticación, perfil, relaciones sociales y gestión de artworks.
    
    Attributes:
        username (str): Nombre de usuario único
        email (str): Email único del usuario
        password_hash (str): Hash de la contraseña del usuario
        points (int): Puntos disponibles para donar
        profile_picture (str): Ruta a la imagen de perfil
        bio (str): Descripción del perfil
        created_at (datetime): Fecha de creación de la cuenta
        artworks (list): Lista de IDs de artworks creados
        following (list): Lista de IDs de usuarios seguidos
        followers (list): Lista de IDs de usuarios seguidores
        
    Note:
        Hereda de UserMixin para proporcionar la implementación por defecto
        de propiedades y métodos requeridos por Flask-Login
    """
    
    def __init__(self, username=None, email=None, password=None):
        """
        Inicializa un nuevo usuario con los atributos básicos
        
        Args:
            username (str, optional): Nombre de usuario
            email (str, optional): Email del usuario  
            password (str, optional): Contraseña sin procesar
        """
        self._id = None
        self.username = username
        self.email = email
        self.password_hash = None
        if password:
            self.set_password(password)
        self.points = 0
        self.profile_picture = None
        self.bio = ""
        self.created_at = datetime.utcnow()
        self.artworks = []
        self.following = []  # Lista de IDs de usuarios que sigue
        self.followers = []  # Lista de IDs de usuarios que lo siguen

    def get_id(self):
        """
        Retorna el ID del usuario para Flask-Login
        
        Este método es requerido por Flask-Login para identificar usuarios
        
        Returns:
            str: ID del usuario o None si no está establecido
        """
        return str(self._id) if self._id else None

    @property
    def id(self):
        """
        Propiedad que retorna el ID del usuario
        
        Returns:
            str: ID interno del usuario
        """
        return self._id

    @id.setter
    def id(self, value):
        """
        Establece el ID del usuario asegurando el formato correcto
        
        Args:
            value: Valor a establecer como ID
            
        Note:
            Convierte el valor a string o None
        """
        if value is None:
            self._id = None
        else:
            self._id = str(value)

    def __eq__(self, other):
        if not other or not isinstance(other, User):
            return False
        return str(self._id) == str(getattr(other, '_id', None))

    def __hash__(self):
        return hash(str(self._id) if self._id else self.username)

    def is_authenticated(self):
        """Retorna True si el usuario está autenticado"""
        return True and bool(self._id)

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def set_password(self, password):
        """Establece la contraseña del usuario"""
        if password:
            self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica la contraseña del usuario"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def add_points(self, points):
        if not isinstance(points, (int, float)) or points < 0:
            raise ValueError("Points debe ser un número positivo")
        self.points += points

    def remove_points(self, points):
        if not isinstance(points, (int, float)) or points < 0:
            raise ValueError("Points debe ser un número positivo")
        if self.points >= points:
            self.points -= points
            return True
        return False

    def can_withdraw(self):
        from src.config import Config
        return self.points >= Config.MIN_WITHDRAWAL_POINTS

    def get_withdrawal_amount(self):
        from src.config import Config
        return self.points * Config.POINTS_TO_CURRENCY_RATE

    def follow(self, user):
        """Sigue a un usuario"""
        if not user or not user.id:
            return False
            
        # Asegurar que ambos usuarios tengan las listas necesarias
        if not hasattr(self, 'following'):
            self.following = []
        if not hasattr(user, 'followers'):
            user.followers = []
            
        # Convertir IDs a string y asegurar que sean numéricos
        try:
            from ..services.sirope_service import SiropeService
            sirope_service = SiropeService()
            str_user_id = str(user.id)
            str_self_id = str(self.id)
            
            # Verificar que los IDs sean válidos
            if not str_user_id or not str_self_id:
                logger.error("IDs inválidos al intentar seguir")
                return False
                
            # Verificar que no se intente seguirse a sí mismo
            if str_user_id == str_self_id:
                return False
                
            # Añadir las relaciones si no existen
            if str_user_id not in self.following:
                self.following.append(str_user_id)
                if str_self_id not in user.followers:
                    user.followers.append(str_self_id)
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error al seguir usuario: {e}")
            return False

    def unfollow(self, user):
        """Deja de seguir a un usuario"""
        if not user or not user.id:
            return False
            
        # Asegurar que ambos usuarios tengan las listas necesarias
        if not hasattr(self, 'following'):
            self.following = []
        if not hasattr(user, 'followers'):
            user.followers = []
            
        # Convertir IDs a string
        try:
            str_user_id = str(user.id)
            str_self_id = str(self.id)
            
            # Verificar que los IDs sean válidos
            if not str_user_id or not str_self_id:
                logger.error("IDs inválidos al intentar dejar de seguir")
                return False
                
            # Verificar que no se intente dejar de seguirse a sí mismo
            if str_user_id == str_self_id:
                return False
                
            # Eliminar las relaciones si existen
            if str_user_id in self.following:
                self.following.remove(str_user_id)
                if str_self_id in user.followers:
                    user.followers.remove(str_self_id)
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error al dejar de seguir usuario: {e}")
            return False

    def add_follower(self, user):
        """Añade un seguidor"""
        if not user or not user.id:
            return False
        if not hasattr(self, 'followers'):
            self.followers = []
        if str(user.id) not in self.followers:
            self.followers.append(str(user.id))
            return True
        return False

    def remove_follower(self, user):
        """Elimina un seguidor"""
        if not user or not user.id:
            return False
        if not hasattr(self, 'followers'):
            self.followers = []
        if str(user.id) in self.followers:
            self.followers.remove(str(user.id))
            return True
        return False

    def is_following(self, user):
        """Verifica si este usuario sigue al usuario dado"""
        if not user or not user.id:
            return False
        if not hasattr(self, 'following'):
            self.following = []
            
        try:
            str_user_id = str(user.id)
            return str_user_id in self.following
        except Exception as e:
            logger.error(f"Error al verificar si sigue al usuario: {e}")
            return False

    def is_followed_by(self, user):
        """Verifica si este usuario es seguido por el usuario dado"""
        if not user or not user.id:
            return False
        if not hasattr(self, 'followers'):
            self.followers = []
            
        try:
            str_user_id = str(user.id)
            return str_user_id in self.followers
        except Exception as e:
            logger.error(f"Error al verificar si es seguido por el usuario: {e}")
            return False

    def ensure_attributes(self):
        """
        Asegura que todos los atributos necesarios estén inicializados
        
        Inicializa con valores por defecto los atributos que podrían faltar,
        especialmente útil al deserializar usuarios antiguos.
        
        Returns:
            User: La instancia actual del usuario con atributos garantizados
            
        Note:
            Este método es idempotente - puede llamarse múltiples veces sin efectos secundarios
        """
        if not hasattr(self, 'artworks'):
            self.artworks = []
        if not hasattr(self, 'followers'):
            self.followers = []
        if not hasattr(self, 'following'):
            self.following = []
        if not hasattr(self, 'points'):
            self.points = 0
        if not hasattr(self, 'created_at'):
            self.created_at = datetime.utcnow()
        if not hasattr(self, 'bio'):
            self.bio = ""
        if not hasattr(self, 'profile_picture'):
            self.profile_picture = None
        return self

    def to_dict(self):
        return {
            '_id': self._id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'points': self.points,
            'profile_picture': self.profile_picture,
            'bio': self.bio,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'artworks': self.artworks,
            'followers': self.followers,
            'following': self.following
        }

    @staticmethod
    def from_dict(data):
        if not isinstance(data, dict):
            raise ValueError("Los datos deben ser un diccionario")

        user = User()
        try:
            user._id = str(data.get('_id')) if data.get('_id') else None
            user.username = data.get('username')
            user.email = data.get('email')
            user.password_hash = data.get('password_hash')
            user.points = int(data.get('points', 0))
            user.profile_picture = data.get('profile_picture')
            user.bio = data.get('bio', '')
            user.artworks = list(data.get('artworks', []))
            user.followers = list(data.get('followers', []))
            user.following = list(data.get('following', []))

            created_at = data.get('created_at')
            if isinstance(created_at, str):
                try:
                    user.created_at = datetime.fromisoformat(created_at)
                except (ValueError, TypeError):
                    user.created_at = datetime.utcnow()
            else:
                user.created_at = created_at if created_at else datetime.utcnow()

        except Exception as e:
            logger.error(f"Error procesando datos de usuario: {str(e)}")
            if not user.created_at:
                user.created_at = datetime.utcnow()

        return user

    def __getstate__(self):
        return self.to_dict()

    def __setstate__(self, state):
        if isinstance(state, dict):
            new_user = self.from_dict(state)
            self.__dict__.update(new_user.__dict__)
        else:
            logger.error("Estado inválido durante la deserialización")
            self.__init__()

    def __str__(self):
        return f"User(username={self.username}, email={self.email}, id={self._id})" 