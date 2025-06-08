from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange

class CustomDataRequired(DataRequired):
    def __init__(self, message=None):
        super().__init__(message=message or 'Este campo es obligatorio.')

class CustomEmail(Email):
    def __init__(self, message=None):
        super().__init__(message=message or 'Por favor, introduce una dirección de email válida.')

class CustomLength(Length):
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

class CustomEqualTo(EqualTo):
    def __init__(self, fieldname, message=None):
        super().__init__(fieldname, message=message or 'Los campos deben coincidir.')

class CustomNumberRange(NumberRange):
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