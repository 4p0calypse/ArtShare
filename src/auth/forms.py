from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed
from .user_model import User
from ..services.sirope_service import SiropeService

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    profile_picture = FileField('Imagen de Perfil', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes (jpg, jpeg, png)')
    ])
    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        sirope = SiropeService()
        user = sirope.find_first(User, lambda u: u.username == username.data)
        if user is not None:
            raise ValidationError('Este nombre de usuario ya está en uso.')

    def validate_email(self, email):
        sirope = SiropeService()
        user = sirope.find_first(User, lambda u: u.email == email.data)
        if user is not None:
            raise ValidationError('Este email ya está registrado.')

class ProfileForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    bio = TextAreaField('Biografía', validators=[Length(max=500)])
    profile_picture = FileField('Imagen de Perfil', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes (jpg, jpeg, png)')
    ])
    submit = SubmitField('Actualizar Perfil')

class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Solicitar Recuperación')

    def validate_email(self, email):
        sirope = SiropeService()
        user = sirope.find_first(User, lambda u: u.email == email.data)
        if user is None:
            raise ValidationError('No existe una cuenta con ese email.')

class DirectPasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Nombre de usuario', validators=[DataRequired()])
    new_password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=6)])
    new_password2 = PasswordField('Repetir Nueva Contraseña', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Cambiar Contraseña')

    def validate(self):
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