from app import app, db
from app.models import Project, CustomFormField

with app.app_context():
    project_id = 2
    project = Project.query.get(project_id)
    if project:
        print(f"Custom Form Fields for Project '{project.name}' (ID: {project_id}):")
        form_fields = CustomFormField.query.filter_by(project_id=project_id).all()
        if form_fields:
            for field in form_fields:
                print(f"- Label: {field.label}, Type: {field.field_type}, Section: {field.section}")
        else:
            print("No custom form fields found for this project.")
    else:
        print(f"Project with ID {project_id} not found.")
