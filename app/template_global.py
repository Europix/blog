from typing import Any, List
from flask import Flask
from flask_login import current_user
from flask import url_for, request
from app.models import Article, Tag, Category
import re


def register_template_filter(app):
    @app.template_filter('hidden_content')
    def hidden_content(content):
        if current_user.is_authenticated:
            return content.replace('[h3_hidden]', '').replace('[/h3_hidden]', '')
        else:
            login_url = url_for('main.login') + '?next=' + request.path
            repl = '''
            <p class="border border-warning p-2 text-center">
            Contents require <a href="{}">Login</a> To View.
            </p>
            '''.format(login_url)
            return re.sub('\[h3_hidden\].*?\[/h3_hidden\]', repl, content, flags=re.DOTALL)


def register_template_global(app: Flask):
    @app.template_global()
    def get_articles(
            categorys: str = None,
            tags: str = None,
            is_hot: bool = False,
            hot_num: int = 0,
            orderby: str = '',
            is_page: bool = False,
            page: int = 1,
            per_page: int = 10
    ) -> Any:

        query = Article.query.filter(Article.state == 1)
        if categorys and len(categorys) > 0:
            query = query.filter(Article.category.has(Category.name.in_(categorys.split(','))))
        if tags and len(tags) > 0:
            query = query.filter(Article.tags.any(Tag.name.in_(tags.split(','))))
        if is_hot:
            query = query.filter(Article.vc >= hot_num)
            query = query.order_by(Article.vc.desc())
        if orderby.lower() == 'asc':
            query = query.order_by(Article.timestamp.asc())
        elif orderby.lower() == 'desc':
            query = query.order_by(Article.timestamp.desc())
        else:
            query = query.order_by(Article.timestamp.desc())
        if is_page:
            if type(page) != int:
                try:
                    page = int(page)
                except:
                    page = 1
            results = query.paginate(page, per_page=per_page, error_out=False)
        else:
            results = query.all()
        return results

    @app.template_global()
    def get_categorys(names: str = None, visible=None) -> List[Category]:
        query = Category.query
        if names and len(names) > 0:
            query = query.filter(Category.name.in_(names.split(',')))
        if visible:
            query = query.filter(Category.visible == visible)
        query = query.order_by(Category.sn.asc())
        return query.all()

    @app.template_global()
    def get_tags(tags: str = None) -> List[Tag]:
        query = Tag.query.filter(Tag.visible == True)
        if tags and len(tags) > 0:
            query = query.filter(Tag.name.in_(tags.split(',')))
        return query.all()
