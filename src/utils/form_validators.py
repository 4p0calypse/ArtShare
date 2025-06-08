from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange

class CustomDataRequired(DataRequired):
    """
    Validador personalizado para campos requeridos
    
    Esta clase extiende DataRequired para proporcionar mensajes en español
    y un manejo más robusto de campos vacíos.
    
    Args:
        message (str, optional): Mensaje de error personalizado
        
    Note:
        Limpia errores previos antes de validar
        Considera espacios en blanco como valor vacío
    """
    
    def __init__(self, message=None):
        if message is None:
            message = 'Este campo es obligatorio.'
        super().__init__(message=message)

    def __call__(self, form, field):
        if not field.data or isinstance(field.data, str) and not field.data.strip():
            field.errors[:] = []  # Limpiar errores previos
            raise ValidationError(self.message)

class CustomEmail(Email):
    """
    Validador personalizado para direcciones de email
    
    Esta clase extiende Email para proporcionar mensajes en español
    y un manejo más amigable de errores.
    
    Args:
        message (str, optional): Mensaje de error personalizado
        
    Note:
        Limpia errores previos antes de validar
        Usa la validación estándar de Email
    """
    
    def __init__(self, message=None):
        if message is None:
            message = 'Por favor, introduce una dirección de email válida.'
        super().__init__(message=message)

    def __call__(self, form, field):
        try:
            super().__call__(form, field)
        except ValidationError:
            field.errors[:] = []  # Limpiar errores previos
            raise ValidationError(self.message)

class CustomLength(Length):
    """
    Validador personalizado para longitud de campos
    
    Esta clase extiende Length para proporcionar mensajes en español
    y manejo flexible de límites mínimos y máximos.
    
    Args:
        min (int): Longitud mínima (-1 para ignorar)
        max (int): Longitud máxima (-1 para ignorar)
        message (str, optional): Mensaje de error personalizado
        
    Note:
        Genera mensajes descriptivos basados en los límites
        Limpia errores previos antes de validar
    """
    
    def __init__(self, min=-1, max=-1, message=None):
        message = message or self._get_message(min, max)
        super().__init__(min=min, max=max, message=message)

    def _get_message(self, min, max):
        if min > -1 and max > -1:
            return f'La longitud debe estar entre {min} y {max} caracteres.'
        elif min > -1:
            return f'Este campo debe tener al menos {min} caracteres.'
        elif max > -1:
            return f'Este campo no puede tener más de {max} caracteres.'
        return None

    def __call__(self, form, field):
        try:
            super().__call__(form, field)
        except ValidationError:
            field.errors[:] = []  # Limpiar errores previos
            raise ValidationError(self.message)

class CustomEqualTo(EqualTo):
    """
    Validador personalizado para comparación de campos
    
    Esta clase extiende EqualTo para proporcionar mensajes en español
    y validación de campos coincidentes.
    
    Args:
        fieldname (str): Nombre del campo a comparar
        message (str, optional): Mensaje de error personalizado
        
    Note:
        Limpia errores previos antes de validar
        Útil para validación de contraseñas
    """
    
    def __init__(self, fieldname, message=None):
        if message is None:
            message = 'Los campos deben coincidir.'
        super().__init__(fieldname, message=message)

    def __call__(self, form, field):
        try:
            super().__call__(form, field)
        except ValidationError:
            field.errors[:] = []  # Limpiar errores previos
            raise ValidationError(self.message)

class CustomNumberRange(NumberRange):
    """
    Validador personalizado para rangos numéricos
    
    Esta clase extiende NumberRange para proporcionar mensajes en español
    y validación flexible de rangos.
    
    Args:
        min (int|float, optional): Valor mínimo
        max (int|float, optional): Valor máximo
        message (str, optional): Mensaje de error personalizado
        
    Note:
        Genera mensajes descriptivos basados en los límites
        Limpia errores previos antes de validar
    """
    
    def __init__(self, min=None, max=None, message=None):
        message = message or self._get_message(min, max)
        super().__init__(min=min, max=max, message=message)

    def _get_message(self, min, max):
        if min is not None and max is not None:
            return f'El valor debe estar entre {min} y {max}.'
        elif min is not None:
            return f'El valor debe ser mayor o igual a {min}.'
        elif max is not None:
            return f'El valor debe ser menor o igual a {max}.'
        return None

    def __call__(self, form, field):
        try:
            super().__call__(form, field)
        except ValidationError:
            field.errors[:] = []  # Limpiar errores previos
            raise ValidationError(self.message) 