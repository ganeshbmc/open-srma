import io # Import io for BytesIO
import zipfile # Import zipfile
from flask import render_template, flash, redirect, url_for, request, send_file, jsonify # Import send_file, jsonify
from app import app, db
from app.forms import ProjectForm, StudyForm, CustomFormFieldForm
from app.models import Project, Study, CustomFormField, StudyDataValue, StudyNumericalOutcome # Import new models
from app.utils import load_template_and_create_form_fields # Import the new utility function
import json # Import json for handling dichotomous_outcome
from pandas import DataFrame # Import pandas DataFrame

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


@app.route('/project/<int:project_id>/form_fields')
def list_form_fields(project_id):
    project = Project.query.get_or_404(project_id)
    fields = (
        CustomFormField.query
        .filter_by(project_id=project.id)
        .order_by(
            CustomFormField.section.asc(),
            db.func.coalesce(CustomFormField.sort_order, CustomFormField.id).asc(),
            CustomFormField.id.asc(),
        )
        .all()
    )
    return render_template('form_fields.html', project=project, fields=fields)


@app.route('/project/<int:project_id>/form_fields/add', methods=['GET', 'POST'])
def add_form_field(project_id):
    project = Project.query.get_or_404(project_id)
    form = CustomFormFieldForm()
    if form.validate_on_submit():
        # Determine next sort_order within this section
        max_order = (
            db.session.query(db.func.max(CustomFormField.sort_order))
            .filter_by(project_id=project.id, section=form.section.data.strip())
            .scalar()
        )
        next_order = (max_order + 1) if max_order is not None else 1
        field = CustomFormField(
            project_id=project.id,
            section=form.section.data.strip(),
            label=form.label.data.strip(),
            field_type=form.field_type.data,
            required=bool(form.required.data),
            help_text=form.help_text.data.strip() if form.help_text.data else None,
            sort_order=next_order,
        )
        db.session.add(field)
        db.session.commit()
        flash('Field added.')
        return redirect(url_for('list_form_fields', project_id=project.id))
    return render_template('edit_form_field.html', project=project, form=form, mode='add')


@app.route('/project/<int:project_id>/form_fields/<int:field_id>/edit', methods=['GET', 'POST'])
def edit_form_field(project_id, field_id):
    project = Project.query.get_or_404(project_id)
    field = CustomFormField.query.filter_by(project_id=project.id, id=field_id).first_or_404()
    form = CustomFormFieldForm(obj=field)
    if form.validate_on_submit():
        old_section = field.section
        field.section = form.section.data.strip()
        field.label = form.label.data.strip()
        field.field_type = form.field_type.data
        field.required = bool(form.required.data)
        field.help_text = form.help_text.data.strip() if form.help_text.data else None
        # If section changed, move to end of new section
        if field.section != old_section:
            max_order = (
                db.session.query(db.func.max(CustomFormField.sort_order))
                .filter_by(project_id=project.id, section=field.section)
                .scalar()
            )
            field.sort_order = (max_order + 1) if max_order is not None else 1
        db.session.commit()
        flash('Field updated.')
        return redirect(url_for('list_form_fields', project_id=project.id))
    return render_template('edit_form_field.html', project=project, form=form, mode='edit')


@app.route('/project/<int:project_id>/form_fields/<int:field_id>/delete', methods=['POST'])
def delete_form_field(project_id, field_id):
    project = Project.query.get_or_404(project_id)
    field = CustomFormField.query.filter_by(project_id=project.id, id=field_id).first_or_404()
    section = field.section
    db.session.delete(field)
    db.session.commit()
    _normalize_section_order(project.id, section)
    flash('Field deleted.')
    return redirect(url_for('list_form_fields', project_id=project.id))


def _normalize_section_order(project_id: int, section: str):
    """Ensure contiguous sort_order values within a section."""
    fields = (
        CustomFormField.query
        .filter_by(project_id=project_id, section=section)
        .order_by(
            db.func.coalesce(CustomFormField.sort_order, CustomFormField.id).asc(),
            CustomFormField.id.asc(),
        )
        .all()
    )
    for idx, f in enumerate(fields, start=1):
        f.sort_order = idx
    db.session.commit()


@app.route('/project/<int:project_id>/form_fields/<int:field_id>/move_up', methods=['POST'])
def move_form_field_up(project_id, field_id):
    project = Project.query.get_or_404(project_id)
    field = CustomFormField.query.filter_by(project_id=project.id, id=field_id).first_or_404()
    _normalize_section_order(project.id, field.section)
    prev_field = (
        CustomFormField.query
        .filter_by(project_id=project.id, section=field.section)
        .filter(CustomFormField.sort_order < field.sort_order)
        .order_by(CustomFormField.sort_order.desc())
        .first()
    )
    if prev_field:
        field.sort_order, prev_field.sort_order = prev_field.sort_order, field.sort_order
        db.session.commit()
    return redirect(url_for('list_form_fields', project_id=project.id))


@app.route('/project/<int:project_id>/form_fields/<int:field_id>/move_down', methods=['POST'])
def move_form_field_down(project_id, field_id):
    project = Project.query.get_or_404(project_id)
    field = CustomFormField.query.filter_by(project_id=project.id, id=field_id).first_or_404()
    _normalize_section_order(project.id, field.section)
    next_field = (
        CustomFormField.query
        .filter_by(project_id=project.id, section=field.section)
        .filter(CustomFormField.sort_order > field.sort_order)
        .order_by(CustomFormField.sort_order.asc())
        .first()
    )
    if next_field:
        field.sort_order, next_field.sort_order = next_field.sort_order, field.sort_order
        db.session.commit()
    return redirect(url_for('list_form_fields', project_id=project.id))

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
            try:
                load_template_and_create_form_fields(project.id, template_id)
                flash('Data extraction form generated from RCT template!')
                return redirect(url_for('project_detail', project_id=project.id))
            except Exception as e:
                flash(f'Failed to generate form: {e}', 'error')
                # fall through to re-render the setup page with error message
        else:
            flash('Invalid template selected or template not yet supported.', 'error')
    return render_template('setup_form.html', project=project)

