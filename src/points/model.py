from datetime import datetime

class PointsTransaction:
    """
    Modelo que representa una transacción de puntos en el sistema.
    
    Esta clase maneja todas las operaciones relacionadas con puntos,
    incluyendo donaciones a artworks y retiros de puntos.
    
    Attributes:
        user_id (str): ID del usuario involucrado en la transacción
        points (int): Cantidad de puntos de la transacción
        type (str): Tipo de transacción ('give', 'receive', 'withdrawal')
        description (str): Descripción detallada de la transacción
        reference_id (str, optional): ID de referencia (ej: artwork_id)
        created_at (datetime): Fecha de la transacción
        status (str, optional): Estado de la transacción ('pending', 'completed', 'failed')
        
    Note:
        Las transacciones son inmutables una vez creadas para mantener
        la integridad del historial de puntos
    """

    TRANSACTION_TYPES = {
        'GIVE': 'give',  # Dar puntos a un artwork
        'RECEIVE': 'receive',  # Recibir puntos por un artwork
        'WITHDRAW': 'withdraw',  # Retirar puntos a dinero real
        'SYSTEM': 'system'  # Transacciones del sistema (bonos, etc)
    }

    def __init__(self, user_id, points, type, description, reference_id=None, created_at=None, status='completed'):
        """
        Inicializa una nueva transacción de puntos
        
        Args:
            user_id (str): ID del usuario
            points (int): Cantidad de puntos
            type (str): Tipo de transacción
            description (str): Descripción
            reference_id (str, optional): ID de referencia
            created_at (datetime, optional): Timestamp
            status (str, optional): Estado inicial
            
        Note:
            Si no se proporciona created_at, se usa el timestamp actual
        """
        self.user_id = user_id
        self.points = points
        self.type = type
        self.description = description
        self.reference_id = reference_id
        self.created_at = created_at or datetime.utcnow()
        self.status = status
        self._id = None

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    def complete(self):
        self.status = 'completed'

    def fail(self):
        self.status = 'failed'

    def cancel(self):
        self.status = 'cancelled'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.points,
            'transaction_type': self.type,
            'reference_id': self.reference_id,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'status': self.status
        }

    @classmethod
    def create_give_transaction(cls, user_id, artwork_id, points):
        """
        Crea una transacción de donación de puntos a un artwork
        
        Args:
            user_id (str): ID del usuario donante
            artwork_id (str): ID del artwork receptor
            points (int): Cantidad de puntos a donar
            
        Returns:
            PointsTransaction: Nueva instancia de transacción de donación
            
        Note:
            El tipo se establece como 'give' y el estado como 'completed'
        """
        return cls(
            user_id=user_id,
            points=points,
            type='give',
            description=f'Donación de {points} puntos',
            reference_id=artwork_id,
            created_at=datetime.utcnow()
        )

    @classmethod
    def create_receive_transaction(cls, user_id, artwork_id, points):
        """
        Crea una transacción de recepción de puntos por un artwork
        
        Args:
            user_id (str): ID del usuario receptor
            artwork_id (str): ID del artwork donado
            points (int): Cantidad de puntos recibidos
            
        Returns:
            PointsTransaction: Nueva instancia de transacción de recepción
            
        Note:
            El tipo se establece como 'receive' y el estado como 'completed'
        """
        return cls(
            user_id=user_id,
            points=points,
            type='receive',
            description=f'Recepción de {points} puntos',
            reference_id=artwork_id,
            created_at=datetime.utcnow()
        )

    @classmethod
    def create_withdrawal_transaction(cls, user_id, points):
        """
        Crea una transacción de retiro de puntos
        
        Args:
            user_id (str): ID del usuario que retira
            points (int): Cantidad de puntos a retirar
            
        Returns:
            PointsTransaction: Nueva instancia de transacción de retiro
            
        Note:
            El tipo se establece como 'withdrawal' y el estado como 'pending'
            hasta que se confirme el retiro
        """
        tx = cls(
            user_id=user_id,
            points=points,
            type='withdrawal',
            description=f'Retiro de {points} puntos',
            created_at=datetime.utcnow()
        )
        tx.status = 'pending'
        return tx 