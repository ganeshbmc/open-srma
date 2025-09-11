from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField, BooleanField, SelectField
from wtforms.validators import DataRequired

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
    submit = SubmitField('Save Field')


class OutcomeForm(FlaskForm):
    name = StringField('Outcome Name', validators=[DataRequired()])
    outcome_type = SelectField(
        'Outcome Type',
        choices=[('dichotomous', 'Dichotomous'), ('continuous', 'Continuous')],
        validators=[DataRequired()],
    )
    submit = SubmitField('Add Outcome')
