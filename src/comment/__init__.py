from flask import Blueprint

bp = Blueprint('comment', __name__)

from . import routes 