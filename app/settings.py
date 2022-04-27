# -*- coding: utf-8 -*-
import os
import sys
import hashlib
from flask import current_app, render_template
from flask.app import Flask

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


# SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'


class BaseConfig(object):
    # Const numbers:
    SECRET_KEY = os.getenv('SECRET_KEY') or hashlib.new(name='md5', data=b'h3blog python@#').hexdigest()
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ECHO = False
    # For mail service
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Europix Admin', MAIL_USERNAME)
    # for site service
    Europix_COMMENT = os.getenv("Europix_COMMENT", False)  # 是否开发评论，默认不开启
    Europix_TEMPLATE = os.getenv('Europix_TEMPLATE', 'tend')  # 前端模板
    # for admin H3BLOG_
    Europix_UPLOAD_TYPE = os.getenv('Europix_UPLOAD_TYPE', '')  # 默认本地上传
    Europix_UPLOAD_PATH = os.path.join(basedir, 'uploads')
    Europix_ALLOWED_IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'webp']
    Europix_TONGJI_SCRIPT = os.getenv('Europix_TONGJI_SCRIPT', '')
    Europix_EXTEND_META = os.getenv('Europix_EXTEND_META', '')

    MAX_CONTENT_LENGTH = 32 * 1024 * 1024
    SITEMAP_URL_SCHEME = os.getenv('SITEMAP_URL_SCHEME', 'http')
    SITEMAP_MAX_URL_COUNT = os.getenv('SITEMAP_MAX_URL_COUNT', 100000)


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', prefix + os.path.join(basedir, 'data.db'))


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # in-memory database


class ProductionConfig(BaseConfig):
    pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}


def exist_config() -> bool:
    return _exist_config(current_app)


def _exist_config(app: Flask) -> bool:
    filename = "{}/config.py".format(app.root_path)
    return os.path.exists(filename)


def create_config(db_uri: str) -> None:
    config_name = current_app.config['CONFIG_NAME']
    import_config = 'ProductionConfig'
    if config_name == 'development':
        import_config = 'DevelopmentConfig'
    elif config_name == 'testing':
        import_config = 'TestingConfig'
    data = render_template("config.tpl", db_uri=db_uri, import_config=import_config)
    filename = '{}/config.py'.format(current_app.root_path)
    with open(filename, 'w') as f:
        f.write(data)


if __name__ == "__main__":
    pass
