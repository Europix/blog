from flask import render_template, redirect, request,\
    url_for, g, abort, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import os
from . import main
from app.models import Article, Tag, Category, Recommend, User, Comment
from .forms import SearchForm, LoginForm, RegistForm, PasswordForm, CommentForm, ProfileForm
from ..import db, sitemap


def build_template_path(tpl: str) -> str:
    return '{}/{}'.format(os.getenv('Europix_TEMPLATE', 'tend'), tpl)


@main.before_request
def before_request():
    if request.endpoint == 'main.static':
        return
    g.search_form = SearchForm(prefix='search')


@main.route('/', methods=['GET'])
def index():
    page = request.args.get('page', 1, type=int)
    articles = Article.query.filter_by(state=1). \
        order_by(Article.timestamp.desc()). \
        paginate(page, per_page=10, error_out=False)

    recommends = Recommend.query.filter(Recommend.state == 1).order_by(Recommend.sn.desc()).all()
    return render_template(build_template_path('index.html'), articles=articles, recommends=recommends)


@main.route('/favicon.ico')
def favicon():
    return main.send_static_file('img/favicon.ico')


@main.route('/hot/', methods=['GET'])
def hot():
    page = request.args.get('page', 1, type=int)
    articles = Article.query.filter_by(state=1). \
        order_by(Article.vc.desc()). \
        paginate(page, per_page=15, error_out=False)
    recommends = Recommend.query.filter(Recommend.state == 1).order_by(Recommend.sn.desc()).all()
    return render_template(build_template_path('index.html'), articles=articles, recommends=recommends)


@main.route('/article/<name>/', methods=['GET', 'POST'])
def article(name):
    article = Article.query.filter_by(name=name).first()
    if article is None:
        abort(404)
    article.vc = article.vc + 1
    db.session.commit()
    category = article.category
    tpl_name = category.tpl_page
    return render_template(build_template_path(tpl_name), article=article)


@main.route('/tags/')
def tags():
    tags = Tag.query.all()
    return render_template(build_template_path('tags.html'),tags = tags)


@main.route('/tag/<t>/', methods=['GET'])
def tag(t):
    page = request.args.get('page', 1, type=int)
    tag = Tag.query.filter(Tag.code == t).first()
    articles = tag.articles.filter(Article.state == 1).\
        order_by(Article.timestamp.desc()). \
        paginate(page, 25, error_out=False)
    return render_template(build_template_path('tag.html'), articles=articles, tag=tag, orderby='time')


@main.route('/tag/<t>/hot/', methods=['GET'])
def tag_hot(t):
    page = request.args.get('page', 1, type=int)
    tag = Tag.query.filter(Tag.code == t).first()
    articles = tag.articles.filter(Article.state == 1).\
        order_by(Article.vc.desc()). \
        paginate(page, per_page=25, error_out=False)
    return render_template(build_template_path('tag.html'), articles=articles, tag=tag, orderby='hot')


@main.route('/category/<c>/hot/', methods=['GET', 'POST'])
def category_hot(c):
    cty = Category.query.filter_by(name=c).first()
    tpl_name = cty.tpl_list
    if cty.tpl_mold == 'single_page':
        tpl_name = cty.tpl_mold
    return render_template(build_template_path(tpl_name), category=cty, orderby='hot')


@main.route('/comment/add/', methods=['GET', 'POST'])
@login_required
def comment_add():
    form = CommentForm()
    ret = {}
    ret['code'] = 0
    if form.validate_on_submit():
        c = Comment()
        form.populate_obj(c)
        c.user_id = current_user.id
        a = Article.query.filter(Article.id == c.article_id).first()
        a.comment_num = a.comments.count()
        if c.reply_id == 0:
            c.reply_id = None
        db.session.add(c)
        db.session.commit()
        ret['code'] = 1
        ret['id'] = c.id

    return jsonify(ret)


