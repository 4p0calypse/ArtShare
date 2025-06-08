from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Message:
    def __init__(self, sender_id=None, receiver_id=None, content=None):
        self._id = None
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.created_at = datetime.utcnow()
        self.read = False

    @property
    def id(self):
        return self._id
        
    @id.setter
    def id(self, value):
        self._id = value

    def __getstate__(self):
        """Método especial para la serialización"""
        state = self.__dict__.copy()
        # Asegurar que todos los campos necesarios existan
        state.setdefault('_id', None)
        state.setdefault('sender_id', None)
        state.setdefault('receiver_id', None)
        state.setdefault('content', '')
        state.setdefault('read', False)
        state.setdefault('created_at', datetime.utcnow())
        
        # Convertir datetime a string ISO
        if 'created_at' in state:
            state['created_at'] = state['created_at'].isoformat()
        return state

    def __setstate__(self, state):
        """Método especial para la deserialización"""
        # Asegurar que todos los campos necesarios existan
        state.setdefault('_id', None)
        state.setdefault('sender_id', None)
        state.setdefault('receiver_id', None)
        state.setdefault('content', '')
        state.setdefault('read', False)
        state.setdefault('created_at', datetime.utcnow().isoformat())
        
        # Convertir string ISO a datetime
        try:
            if 'created_at' in state:
                state['created_at'] = datetime.fromisoformat(state['created_at'])
        except (ValueError, TypeError) as e:
            logger.error(f"Error al convertir fecha: {e}")
            state['created_at'] = datetime.utcnow()
            
        self.__dict__.update(state)

    def __str__(self):
        return f"Message(id={self.id}, sender={self.sender_id}, receiver={self.receiver_id})"

    def __eq__(self, other):
        """Método especial para comparación de igualdad"""
        if not isinstance(other, Message):
            return False
        return self.id == other.id

    def __hash__(self):
        """Método especial para generar hash"""
        return hash(self.id)

    def mark_as_read(self):
        """Marca el mensaje como leído"""
        self.read = True

    def to_dict(self):
        """Convierte el mensaje a diccionario para serialización"""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'content': self.content,
            'created_at': self.created_at,
            'read': self.read
        }
        
    @staticmethod
    def from_dict(data):
        """Crea un mensaje desde un diccionario"""
        message = Message(
            sender_id=data['sender_id'],
            receiver_id=data['receiver_id'],
            content=data['content']
        )
        message.id = data.get('id')
        message.read = data.get('read', False)
        message.created_at = data.get('created_at')
        return message 