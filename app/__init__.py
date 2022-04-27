import os
import logging
import click
from logging.handlers import RotatingFileHandler
from flask import Flask, request, redirect, url_for

from app.util import pretty_date
from app.ext import db, sitemap, login_manager, csrf, migrate,app_helper, db_config,scheduler
from app.settings import config, TestingConfig, DevelopmentConfig
from app.template_global import register_template_filter, register_template_global
from app.models import AccessLog

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask(__name__)
    app.config['CONFIG_NAME'] = config_name
    if config_name == 'testing':
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(config[config_name])
    check_setup(app)

    register_logging(app)
    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_errors(app)
    register_shell_context(app)
    # register_request_handlers(app)
    register_jiaja2_filters(app)
    register_template_filter(app)
    register_template_global(app)

    return app


def check_setup(app: Flask) -> None:
    app.start = False
    from app.settings import _exist_config
    if _exist_config(app):
        from app.config import Config
        app.config.from_object(Config)
        app.start = True

    @app.before_request
    def request_check_start():
        if app.start:
            return
        ends = frozenset(["admin.setup", "admin.static"])
        if request.endpoint in ends:
            return
        if not _exist_config(app):
            return redirect(url_for("admin.setup"))
        return 


def register_logging(app):
    # Logging for CW2
    # Generate a blog.log in logs/blog.log
    file_handler = RotatingFileHandler(os.path.join(basedir, 'logs/blog.log'),
                                       maxBytes=10 * 1024 * 1024, backupCount=10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    #  app.logger.setLevel(logging.INFO)
    app.logger.setLevel(logging.DEBUG)
    # app.logger.setLevel(logging.WARNING)
    # Start handler
    app.logger.info("Blog StartUP")
    app.logger.debug("Debug \n")
    app.logger.warning("Warning \n")
    # Different Levels of Log


def register_extensions(app):
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    sitemap.init_app(app)
    migrate.init_app(app, db=db)
    app_helper.init_app(app)
    db_config.init_app(app, db=db)

    # scheduler.start()


def register_blueprints(app):
    # 注册蓝本 main
    from app.main import main as main_blueprint, change_static_folder
    change_static_folder(main_blueprint, os.getenv('Europix_TEMPLATE', 'tend'))
    app.register_blueprint(main_blueprint)

    # 注册蓝本 admin
    from app.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    login_manager.blueprint_login_views = {
        'admin': 'admin.login',
        'main' : 'main.login'
    }


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        from app.models import User, Article, Category, \
            Tag, article_tag, Recommend, Picture, Setting
        return dict(db=db, User=User, Article=Article, \
            Category=Category, Tag=Tag, Recommend = Recommend, \
                AccessLog = AccessLog, Picture = Picture, Setting = Setting)


def register_errors(app):
    pass


def register_jiaja2_filters(app):
    env = app.jinja_env
    env.filters['pretty_date'] = pretty_date


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop):
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')