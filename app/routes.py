import io # Import io for BytesIO
import zipfile # Import zipfile
from flask import render_template, flash, redirect, url_for, request, send_file, jsonify, abort # Import send_file, jsonify, abort
from flask_login import current_user, login_user, logout_user, login_required
from app import app, db
from app.forms import ProjectForm, StudyForm, CustomFormFieldForm, OutcomeForm, RegisterForm, LoginForm, AddMemberForm
from app.models import Project, Study, CustomFormField, StudyDataValue, StudyNumericalOutcome, ProjectOutcome, StudyContinuousOutcome, User, ProjectMembership, FormChangeRequest # Import new models
from app.utils import load_template_and_create_form_fields # Import the new utility function
import json # Import json for handling dichotomous_outcome
from pandas import DataFrame # Import pandas DataFrame

# -------------------- RBAC helpers --------------------

def is_admin() -> bool:
    return bool(getattr(current_user, 'is_authenticated', False) and getattr(current_user, 'is_admin', False))


def get_membership_for(project_id: int):
    if not getattr(current_user, 'is_authenticated', False):
        return None
    return ProjectMembership.query.filter_by(user_id=current_user.id, project_id=project_id).first()


def require_project_member(project_id: int):
    if is_admin():
        return
    ms = get_membership_for(project_id)
    if not ms:
        abort(403)


def require_project_owner(project_id: int):
    if is_admin():
        return
    ms = get_membership_for(project_id)
    if not ms or (ms.role or '').lower() != 'owner':
        abort(403)


def _propose_change(project_id: int, action_type: str, payload: dict, reason: str | None = None):
    fcr = FormChangeRequest(
        project_id=project_id,
        requested_by=current_user.id,
        action_type=action_type,
        payload=json.dumps(payload or {}),
        reason=(reason.strip() if isinstance(reason, str) and reason.strip() else None),
        status='pending',
    )
    db.session.add(fcr)
    db.session.commit()
    return fcr

@app.route('/')
@login_required
def index():
    if is_admin():
        projects = Project.query.order_by(Project.id.asc()).all()
        roles_by_project = {p.id: 'Admin' for p in projects}
    else:
        # Only projects where the user is a member/owner
        projects = (
            Project.query
            .join(ProjectMembership, ProjectMembership.project_id == Project.id)
            .filter(ProjectMembership.user_id == current_user.id)
            .order_by(Project.id.asc())
            .all()
        )
        # Map project -> role label
        pm_rows = (
            ProjectMembership.query
            .filter(ProjectMembership.user_id == current_user.id,
                    ProjectMembership.project_id.in_([p.id for p in projects]))
            .all()
        )
        roles_by_project = {pm.project_id: (pm.role or '').capitalize() for pm in pm_rows}
    return render_template('index.html', projects=projects, roles_by_project=roles_by_project)


# -------------------- Auth routes --------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if getattr(current_user, 'is_authenticated', False):
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter(db.func.lower(User.email) == email).first():
            flash('Email already registered.', 'error')
            return render_template('auth_register.html', form=form)
        user = User(name=form.name.data.strip(), email=email)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. You can now log in.')
        return redirect(url_for('login'))
    return render_template('auth_register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if getattr(current_user, 'is_authenticated', False):
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter(db.func.lower(User.email) == email).first()
        if not user or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'error')
            return render_template('auth_login.html', form=form)
        if not user.is_active:
            flash('Account is disabled.', 'error')
            return render_template('auth_login.html', form=form)
        login_user(user)
        return redirect(url_for('index'))
    return render_template('auth_login.html', form=form)


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_project', methods=['GET', 'POST'])
@login_required
def add_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(name=form.name.data, description=form.description.data)
        db.session.add(project)
        db.session.commit()
        # Make creator an owner
        try:
            pm = ProjectMembership(user_id=current_user.id, project_id=project.id, role='owner', status='active')
            db.session.add(pm)
            db.session.commit()
        except Exception:
            db.session.rollback()
        flash('Project created successfully! Now, set up your data extraction form.')
        return redirect(url_for('setup_form', project_id=project.id))
    return render_template('add_project.html', form=form)

@app.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)
    studies = project.studies.all()
    try:
        field_count = project.form_fields.count()
    except Exception:
        # In case relationship is not loaded as query
        field_count = len(project.form_fields.all()) if hasattr(project.form_fields, 'all') else 0
    # Count recorded outcomes (any type) for this project
    try:
        dich_count = (
            db.session.query(db.func.count(StudyNumericalOutcome.id))
            .join(Study, StudyNumericalOutcome.study_id == Study.id)
            .filter(Study.project_id == project.id)
            .scalar()
        ) or 0
    except Exception:
        dich_count = 0
    try:
        cont_count = (
            db.session.query(db.func.count(StudyContinuousOutcome.id))
            .join(Study, StudyContinuousOutcome.study_id == Study.id)
            .filter(Study.project_id == project.id)
            .scalar()
        ) or 0
    except Exception:
        cont_count = 0
    outcome_row_count = int(dich_count) + int(cont_count)

    # Pending change requests for owners/admins
    ms = get_membership_for(project.id)
    is_owner_or_admin = bool(is_admin() or (ms and (ms.role or '').lower() == 'owner'))
    if is_admin():
        role_label = 'Admin'
    elif ms and ms.role:
        role_label = ms.role.capitalize()
    else:
        role_label = ''
    pending_count = project.change_requests.filter_by(status='pending').count() if is_owner_or_admin else 0
    return render_template(
        'project_detail.html',
        project=project,
        studies=studies,
        field_count=field_count,
        study_count=len(studies),
        outcome_row_count=outcome_row_count,
        pending_count=pending_count,
        is_owner_or_admin=is_owner_or_admin,
        role_label=role_label,
    )


@app.route('/project/<int:project_id>/form_fields')
@login_required
def list_form_fields(project_id):
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)
    fields = (
        CustomFormField.query
        .filter_by(project_id=project.id)
        .order_by(
            db.func.coalesce(CustomFormField.section_order, 999999).asc(),
            CustomFormField.section.asc(),
            db.func.coalesce(CustomFormField.sort_order, CustomFormField.id).asc(),
            CustomFormField.id.asc(),
        )
        .all()
    )
    # Build ordered sections preserving section order
    grouped_fields = []
    cur_section = None
    for f in fields:
        if not grouped_fields or grouped_fields[-1]['name'] != f.section:
            grouped_fields.append({'name': f.section, 'fields': []})
        grouped_fields[-1]['fields'].append(f)
    outcomes = project.outcomes.order_by(ProjectOutcome.name.asc()).all()
    outcome_form = OutcomeForm()
    # Show pending change request count to owners
    pending_count = 0
    ms = get_membership_for(project.id)
    is_owner_or_admin = bool(is_admin() or (ms and (ms.role or '').lower() == 'owner'))
    if is_owner_or_admin:
        pending_count = project.change_requests.filter_by(status='pending').count()
    if is_admin():
        role_label = 'Admin'
    elif ms and ms.role:
        role_label = ms.role.capitalize()
    else:
        role_label = ''
    return render_template(
        'form_fields.html',
        project=project,
        grouped_fields=grouped_fields,
        outcomes=outcomes,
        outcome_form=outcome_form,
        pending_count=pending_count,
        is_owner_or_admin=is_owner_or_admin,
        role_label=role_label,
    )


