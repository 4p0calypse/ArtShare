from flask import Blueprint

bp = Blueprint('artwork', __name__)

from . import routes 