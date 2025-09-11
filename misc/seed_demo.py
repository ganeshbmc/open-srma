from app import app, db
from app.models import (
    Project,
    Study,
    CustomFormField,
    StudyDataValue,
    StudyNumericalOutcome,
    ProjectOutcome,
    StudyContinuousOutcome,
    User,
    ProjectMembership,
)
import json


PROJECT_NAME = "Demo SRMA"
OWNER_EMAIL = "owner@example.com"
OWNER_NAME = "Demo Owner"
OWNER_PASSWORD = "demo123"
MEMBER_EMAIL = "member@example.com"
MEMBER_NAME = "Demo Member"


def get_or_create_project(name: str, description: str = "Demo project for exports and data entry") -> Project:
    proj = Project.query.filter_by(name=name).first()
    if proj:
        return proj
    proj = Project(name=name, description=description)
    db.session.add(proj)
    db.session.commit()
    return proj


def get_or_create_user(email: str, name: str, password: str, is_admin: bool = False) -> User:
    u = User.query.filter(db.func.lower(User.email) == (email or '').lower()).first()
    if u:
        # ensure admin flag aligns if passed
        if is_admin and not u.is_admin:
            u.is_admin = True
            db.session.commit()
        return u
    u = User(email=email.strip().lower(), name=name.strip(), is_admin=is_admin)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return u


def ensure_form_field(project_id: int, section: str, label: str, field_type: str, required: bool = False, help_text: str | None = None) -> CustomFormField:
    f = (
        CustomFormField.query
        .filter_by(project_id=project_id, section=section, label=label)
        .first()
    )
    if f:
        return f
    # compute next sort_order for section
    max_order = (
        db.session.query(db.func.max(CustomFormField.sort_order))
        .filter_by(project_id=project_id, section=section)
        .scalar()
    )
    next_order = (max_order + 1) if max_order is not None else 1
    f = CustomFormField(
        project_id=project_id,
        section=section,
        label=label,
        field_type=field_type,
        required=required,
        help_text=help_text,
        sort_order=next_order,
    )
    db.session.add(f)
    db.session.commit()
    return f


def ensure_outcome(project_id: int, name: str, outcome_type: str = "dichotomous") -> ProjectOutcome:
    o = (
        ProjectOutcome.query
        .filter(ProjectOutcome.project_id == project_id, db.func.lower(ProjectOutcome.name) == db.func.lower(name))
        .first()
    )
    if o:
        return o
    o = ProjectOutcome(project_id=project_id, name=name, outcome_type=outcome_type)
    db.session.add(o)
    db.session.commit()
    return o


def ensure_study(project: Project, title: str, author: str, year: int) -> Study:
    s = Study.query.filter_by(project_id=project.id, title=title).first()
    if s:
        return s
    # default creator is the first owner membership, if any
    owner_ms = ProjectMembership.query.filter_by(project_id=project.id, role='owner').first()
    created_by = owner_ms.user_id if owner_ms else None
    s = Study(title=title, author=author, year=year, project=project, created_by=created_by)
    db.session.add(s)
    db.session.commit()
    return s


def set_field_value(study: Study, field: CustomFormField, value_obj_or_str):
    sdv = StudyDataValue.query.filter_by(study_id=study.id, form_field_id=field.id).first()
    if isinstance(value_obj_or_str, (dict, list)):
        value_str = json.dumps(value_obj_or_str)
    else:
        value_str = value_obj_or_str
    if sdv:
        sdv.value = value_str
    else:
        sdv = StudyDataValue(study_id=study.id, form_field_id=field.id, value=value_str)
        db.session.add(sdv)