def _normalize_section_orders(project_id: int):
    sections = (
        db.session.query(CustomFormField.section, db.func.min(CustomFormField.section_order))
        .filter_by(project_id=project_id)
        .group_by(CustomFormField.section)
        .order_by(db.func.coalesce(db.func.min(CustomFormField.section_order), 999999).asc(), db.func.min(CustomFormField.id).asc())
        .all()
    )
    mapping = {}
    for idx, (name, _min_order) in enumerate(sections, start=1):
        mapping[name] = idx
    # Apply mapping to all rows in each section
    for name, order in mapping.items():
        CustomFormField.query.filter_by(project_id=project_id, section=name).update({CustomFormField.section_order: order})
    db.session.commit()


# -------------------- Project membership management --------------------

@app.route('/project/<int:project_id>/members', methods=['GET', 'POST'])
@login_required
def manage_members(project_id):
    project = Project.query.get_or_404(project_id)
    require_project_owner(project.id)
    form = AddMemberForm()
    if form.validate_on_submit():
        email = (form.email.data or '').strip().lower()
        role = (form.role.data or 'member').lower()
        user = User.query.filter(db.func.lower(User.email) == email).first()
        if not user:
            flash('No user found with that email. Ask them to register first.', 'error')
            return redirect(url_for('manage_members', project_id=project.id))
        existing = ProjectMembership.query.filter_by(user_id=user.id, project_id=project.id).first()
        if existing:
            existing.role = role
            db.session.commit()
            flash('Updated existing member role.')
        else:
            pm = ProjectMembership(user_id=user.id, project_id=project.id, role=role, status='active')
            db.session.add(pm)
            db.session.commit()
            flash('Member added.')
        return redirect(url_for('manage_members', project_id=project.id))

    members = (
        ProjectMembership.query
        .filter_by(project_id=project.id)
        .join(User, User.id == ProjectMembership.user_id)
        .order_by(User.name.asc())
        .all()
    )
    return render_template('members.html', project=project, form=form, members=members)


# -------------------- Change requests (owner review) --------------------

@app.route('/project/<int:project_id>/requests')
@login_required
def list_change_requests(project_id):
    project = Project.query.get_or_404(project_id)
    require_project_owner(project.id)
    pending = project.change_requests.order_by(FormChangeRequest.created_at.desc()).all()
    return render_template('requests.html', project=project, requests=pending)


def _apply_change_request(project, req: FormChangeRequest):
    payload = json.loads(req.payload or '{}')
    action = (req.action_type or '').lower()
    # Minimal supported actions
    if action == 'add_field':
        sec = (payload.get('section') or '').strip()
        lbl = (payload.get('label') or '').strip()
        ftype = (payload.get('field_type') or 'text').strip()
        required = bool(payload.get('required') or False)
        help_text = (payload.get('help_text') or None)
        # section_order: place at end or inherit
        sec_order = (
            db.session.query(db.func.min(CustomFormField.section_order))
            .filter_by(project_id=project.id, section=sec)
            .scalar()
        )
        if sec_order is None:
            max_sec = db.session.query(db.func.max(CustomFormField.section_order)).filter_by(project_id=project.id).scalar() or 0
            sec_order = int(max_sec) + 1
        max_order = db.session.query(db.func.max(CustomFormField.sort_order)).filter_by(project_id=project.id, section=sec).scalar()
        next_order = (max_order + 1) if max_order is not None else 1
        cf = CustomFormField(
            project_id=project.id,
            section=sec,
            section_order=sec_order,
            label=lbl,
            field_type=ftype,
            required=required,
            help_text=help_text,
            sort_order=next_order,
        )
        db.session.add(cf)
        db.session.commit()
        return True
    elif action == 'edit_field':
        fid = int(payload.get('field_id'))
        f = CustomFormField.query.filter_by(project_id=project.id, id=fid).first()
        if not f:
            return False
        changes = payload.get('changes') or {}
        if 'section' in changes and changes['section']:
            new_sec = changes['section'].strip()
            if new_sec != f.section:
                f.section = new_sec
                # section order and sort order adjustments similar to edit route
                sec_order = (
                    db.session.query(db.func.min(CustomFormField.section_order))
                    .filter_by(project_id=project.id, section=f.section)
                    .scalar()
                )
                if sec_order is None:
                    max_sec = db.session.query(db.func.max(CustomFormField.section_order)).filter_by(project_id=project.id).scalar() or 0
                    f.section_order = int(max_sec) + 1
                else:
                    f.section_order = sec_order
                max_order = db.session.query(db.func.max(CustomFormField.sort_order)).filter_by(project_id=project.id, section=f.section).scalar()
                f.sort_order = (max_order + 1) if max_order is not None else 1
        if 'label' in changes and changes['label'] is not None:
            f.label = (changes['label'] or '').strip()
        if 'field_type' in changes and changes['field_type'] is not None:
            f.field_type = (changes['field_type'] or '').strip()
        if 'required' in changes and changes['required'] is not None:
            f.required = bool(changes['required'])
        if 'help_text' in changes:
            txt = changes['help_text']
            f.help_text = (txt.strip() if isinstance(txt, str) else None)
        db.session.commit()
        return True
    elif action == 'delete_field':
        fid = int(payload.get('field_id'))
        f = CustomFormField.query.filter_by(project_id=project.id, id=fid).first()
        if not f:
            return False
        section = f.section
        db.session.delete(f)
        db.session.commit()
        # normalize order
        _normalize_section_order(project.id, section)
        return True
    elif action == 'add_outcome':
        name = (payload.get('name') or '').strip()
        otype = (payload.get('outcome_type') or 'dichotomous').strip()
        if not name:
            return False
        exists = ProjectOutcome.query.filter(
            ProjectOutcome.project_id == project.id,
            db.func.lower(ProjectOutcome.name) == db.func.lower(name)
        ).first()
        if exists:
            return True
        po = ProjectOutcome(project_id=project.id, name=name, outcome_type=otype)
        db.session.add(po)
        db.session.commit()
        return True
    elif action == 'delete_outcome':
        oid = payload.get('outcome_id')
        if oid:
            outcome = ProjectOutcome.query.filter_by(project_id=project.id, id=int(oid)).first()
        else:
            # fallback by name
            name = (payload.get('name') or '').strip()
            outcome = ProjectOutcome.query.filter(
                ProjectOutcome.project_id == project.id,
                db.func.lower(ProjectOutcome.name) == db.func.lower(name)
            ).first()
        if not outcome:
            return False
        db.session.delete(outcome)
        db.session.commit()
        return True
    return False


@app.route('/project/<int:project_id>/requests/<int:req_id>/<action>', methods=['POST'])
@login_required
def act_on_change_request(project_id, req_id, action):
    project = Project.query.get_or_404(project_id)
    require_project_owner(project.id)
    req = FormChangeRequest.query.filter_by(project_id=project.id, id=req_id).first_or_404()
    if req.status != 'pending':
        flash('Request already processed.')
        return redirect(url_for('list_change_requests', project_id=project.id))
    if action == 'approve':
        ok = _apply_change_request(project, req)
        if not ok:
            flash('Failed to apply change request.', 'error')
        else:
            req.status = 'approved'
            req.reviewed_by = current_user.id
            req.reviewed_at = db.func.now()
            db.session.commit()
            flash('Change request approved and applied.')
    elif action == 'reject':
        req.status = 'rejected'
        req.reviewed_by = current_user.id
        req.reviewed_at = db.func.now()
        db.session.commit()
        flash('Change request rejected.')
    else:
        abort(400)
    return redirect(url_for('list_change_requests', project_id=project.id))


