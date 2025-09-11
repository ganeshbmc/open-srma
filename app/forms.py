from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField, BooleanField, SelectField
from wtforms.validators import DataRequired
from wtforms.validators import Email, EqualTo, Length

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Create Project')

class StudyForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired()])
    submit = SubmitField('Add Study')


class CustomFormFieldForm(FlaskForm):
    section = StringField('Section', validators=[DataRequired()])
    label = StringField('Label', validators=[DataRequired()])
    help_text = TextAreaField('Help text (tooltip)', description='Optional help shown as a tooltip next to the label')
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
    name = StringField('Outcome Name', validators=[DataRequired()])
    outcome_type = SelectField(
        'Outcome Type',
        choices=[('dichotomous', 'Dichotomous'), ('continuous', 'Continuous')],
        validators=[DataRequired()],
    )
    reason = TextAreaField('Reason for request (optional)')
    submit = SubmitField('Add Outcome')


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    password = StringField('Password', validators=[DataRequired(), Length(min=6, max=128)])
    confirm = StringField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class AddMemberForm(FlaskForm):
    email = StringField('Member Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('member', 'Member'), ('owner', 'Owner')], validators=[DataRequired()])
    submit = SubmitField('Add Member')
