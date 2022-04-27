from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField(label='Remember me!', default=False)
    submit = SubmitField('Login')


class RegistForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(1, 16, message='Please enter VALID Username.')])
    email = StringField('Email', validators=[DataRequired(), Length(6, 64, message='Please enter VALID Email'),
                                             Email(message='Not Valid!')])
    password = PasswordField('Password',
                             validators=[DataRequired(), EqualTo('password2', message="Can't confirm password!")])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('SUBMIT')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username Duplicated!')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email Duplicated!')


class PasswordForm(FlaskForm):
    pwd = PasswordField('Your Password', validators=[DataRequired()])
    password = PasswordField('pwd', validators=[DataRequired(), EqualTo('password2', message="Can't confirm password!")])
    password2 = PasswordField('confirm pwd', validators=[DataRequired()])
    submit = SubmitField('SUBMIT')

    def validate_pwd(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError('Invalid password!')


class ProfileForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(1, 16, message='Please enter VALID Username.')])
    email = StringField('Email', validators=[DataRequired(), Length(6, 64, message='Please enter VALID Email'),
                                             Email(message='Not Valid!')])
    submit = SubmitField('SUBMIT')


class SearchForm(FlaskForm):
    search = StringField('search', validators=[DataRequired(), Length(1, 64, message='Invalid Search content')])


class CommentForm(FlaskForm):
    article_id = IntegerField('Article', validators=[DataRequired()])
    reply_id = IntegerField('Reply', default=0)
    content = StringField('Comment', validators=[DataRequired()])