@main.route('/archive/', methods=['GET'])
def archive():
    articles = Article.query.filter_by(state=1).order_by(Article.timestamp.desc()).all()
    time_tag = []
    current_tag = ''
    for a in articles:
        a_t = a.timestamp.strftime('%Y-%m')
        if  a_t != current_tag:
            tag = dict()
            tag['name'] = a_t
            tag['articles'] = []
            time_tag.append(tag)
            current_tag = a_t
        tag = time_tag[-1]
        tag['articles'].append(a)
    return render_template(build_template_path('archives.html'),time_tag = time_tag)


@main.route('/search/', methods=['POST'])
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('.index'))
    return redirect(url_for('.search_results', query=g.search_form.search.data.strip()))


@main.route('/search_results/<query>', methods=['GET', 'POST'])
def search_results(query):
    page = request.args.get('page', 1, type=int)
    articles = Article.query.filter(Article.content_html.like('%%%s%%' % query), Article.state == 1).order_by(
        Article.timestamp.desc()). \
        paginate(page, per_page=25, error_out=False)
    return render_template(build_template_path('search_result.html'), articles=articles, query=query)


@sitemap.register_generator
def sitemap():
    articles = Article.query.filter(Article.state == 1).all()
    categories = Category.query.all()
    tags = Tag.query.all()
    import datetime
    now = datetime.datetime.now()
    yield 'main.index', {}, now.strftime('%Y-%m-%dT%H:%M:%S'), 'always', 1.0
    yield 'main.about', {}, now.strftime('%Y-%m-%dT%H:%M:%S'), 'always', 0.5
    for category in categories:
        yield 'main.category', {'c': category.name}, now.strftime('%Y-%m-%dT%H:%M:%S'), 'always', 0.9
    for categories in categories:
        yield 'main.category_hot', {'c': category.name}, now.strftime('%Y-%m-%dT%H:%M:%S'), 'always', 0.9
    yield 'main.tags', {}, now.strftime('%Y-%m-%dT%H:%M:%S'), 'always', 0.9
    for t in tags:
        yield 'main.tag', {'t': t.code}, now.strftime('%Y-%m-%dT%H:%M:%S'), 'always', 0.9
    for t in tags:
        yield 'main.tag_hot', {'t': t.code}, now.strftime('%Y-%m-%dT%H:%M:%S'), 'always', 0.9
    for a in articles:
        yield 'main.article', {'name': a.name}


@main.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(prefix='login')
    if login_form.validate_on_submit():
        u = User.query.filter_by(username=login_form.username.data.strip()).first()
        if u is None:
            flash({'error': 'Account Not Signed Up!'})
        elif u is not None and u.verify_password(login_form.password.data.strip()) and u.status:
            login_user(user=u, remember=login_form.remember_me.data)
            flash({'success': 'Login Success'.format(u.username)})
            return redirect(request.args.get('next', url_for('main.index')))
        elif not u.status:
            flash({'error': 'Unknown error!'})
        elif not u.verify_password(login_form.password.data.strip()):
            flash({'error': 'Incorrect password'})

    return render_template(build_template_path('login.html'), form=login_form)


@main.route('/regist', methods=['GET', 'POST'])
def regist():
    form = RegistForm(prefix='regist')
    if form.validate_on_submit(): 
        u = User(username=form.username.data.strip(), email=form.email.data.strip(), password=form.password.data.strip()
                 , status=True, role=False)
        db.session.add(u)
        db.session.commit()
        login_user(user=u)
        flash({'success': 'Welcome, This website uses cookies.'.format(u.username)})
        return redirect(request.args.get('next', url_for('main.index')))
    return render_template(build_template_path('regist.html'), form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@main.route('/profile/', methods=['GET'])
@login_required
def profile():
    return render_template(build_template_path('profile.html'))


@main.route('/password', methods=['GET', 'POST'])
def password():
    form = PasswordForm()
    if not form.validate_on_submit():
        return render_template(build_template_path('password.html'), form=form)
    if current_user.verify_password(form.pwd.data):
        current_user.password = form.password.data
        db.session.commit()
    flash({'success': 'Success'})
    return redirect(url_for('.profile'))


@main.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data.strip()
        current_user.email = form.email.data.strip()
        db.session.commit()
        flash({'success': 'Success'})
        return redirect(url_for('.profile'))
    return render_template(build_template_path('edit_profile.html'), form=form)
