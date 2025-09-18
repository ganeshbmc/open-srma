import re

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField, BooleanField, SelectField, HiddenField
from wtforms.fields import EmailField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Regexp, ValidationError

from app import db
from app.models import User

class ProjectForm(FlaskForm):
    name = StringField(
        'Project Name',
        filters=[lambda x: x.strip() if isinstance(x, str) else x],
        validators=[DataRequired(message='Project name is required.'), Length(max=120, message='Project name must be 120 characters or fewer.')],
    )
    description = TextAreaField('Description', filters=[lambda x: x.strip() if isinstance(x, str) else x])
    submit = SubmitField('Create Project')

class StudyForm(FlaskForm):
    title = StringField('Title', filters=[lambda x: x.strip() if isinstance(x, str) else x], validators=[DataRequired(message='Title is required.'), Length(max=300, message='Title must be 300 characters or fewer.')])
    author = StringField('Author', filters=[lambda x: x.strip() if isinstance(x, str) else x], validators=[DataRequired(message='Author is required.'), Length(max=120, message='Author must be 120 characters or fewer.')])
    year = IntegerField('Year', validators=[DataRequired(message='Publication year is required.'), NumberRange(min=1800, max=2100, message='Enter a valid publication year.')])
    submit = SubmitField('Add Study')


class CustomFormFieldForm(FlaskForm):
    section = StringField('Section', filters=[lambda x: x.strip() if isinstance(x, str) else x], validators=[DataRequired(message='Section name is required.'), Length(max=100, message='Section name must be 100 characters or fewer.')])
    label = StringField('Label', filters=[lambda x: x.strip() if isinstance(x, str) else x], validators=[DataRequired(message='Field label is required.'), Length(max=200, message='Field label must be 200 characters or fewer.')])
    help_text = TextAreaField('Help text (tooltip)', description='Optional help shown as a tooltip next to the label', filters=[lambda x: x.strip() if isinstance(x, str) else x])
    field_type = SelectField(
        'Field Type',
        choices=[
            ('text', 'Text'),
            ('textarea', 'Text Area'),
            ('integer', 'Integer'),
            ('date', 'Date'),
            ('dichotomous_outcome', 'Dichotomous Outcome'),
            ('baseline_continuous', 'Baseline: Continuous (mean/sd by group)'),
            ('baseline_categorical', 'Baseline: Categorical (% by group)'),
        ],
        validators=[DataRequired()],
    )
    required = BooleanField('Required')
    change_reason = TextAreaField('Reason for request (optional)', description='Shown to project owners when approving member proposals')
    submit = SubmitField('Save Field')


class OutcomeForm(FlaskForm):
    name = StringField('Outcome Name', filters=[lambda x: x.strip() if isinstance(x, str) else x], validators=[DataRequired(message='Outcome name is required.'), Length(max=200, message='Outcome name must be 200 characters or fewer.')])
    outcome_type = SelectField(
        'Outcome Type',
        choices=[('dichotomous', 'Dichotomous'), ('continuous', 'Continuous')],
        validators=[DataRequired()],
    )
    reason = TextAreaField('Reason for request (optional)')
    submit = SubmitField('Add Outcome')


class RegisterForm(FlaskForm):
    name = StringField(
        'Name',
        filters=[lambda x: x.strip() if isinstance(x, str) else x],
        validators=[
            DataRequired(message='Please provide your name.'),
            Length(max=120, message='Name must be 120 characters or fewer.'),
            Regexp(r"^[A-Za-z0-9 ,.'-]+$", message="Name contains invalid characters."),
        ],
    )
    email = EmailField(
        'Email',
        filters=[
            lambda x: x.strip() if isinstance(x, str) else x,
            lambda x: x.lower() if isinstance(x, str) else x,
        ],
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Enter a valid email address.'),
            Length(max=255, message='Email must be 255 characters or fewer.'),
        ],
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(min=8, max=128, message='Password must be between 8 and 128 characters.'),
        ],
    )
    confirm = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.'),
        ],
    )
    submit = SubmitField('Register')

    def validate_email(self, field):
        if field.data:
            exists = User.query.filter(db.func.lower(User.email) == field.data.lower()).first()
            if exists:
                raise ValidationError('This email is already registered.')

    def validate_password(self, field):
        password = field.data or ''
        if password.strip() != password:
            raise ValidationError('Password cannot start or end with spaces.')
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError('Password must include at least one letter.')
        if not re.search(r'[0-9]', password):
            raise ValidationError('Password must include at least one number.')


class LoginForm(FlaskForm):
    email = EmailField(
        'Email',
        filters=[
            lambda x: x.strip() if isinstance(x, str) else x,
            lambda x: x.lower() if isinstance(x, str) else x,
        ],
        validators=[DataRequired(message='Email is required.'), Email(message='Enter a valid email address.')],
    )
    password = PasswordField('Password', validators=[DataRequired(message='Password is required.')])
    submit = SubmitField('Login')


class AddMemberForm(FlaskForm):
    email = StringField('Member Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('member', 'Member'), ('owner', 'Owner')], validators=[DataRequired()])
    submit = SubmitField('Add Member')


class ForgotPasswordForm(FlaskForm):
    email = EmailField(
        'Email',
        filters=[
            lambda x: x.strip() if isinstance(x, str) else x,
            lambda x: x.lower() if isinstance(x, str) else x,
        ],
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Enter a valid email address.'),
            Length(max=255, message='Email must be 255 characters or fewer.'),
        ],
    )
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    token = HiddenField('Token')
    password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(min=8, max=128, message='Password must be between 8 and 128 characters.'),
        ],
    )
    confirm = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.'),
        ],
    )
    submit = SubmitField('Reset Password')

    def validate_password(self, field):
        password = field.data or ''
        if password.strip() != password:
            raise ValidationError('Password cannot start or end with spaces.')
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError('Password must include at least one letter.')
        if not re.search(r'[0-9]', password):
            raise ValidationError('Password must include at least one number.')