def _move_section(project_id: int, section_name: str, direction: str):
    _normalize_section_orders(project_id)
    # Fetch ordered list of sections
    rows = (
        db.session.query(CustomFormField.section)
        .filter_by(project_id=project_id)
        .group_by(CustomFormField.section)
        .order_by(db.func.min(CustomFormField.section_order).asc())
        .all()
    )
    names = [r[0] for r in rows]
    if section_name not in names:
        return
    i = names.index(section_name)
    if direction == 'up' and i > 0:
        names[i-1], names[i] = names[i], names[i-1]
    elif direction == 'down' and i < len(names) - 1:
        names[i], names[i+1] = names[i+1], names[i]
    else:
        return
    # Reassign orders based on new sequence
    for idx, name in enumerate(names, start=1):
        CustomFormField.query.filter_by(project_id=project_id, section=name).update({CustomFormField.section_order: idx})
    db.session.commit()


@app.route('/project/<int:project_id>/form_sections/<path:section>/move_up', methods=['POST'])
@login_required
def move_form_section_up(project_id, section):
    project = Project.query.get_or_404(project_id)
    ms = get_membership_for(project.id)
    if not (is_admin() or (ms and (ms.role or '').lower() == 'owner')):
        _propose_change(
            project.id,
            'reorder_section',
            {'section': section, 'direction': 'up'},
            reason=request.form.get('reason')
        )
        flash('Move section request submitted for approval.')
        return redirect(url_for('list_form_fields', project_id=project.id))
    _move_section(project.id, section, 'up')
    return redirect(url_for('list_form_fields', project_id=project.id))


@app.route('/project/<int:project_id>/form_sections/<path:section>/move_down', methods=['POST'])
@login_required
def move_form_section_down(project_id, section):
    project = Project.query.get_or_404(project_id)
    ms = get_membership_for(project.id)
    if not (is_admin() or (ms and (ms.role or '').lower() == 'owner')):
        _propose_change(
            project.id,
            'reorder_section',
            {'section': section, 'direction': 'down'},
            reason=request.form.get('reason')
        )
        flash('Move section request submitted for approval.')
        return redirect(url_for('list_form_fields', project_id=project.id))
    _move_section(project.id, section, 'down')
    return redirect(url_for('list_form_fields', project_id=project.id))


@app.route('/project/<int:project_id>/form_fields/add', methods=['GET', 'POST'])
@login_required
def add_form_field(project_id):
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)
    form = CustomFormFieldForm()
    # Existing sections for this project's form
    sections = [
        row[0]
        for row in (
            db.session.query(CustomFormField.section)
            .filter_by(project_id=project.id)
            .distinct()
            .order_by(CustomFormField.section.asc())
            .all()
        )
        if row[0]
    ]
    if form.validate_on_submit():
        ms = get_membership_for(project.id)
        if not (is_admin() or (ms and (ms.role or '').lower() == 'owner')):
            payload = {
                'section': form.section.data.strip(),
                'label': form.label.data.strip(),
                'field_type': form.field_type.data,
                'required': bool(form.required.data),
                'help_text': (form.help_text.data.strip() if form.help_text.data else None),
            }
            _propose_change(project.id, 'add_field', payload, reason=form.change_reason.data)
            flash('Field addition proposed for approval.')
            return redirect(url_for('list_form_fields', project_id=project.id))
        # Determine next sort_order within this section
        sec_name = form.section.data.strip()
        max_order = (
            db.session.query(db.func.max(CustomFormField.sort_order))
            .filter_by(project_id=project.id, section=sec_name)
            .scalar()
        )
        next_order = (max_order + 1) if max_order is not None else 1
        # Determine section_order for the section
        sec_order = (
            db.session.query(db.func.min(CustomFormField.section_order))
            .filter_by(project_id=project.id, section=sec_name)
            .scalar()
        )
        if sec_order is None:
            max_sec = (
                db.session.query(db.func.max(CustomFormField.section_order))
                .filter_by(project_id=project.id)
                .scalar()
            ) or 0
            sec_order = int(max_sec) + 1
        field = CustomFormField(
            project_id=project.id,
            section=sec_name,
            section_order=sec_order,
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
    return render_template('edit_form_field.html', project=project, form=form, mode='add', sections=sections)


@app.route('/project/<int:project_id>/form_fields/<int:field_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_form_field(project_id, field_id):
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)
    field = CustomFormField.query.filter_by(project_id=project.id, id=field_id).first_or_404()
    form = CustomFormFieldForm(obj=field)
    sections = [
        row[0]
        for row in (
            db.session.query(CustomFormField.section)
            .filter_by(project_id=project.id)
            .distinct()
            .order_by(CustomFormField.section.asc())
            .all()
        )
        if row[0]
    ]
    if form.validate_on_submit():
        ms = get_membership_for(project.id)
        if not (is_admin() or (ms and (ms.role or '').lower() == 'owner')):
            payload = {
                'field_id': field.id,
                'changes': {
                    'section': form.section.data.strip(),
                    'label': form.label.data.strip(),
                    'field_type': form.field_type.data,
                    'required': bool(form.required.data),
                    'help_text': (form.help_text.data.strip() if form.help_text.data else None),
                }
            }
            _propose_change(project.id, 'edit_field', payload, reason=form.change_reason.data)
            flash('Field edit proposed for approval.')
            return redirect(url_for('list_form_fields', project_id=project.id))
        old_section = field.section
        field.section = form.section.data.strip()
        field.label = form.label.data.strip()
        field.field_type = form.field_type.data
        field.required = bool(form.required.data)
        field.help_text = form.help_text.data.strip() if form.help_text.data else None
        # If section changed, move to end of new section
        if field.section != old_section:
            # Update section_order: inherit from target section if exists, else append as new section at end
            sec_order = (
                db.session.query(db.func.min(CustomFormField.section_order))
                .filter_by(project_id=project.id, section=field.section)
                .scalar()
            )
            if sec_order is None:
                max_sec = (
                    db.session.query(db.func.max(CustomFormField.section_order))
                    .filter_by(project_id=project.id)
                    .scalar()
                ) or 0
                sec_order = int(max_sec) + 1
            field.section_order = sec_order
            max_order = (
                db.session.query(db.func.max(CustomFormField.sort_order))
                .filter_by(project_id=project.id, section=field.section)
                .scalar()
            )
            field.sort_order = (max_order + 1) if max_order is not None else 1
        db.session.commit()
        flash('Field updated.')
        return redirect(url_for('list_form_fields', project_id=project.id))
    return render_template('edit_form_field.html', project=project, form=form, mode='edit', sections=sections)


@app.route('/project/<int:project_id>/outcomes/add', methods=['POST'])
@login_required
def add_project_outcome(project_id):
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)
    form = OutcomeForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        outcome_type = form.outcome_type.data
        ms = get_membership_for(project.id)
        if not (is_admin() or (ms and (ms.role or '').lower() == 'owner')):
            _propose_change(project.id, 'add_outcome', {'name': name, 'outcome_type': outcome_type}, reason=form.reason.data)
            flash('Outcome addition proposed for approval.')
            return redirect(url_for('list_form_fields', project_id=project.id))
        # Prevent duplicates by name (case-insensitive)
        exists = (
            ProjectOutcome.query.filter(
                ProjectOutcome.project_id == project.id,
                db.func.lower(ProjectOutcome.name) == db.func.lower(name)
            ).first()
        )
        if exists:
            flash('An outcome with this name already exists.', 'error')
        else:
            po = ProjectOutcome(project_id=project.id, name=name, outcome_type=outcome_type)
            db.session.add(po)
            db.session.commit()
            flash('Outcome added.')
    else:
        flash('Invalid outcome details.', 'error')
    return redirect(url_for('list_form_fields', project_id=project.id))


