from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import ProjectForm, StudyForm
from app.models import Project, Study, CustomFormField, StudyDataValue, StudyNumericalOutcome # Import new models
from app.utils import load_template_and_create_form_fields # Import the new utility function
import json # Import json for handling dichotomous_outcome

@app.route('/')
def index():
    projects = Project.query.all()
    return render_template('index.html', projects=projects)

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(name=form.name.data, description=form.description.data)
        db.session.add(project)
        db.session.commit()
        flash('Project created successfully! Now, set up your data extraction form.')
        return redirect(url_for('setup_form', project_id=project.id))
    return render_template('add_project.html', form=form)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    studies = project.studies.all()
    return render_template('project_detail.html', project=project, studies=studies)

@app.route('/project/<int:project_id>/add_study', methods=['GET', 'POST'])
def add_study(project_id):
    project = Project.query.get_or_404(project_id)
    form = StudyForm()
    if form.validate_on_submit():
        study = Study(title=form.title.data, author=form.author.data, year=form.year.data, project=project)
        db.session.add(study)
        db.session.commit()
        flash('Study added successfully!')
        return redirect(url_for('project_detail', project_id=project.id))
    return render_template('add_study.html', form=form, project=project)

@app.route('/project/<int:project_id>/setup_form', methods=['GET', 'POST'])
def setup_form(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        template_id = request.form.get('template_id')
        if template_id == 'rct_v1': # Only RCT template is supported for now
            load_template_and_create_form_fields(project.id, template_id)
            flash('Data extraction form generated from RCT template!')
            return redirect(url_for('project_detail', project_id=project.id))
        else:
            flash('Invalid template selected or template not yet supported.', 'error')
    return render_template('setup_form.html', project=project)

@app.route('/project/<int:project_id>/study/<int:study_id>/enter_data', methods=['GET', 'POST'])
def enter_data(project_id, study_id):
    project = Project.query.get_or_404(project_id)
    study = Study.query.get_or_404(study_id)
    
    # Get custom form fields for this project
    form_fields = CustomFormField.query.filter_by(project_id=project.id).order_by(CustomFormField.section).all()

    # Get existing data values for static fields for this study
    existing_data = {dv.form_field_id: dv.value for dv in study.data_values}

    # Get existing numerical outcome data for this study
    existing_numerical_outcomes_objects = study.numerical_outcomes.all()
    existing_numerical_outcomes = []
    for outcome_obj in existing_numerical_outcomes_objects:
        existing_numerical_outcomes.append({
            'outcome_name': outcome_obj.outcome_name,
            'events_intervention': outcome_obj.events_intervention,
            'total_intervention': outcome_obj.total_intervention,
            'events_control': outcome_obj.events_control,
            'total_control': outcome_obj.total_control
        })

    if request.method == 'POST':
        # Save static form fields
        for field in form_fields:
            field_name = f'field_{field.id}'
            if field.field_type == 'dichotomous_outcome':
                events_key = f'{field_name}_events'
                total_key = f'{field_name}_total'
                
                events = request.form.get(events_key, type=int)
                total = request.form.get(total_key, type=int)

                if events is not None and total is not None: 
                    value_data = {'events': events, 'total': total}
                    value_str = json.dumps(value_data)
                else:
                    value_str = None
            else:
                value_str = request.form.get(field_name)

            data_value = StudyDataValue.query.filter_by(study_id=study.id, form_field_id=field.id).first()
            if data_value:
                data_value.value = value_str
            else:
                data_value = StudyDataValue(study_id=study.id, form_field_id=field.id, value=value_str)
                db.session.add(data_value)
        
        # Save numerical outcomes
        # First, delete all existing numerical outcomes for this study to handle removals
        StudyNumericalOutcome.query.filter_by(study_id=study.id).delete()
        
        # Iterate through submitted numerical outcome data
        # We use outcome_row_index hidden fields to get all submitted row indices
        outcome_indices = set()
        for index_str in request.form.getlist('outcome_row_index'):
            try:
                index = int(index_str)
                outcome_indices.add(index)
            except ValueError:
                pass # Not a valid outcome index

        for index in sorted(list(outcome_indices)):
            outcome_name = request.form.get(f'outcome_name_{index}')
            events_intervention = request.form.get(f'events_intervention_{index}', type=int)
            total_intervention = request.form.get(f'total_intervention_{index}', type=int)
            events_control = request.form.get(f'events_control_{index}', type=int)
            total_control = request.form.get(f'total_control_{index}', type=int)

            if outcome_name: # Only save if outcome name is provided
                numerical_outcome = StudyNumericalOutcome(
                    study_id=study.id,
                    outcome_name=outcome_name,
                    events_intervention=events_intervention,
                    total_intervention=total_intervention,
                    events_control=events_control,
                    total_control=total_control
                )
                db.session.add(numerical_outcome)

        db.session.commit()
        flash('Study data saved successfully!')
        return redirect(url_for('project_detail', project_id=project.id))

    return render_template('enter_data.html', project=project, study=study, form_fields=form_fields, existing_data=existing_data, existing_numerical_outcomes=existing_numerical_outcomes)