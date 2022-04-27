from flask import render_template, request, redirect, url_for, flash, current_app, jsonify, \
    send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from app import util
from . import admin
from app.ext import db
from .forms import AddAdminForm, LoginForm, AddUserForm, DeleteUserForm, EditUserForm, ArticleForm, \
        ChangePasswordForm, TagForm, DeleteArticleForm
from app.models import User, Category, Tag, Article, Picture
from app.util import admin_required, isAjax


@admin.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def index():
    return render_template('admin/index.html')


@admin.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(prefix='login')
    user = User.query.filter_by(status=True).first()
    if not user:
        # If the user isn't exist
        add_admin_form = AddAdminForm(prefix='add_admin')
        if request.method == 'POST' and add_admin_form.validate_on_submit():
            u = User(username=add_admin_form.username.data.strip(),
                     email=add_admin_form.email.data.strip(),
                     password=add_admin_form.password.data.strip(),
                     status=True, role=1
                     )
            db.session.add(u)
            db.session.commit()
            login_user(user=u)
            return redirect(url_for('admin.index'))

        return render_template('admin/add_admin.html', addAdminForm=add_admin_form)
    else:
        if request.method == 'POST' and login_form.validate_on_submit():
            u = User.query.filter_by(username=login_form.username.data.strip()).first()
            if u is None:
                flash({'error': 'Not Registered'})
            elif u is not None and u.verify_password(login_form.password.data.strip()) and u.status:
                login_user(user=u, remember=login_form.remember_me.data)
                return redirect(url_for('admin.index'))
            elif not u.status:
                flash({'error': 'User have been eliminated'})
            elif not u.verify_password(login_form.password.data.strip()):
                flash({'error': 'Invalid Password'})

    return render_template('admin/login.html', loginForm=login_form)


@admin.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
    # Logout


@admin.route('/articles', methods=['GET', 'POST'])
@login_required
@admin_required
def articles():
    title = request.args.get('title', '')
    page = request.args.get('page', 1, type=int)
    delete_article = DeleteArticleForm(prefix='delete_article')
    if delete_article.validate_on_submit():
        u = Article.query.get_or_404(int(delete_article.article_id.data.strip()))
        db.session.delete(u)
        flash({'success': 'Delete Article Success！'})
    articles = Article.query.filter(
        Article.title.like("%" + title + "%") if title is not None else ''
        ).order_by(Article.timestamp.desc()).paginate(page, per_page=25, error_out=False)

    return render_template('admin/articles.html', articles=articles, title=title,deleteForm=delete_article)


@admin.route('/article/edit/<id>', methods=['GET'])
@login_required
@admin_required
def article_edit(id):
    article = Article.query.get(int(id))
    form = ArticleForm(obj=article)
    editor = request.args.get('editor', article.editor)
    form.editor.data = editor
    form.tags.data = ','.join([t.name for t in article.tags.all()])
    return render_template('admin/write.html', form=form)


@admin.route('/article/delete/<id>', methods=['GET'])
@login_required
@admin_required
def article_delete(id):
    article = Article.query.get(id)
    db.session.delete(article)
    db.session.commit()
    flash({'success': 'Delete Article Success！'})
    title = request.args.get('title', '')
    page = request.args.get('page', 1, type=int)
    articles = Article.query.filter(
        Article.title.like("%" + title + "%") if title is not None else ''
    ).order_by(Article.timestamp.desc()).paginate(page, per_page=25, error_out=False)

    return redirect(url_for(articles))


@admin.route('/article/write', methods=['GET', 'POST'])
@login_required
@admin_required
def write():
    # Write Article form
    form = ArticleForm()
    if request.method == 'POST' and form.validate_on_submit():
        cty = Category.query.get(int(form.category_id.data))
        a = None
        if form.id.data:
            a = Article.query.get(int(form.id.data))
        if a:
            a.title = form.title.data.strip()
            a.editor = form.editor.data
            a.content = form.content.data
            a.content_html = a.content_to_html() if a.editor == 'markdown' else form.content_html.data
            a.summary = form.summary.data
            a.thumbnail = form.thumbnail.data
            a.category = cty
            a.name = form.name.data.strip()
            a.state = form.state.data
            a.timestamp = form.timestamp.data
            a.h_role = form.h_role.data
            a.h_content = form.h_content.data
            if not a.name and len(a.name) == 0:
                a.name = a.id
            db.session.commit()
        else:
            a = Article(title=form.title.data.strip(), content=form.content.data, editor=form.editor.data,
                        thumbnail=form.thumbnail.data, name=form.name.data.strip(),
                        state=form.state.data, summary=form.summary.data,
                        category=cty, author=current_user._get_current_object())
            a.content_html = a.content_to_html() if a.editor == 'markdown' else form.content_html.data
            db.session.add(a)
            db.session.commit()
            if not a.name and len(a.name) == 0:
                a.name = a.id
                db.session.commit()
        a.tags = []
        for tg in form.tags.data.split(','):
            if tg.strip() == '':
                continue
            t = Tag.add(tg)
            if t not in a.tags:
                a.tags.append(t)
        if isAjax():
            msg = 'Success'
            return jsonify({'code': 1, 'msg': msg, 'id': a.id})
    
    editor = 'markdown'
    form.editor.data = editor
    return render_template('admin/write.html', form=form)


