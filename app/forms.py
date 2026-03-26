from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, HiddenField, DateField, DateTimeLocalField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from app.models import User

CATEGORIES = [
    ('Housing', 'Housing'),
    ('Employment', 'Employment'),
    ('Immigration', 'Immigration'),
    ('Healthcare', 'Healthcare'),
    ('Legal', 'Legal'),
    ('Academics', 'Academics'),
    ('General', 'General'),
]


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('I am a', choices=[('customer', 'Student / Community Member'), ('agent', 'Immigration Agent / Advisor')], default='customer')
    submit = SubmitField('Create Account')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    body = TextAreaField('Body', validators=[DataRequired()])
    category = SelectField('Category', choices=CATEGORIES, validators=[DataRequired()])
    tags = StringField('Tags (comma-separated)', validators=[Optional(), Length(max=200)])
    is_anonymous = BooleanField('Post Anonymously')
    submit = SubmitField('Post')


class ReplyForm(FlaskForm):
    body = TextAreaField('Reply', validators=[DataRequired()])
    is_anonymous = BooleanField('Reply Anonymously')
    submit = SubmitField('Post Reply')


class MessageForm(FlaskForm):
    recipient_username = StringField('To', validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    body = TextAreaField('Message', validators=[DataRequired()])
    reference_post_id = HiddenField('Reference Post')
    submit = SubmitField('Send')

    def validate_recipient_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if not user:
            raise ValidationError('User not found.')


class ProfileEditForm(FlaskForm):
    full_name = StringField('Full Name', validators=[Optional(), Length(max=100)])
    bio = TextAreaField('Bio', validators=[Optional()])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    visa_type = StringField('Visa Type', validators=[Optional(), Length(max=20)])
    university = StringField('University', validators=[Optional(), Length(max=100)])
    student_status = SelectField('Student Status', choices=[
        ('', 'Not specified'),
        ('prospective', 'Prospective'),
        ('applied', 'Applied'),
        ('admitted', 'Admitted'),
        ('enrolled', 'Enrolled'),
        ('graduated', 'Graduated'),
    ], validators=[Optional()])
    specializations = StringField('Specializations (comma-separated)', validators=[Optional()])
    availability_status = SelectField('Availability', choices=[
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ], validators=[Optional()])
    submit = SubmitField('Save Changes')


class VerificationForm(FlaskForm):
    license_number = StringField('License Number', validators=[DataRequired(), Length(max=100)])
    issuing_authority = StringField('Issuing Authority', validators=[DataRequired(), Length(max=100)])
    expiry_date = DateField('Expiry Date', validators=[DataRequired()])
    document_url = StringField('Document URL', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Submit for Verification')


class ConsultationRequestForm(FlaskForm):
    topic = SelectField('Topic', choices=[
        ('Student Visa', 'Student Visa'),
        ('OPT/CPT', 'OPT/CPT'),
        ('Housing', 'Housing'),
        ('Employment', 'Employment'),
        ('Green Card', 'Green Card'),
        ('General Advice', 'General Advice'),
    ], validators=[DataRequired()])
    preferred_time = DateTimeLocalField('Preferred Time', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    message = TextAreaField('Message', validators=[Optional()])
    submit = SubmitField('Request Consultation')
