import yaml
from app import db
from app.models import CustomFormField
import os

def load_template_and_create_form_fields(project_id, template_id):
    template_path = os.path.join(os.path.dirname(__file__), 'form_templates', f'{template_id}.yaml')
    
    with open(template_path, 'r') as f:
        template_data = yaml.safe_load(f)

    for section_data in template_data.get('sections', []):
        section_name = section_data.get('section_name')
        for field_data in section_data.get('fields', []):
            field = CustomFormField(
                project_id=project_id,
                section=section_name,
                label=field_data.get('label'),
                field_type=field_data.get('field_type'),
                required=field_data.get('required', False)
            )
            db.session.add(field)
    db.session.commit()
