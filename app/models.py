from typing import Any
from app import util

from . import db
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import hashlib
import markdown
from flask_login import current_user
from flask import url_for, request


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    email_state = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64), nullable=False, default='')
    website = db.Column(db.String(128), nullable=False, default='', comment='website')
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    status = db.Column(db.Boolean, default=False)
    role = db.Column(db.Integer, default=2)  # 1=admin
    avatar = db.Column(db.String(120), default='')
    articles = db.relationship('Article', backref='author', lazy='dynamic')

    @property
    def password(self):
        raise ArithmeticError('Error')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password=password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password=password)

    def is_admin(self):
        return self.role == 1
    
    def is_vip(self):
        return self.role == 3
        
    @property
    def role_name(self):
        name = ''
        if self.role == 1:
            name = 'Admin'
        else:
            name = 'Normal User'
        return name

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def is_author(self):
        return Article.query.filter_by(author_id=self.id).first()

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def is_admin(self):
        return False


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64), unique=True, index=True)
    desp = db.Column(db.String(300))
    tpl_list = db.Column(db.String(300))
    tpl_page = db.Column(db.String(300))
    tpl_mold = db.Column(db.String(20))
    content = db.Column(db.Text)
    seo_title = db.Column(db.String(100))
    seo_description = db.Column(db.String(300))
    seo_keywords = db.Column(db.String(300))
    sn = db.Column(db.Integer, default=0)
    visible = db.Column(db.Boolean, default=True)
    articles = db.relationship('Article', backref='category', lazy='dynamic')
    icon = db.Column(db.String(128), default='')

    def __repr__(self):
        return '<Name %r>' % self.name


article_tag = db.Table('article_tag',
                       db.Column('article_id', db.Integer, db.ForeignKey('article.id'), primary_key=True),
                       db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True))


class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False, unique=True, index=True)
    code = db.Column(db.String(64), nullable=False, unique=True, index=True)
    visible = db.Column(db.Boolean, default=True)

    @classmethod
    def add(self, name: str) -> Any:
        tag = Tag.query.filter(Tag.name == name).first()
        if tag is not None:
            return tag
        code = util.get_short_id()
        while db.session.query(Tag.query.filter(Tag.code == code).exists()).scalar():
            code = util.get_short_id()
        tag = Tag(name=name, code=code, visible=True)
        db.session.add(tag)
        db.session.commit()
        return tag

    def __repr__(self):
        return '<Name %r>' % self.name


class Article(db.Model):
    __tablename__ = 'article'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), index=True)
    name = db.Column(db.String(64),index=True,unique=True)
    editor = db.Column(db.String(10),nullable=False, default='')
    content = db.Column(db.Text)
    content_html = db.Column(db.Text)
    summary = db.Column(db.String(300))
    thumbnail = db.Column(db.String(200))
    state = db.Column(db.Integer, default=0)
    vc = db.Column(db.Integer, default=0)
    comment_num = db.Column(db.Integer, nullable=False, default=0)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    tags = db.relationship('Tag',secondary=article_tag,backref=db.backref('articles',lazy='dynamic'),lazy='dynamic')
    h_content = db.Column(db.String(800), nullable=False, default='')
    h_role = db.Column(db.Integer, default=0)
    is_crawl = db.Column(db.Integer, default=0)
    origin_url = db.Column(db.String(200), default='',)
    origin_author = db.Column(db.String(100), default='')

    def content_to_html(self):
        return markdown.markdown(self.content, extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            ])

    @property
    def category(self):
        return Category.query.get(self.category_id)

    @property
    def category_name(self):
        return Category.query.get(self.category_id).name

    @property
    def previous(self):
        a = self.query.filter(Article.state==1,Article.id < self.id). \
            order_by(Article.timestamp.desc()).first()
        return a

    @property
    def next(self):
        a = self.query.filter(Article.state==1, Article.id > self.id). \
            order_by(Article.timestamp.asc()).first()
        return a

    @property
    def tag_names(self):
        tags = []
        for tag in self.tags:
            tags.append(tag.name)
        return ', '.join(tags)

    @property
    def thread_key(self): # 用于评论插件
        return hashlib.new(name='md5', string=str(self.id)).hexdigest()

    @property
    def show_h_content(self) -> str:
        if current_user.is_authenticated and current_user.role == self.h_role:
            return self.h_content
        else:
            # url = url_for('main.profile')
            url = url_for('main.login') + '?next=' + request.path
            repl = '''
            <p class="border border-warning p-2 text-center">
                本文隐藏内容 <a href="{}">登陆</a> 后才可以浏览
            </p>
            '''.format(url)
            return repl

    def __repr__(self):
        return '<Title %r>' % self.title


class Comment(db.Model):
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, default=0)
    user = db.relationship('User',backref=db.backref('comments',lazy='dynamic'), lazy=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False, default=0, comment='关联的文章id')
    article = db.relationship('Article',backref=db.backref('comments',lazy='dynamic',order_by=id.desc()), lazy=True)
    content = db.Column(db.String(1024))
    reply_id = db.Column(db.Integer, db.ForeignKey('comment.id'), default=None, comment='回复对应的评论id')
    replies = db.relationship('Comment', back_populates='comment')
    comment = db.relationship('Comment', back_populates='replies', remote_side=[id])
    timestamp = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return '<user_id: %r, article_id: %r,reply_id: %r, content: %r>' % (self.user_id,self.article_id,self.reply_id,self.content)


class Recommend(db.Model):
    __tablename__ = 'recommend'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    img = db.Column(db.String(200))
    url = db.Column(db.String(200))
    sn = db.Column(db.Integer, default=0)
    state = db.Column(db.Integer, default=1)
    timestamp = db.Column(db.DateTime, default=datetime.now)


class AccessLog(db.Model):
    __tablename__ = 'access_log'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(20))
    url = db.Column(db.String(120))
    timestamp = db.Column(db.DateTime, default=datetime.now)
    remark = db.Column(db.String(32))


class Picture(db.Model):
    __tablename__ = 'picture'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.now)
    url = db.Column(db.String(120))
    remark = db.Column(db.String(32))


class Setting(db.Model):
    __tablename__ = 'setting'
    id = db.Column(db.Integer, primary_key=True)
    skey = db.Column(db.String(64), index=True, unique=True)
    svalue = db.Column(db.String(800), default='')

