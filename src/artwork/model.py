from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Artwork:
    def __init__(self, title, description, image_path, author_id, tags=None):
        self.title = title
        self.description = description
        self.image_path = image_path
        self.author_id = str(author_id).split('@')[-1] if '@' in str(author_id) else str(author_id)  # Asegurar formato consistente
        self.tags = tags.split(',') if tags and isinstance(tags, str) else []  # Lista de etiquetas
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
        self.likes = []  # Lista de IDs de usuarios que dieron like
        self.comments = []  # Lista de IDs de comentarios
        self.views = 0
        self.points_received = 0  # Puntos donados por otros usuarios
        self.donors = []  # Lista de IDs de usuarios que han donado puntos
        self._id = None  # ID interno

    @property
    def id(self):
        """Retorna el ID numérico para uso externo"""
        try:
            if self._id is None:
                return None
            if '@' in str(self._id):
                return str(self._id).split('@')[-1]
            return str(self._id)
        except Exception as e:
            logger.error(f"Error al obtener ID: {e}")
            return None

    @id.setter
    def id(self, value):
        """Almacena el ID"""
        try:
            if value is None:
                self._id = None
            elif '@' in str(value):
                self._id = str(value).split('@')[-1]
            else:
                self._id = str(value)
            logger.debug(f"ID establecido: {self._id}")
        except Exception as e:
            logger.error(f"Error al establecer ID: {e}")
            self._id = None

    def add_like(self, user_id):
        if not hasattr(self, 'likes'):
            self.likes = []
        if user_id not in self.likes:
            self.likes.append(user_id)
            return True
        return False

    def remove_like(self, user_id):
        if not hasattr(self, 'likes'):
            self.likes = []
        if user_id in self.likes:
            self.likes.remove(user_id)
            return True
        return False

    def add_comment(self, comment_id):
        if not hasattr(self, 'comments'):
            self.comments = []
        self.comments.append(comment_id)

    def remove_comment(self, comment_id):
        if not hasattr(self, 'comments'):
            self.comments = []
        if comment_id in self.comments:
            self.comments.remove(comment_id)

    def add_points(self, points, donor_id):
        """Añade puntos donados por un usuario"""
        if not hasattr(self, 'donors'):
            self.donors = []
        if not hasattr(self, 'points_received'):
            self.points_received = 0
        
        # Asegurar formato consistente del donor_id
        clean_donor_id = str(donor_id).split('@')[-1] if '@' in str(donor_id) else str(donor_id)
        
        if clean_donor_id not in self.donors:
            self.points_received += points
            self.donors.append(clean_donor_id)
            return True
        return False

    def increment_views(self):
        if not hasattr(self, 'views'):
            self.views = 0
        self.views += 1

    def to_dict(self):
        # Asegurar que todos los atributos necesarios existan
        if not hasattr(self, 'likes'):
            self.likes = []
        if not hasattr(self, 'comments'):
            self.comments = []
        if not hasattr(self, 'views'):
            self.views = 0
        if not hasattr(self, 'points_received'):
            self.points_received = 0
        if not hasattr(self, 'donors'):
            self.donors = []
        if not hasattr(self, 'tags'):
            self.tags = []
            
        return {
            'id': self.id,
            'title': getattr(self, 'title', ''),
            'description': getattr(self, 'description', ''),
            'image_path': getattr(self, 'image_path', ''),
            'author_id': getattr(self, 'author_id', None),
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') else datetime.utcnow().isoformat(),
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') else datetime.utcnow().isoformat(),
            'likes_count': len(self.likes),
            'comments_count': len(self.comments),
            'views': self.views,
            'points_received': self.points_received,
            'donors_count': len(self.donors)
        }

    def __getstate__(self):
        """Método especial para la serialización"""
        state = self.__dict__.copy()
        # Asegurar que todos los campos necesarios existan
        state.setdefault('_id', None)
        state.setdefault('title', '')
        state.setdefault('description', '')
        state.setdefault('image_path', '')
        state.setdefault('author_id', None)
        state.setdefault('tags', [])
        state.setdefault('likes', [])
        state.setdefault('comments', [])
        state.setdefault('views', 0)
        state.setdefault('points_received', 0)
        state.setdefault('donors', [])
        
        # Convertir datetime a string ISO
        if 'created_at' in state:
            state['created_at'] = state['created_at'].isoformat()
        if 'updated_at' in state:
            state['updated_at'] = state['updated_at'].isoformat()
        return state

    def __setstate__(self, state):
        """Método especial para la deserialización"""
        # Asegurar que todos los campos necesarios existan
        state.setdefault('_id', None)
        state.setdefault('title', '')
        state.setdefault('description', '')
        state.setdefault('image_path', '')
        state.setdefault('author_id', None)
        state.setdefault('tags', [])
        state.setdefault('likes', [])
        state.setdefault('comments', [])
        state.setdefault('views', 0)
        state.setdefault('points_received', 0)
        state.setdefault('donors', [])
        
        # Convertir strings ISO a datetime
        try:
            if 'created_at' in state:
                state['created_at'] = datetime.fromisoformat(state['created_at'])
            else:
                state['created_at'] = datetime.utcnow()
                
            if 'updated_at' in state:
                state['updated_at'] = datetime.fromisoformat(state['updated_at'])
            else:
                state['updated_at'] = datetime.utcnow()
        except (ValueError, TypeError) as e:
            logger.error(f"Error al convertir fechas: {e}")
            state['created_at'] = datetime.utcnow()
            state['updated_at'] = datetime.utcnow()
            
        self.__dict__.update(state)

    def __str__(self):
        return f"Artwork(title={self.title}, id={self.id}, _id={self._id})" 