@app.route('/project/<int:project_id>/study/<int:study_id>/enter_data', methods=['GET', 'POST'])
def enter_data(project_id, study_id):
    project = Project.query.get_or_404(project_id)
    study = Study.query.get_or_404(study_id)
    
    # Get custom form fields for this project, ordered by section and in-section order
    form_fields = (
        CustomFormField.query
        .filter_by(project_id=project.id)
        .order_by(
            CustomFormField.section.asc(),
            db.func.coalesce(CustomFormField.sort_order, CustomFormField.id).asc(),
            CustomFormField.id.asc(),
        )
        .all()
    )

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


@app.route('/project/<int:project_id>/study/<int:study_id>/autosave', methods=['POST'])
def autosave_study_data(project_id, study_id):
    project = Project.query.get_or_404(project_id)
    study = Study.query.get_or_404(study_id)

    data = request.get_json(silent=True) or {}
    section = data.get('section')
    if not section:
        return jsonify({'ok': False, 'error': 'Missing section'}), 400

    try:
        if section == 'numerical_outcomes':
            # Replace all numerical outcomes for this study with provided rows
            StudyNumericalOutcome.query.filter_by(study_id=study.id).delete()
            rows = data.get('numerical_outcomes') or []
            for row in rows:
                outcome_name = (row.get('outcome_name') or '').strip()
                if not outcome_name:
                    continue
                def to_int(v):
                    if v is None or v == '':
                        return None
                    try:
                        return int(v)
                    except (TypeError, ValueError):
                        return None
                numerical_outcome = StudyNumericalOutcome(
                    study_id=study.id,
                    outcome_name=outcome_name,
                    events_intervention=to_int(row.get('events_intervention')),
                    total_intervention=to_int(row.get('total_intervention')),
                    events_control=to_int(row.get('events_control')),
                    total_control=to_int(row.get('total_control')),
                )
                db.session.add(numerical_outcome)
            db.session.commit()
            return jsonify({'ok': True})

        # Otherwise handle a regular section of static form fields
        fields = data.get('fields') or []
        # Build a map of id -> payload for quick access
        by_id = {}
        for f in fields:
            try:
                fid = int(f.get('id'))
            except (TypeError, ValueError):
                continue
            by_id[fid] = f

        if not by_id:
            return jsonify({'ok': True, 'note': 'No fields to save'})

        # Load DB fields for this section to ensure consistency and permissions
        db_fields = (
            CustomFormField.query
            .filter_by(project_id=project.id, section=section)
            .filter(CustomFormField.id.in_(list(by_id.keys())))
            .all()
        )

        for db_field in db_fields:
            payload = by_id.get(db_field.id) or {}
            if db_field.field_type == 'dichotomous_outcome':
                # Expect 'events' and 'total' keys
                events = payload.get('events')
                total = payload.get('total')
                def to_int(v):
                    if v is None or v == '':
                        return None
                    try:
                        return int(v)
                    except (TypeError, ValueError):
                        return None
                if events is None and total is None:
                    value_str = None
                else:
                    value_str = json.dumps({'events': to_int(events), 'total': to_int(total)})
            else:
                value = payload.get('value')
                value_str = None if value is None or value == '' else str(value)

            sdv = StudyDataValue.query.filter_by(study_id=study.id, form_field_id=db_field.id).first()
            if sdv:
                sdv.value = value_str
            else:
                sdv = StudyDataValue(study_id=study.id, form_field_id=db_field.id, value=value_str)
                db.session.add(sdv)

        db.session.commit()
        return jsonify({'ok': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/project/<int:project_id>/export_jamovi')
def export_jamovi(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Get all studies for the project
    studies = project.studies.all()
    
    # Create an in-memory buffer for the zip file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        # Define columns for Jamovi export
        jamovi_columns = ['Study', 'Intervention_events', 'Intervention_total', 'Control_events', 'Control_Total']

        # Dictionary to hold data for each outcome, keyed by outcome name
        outcomes_data = {}

        for study in studies:
            numerical_outcomes = study.numerical_outcomes.all()
            for num_outcome in numerical_outcomes:
                outcome_name = num_outcome.outcome_name
                
                # Initialize list for outcome if not already present
                if outcome_name not in outcomes_data:
                    outcomes_data[outcome_name] = []
                
                # Append data for the current outcome
                outcomes_data[outcome_name].append({
                    'Study': study.title,
                    'Intervention_events': num_outcome.events_intervention,
                    'Intervention_total': num_outcome.total_intervention,
                    'Control_events': num_outcome.events_control,
                    'Control_Total': num_outcome.total_control
                })
        
        # Create a separate CSV for each outcome
        for outcome_name, data_rows in outcomes_data.items():
            df = DataFrame(data_rows, columns=jamovi_columns)
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            # Add the CSV to the zip file
            # Sanitize outcome_name for filename
            safe_outcome_name = "".join([c for c in outcome_name if c.isalnum() or c in (' ', '.', '_')]).rstrip()
            filename = f"{project.name}_{safe_outcome_name}_Jamovi_Export.csv"
            zf.writestr(filename, output.getvalue())

    zip_buffer.seek(0)
    
    return send_file(zip_buffer, download_name=f'{project.name}_Jamovi_Exports.zip', as_attachment=True, mimetype='application/zip')
