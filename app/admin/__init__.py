
from flask import Blueprint

admin = Blueprint('admin', __name__, template_folder="templates", static_url_path='/statics', static_folder='static')

# Circular import Prevent!
from . import views
