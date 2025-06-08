from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import Optional
from ..utils.form_validators import CustomDataRequired, CustomLength, CustomNumberRange

class ArtworkForm(FlaskForm):
    """
    Formulario para crear una nueva obra de arte
    
    Este formulario maneja la creación de artworks:
    - Título y descripción requeridos
    - Imagen obligatoria
    - Etiquetas opcionales
    
    Attributes:
        title (StringField): Título de la obra
        description (TextAreaField): Descripción detallada
        image (FileField): Archivo de imagen
        tags (StringField): Etiquetas separadas por comas
        submit (SubmitField): Botón de envío
        
    Note:
        Las etiquetas son opcionales pero tienen límite de longitud
        Solo acepta formatos de imagen específicos
    """
    title = StringField('Título', validators=[CustomDataRequired(), CustomLength(max=100)])
    description = TextAreaField('Descripción', validators=[CustomDataRequired(), CustomLength(max=500)])
    image = FileField('Imagen', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo se permiten imágenes.')
    ])
    tags = StringField('Etiquetas', validators=[Optional(), CustomLength(max=200)])
    submit = SubmitField('Publicar Artwork')

class EditArtworkForm(FlaskForm):
    """
    Formulario para editar una obra de arte existente
    
    Este formulario maneja la edición de artworks:
    - Título y descripción requeridos
    - Imagen opcional
    - Etiquetas opcionales
    
    Attributes:
        title (StringField): Título de la obra
        description (TextAreaField): Descripción detallada
        image (FileField): Archivo de imagen nuevo
        tags (StringField): Etiquetas separadas por comas
        submit (SubmitField): Botón de envío
        
    Note:
        La imagen es opcional ya que puede mantener la existente
        Las etiquetas se pueden actualizar o eliminar
    """
    title = StringField('Título', validators=[CustomDataRequired(), CustomLength(max=100)])
    description = TextAreaField('Descripción', validators=[CustomDataRequired(), CustomLength(max=500)])
    image = FileField('Imagen', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo se permiten imágenes.')
    ])
    tags = StringField('Etiquetas', validators=[Optional(), CustomLength(max=200)])
    submit = SubmitField('Guardar Cambios')

class GivePointsForm(FlaskForm):
    """
    Formulario para donar puntos a una obra de arte
    
    Este formulario maneja la donación de puntos:
    - Cantidad de puntos requerida
    - Validación de rango
    
    Attributes:
        points (IntegerField): Cantidad de puntos a donar
        submit (SubmitField): Botón de envío
        
    Note:
        La cantidad debe ser positiva y estar dentro del saldo disponible
    """
    points = IntegerField('Puntos', validators=[
        CustomDataRequired(),
        CustomNumberRange(min=1, message='Debes donar al menos 1 punto.')
    ])
    submit = SubmitField('Donar Puntos') 