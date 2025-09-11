import yaml
from app import db
from app.models import CustomFormField
import os

def load_template_and_create_form_fields(project_id, template_id):
    template_path = os.path.join(os.path.dirname(__file__), 'form_templates', f'{template_id}.yaml')

    try:
        with open(template_path, 'r') as f:
            template_data = yaml.safe_load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Template file not found: {template_path}") from e
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in template {template_path}: {e}") from e

    for idx, section_data in enumerate(template_data.get('sections', []), start=1):
        section_name = section_data.get('section_name')
        for field_data in section_data.get('fields', []):
            field = CustomFormField(
                project_id=project_id,
                section=section_name,
                section_order=idx,
                label=field_data.get('label'),
                field_type=field_data.get('field_type'),
                required=field_data.get('required', False),
                help_text=field_data.get('help') or field_data.get('help_text')
            )
            db.session.add(field)
    db.session.commit()
