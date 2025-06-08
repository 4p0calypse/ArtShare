from flask import Blueprint

bp = Blueprint('points', __name__)

from . import routes 