from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from ..utils.form_validators import CustomDataRequired, CustomLength
 
class CommentForm(FlaskForm):
    """
    Formulario para crear un nuevo comentario
    
    Este formulario maneja la creación de comentarios:
    - Contenido requerido
    - Límite de longitud
    - Estilo visual adaptado
    
    Attributes:
        content (TextAreaField): Contenido del comentario
        submit (SubmitField): Botón de envío
        
    Note:
        El campo de texto se renderiza con 3 filas
        Incluye placeholder para mejor UX
    """
    content = TextAreaField('Comentario', 
                          validators=[CustomDataRequired(), CustomLength(min=1, max=500)],
                          render_kw={"placeholder": "Escribe un comentario...", "rows": 3})
    submit = SubmitField('Publicar') 