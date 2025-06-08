from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class ArtworkForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción', validators=[DataRequired(), Length(max=500)])
    image = FileField('Imagen', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo se permiten imágenes.')
    ])
    tags = StringField('Etiquetas', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Publicar Artwork')

class EditArtworkForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción', validators=[DataRequired(), Length(max=500)])
    image = FileField('Imagen', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo se permiten imágenes.')
    ])
    tags = StringField('Etiquetas', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Actualizar Artwork')

class GivePointsForm(FlaskForm):
    points = IntegerField('¿Cuántos puntos quieres donar?', validators=[
        DataRequired(),
        NumberRange(min=1, message='Debes donar al menos 1 punto.')
    ])
    submit = SubmitField('Donar Puntos') 