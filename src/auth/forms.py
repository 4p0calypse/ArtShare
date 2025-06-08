from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import ValidationError
from flask_wtf.file import FileField, FileAllowed
from .user_model import User
from ..services.sirope_service import SiropeService
from ..utils.form_validators import CustomDataRequired, CustomEmail, CustomLength, CustomEqualTo

class LoginForm(FlaskForm):
    """
    Formulario de inicio de sesión
    
    Este formulario maneja la autenticación de usuarios:
    - Email y contraseña requeridos
    - Opción de recordar sesión
    
    Attributes:
        email (StringField): Campo de email con validación
        password (PasswordField): Campo de contraseña
        remember_me (BooleanField): Opción para mantener sesión
        submit (SubmitField): Botón de envío
    """
    email = StringField('Email', validators=[CustomDataRequired(), CustomEmail()])
    password = PasswordField('Contraseña', validators=[CustomDataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    """
    Formulario de registro de usuarios
    
    Este formulario maneja el registro de nuevos usuarios:
    - Validación de campos requeridos
    - Validación de formato de email
    - Confirmación de contraseña
    - Subida opcional de imagen de perfil
    
    Attributes:
        username (StringField): Nombre de usuario único
        email (StringField): Email único
        password (PasswordField): Contraseña
        password2 (PasswordField): Confirmación de contraseña
        profile_picture (FileField): Imagen de perfil opcional
        submit (SubmitField): Botón de envío
        
    Note:
        Incluye validación personalizada de username y email
        para evitar duplicados
    """
    username = StringField('Nombre de usuario', validators=[CustomDataRequired(), CustomLength(min=3, max=64)])
    email = StringField('Email', validators=[CustomDataRequired(), CustomEmail(), CustomLength(max=120)])
    password = PasswordField('Contraseña', validators=[CustomDataRequired(), CustomLength(min=6)])
    password2 = PasswordField('Repetir Contraseña', validators=[CustomDataRequired(), CustomEqualTo('password')])
    profile_picture = FileField('Imagen de Perfil', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes (jpg, jpeg, png)')
    ])
    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        """
        Valida que el nombre de usuario no esté en uso
        
        Args:
            username (StringField): Campo de nombre de usuario
            
        Raises:
            ValidationError: Si el username ya existe
        """
        sirope = SiropeService()
        user = sirope.find_first(User, lambda u: u.username == username.data)
        if user is not None:
            raise ValidationError('Este nombre de usuario ya está en uso.')

    def validate_email(self, email):
        """
        Valida que el email no esté registrado
        
        Args:
            email (StringField): Campo de email
            
        Raises:
            ValidationError: Si el email ya existe
        """
        sirope = SiropeService()
        user = sirope.find_first(User, lambda u: u.email == email.data)
        if user is not None:
            raise ValidationError('Este email ya está registrado.')

class ProfileForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[CustomDataRequired(), CustomLength(min=3, max=64)])
    email = StringField('Email', validators=[CustomDataRequired(), CustomEmail(), CustomLength(max=120)])
    bio = TextAreaField('Biografía', validators=[CustomLength(max=500)])
    profile_picture = FileField('Imagen de Perfil', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes (jpg, jpeg, png)')
    ])
    submit = SubmitField('Actualizar Perfil')

class RequestPasswordResetForm(FlaskForm):
    """
    Formulario para solicitar recuperación de contraseña
    
    Este formulario maneja solicitudes de recuperación:
    - Validación de email existente
    
    Attributes:
        email (StringField): Email de la cuenta a recuperar
        submit (SubmitField): Botón de envío
        
    Note:
        Verifica que el email corresponda a una cuenta existente
    """
    email = StringField('Email', validators=[CustomDataRequired(), CustomEmail()])
    submit = SubmitField('Solicitar Recuperación')

    def validate_email(self, email):
        """
        Valida que el email corresponda a una cuenta existente
        
        Args:
            email (StringField): Campo de email
            
        Raises:
            ValidationError: Si el email no existe
        """
        sirope = SiropeService()
        user = sirope.find_first(User, lambda u: u.email == email.data)
        if user is None:
            raise ValidationError('No existe una cuenta con ese email.')

class DirectPasswordResetForm(FlaskForm):
    """
    Formulario para cambio directo de contraseña
    
    Este formulario maneja el cambio de contraseña:
    - Validación de credenciales
    - Nueva contraseña y confirmación
    
    Attributes:
        email (StringField): Email de la cuenta
        username (StringField): Nombre de usuario
        new_password (PasswordField): Nueva contraseña
        new_password2 (PasswordField): Confirmación de nueva contraseña
        submit (SubmitField): Botón de envío
        
    Note:
        Verifica que el email y username coincidan con una cuenta
    """
    email = StringField('Email', validators=[CustomDataRequired(), CustomEmail()])
    username = StringField('Nombre de usuario', validators=[CustomDataRequired()])
    new_password = PasswordField('Nueva Contraseña', validators=[CustomDataRequired(), CustomLength(min=6)])
    new_password2 = PasswordField('Repetir Nueva Contraseña', validators=[CustomDataRequired(), CustomEqualTo('new_password')])
    submit = SubmitField('Cambiar Contraseña')

    def validate(self):
        """
        Valida que el email y username correspondan a la misma cuenta
        
        Returns:
            bool: True si los datos son válidos, False en caso contrario
        """
        if not super().validate():
            return False
        
        sirope = SiropeService()
        user = sirope.find_first(
            User, 
            lambda u: u.email == self.email.data and u.username == self.username.data
        )
        
        if user is None:
            self.email.errors.append('El email y nombre de usuario no coinciden con ninguna cuenta.')
            return False
            
        return True 