@admin.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    add_user_form = AddUserForm(prefix='add_user')
    delete_user_form = DeleteUserForm(prefix='delete_user')
    if request.method == 'POST' and add_user_form.validate_on_submit():
        if add_user_form.status.data == 'True':
            status = True
        else:
            status = False
        u = User(username=add_user_form.username.data.strip(), email=add_user_form.email.data.strip(),
                 role=add_user_form.role.data, status=status, password='123456')
        db.session.add(u)
        flash({'success': 'Add <%s> Success！' % add_user_form.username.data.strip()})
    if delete_user_form.validate_on_submit():
        u = User.query.get_or_404(int(delete_user_form.user_id.data.strip()))
        db.session.delete(u)
        flash({'success': 'Delete <%s> Success！' % u.username})

    users = User.query.all()

    return render_template('admin/users.html', users=users, addUserForm=add_user_form,
                           deleteUserForm=delete_user_form)


@admin.route('/user-edit/<user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(user_id):
    user = User.query.get_or_404(user_id)
    edit_user_form = EditUserForm(prefix='edit_user', obj=user)
    if edit_user_form.validate_on_submit():
        user.username = edit_user_form.username.data.strip()
        user.email = edit_user_form.email.data.strip()
        user.role = edit_user_form.role.data
        if edit_user_form.status.data == 'True':
            user.status = True
        else:
            user.status = False
        flash({'success': 'Edit success!'})

    return render_template('admin/edit_user.html', editUserForm=edit_user_form, user=user)


@admin.route('/password', methods=['GET', 'POST'])
@login_required
@admin_required
def password():
    change_password_form = ChangePasswordForm(prefix='change_password')
    if request.method == 'POST' and change_password_form.validate_on_submit():
        if current_user.verify_password(change_password_form.old_password.data.strip()):
            current_user.password = change_password_form.password.data.strip()
            # db.session.add(current_user)
            db.session.commit()
            flash({'success': 'Edit Success!'})
        else:
            flash({'error': 'Invalid Password'})

    return render_template('admin/password.html', changePasswordForm=change_password_form)


@admin.route('/tags')
@login_required
@admin_required
def tags():
    name = request.values.get('name', '')
    page = request.args.get('page', 1, type=int)
    tags = Tag.query.filter(
        Tag.name.like("%" + name + "%") if name is not None else ''
        ).order_by(Tag.id.asc()). \
        paginate(page, per_page=25, error_out=False)
    return   render_template('admin/tags.html',tags=tags, name = name)


@admin.route('/tags/add', methods=['GET', 'POST'])
@login_required
@admin_required
def tag_add():
    form = TagForm()
    if request.method == 'POST' and form.validate_on_submit():
        Tag.add(form.name.data.strip())
        return redirect(url_for('admin.tags'))

    return render_template('admin/tag.html', form=form)


@admin.route('/tags/edit', methods=['GET','POST'])
@login_required
@admin_required
def tag_edit():
    id = request.values.get('id', 0, type=int)
    c = Tag.query.get(id)
    form = TagForm()
    if request.method == 'POST' and form.validate_on_submit():
        form.populate_obj(c)
        db.session.commit()
        return redirect(url_for('admin.tags'))

    form = TagForm(obj=c)
    return render_template('admin/tag.html',form=form)


@admin.route('/categorys', methods=['GET'])
@login_required
@admin_required
def categorys():
    page = request.args.get('page', 1, type=int)
    categorys = Category.query.order_by(Category.visible.desc(), Category.sn.asc()).paginate(page, per_page=25, error_out=False)
    return render_template('admin/categorys.html', categorys=categorys)


@admin.route('/uploads/<path:filename>')
def get_image(filename):
    return send_from_directory(current_app.config['Europix_UPLOAD_PATH'], filename)


@admin.route('/imagehosting')
@login_required
@admin_required
def image_hosting():
    page = request.args.get('page', 1, type=int)
    imgs = Picture.query.order_by(Picture.id.desc()). \
        paginate(page, per_page=20, error_out=False)


@admin.route('/import_article', methods=['POST'])
def import_article():
    from readability import Document
    url = request.form.get('url')
    download_img = request.form.get('download_img', 0, type=int)
    is_download_img = True if download_img == 1 else False
    req_html = request.form.get('html')
    if req_html and 0 < len(req_html) <= 1024:
        html = req_html
    else:
        html = util.open_url(url)
        html = util.strdecode(html)
        
        doc = Document(html)
        html = doc.summary()
    markdown = util.html2markdown(html, url, is_download_img, '')
    return jsonify(markdown)
