from app import app, db
from app.models import Project, Study, ProjectMembership

NAME = "Demo SRMA"

def main():
    with app.app_context():
        p = Project.query.filter_by(name=NAME).first()
        if p:
            # Explicitly delete child objects to satisfy FKs (since ON DELETE CASCADE isn't set)
            try:
                # Delete studies (cascades to outcomes and data_values via ORM backrefs)
                for s in p.studies.all() if hasattr(p.studies, 'all') else []:
                    db.session.delete(s)
                # Delete form fields (cascades to data_values via ORM backrefs)
                if hasattr(p, 'form_fields'):
                    for f in p.form_fields.all():
                        db.session.delete(f)
                # Delete memberships for the project
                for ms in p.memberships.all() if hasattr(p, 'memberships') else []:
                    db.session.delete(ms)
                db.session.flush()
            except Exception:
                pass
            db.session.delete(p)
            db.session.commit()
            print(f"Deleted project '{NAME}'.")
        else:
            print(f"Project '{NAME}' not found.")


if __name__ == "__main__":
    main()