@app.route('/project/<int:project_id>/outcomes/<int:outcome_id>/delete', methods=['POST'])
@login_required
def delete_project_outcome(project_id, outcome_id):
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)
    ms = get_membership_for(project.id)
    if not (is_admin() or (ms and (ms.role or '').lower() == 'owner')):
        _propose_change(project.id, 'delete_outcome', {'outcome_id': outcome_id}, reason=request.form.get('reason'))
        flash('Outcome deletion proposed for approval.')
        return redirect(url_for('list_form_fields', project_id=project.id))
    outcome = ProjectOutcome.query.filter_by(project_id=project.id, id=outcome_id).first_or_404()
    db.session.delete(outcome)
    db.session.commit()
    flash('Outcome deleted.')
    return redirect(url_for('list_form_fields', project_id=project.id))


@app.route('/project/<int:project_id>/form_fields/<int:field_id>/delete', methods=['POST'])
@login_required
def delete_form_field(project_id, field_id):
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)
    field = CustomFormField.query.filter_by(project_id=project.id, id=field_id).first_or_404()
    ms = get_membership_for(project.id)
    if not (is_admin() or (ms and (ms.role or '').lower() == 'owner')):
        _propose_change(project.id, 'delete_field', {'field_id': field.id}, reason=request.form.get('reason'))
        flash('Field deletion proposed for approval.')
        return redirect(url_for('list_form_fields', project_id=project.id))
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
@login_required
def move_form_field_up(project_id, field_id):
    project = Project.query.get_or_404(project_id)
    ms = get_membership_for(project.id)
    if not (is_admin() or (ms and (ms.role or '').lower() == 'owner')):
        _propose_change(project.id, 'reorder_field', {'field_id': field_id, 'direction': 'up'}, reason=request.form.get('reason'))
        flash('Move field request submitted for approval.')
        return redirect(url_for('list_form_fields', project_id=project.id))
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
@login_required
def move_form_field_down(project_id, field_id):
    project = Project.query.get_or_404(project_id)
    ms = get_membership_for(project.id)
    if not (is_admin() or (ms and (ms.role or '').lower() == 'owner')):
        _propose_change(project.id, 'reorder_field', {'field_id': field_id, 'direction': 'down'}, reason=request.form.get('reason'))
        flash('Move field request submitted for approval.')
        return redirect(url_for('list_form_fields', project_id=project.id))
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


@app.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    require_project_owner(project.id)
    # Gather counts for messaging
    study_q = project.studies
    studies = study_q.all() if hasattr(study_q, 'all') else []
    study_count = len(studies)
    try:
        field_count = project.form_fields.count()
    except Exception:
        field_count = len(project.form_fields.all()) if hasattr(project.form_fields, 'all') else 0

    # Delete child rows to satisfy FK constraints and cascades
    # Delete studies (cascades to StudyDataValue and StudyNumericalOutcome via backrefs)
    for s in studies:
        db.session.delete(s)
    # Delete custom form fields explicitly in case relationship cascade is not configured at DB level
    if hasattr(project, 'form_fields'):
        for f in project.form_fields.all():
            db.session.delete(f)

    # Finally delete the project itself
    db.session.delete(project)
    db.session.commit()
    flash(f"Project deleted. Removed {study_count} study(ies) and {field_count} form field(s).")
    return redirect(url_for('index'))

@app.route('/project/<int:project_id>/add_study', methods=['GET', 'POST'])
@login_required
def add_study(project_id):
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)
    form = StudyForm()
    if form.validate_on_submit():
        study = Study(title=form.title.data, author=form.author.data, year=form.year.data, project=project, created_by=current_user.id)
        db.session.add(study)
        db.session.commit()
        flash('Study added successfully!')
        return redirect(url_for('project_detail', project_id=project.id))
    return render_template('add_study.html', form=form, project=project)

@app.route('/project/<int:project_id>/setup_form', methods=['GET', 'POST'])
@login_required
def setup_form(project_id):
    project = Project.query.get_or_404(project_id)
    require_project_owner(project.id)
    if request.method == 'POST':
        template_id = request.form.get('template_id')
        setup_mode = (request.form.get('setup_mode') or 'auto').lower()  # 'auto' | 'customize' | 'scratch'

        # Start from scratch ignores template selection
        if setup_mode == 'scratch':
            flash('Starting from scratch. Add sections and fields to build your form.')
            return redirect(url_for('list_form_fields', project_id=project.id))

        # For auto/customize, a supported template must be chosen
        if template_id == 'rct_v1':  # Only RCT template is supported for now
            # Guard: if fields already exist, do not recreate from template
            existing_count = (
                db.session.query(db.func.count(CustomFormField.id))
                .filter_by(project_id=project.id)
                .scalar()
            ) or 0
            if existing_count > 0:
                if setup_mode == 'customize':
                    flash('A data extraction form already exists for this project. Customize it below.')
                    return redirect(url_for('list_form_fields', project_id=project.id))
                else:
                    flash('A data extraction form already exists for this project.')
                    return redirect(url_for('project_detail', project_id=project.id))
            try:
                load_template_and_create_form_fields(project.id, template_id)
                if setup_mode == 'customize':
                    flash('Base form created from template. Customize it below.')
                    return redirect(url_for('list_form_fields', project_id=project.id))
                else:
                    flash('Data extraction form generated from RCT template!')
                    return redirect(url_for('project_detail', project_id=project.id))
            except Exception as e:
                flash(f'Failed to generate form: {e}', 'error')
        else:
            flash('Invalid template selected or template not yet supported.', 'error')
    return render_template('setup_form.html', project=project)

