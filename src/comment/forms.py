from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
 
class CommentForm(FlaskForm):
    content = TextAreaField('Comentario', 
                          validators=[DataRequired(), Length(min=1, max=500)],
                          render_kw={"placeholder": "Escribe un comentario...", "rows": 3})
    submit = SubmitField('Publicar') 