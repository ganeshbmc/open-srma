import yaml
from app import db
from app.models import CustomFormField
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from flask import current_app

ALLOWED_FIELD_TYPES = {
    'text', 'textarea', 'integer', 'date',
    'dichotomous_outcome',
    'baseline_continuous', 'baseline_categorical',
    'select', 'select_member',
}


def _validate_template_data(template_data: dict):
    if not isinstance(template_data, dict):
        raise ValueError('Template must be a YAML mapping (object).')
    sections = template_data.get('sections')
    if not isinstance(sections, list) or not sections:
        raise ValueError('Template must define a non-empty "sections" list.')
    for si, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            raise ValueError(f'Section #{si} must be an object.')
        sname = section.get('section_name')
        if not sname or not isinstance(sname, str):
            raise ValueError(f'Section #{si} is missing a valid "section_name".')
        fields = section.get('fields', [])
        if fields is None:
            fields = []
        if not isinstance(fields, list):
            raise ValueError(f'Section "{sname}": "fields" must be a list.')
        for fi, field in enumerate(fields, start=1):
            if not isinstance(field, dict):
                raise ValueError(f'Section "{sname}": field #{fi} must be an object.')
            label = field.get('label')
            ftype = field.get('field_type')
            if not label or not isinstance(label, str):
                raise ValueError(f'Section "{sname}": field #{fi} missing valid "label".')
            if not ftype or not isinstance(ftype, str):
                raise ValueError(f'Section "{sname}", field "{label}": missing valid "field_type".')
            if ftype not in ALLOWED_FIELD_TYPES:
                raise ValueError(f'Section "{sname}", field "{label}": unsupported field_type "{ftype}".')
            opts = field.get('options')
            if ftype == 'select':
                if not isinstance(opts, dict):
                    raise ValueError(f'Section "{sname}", field "{label}": select requires an "options" object.')
                choices = opts.get('choices')
                if not isinstance(choices, list) or not all(isinstance(c, str) for c in choices):
                    raise ValueError(f'Section "{sname}", field "{label}": options.choices must be a list of strings.')
                if 'include_nr' in opts and not isinstance(opts.get('include_nr'), bool):
                    raise ValueError(f'Section "{sname}", field "{label}": options.include_nr must be boolean.')
            if ftype == 'select_member':
                if opts is not None and not isinstance(opts, dict):
                    raise ValueError(f'Section "{sname}", field "{label}": options must be an object when provided.')
                if opts and 'roles' in opts:
                    roles = opts.get('roles')
                    if not isinstance(roles, list) or not all(isinstance(r, str) for r in roles):
                        raise ValueError(f'Section "{sname}", field "{label}": options.roles must be a list of strings.')
                if opts and 'include_nr' in opts and not isinstance(opts.get('include_nr'), bool):
                    raise ValueError(f'Section "{sname}", field "{label}": options.include_nr must be boolean.')


def _create_fields_from_template_data(project_id, template_data):
    for idx, section_data in enumerate(template_data.get('sections', []), start=1):
        section_name = section_data.get('section_name')
        for field_data in section_data.get('fields', []):
            options = field_data.get('options') if isinstance(field_data.get('options'), (dict, list)) else None
            field = CustomFormField(
                project_id=project_id,
                section=section_name,
                section_order=idx,
                label=field_data.get('label'),
                field_type=field_data.get('field_type'),
                required=field_data.get('required', False),
                help_text=field_data.get('help') or field_data.get('help_text'),
                options=json.dumps(options) if options is not None else None,
            )
            db.session.add(field)
    db.session.commit()

def load_template_and_create_form_fields(project_id, template_id):
    template_path = os.path.join(os.path.dirname(__file__), 'form_templates', f'{template_id}.yaml')

    try:
        with open(template_path, 'r') as f:
            template_data = yaml.safe_load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Template file not found: {template_path}") from e
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in template {template_path}: {e}") from e
    _validate_template_data(template_data)
    _create_fields_from_template_data(project_id, template_data)


def load_template_from_yaml_content(project_id, yaml_text: str):
    try:
        template_data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}") from e
    if not isinstance(template_data, dict) or 'sections' not in template_data:
        raise ValueError('YAML must define a top-level "sections" list')
    _validate_template_data(template_data)
    _create_fields_from_template_data(project_id, template_data)


def _build_mail_connection(app):
    server = app.config.get('MAIL_SERVER')
    if not server or app.config.get('MAIL_SUPPRESS_SEND'):
        return None, None
    port = app.config.get('MAIL_PORT') or 587
    use_ssl = bool(app.config.get('MAIL_USE_SSL'))
    use_tls = bool(app.config.get('MAIL_USE_TLS')) and not use_ssl
    username = app.config.get('MAIL_USERNAME')
    password = app.config.get('MAIL_PASSWORD')

    if use_ssl:
        context = ssl.create_default_context()
        conn = smtplib.SMTP_SSL(server, port, context=context, timeout=20)
    else:
        conn = smtplib.SMTP(server, port, timeout=20)
        if use_tls:
            context = ssl.create_default_context()
            conn.starttls(context=context)

    if username and password:
        conn.login(username, password)
    return conn, username


def send_email(subject: str, recipients: list[str], body: str) -> bool:
    app = current_app
    if not recipients:
        return False
    if app.config.get('MAIL_SUPPRESS_SEND'):
        app.logger.info('MAIL_SUPPRESS_SEND is enabled; skipping email send.')
        return False
    conn, fallback_sender = _build_mail_connection(app)
    if not conn:
        app.logger.warning('Mail server not configured; unable to send email.')
        return False
    try:
        sender = app.config.get('MAIL_FROM') or fallback_sender
        if not sender:
            app.logger.warning('MAIL_FROM not configured and no login user; skipping email send.')
            return False
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)
        msg.set_content(body)
        conn.send_message(msg)
        return True
    except Exception as exc:
        app.logger.exception('Failed to send email: %s', exc)
        return False
    finally:
        try:
            conn.quit()
        except Exception:
            pass


def send_password_reset_email(user, reset_url: str) -> bool:
    app = current_app
    subject = 'Reset your open-srma password'
    body = (
        f"Hello {user.name},\n\n"
        "We received a request to reset your open-srma password. "
        "Use the link below to set a new password. The link expires in one hour.\n\n"
        f"{reset_url}\n\n"
        "If you did not request this change, you can ignore this email.\n"
    )
    return send_email(subject, [user.email], body)
