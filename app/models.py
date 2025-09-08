from app import db

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    studies = db.relationship('Study', backref='project', lazy='dynamic')

class Study(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)

class CustomFormField(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    section = db.Column(db.String(100), nullable=False)
    label = db.Column(db.String(200), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)
    required = db.Column(db.Boolean, default=False, nullable=False)

    project = db.relationship('Project', backref=db.backref('form_fields', lazy='dynamic', cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<CustomFormField {self.label}>'

class StudyDataValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'), nullable=False)
    form_field_id = db.Column(db.Integer, db.ForeignKey('custom_form_field.id'), nullable=False)
    value = db.Column(db.Text, nullable=True)

    study = db.relationship('Study', backref=db.backref('data_values', lazy='dynamic', cascade="all, delete-orphan"))
    form_field = db.relationship('CustomFormField', backref=db.backref('data_values', cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<StudyDataValue {self.value}>'
