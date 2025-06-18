from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Artwork:
    """
    Modelo que representa una obra de arte en la aplicación ArtShare.
    
    Esta clase maneja toda la información y funcionalidad relacionada con las obras de arte,
    incluyendo metadatos, interacciones sociales (likes, comentarios) y sistema de puntos.
    
    Attributes:
        title (str): Título de la obra
        description (str): Descripción detallada
        image_path (str): Ruta al archivo de imagen
        author_id (str): ID del usuario creador
        tags (list): Lista de etiquetas asociadas
        created_at (datetime): Fecha de creación
        updated_at (datetime): Fecha de última modificación
        likes (list): Lista de IDs de usuarios que dieron like
        comments (list): Lista de IDs de comentarios
        views (int): Contador de visualizaciones
        points_received (int): Puntos recibidos por donaciones
        donors (list): Lista de IDs de usuarios que donaron puntos
        
    Note:
        Los IDs se manejan en formato string y se limpian de caracteres especiales
        para mantener consistencia en la base de datos
    """
    
    def __init__(self, title, description, image_path, author_id, tags=None):
        """
        Inicializa una nueva obra de arte con los atributos básicos
        
        Args:
            title (str): Título de la obra
            description (str): Descripción detallada
            image_path (str): Ruta al archivo de imagen
            author_id (str): ID del usuario creador
            tags (str|list, optional): Etiquetas separadas por comas o lista
        """
        self.title = title
        self.description = description
        self.image_path = image_path
        self.author_id = str(author_id).split('@')[-1] if '@' in str(author_id) else str(author_id)
        self.tags = tags.split(',') if tags and isinstance(tags, str) else []
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
        self.likes = []
        self.comments = []
        self.views = 0
        self.points_received = 0
        self.donors = []
        self._id = None

    @property
    def id(self):
        """
        Retorna el ID numérico para uso externo
        
        Limpia el ID de caracteres especiales para mantener consistencia
        
        Returns:
            str: ID limpio de la obra o None si no está establecido
            
        Note:
            Maneja errores silenciosamente para evitar interrupciones
        """
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
        """
        Almacena el ID asegurando el formato correcto
        
        Args:
            value: Valor a establecer como ID
            
        Note:
            Limpia el ID de caracteres especiales y registra errores
        """
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
        """
        Añade un like de un usuario a la obra
        
        Args:
            user_id (str): ID del usuario que da like
            
        Returns:
            bool: True si se añadió el like, False si ya existía
            
        Note:
            Asegura la existencia del atributo likes antes de modificar
            Limpia los IDs para mantener consistencia
        """
        if not hasattr(self, 'likes'):
            self.likes = []
            
        # Limpiar ID del usuario
        clean_user_id = str(user_id).split('@')[-1] if '@' in str(user_id) else str(user_id)
        
        # Limpiar IDs existentes
        clean_likes = [str(like_id).split('@')[-1] if '@' in str(like_id) else str(like_id) for like_id in self.likes]
        
        if clean_user_id not in clean_likes:
            self.likes.append(clean_user_id)
            return True
        return False

    def remove_like(self, user_id):
        """
        Elimina el like de un usuario de la obra
        
        Args:
            user_id (str): ID del usuario que quita el like
            
        Returns:
            bool: True si se eliminó el like, False si no existía
            
        Note:
            Asegura la existencia del atributo likes antes de modificar
            Limpia los IDs para mantener consistencia
        """
        if not hasattr(self, 'likes'):
            self.likes = []
            
        # Limpiar ID del usuario
        clean_user_id = str(user_id).split('@')[-1] if '@' in str(user_id) else str(user_id)
        
        # Limpiar IDs existentes y buscar el like a eliminar
        for i, like_id in enumerate(self.likes):
            clean_like_id = str(like_id).split('@')[-1] if '@' in str(like_id) else str(like_id)
            if clean_like_id == clean_user_id:
                self.likes.pop(i)
                return True
        return False

    def add_comment(self, comment_id):
        """
        Añade un comentario a la obra
        
        Args:
            comment_id (str): ID del comentario a añadir
            
        Note:
            Asegura la existencia del atributo comments antes de modificar
        """
        if not hasattr(self, 'comments'):
            self.comments = []
        self.comments.append(comment_id)

    def remove_comment(self, comment_id):
        """
        Elimina un comentario de la obra
        
        Args:
            comment_id (str): ID del comentario a eliminar
            
        Note:
            Asegura la existencia del atributo comments antes de modificar
        """
        if not hasattr(self, 'comments'):
            self.comments = []
        if comment_id in self.comments:
            self.comments.remove(comment_id)

    def add_points(self, points, donor_id):
        """
        Añade puntos donados por un usuario
        
        Args:
            points (int): Cantidad de puntos a añadir
            donor_id (str): ID del usuario donante
            
        Returns:
            bool: True si se añadieron los puntos, False si el usuario ya había donado
            
        Note:
            Asegura la existencia de los atributos necesarios y limpia el donor_id
        """
        if not hasattr(self, 'donors'):
            self.donors = []
        if not hasattr(self, 'points_received'):
            self.points_received = 0
        
        clean_donor_id = str(donor_id).split('@')[-1] if '@' in str(donor_id) else str(donor_id)
        
        if clean_donor_id not in self.donors:
            self.points_received += points
            self.donors.append(clean_donor_id)
            return True
        return False

    def increment_views(self):
        """
        Incrementa el contador de visualizaciones
        
        Note:
            Asegura la existencia del atributo views antes de modificar
        """
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