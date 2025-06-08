from datetime import datetime

class PointsTransaction:
    TRANSACTION_TYPES = {
        'GIVE': 'give',  # Dar puntos a un artwork
        'RECEIVE': 'receive',  # Recibir puntos por un artwork
        'WITHDRAW': 'withdraw',  # Retirar puntos a dinero real
        'SYSTEM': 'system'  # Transacciones del sistema (bonos, etc)
    }

    def __init__(self, user_id, points, type, description=None, reference_id=None, created_at=None):
        self.user_id = user_id
        self.points = points
        self.type = type  # 'give', 'receive', 'purchase', 'withdrawal'
        self.description = description
        self.reference_id = reference_id  # ID del artwork relacionado, si aplica
        self.created_at = created_at or datetime.utcnow()
        self.status = 'completed'  # 'completed', 'pending', 'failed'
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
        tx = cls(
            user_id=user_id,
            points=points,
            type='withdrawal',
            description=f'Retiro de {points} puntos',
            created_at=datetime.utcnow()
        )
        tx.status = 'pending'  # Establecer el estado después de la creación
        return tx 