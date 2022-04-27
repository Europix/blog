from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField, BooleanField, SubmitField, SelectField, TextAreaField, \
    DateTimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from wtforms import ValidationError
from ..models import User, Category
from datetime import datetime


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField(label='Remember me', default=False)
    submit = SubmitField('SUBMIT')


class AddAdminForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 64, message='Invalid Username')])
    email = StringField('Email', validators=[DataRequired(), Length(6, 64, message='Invalid E-mail'),
                                             Email(message='Invalid E-mail')])
    password = PasswordField('New Password', validators=[DataRequired(), EqualTo('password2', message='Check your confi'
                                                                                                      'rm password!')])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username Duplicated!')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('E-mail Duplicated!')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Your Password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[DataRequired(), EqualTo('password2', message='Check your confi'
                                                                                                      'rm password!')])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 64, message='Invalid Username')])
    email = StringField('Email', validators=[DataRequired(), Length(6, 64, message='Invalid E-mail'),
                                             Email(message='Invalid E-mail')])
    role = SelectField('Priority', choices=[('1', 'Admin'), ('0', 'User')])
    status = SelectField('Status', choices=[('True', 'Normal'), ('False', 'Eliminated')])
    submit = SubmitField('Edit')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username Duplicated!')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('E-mail Duplicated!')


class DeleteUserForm(FlaskForm):
    user_id = StringField(validators=[DataRequired()])


class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 64, message='Invalid Username')])
    email = StringField('Email', validators=[DataRequired(), Length(6, 64, message='Invalid E-mail'),
                                             Email(message='Invalid E-mail')])
    role = SelectField('Priority', choices=[('1', 'Admin'), ('0', 'User')])
    status = SelectField('Status', choices=[('True', 'Normal'), ('False', 'Eliminated')])
    submit = SubmitField('Edit')


class ArticleForm(FlaskForm):
    id = HiddenField('id')
    title = StringField('Title', validators=[DataRequired('Invalid Title')])
    name = StringField('name', render_kw={'placeholder': 'Custom URL'})
    content = TextAreaField('Article content HERE')
    content_html = TextAreaField('Article content HERE')
    editor = HiddenField('Editor', default='')
    category_id = SelectField('Category', coerce=int, default=1, validators=[DataRequired('Please select category')])
    tags = StringField('Tags', render_kw={'data-role': 'tagsinput'})
    state = HiddenField('Status', default=0)
    thumbnail = HiddenField('Image', default='main/static/img/avatar.jpg')
    summary = TextAreaField('Summary', validators=[Length(0, 300, message='Invalid Summary')])
    timestamp = DateTimeField('PostTime', default=datetime.now)
    save = SubmitField('Save')
    h_content = TextAreaField('qwq', default='')
    h_role = SelectField('Visible', default='0', choices=[('1', 'Admin'), ('0', 'User')])

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(category.id, category.title)
                                    for category in Category.query.filter(Category.tpl_mold == 'list').
                                        order_by(Category.title).all()]


class DeleteArticleForm(FlaskForm):
    article_id = StringField(validators=[DataRequired()])


class TagForm(FlaskForm):
    id = HiddenField('id')
    name = StringField('name', validators=[DataRequired()])
    visible = BooleanField('show', default=True)
    submit = SubmitField('SUBMIT')


class AddFolderForm(FlaskForm):
    directory = StringField('directory')
    submit = SubmitField('SUBMIT')
