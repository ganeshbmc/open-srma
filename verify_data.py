from app import app, db
from app.models import Project, Study, CustomFormField, StudyDataValue, StudyNumericalOutcome
import json

with app.app_context():
    project_id = 2
    study_id = 2

    project = Project.query.get(project_id)
    study = Study.query.get(study_id)

    if project and study:
        print(f"--- Data for Study: {study.title} (Project: {project.name}) ---")

        # Verify CustomFormField data
        print("\n--- Static Form Fields ---")
        static_data_values = StudyDataValue.query.filter_by(study_id=study.id).all()
        if static_data_values:
            for dv in static_data_values:
                field = CustomFormField.query.get(dv.form_field_id)
                if field:
                    if field.field_type == 'dichotomous_outcome' and dv.value:
                        try:
                            value_data = json.loads(dv.value)
                            print(f"- {field.label}: Events={value_data.get('events')}, Total={value_data.get('total')}")
                        except json.JSONDecodeError:
                            print(f"- {field.label}: (Invalid JSON) {dv.value}")
                    else:
                        print(f"- {field.label}: {dv.value}")
                else:
                    print(f"- Field ID {dv.form_field_id}: {dv.value} (Field definition not found)")
        else:
            print("No static form data found for this study.")

        # Verify StudyNumericalOutcome data
        print("\n--- Numerical Outcomes ---")
        numerical_outcomes = StudyNumericalOutcome.query.filter_by(study_id=study.id).all()
        if numerical_outcomes:
            for no in numerical_outcomes:
                print(f"- Outcome: {no.outcome_name}, Intervention: {no.events_intervention}/{no.total_intervention}, Control: {no.events_control}/{no.total_control}")
        else:
            print("No numerical outcome data found for this study.")
    else:
        print(f"Project (ID: {project_id}) or Study (ID: {study_id}) not found.")