@app.route('/project/<int:project_id>/study/<int:study_id>/enter_data', methods=['GET', 'POST'])
@login_required
def enter_data(project_id, study_id):
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)
    study = Study.query.get_or_404(study_id)
    
    # Get custom form fields for this project, ordered by section and in-section order
    form_fields = (
        CustomFormField.query
        .filter_by(project_id=project.id)
        .order_by(
            db.func.coalesce(CustomFormField.section_order, 999999).asc(),
            CustomFormField.section.asc(),
            db.func.coalesce(CustomFormField.sort_order, CustomFormField.id).asc(),
            CustomFormField.id.asc(),
        )
        .all()
    )
    # Build ordered sections for rendering without re-sorting by section name
    grouped_fields = []
    for f in form_fields:
        if not grouped_fields or grouped_fields[-1]['name'] != f.section:
            grouped_fields.append({'name': f.section, 'fields': []})
        grouped_fields[-1]['fields'].append(f)

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
    # Get existing continuous outcome data for this study
    existing_continuous_outcomes_objects = study.continuous_outcomes.all()
    existing_continuous_outcomes = []
    for co in existing_continuous_outcomes_objects:
        existing_continuous_outcomes.append({
            'outcome_name': co.outcome_name,
            'mean_intervention': co.mean_intervention,
            'sd_intervention': co.sd_intervention,
            'n_intervention': co.n_intervention,
            'mean_control': co.mean_control,
            'sd_control': co.sd_control,
            'n_control': co.n_control,
        })

    # Membership role for enforcement
    ms = get_membership_for(project.id)
    is_owner_or_admin = bool(is_admin() or (ms and (ms.role or '').lower() == 'owner'))

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
            elif field.field_type == 'baseline_continuous':
                int_mean = request.form.get(f'{field_name}_int_mean')
                int_sd = request.form.get(f'{field_name}_int_sd')
                ctrl_mean = request.form.get(f'{field_name}_ctrl_mean')
                ctrl_sd = request.form.get(f'{field_name}_ctrl_sd')
                def to_float(v):
                    if v is None or v == '':
                        return None
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return None
                payload = {
                    'intervention': {'mean': to_float(int_mean), 'sd': to_float(int_sd)},
                    'control': {'mean': to_float(ctrl_mean), 'sd': to_float(ctrl_sd)},
                }
                # If all values are None, store None
                if all(payload[g][k] is None for g in ('intervention','control') for k in ('mean','sd')):
                    value_str = None
                else:
                    value_str = json.dumps(payload)
            elif field.field_type == 'baseline_categorical':
                int_pct = request.form.get(f'{field_name}_int_pct')
                ctrl_pct = request.form.get(f'{field_name}_ctrl_pct')
                def to_float_pct(v):
                    if v is None or v == '':
                        return None
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return None
                payload = {
                    'intervention': {'percent': to_float_pct(int_pct)},
                    'control': {'percent': to_float_pct(ctrl_pct)},
                }
                if payload['intervention']['percent'] is None and payload['control']['percent'] is None:
                    value_str = None
                else:
                    value_str = json.dumps(payload)
            else:
                value_str = request.form.get(field_name)

            data_value = StudyDataValue.query.filter_by(study_id=study.id, form_field_id=field.id).first()
            if data_value:
                data_value.value = value_str
            else:
                data_value = StudyDataValue(study_id=study.id, form_field_id=field.id, value=value_str)
                db.session.add(data_value)
        
        # Save numerical outcomes (dichotomous)
        # Gather submitted rows first; for members we will upsert per name
        outcome_indices = set()
        for index_str in request.form.getlist('outcome_row_index'):
            try:
                index = int(index_str)
                outcome_indices.add(index)
            except ValueError:
                pass # Not a valid outcome index

        submitted_dich = []
        for index in sorted(list(outcome_indices)):
            outcome_name = (request.form.get(f'outcome_name_{index}') or '').strip()
            if not outcome_name:
                continue
            submitted_dich.append({
                'name': outcome_name,
                'ei': request.form.get(f'events_intervention_{index}', type=int),
                'ti': request.form.get(f'total_intervention_{index}', type=int),
                'ec': request.form.get(f'events_control_{index}', type=int),
                'tc': request.form.get(f'total_control_{index}', type=int),
            })

        if is_owner_or_admin:
            # Replace all for owners/admins
            StudyNumericalOutcome.query.filter_by(study_id=study.id).delete()
            for row in submitted_dich:
                db.session.add(StudyNumericalOutcome(
                    study_id=study.id,
                    outcome_name=row['name'],
                    events_intervention=row['ei'],
                    total_intervention=row['ti'],
                    events_control=row['ec'],
                    total_control=row['tc'],
                ))
        else:
            # Upsert allowed rows; do not remove other existing outcomes
            allowed_dich = set([ (o.name or '').strip().lower() for o in project.outcomes.filter_by(outcome_type='dichotomous').all() ])
            names_to_apply = [r['name'] for r in submitted_dich if r['name'].lower() in allowed_dich]
            if names_to_apply:
                (StudyNumericalOutcome.query
                    .filter_by(study_id=study.id)
                    .filter(StudyNumericalOutcome.outcome_name.in_(names_to_apply))
                    .delete(synchronize_session=False))
                for row in submitted_dich:
                    if row['name'].lower() not in allowed_dich:
                        continue
                    db.session.add(StudyNumericalOutcome(
                        study_id=study.id,
                        outcome_name=row['name'],
                        events_intervention=row['ei'],
                        total_intervention=row['ti'],
                        events_control=row['ec'],
                        total_control=row['tc'],
                    ))

        # Save continuous outcomes
        cont_indices = set()
        for index_str in request.form.getlist('cont_outcome_row_index'):
            try:
                cont_indices.add(int(index_str))
            except ValueError:
                pass
        def to_float(v):
            if v is None or v == '':
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
        def to_int(v):
            if v is None or v == '':
                return None
            try:
                return int(v)
            except (TypeError, ValueError):
                return None
        submitted_cont = []
        for index in sorted(list(cont_indices)):
            cname = (request.form.get(f'cont_outcome_name_{index}') or '').strip()
            mi = to_float(request.form.get(f'cont_mean_intervention_{index}'))
            sdi = to_float(request.form.get(f'cont_sd_intervention_{index}'))
            ni = to_int(request.form.get(f'cont_n_intervention_{index}'))
            mc = to_float(request.form.get(f'cont_mean_control_{index}'))
            sdc = to_float(request.form.get(f'cont_sd_control_{index}'))
            nc = to_int(request.form.get(f'cont_n_control_{index}'))
            if cname:
                submitted_cont.append({'name': cname, 'mi': mi, 'sdi': sdi, 'ni': ni, 'mc': mc, 'sdc': sdc, 'nc': nc})

        if is_owner_or_admin:
            StudyContinuousOutcome.query.filter_by(study_id=study.id).delete()
            for row in submitted_cont:
                db.session.add(StudyContinuousOutcome(
                    study_id=study.id,
                    outcome_name=row['name'],
                    mean_intervention=row['mi'],
                    sd_intervention=row['sdi'],
                    n_intervention=row['ni'],
                    mean_control=row['mc'],
                    sd_control=row['sdc'],
                    n_control=row['nc'],
                ))
        else:
            allowed_cont = set([ (o.name or '').strip().lower() for o in project.outcomes.filter_by(outcome_type='continuous').all() ])
            names_to_apply_c = [r['name'] for r in submitted_cont if r['name'].lower() in allowed_cont]
            if names_to_apply_c:
                (StudyContinuousOutcome.query
                    .filter_by(study_id=study.id)
                    .filter(StudyContinuousOutcome.outcome_name.in_(names_to_apply_c))
                    .delete(synchronize_session=False))
                for row in submitted_cont:
                    if row['name'].lower() not in allowed_cont:
                        continue
                    db.session.add(StudyContinuousOutcome(
                        study_id=study.id,
                        outcome_name=row['name'],
                        mean_intervention=row['mi'],
                        sd_intervention=row['sdi'],
                        n_intervention=row['ni'],
                        mean_control=row['mc'],
                        sd_control=row['sdc'],
                        n_control=row['nc'],
                    ))

        db.session.commit()
        flash('Study data saved successfully!')
        return redirect(url_for('project_detail', project_id=project.id))

    # Role label for UI badge
    if is_admin():
        role_label = 'Admin'
    elif ms and ms.role:
        role_label = ms.role.capitalize()
    else:
        role_label = ''

    return render_template(
        'enter_data.html',
        project=project,
        study=study,
        grouped_fields=grouped_fields,
        existing_data=existing_data,
        existing_numerical_outcomes=existing_numerical_outcomes,
        existing_continuous_outcomes=existing_continuous_outcomes,
        role_label=role_label,
        is_owner_or_admin=is_owner_or_admin,
    )


