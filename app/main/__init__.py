from flask import Blueprint
from app.settings import BaseConfig

tpl_path = BaseConfig.Europix_TEMPLATE

main = Blueprint('main', __name__, template_folder="themes", static_url_path='/statics',
                 static_folder='themes')


def change_static_folder(blueprint: Blueprint, template_path: str = None):
    if template_path == None:
        return
    # blueprint.template_folder = "themes/{}".format(template_path)
    blueprint.static_folder = 'themes/{}/static'.format(template_path)


from . import views