def seed():
    project = get_or_create_project(PROJECT_NAME)

    # Users and memberships
    owner = get_or_create_user(OWNER_EMAIL, OWNER_NAME, OWNER_PASSWORD, is_admin=True)
    member = get_or_create_user(MEMBER_EMAIL, MEMBER_NAME, OWNER_PASSWORD, is_admin=False)
    # Owner membership
    ms_owner = ProjectMembership.query.filter_by(user_id=owner.id, project_id=project.id).first()
    if not ms_owner:
        db.session.add(ProjectMembership(user_id=owner.id, project_id=project.id, role='owner', status='active'))
    # Member membership
    ms_member = ProjectMembership.query.filter_by(user_id=member.id, project_id=project.id).first()
    if not ms_member:
        db.session.add(ProjectMembership(user_id=member.id, project_id=project.id, role='member', status='active'))
    db.session.commit()

    # Ensure a few baseline fields
    age_field = ensure_form_field(project.id, section="Participants", label="Age", field_type="baseline_continuous", help_text="Mean/SD by group")
    female_field = ensure_form_field(project.id, section="Participants", label="Female sex", field_type="baseline_categorical", help_text="Percentage by group")
    reg_field = ensure_form_field(project.id, section="Study Identification", label="Study registration", field_type="text")

    # Ensure predefined outcomes
    out_mortality = ensure_outcome(project.id, "Mortality at 30 days", outcome_type="dichotomous")
    out_bmi = ensure_outcome(project.id, "BMI at baseline", outcome_type="continuous")

    # Studies
    s1 = ensure_study(project, title="Trial A", author="Smith", year=2020)
    s2 = ensure_study(project, title="Trial B", author="Lee", year=2021)

    # Baseline values (Age continuous, Female categorical, Registration text)
    set_field_value(s1, age_field, {"intervention": {"mean": 62.3, "sd": 10.1}, "control": {"mean": 61.8, "sd": 9.7}})
    set_field_value(s2, age_field, {"intervention": {"mean": 59.4, "sd": 8.9}, "control": {"mean": 60.2, "sd": 9.3}})
    set_field_value(s1, female_field, {"intervention": {"percent": 48.0}, "control": {"percent": 47.5}})
    set_field_value(s2, female_field, {"intervention": {"percent": 50.5}, "control": {"percent": 49.0}})
    set_field_value(s1, reg_field, "NCT00000001")
    set_field_value(s2, reg_field, "NCT00000002")

    # Dichotomous outcomes (Mortality)
    # Clear any prior rows to keep idempotence on rerun
    StudyNumericalOutcome.query.filter_by(study_id=s1.id).delete()
    StudyNumericalOutcome.query.filter_by(study_id=s2.id).delete()
    db.session.add(StudyNumericalOutcome(study_id=s1.id, outcome_name=out_mortality.name, events_intervention=12, total_intervention=200, events_control=18, total_control=198))
    db.session.add(StudyNumericalOutcome(study_id=s2.id, outcome_name=out_mortality.name, events_intervention=8, total_intervention=150, events_control=11, total_control=152))

    # Continuous outcomes (BMI)
    StudyContinuousOutcome.query.filter_by(study_id=s1.id).delete()
    StudyContinuousOutcome.query.filter_by(study_id=s2.id).delete()
    db.session.add(StudyContinuousOutcome(study_id=s1.id, outcome_name=out_bmi.name, mean_intervention=27.4, sd_intervention=3.2, n_intervention=200, mean_control=27.1, sd_control=3.0, n_control=198))
    db.session.add(StudyContinuousOutcome(study_id=s2.id, outcome_name=out_bmi.name, mean_intervention=28.0, sd_intervention=2.8, n_intervention=150, mean_control=27.9, sd_control=2.7, n_control=152))

    db.session.commit()
    print(f"Seeded demo project '{project.name}' with 2 studies, baseline fields, and outcomes.")
    print(f"Login as owner: {OWNER_EMAIL} / {OWNER_PASSWORD}")
    print(f"Login as member: {MEMBER_EMAIL} / {OWNER_PASSWORD}")


if __name__ == "__main__":
    with app.app_context():
        seed()