@app.route('/project/<int:project_id>/study/<int:study_id>/autosave', methods=['POST'])
@login_required
def autosave_study_data(project_id, study_id):
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)
    study = Study.query.get_or_404(study_id)

    data = request.get_json(silent=True) or {}
    section = data.get('section')
    if not section:
        return jsonify({'ok': False, 'error': 'Missing section'}), 400

    try:
        if section == 'numerical_outcomes':
            rows = data.get('numerical_outcomes') or []
            ms = get_membership_for(project.id)
            is_owner_or_admin = bool(is_admin() or (ms and (ms.role or '').lower() == 'owner'))
            allowed = set([ (o.name or '').strip().lower() for o in project.outcomes.filter_by(outcome_type='dichotomous').all() ])
            # Validate first for members
            if not is_owner_or_admin:
                for row in rows:
                    name = (row.get('outcome_name') or '').strip()
                    if name and name.lower() not in allowed:
                        return jsonify({'ok': False, 'error': f'Unauthorized outcome name: {name}'}), 400
                # Upsert by names provided; preserve others
                names = [ (row.get('outcome_name') or '').strip() for row in rows if (row.get('outcome_name') or '').strip() ]
                if names:
                    (StudyNumericalOutcome.query
                        .filter_by(study_id=study.id)
                        .filter(StudyNumericalOutcome.outcome_name.in_(names))
                        .delete(synchronize_session=False))
                def to_int(v):
                    if v is None or v == '':
                        return None
                    try:
                        return int(v)
                    except (TypeError, ValueError):
                        return None
                for row in rows:
                    name = (row.get('outcome_name') or '').strip()
                    if not name:
                        continue
                    db.session.add(StudyNumericalOutcome(
                        study_id=study.id,
                        outcome_name=name,
                        events_intervention=to_int(row.get('events_intervention')),
                        total_intervention=to_int(row.get('total_intervention')),
                        events_control=to_int(row.get('events_control')),
                        total_control=to_int(row.get('total_control')),
                    ))
            else:
                # Owners/admins replace all rows
                StudyNumericalOutcome.query.filter_by(study_id=study.id).delete()
                def to_int(v):
                    if v is None or v == '':
                        return None
                    try:
                        return int(v)
                    except (TypeError, ValueError):
                        return None
                for row in rows:
                    name = (row.get('outcome_name') or '').strip()
                    if not name:
                        continue
                    db.session.add(StudyNumericalOutcome(
                        study_id=study.id,
                        outcome_name=name,
                        events_intervention=to_int(row.get('events_intervention')),
                        total_intervention=to_int(row.get('total_intervention')),
                        events_control=to_int(row.get('events_control')),
                        total_control=to_int(row.get('total_control')),
                    ))
            db.session.commit()
            return jsonify({'ok': True})

        if section == 'continuous_outcomes':
            rows = data.get('continuous_outcomes') or []
            ms = get_membership_for(project.id)
            is_owner_or_admin = bool(is_admin() or (ms and (ms.role or '').lower() == 'owner'))
            allowed = set([ (o.name or '').strip().lower() for o in project.outcomes.filter_by(outcome_type='continuous').all() ])
            def to_float(v):
                if v is None or v == '':
                    return None
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None
            def to_int(v):
                if v is None or v == '':
                    return None
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return None
            if not is_owner_or_admin:
                for row in rows:
                    name = (row.get('outcome_name') or '').strip()
                    if name and name.lower() not in allowed:
                        return jsonify({'ok': False, 'error': f'Unauthorized outcome name: {name}'}), 400
                names = [ (row.get('outcome_name') or '').strip() for row in rows if (row.get('outcome_name') or '').strip() ]
                if names:
                    (StudyContinuousOutcome.query
                        .filter_by(study_id=study.id)
                        .filter(StudyContinuousOutcome.outcome_name.in_(names))
                        .delete(synchronize_session=False))
                for row in rows:
                    name = (row.get('outcome_name') or '').strip()
                    if not name:
                        continue
                    db.session.add(StudyContinuousOutcome(
                        study_id=study.id,
                        outcome_name=name,
                        mean_intervention=to_float(row.get('mean_intervention')),
                        sd_intervention=to_float(row.get('sd_intervention')),
                        n_intervention=to_int(row.get('n_intervention')),
                        mean_control=to_float(row.get('mean_control')),
                        sd_control=to_float(row.get('sd_control')),
                        n_control=to_int(row.get('n_control')),
                    ))
            else:
                StudyContinuousOutcome.query.filter_by(study_id=study.id).delete()
                for row in rows:
                    name = (row.get('outcome_name') or '').strip()
                    if not name:
                        continue
                    db.session.add(StudyContinuousOutcome(
                        study_id=study.id,
                        outcome_name=name,
                        mean_intervention=to_float(row.get('mean_intervention')),
                        sd_intervention=to_float(row.get('sd_intervention')),
                        n_intervention=to_int(row.get('n_intervention')),
                        mean_control=to_float(row.get('mean_control')),
                        sd_control=to_float(row.get('sd_control')),
                        n_control=to_int(row.get('n_control')),
                    ))
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
            elif db_field.field_type == 'baseline_continuous':
                def to_float(v):
                    if v is None or v == '':
                        return None
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return None
                value_obj = {
                    'intervention': {
                        'mean': to_float(payload.get('int_mean')),
                        'sd': to_float(payload.get('int_sd')),
                    },
                    'control': {
                        'mean': to_float(payload.get('ctrl_mean')),
                        'sd': to_float(payload.get('ctrl_sd')),
                    }
                }
                if all(value_obj[g][k] is None for g in ('intervention','control') for k in ('mean','sd')):
                    value_str = None
                else:
                    value_str = json.dumps(value_obj)
            elif db_field.field_type == 'baseline_categorical':
                def to_float(v):
                    if v is None or v == '':
                        return None
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return None
                value_obj = {
                    'intervention': {'percent': to_float(payload.get('int_pct'))},
                    'control': {'percent': to_float(payload.get('ctrl_pct'))},
                }
                if value_obj['intervention']['percent'] is None and value_obj['control']['percent'] is None:
                    value_str = None
                else:
                    value_str = json.dumps(value_obj)
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

