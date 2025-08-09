from flask import Blueprint

bp = Blueprint('diary', __name__)

from . import routes