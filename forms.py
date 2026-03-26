from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('I am a', choices=[
        ('customer', 'Customer (Student / Worker / Immigrant)'),
        ('agent', 'Agent (Support Staff)')
    ], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered. Please use a different email.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    category = SelectField('Category', choices=[
        ('General', 'General'),
        ('Housing', 'Housing'),
        ('Employment', 'Employment'),
        ('Education', 'Education'),
        ('Immigration', 'Immigration'),
        ('Healthcare', 'Healthcare'),
        ('Legal', 'Legal'),
        ('Other', 'Other'),
    ])
    body = TextAreaField('Description', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Post')


class ReplyForm(FlaskForm):
    body = TextAreaField('Your Reply', validators=[DataRequired(), Length(min=2)])
    submit = SubmitField('Submit Reply')


class MessageForm(FlaskForm):
    recipient = StringField('To (username)', validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    body = TextAreaField('Message', validators=[DataRequired(), Length(min=2)])
    submit = SubmitField('Send Message')

    def validate_recipient(self, field):
        if not User.query.filter_by(username=field.data).first():
            raise ValidationError('User not found. Please check the username.')