@app.route('/project/<int:project_id>/export_outcomes')
@app.route('/project/<int:project_id>/export_jamovi')  # backward-compatible alias
@login_required
def export_outcomes(project_id):
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)

    # Get all studies for the project in a stable order
    studies = project.studies.order_by(Study.id.asc()).all()

    # Create an in-memory buffer for the zip file
    zip_buffer = io.BytesIO()

    def safe(name: str) -> str:
        return "".join([c for c in (name or '') if c.isalnum() or c in (' ', '.', '_', '-')]).strip() or 'outcome'

    with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        # Define columns for outcomes export
        outcome_columns = ['Study', 'Intervention_events', 'Intervention_total', 'Control_events', 'Control_Total']

        # Try primary source: StudyNumericalOutcome rows
        outcomes_data = {}
        for study in studies:
            for num_outcome in study.numerical_outcomes.all():
                name = (num_outcome.outcome_name or '').strip()
                if not name:
                    # Skip unnamed outcomes
                    continue
                outcomes_data.setdefault(name, []).append({
                    'Study': study.title,
                    'Intervention_events': num_outcome.events_intervention,
                    'Intervention_total': num_outcome.total_intervention,
                    'Control_events': num_outcome.events_control,
                    'Control_Total': num_outcome.total_control,
                })

        wrote_any = False
        for outcome_name, data_rows in outcomes_data.items():
            if not data_rows:
                continue
            df = DataFrame(data_rows, columns=outcome_columns)
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            zf.writestr(f"{safe(project.name)}_{safe(outcome_name)}_Dichotomous_Export.csv", output.getvalue())
            wrote_any = True

        # Fallback: build outcomes from legacy 'dichotomous_outcome' static fields
        if not wrote_any:
            legacy_fields = (
                CustomFormField.query
                .filter_by(project_id=project.id, field_type='dichotomous_outcome')
                .order_by(
                    CustomFormField.section.asc(),
                    db.func.coalesce(CustomFormField.sort_order, CustomFormField.id).asc(),
                    CustomFormField.id.asc(),
                )
                .all()
            )

            for f in legacy_fields:
                rows = []
                for study in studies:
                    dv = StudyDataValue.query.filter_by(study_id=study.id, form_field_id=f.id).first()
                    events_val = total_val = None
                    if dv and dv.value:
                        try:
                            parsed = json.loads(dv.value)
                            events_val = parsed.get('events')
                            total_val = parsed.get('total')
                        except Exception:
                            pass
                    # Only add row if at least one value present
                    if events_val is not None or total_val is not None:
                        rows.append({
                            'Study': study.title,
                            'Intervention_events': events_val,
                            'Intervention_total': total_val,
                            'Control_events': None,
                            'Control_Total': None,
                        })
                if rows:
                    df = DataFrame(rows, columns=outcome_columns)
                    output = io.StringIO()
                    df.to_csv(output, index=False)
                    output.seek(0)
                    zf.writestr(f"{safe(project.name)}_{safe(f.label)}_Dichotomous_Export.csv", output.getvalue())
                    wrote_any = True

        # Additionally include continuous outcomes, grouped per outcome name
        cont_columns = [
            'Study',
            'Intervention_mean', 'Intervention_sd', 'Intervention_n',
            'Control_mean', 'Control_sd', 'Control_n',
        ]
        cont_data = {}
        for study in studies:
            for co in study.continuous_outcomes.all():
                name = (co.outcome_name or '').strip()
                if not name:
                    continue
                cont_data.setdefault(name, []).append({
                    'Study': study.title,
                    'Intervention_mean': co.mean_intervention,
                    'Intervention_sd': co.sd_intervention,
                    'Intervention_n': co.n_intervention,
                    'Control_mean': co.mean_control,
                    'Control_sd': co.sd_control,
                    'Control_n': co.n_control,
                })
        wrote_any_cont = False
        for outcome_name, data_rows in cont_data.items():
            if not data_rows:
                continue
            dfc = DataFrame(data_rows, columns=cont_columns)
            outc = io.StringIO()
            dfc.to_csv(outc, index=False)
            outc.seek(0)
            # add a type suffix to distinguish
            zf.writestr(f"{safe(project.name)}_{safe(outcome_name)}_Continuous_Export.csv", outc.getvalue())
            wrote_any_cont = True

        # If still nothing to write, include a README in the zip to avoid an empty archive
        if not wrote_any and not wrote_any_cont:
            zf.writestr(
                "README.txt",
                "No outcomes found for this project.\n"
                "- Enter dichotomous outcomes or continuous outcomes on the study page, or\n"
                "- Use legacy dichotomous outcome fields and resubmit.\n",
            )

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        download_name=f"{safe(project.name)}_Outcomes_Export.zip",
        as_attachment=True,
        mimetype='application/zip',
    )


@app.route('/project/<int:project_id>/export_static')
@login_required
def export_static(project_id):
    """Export all static (non-tabular) custom form fields for all studies in a project as CSV.

    Produces a flat table with columns:
    - Study metadata: Study, Author, Year
    - One column per CustomFormField (or multiple columns for composite types)
    """
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)

    # Load fields in a stable, user-visible order
    fields = (
        CustomFormField.query
        .filter_by(project_id=project.id)
        .order_by(
            db.func.coalesce(CustomFormField.section_order, 999999).asc(),
            CustomFormField.section.asc(),
            db.func.coalesce(CustomFormField.sort_order, CustomFormField.id).asc(),
            CustomFormField.id.asc(),
        )
        .all()
    )

    # Build ordered column list
    def col_base(field):
        return f"{field.section} - {field.label}".strip()

    columns = ['Study', 'Author', 'Year']
    expanded_fields = []  # (field, kind) where kind is 'single'|'events'|'total'
    for f in fields:
        if f.field_type == 'dichotomous_outcome':
            columns.append(f"{col_base(f)} (events)")
            columns.append(f"{col_base(f)} (total)")
            expanded_fields.append((f, 'events'))
            expanded_fields.append((f, 'total'))
        elif f.field_type == 'baseline_continuous':
            columns.append(f"{col_base(f)} (intervention mean)")
            columns.append(f"{col_base(f)} (intervention sd)")
            columns.append(f"{col_base(f)} (control mean)")
            columns.append(f"{col_base(f)} (control sd)")
            expanded_fields.append((f, 'int_mean'))
            expanded_fields.append((f, 'int_sd'))
            expanded_fields.append((f, 'ctrl_mean'))
            expanded_fields.append((f, 'ctrl_sd'))
        elif f.field_type == 'baseline_categorical':
            columns.append(f"{col_base(f)} (intervention %)")
            columns.append(f"{col_base(f)} (control %)")
            expanded_fields.append((f, 'int_pct'))
            expanded_fields.append((f, 'ctrl_pct'))
        else:
            columns.append(col_base(f))
            expanded_fields.append((f, 'single'))

    # Gather rows across studies
    rows = []
    for study in project.studies.order_by(Study.id.asc()).all():
        row = { 'Study': study.title, 'Author': study.author, 'Year': study.year }
        # Map of form_field_id -> raw value string
        data_map = { dv.form_field_id: dv.value for dv in study.data_values }
        for f, kind in expanded_fields:
            base = col_base(f)
            if kind == 'single':
                row[f"{base}"] = data_map.get(f.id)
            else:
                raw = data_map.get(f.id)
                parsed = None
                if raw:
                    try:
                        parsed = json.loads(raw)
                    except Exception:
                        parsed = None
                if f.field_type == 'dichotomous_outcome':
                    events_val = parsed.get('events') if parsed else None
                    total_val = parsed.get('total') if parsed else None
                    if kind == 'events':
                        row[f"{base} (events)"] = events_val
                    else:
                        row[f"{base} (total)"] = total_val
                elif f.field_type == 'baseline_continuous':
                    int_mean = parsed.get('intervention', {}).get('mean') if parsed else None
                    int_sd = parsed.get('intervention', {}).get('sd') if parsed else None
                    ctrl_mean = parsed.get('control', {}).get('mean') if parsed else None
                    ctrl_sd = parsed.get('control', {}).get('sd') if parsed else None
                    if kind == 'int_mean':
                        row[f"{base} (intervention mean)"] = int_mean
                    elif kind == 'int_sd':
                        row[f"{base} (intervention sd)"] = int_sd
                    elif kind == 'ctrl_mean':
                        row[f"{base} (control mean)"] = ctrl_mean
                    elif kind == 'ctrl_sd':
                        row[f"{base} (control sd)"] = ctrl_sd
                elif f.field_type == 'baseline_categorical':
                    int_pct = parsed.get('intervention', {}).get('percent') if parsed else None
                    ctrl_pct = parsed.get('control', {}).get('percent') if parsed else None
                    if kind == 'int_pct':
                        row[f"{base} (intervention %)"] = int_pct
                    elif kind == 'ctrl_pct':
                        row[f"{base} (control %)"] = ctrl_pct
        rows.append(row)

    df = DataFrame(rows, columns=columns)

    # Safe filename components
    def safe(name: str):
        return "".join([c for c in name or '' if c.isalnum() or c in (' ', '.', '_', '-')]).strip() or 'project'
    # CSV only
    sio = io.StringIO()
    df.to_csv(sio, index=False)
    data = io.BytesIO(sio.getvalue().encode('utf-8'))
    data.seek(0)
    return send_file(
        data,
        download_name=f"{safe(project.name)}_Static_Fields.csv",
        as_attachment=True,
        mimetype='text/csv',
    )


