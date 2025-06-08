from datetime import datetime

class Comment:
    """
    Modelo que representa un comentario en una obra de arte.
    
    Esta clase maneja los comentarios que los usuarios pueden hacer en las obras,
    incluyendo el contenido, autor, timestamps y funcionalidad de edición.
    
    Attributes:
        content (str): Contenido del comentario
        author_id (str): ID del usuario que creó el comentario
        artwork_id (str): ID de la obra comentada
        created_at (datetime): Fecha de creación
        updated_at (datetime): Fecha de última modificación
        
    Note:
        Los timestamps se manejan en UTC para consistencia global
    """
    
    def __init__(self, content, author_id, artwork_id, created_at=None):
        """
        Inicializa un nuevo comentario
        
        Args:
            content (str): Contenido del comentario
            author_id (str): ID del usuario autor
            artwork_id (str): ID de la obra comentada
            created_at (datetime, optional): Timestamp de creación
            
        Note:
            Si no se proporciona created_at, se usa el timestamp actual
        """
        self.content = content
        self.author_id = author_id
        self.artwork_id = artwork_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = self.created_at
        self._id = None

    @property
    def id(self):
        """
        Retorna el ID del comentario
        
        Returns:
            str: ID del comentario o None si no está establecido
        """
        return self._id

    @id.setter
    def id(self, value):
        """
        Establece el ID del comentario
        
        Args:
            value: Valor a establecer como ID
        """
        self._id = value

    def edit_content(self, new_content):
        """
        Modifica el contenido del comentario
        
        Args:
            new_content (str): Nuevo contenido del comentario
            
        Note:
            Actualiza el timestamp de modificación al editar
        """
        self.content = new_content
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """
        Convierte el comentario a un diccionario
        
        Returns:
            dict: Representación del comentario en formato diccionario
            
        Note:
            Incluye todos los atributos relevantes y formatea las fechas en ISO
        """
        return {
            'id': getattr(self, 'id', None),
            'content': self.content,
            'author_id': self.author_id,
            'artwork_id': self.artwork_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __str__(self):
        """
        Retorna una representación en string del comentario
        
        Returns:
            str: Representación legible del comentario
            
        Note:
            Trunca el contenido a 30 caracteres para mejor legibilidad
        """
        return f"Comment(content={self.content[:30]}...)" 