@app.route('/project/<int:project_id>/export_all_zip')
@login_required
def export_all_zip(project_id):
    """Create a single zip containing:
    - One CSV with all static fields across studies
    - One CSV per numerical outcome (jamovi-style), if present
    """
    project = Project.query.get_or_404(project_id)
    require_project_member(project.id)

    def safe(name: str):
        return "".join([c for c in (name or '') if c.isalnum() or c in (' ', '.', '_', '-')]).strip() or 'project'

    # Build static DataFrame (reuse logic similar to export_static)
    fields = (
        CustomFormField.query
        .filter_by(project_id=project.id)
        .order_by(
            db.func.coalesce(CustomFormField.section_order, 999999).asc(),
            CustomFormField.section.asc(),
            db.func.coalesce(CustomFormField.sort_order, CustomFormField.id).asc(),
            CustomFormField.id.asc(),
        )
        .all()
    )
    def col_base(field):
        return f"{field.section} - {field.label}".strip()
    columns = ['Study', 'Author', 'Year']
    expanded_fields = []
    for f in fields:
        if f.field_type == 'dichotomous_outcome':
            columns += [f"{col_base(f)} (events)", f"{col_base(f)} (total)"]
            expanded_fields += [(f, 'events'), (f, 'total')]
        elif f.field_type == 'baseline_continuous':
            columns += [
                f"{col_base(f)} (intervention mean)",
                f"{col_base(f)} (intervention sd)",
                f"{col_base(f)} (control mean)",
                f"{col_base(f)} (control sd)",
            ]
            expanded_fields += [(f, 'int_mean'), (f, 'int_sd'), (f, 'ctrl_mean'), (f, 'ctrl_sd')]
        elif f.field_type == 'baseline_categorical':
            columns += [f"{col_base(f)} (intervention %)", f"{col_base(f)} (control %)"]
            expanded_fields += [(f, 'int_pct'), (f, 'ctrl_pct')]
        else:
            columns.append(col_base(f))
            expanded_fields.append((f, 'single'))

    rows = []
    for study in project.studies.order_by(Study.id.asc()).all():
        row = {'Study': study.title, 'Author': study.author, 'Year': study.year}
        data_map = {dv.form_field_id: dv.value for dv in study.data_values}
        for f, kind in expanded_fields:
            base = col_base(f)
            raw = data_map.get(f.id)
            parsed = None
            if raw:
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = None
            if kind == 'single':
                row[f"{base}"] = raw
            elif f.field_type == 'dichotomous_outcome':
                if kind == 'events':
                    row[f"{base} (events)"] = parsed.get('events') if parsed else None
                else:
                    row[f"{base} (total)"] = parsed.get('total') if parsed else None
            elif f.field_type == 'baseline_continuous':
                if kind == 'int_mean':
                    row[f"{base} (intervention mean)"] = parsed.get('intervention', {}).get('mean') if parsed else None
                elif kind == 'int_sd':
                    row[f"{base} (intervention sd)"] = parsed.get('intervention', {}).get('sd') if parsed else None
                elif kind == 'ctrl_mean':
                    row[f"{base} (control mean)"] = parsed.get('control', {}).get('mean') if parsed else None
                elif kind == 'ctrl_sd':
                    row[f"{base} (control sd)"] = parsed.get('control', {}).get('sd') if parsed else None
            elif f.field_type == 'baseline_categorical':
                if kind == 'int_pct':
                    row[f"{base} (intervention %)"] = parsed.get('intervention', {}).get('percent') if parsed else None
                elif kind == 'ctrl_pct':
                    row[f"{base} (control %)"] = parsed.get('control', {}).get('percent') if parsed else None
        rows.append(row)

    static_df = DataFrame(rows, columns=columns)

    # Build outcome CSVs (same logic as export_outcomes)
    outcome_columns = ['Study', 'Intervention_events', 'Intervention_total', 'Control_events', 'Control_Total']
    outcomes_data = {}
    studies = project.studies.order_by(Study.id.asc()).all()
    for study in studies:
        for num_outcome in study.numerical_outcomes.all():
            name = (num_outcome.outcome_name or '').strip()
            if not name:
                continue
            outcomes_data.setdefault(name, []).append({
                'Study': study.title,
                'Intervention_events': num_outcome.events_intervention,
                'Intervention_total': num_outcome.total_intervention,
                'Control_events': num_outcome.events_control,
                'Control_Total': num_outcome.total_control,
            })

    # Create zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        # Write static CSV
        sio = io.StringIO()
        static_df.to_csv(sio, index=False)
        sio.seek(0)
        zf.writestr(f"{safe(project.name)}_Static_Fields.csv", sio.getvalue())

        wrote_any_dich = False
        for outcome_name, data_rows in outcomes_data.items():
            if not data_rows:
                continue
            df = DataFrame(data_rows, columns=outcome_columns)
            out_sio = io.StringIO()
            df.to_csv(out_sio, index=False)
            out_sio.seek(0)
            zf.writestr(f"{safe(project.name)}_{safe(outcome_name)}_Dichotomous_Export.csv", out_sio.getvalue())
            wrote_any_dich = True

        # Continuous outcomes per outcome file
        cont_columns = [
            'Study', 'Intervention_mean', 'Intervention_sd', 'Intervention_n',
            'Control_mean', 'Control_sd', 'Control_n',
        ]
        cont_data = {}
        for study in studies:
            for co in study.continuous_outcomes.all():
                name = (co.outcome_name or '').strip()
                if not name:
                    continue
                cont_data.setdefault(name, []).append({
                    'Study': study.title,
                    'Intervention_mean': co.mean_intervention,
                    'Intervention_sd': co.sd_intervention,
                    'Intervention_n': co.n_intervention,
                    'Control_mean': co.mean_control,
                    'Control_sd': co.sd_control,
                    'Control_n': co.n_control,
                })
        wrote_any_cont = False
        for outcome_name, data_rows in cont_data.items():
            if not data_rows:
                continue
            cont_df = DataFrame(data_rows, columns=cont_columns)
            csio = io.StringIO()
            cont_df.to_csv(csio, index=False)
            csio.seek(0)
            zf.writestr(f"{safe(project.name)}_{safe(outcome_name)}_Continuous_Export.csv", csio.getvalue())
            wrote_any_cont = True

        if not wrote_any_dich and not wrote_any_cont:
            zf.writestr(
                "README_outcomes.txt",
                "No outcomes found for this project.\n"
                "The zip includes only the static fields CSV.\n",
            )

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        download_name=f"{safe(project.name)}_All_Data.zip",
        as_attachment=True,
        mimetype='application/zip',
    )
