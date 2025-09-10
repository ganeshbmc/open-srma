from app import db

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    studies = db.relationship('Study', backref='project', lazy='dynamic')
    # Project-level predefined outcomes
    outcomes = db.relationship(
        'ProjectOutcome',
        backref='project',
        lazy='dynamic',
        cascade="all, delete-orphan",
    )

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
    section_order = db.Column(db.Integer, nullable=True)  # preserves original section order
    label = db.Column(db.String(200), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)
    required = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, nullable=True)
    help_text = db.Column(db.Text, nullable=True)

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

class StudyNumericalOutcome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'), nullable=False)
    outcome_name = db.Column(db.String(200), nullable=False)
    events_intervention = db.Column(db.Integer, nullable=True)
    total_intervention = db.Column(db.Integer, nullable=True)
    events_control = db.Column(db.Integer, nullable=True)
    total_control = db.Column(db.Integer, nullable=True)

    study = db.relationship('Study', backref=db.backref('numerical_outcomes', lazy='dynamic', cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<StudyNumericalOutcome {self.outcome_name} for Study {self.study_id}>'


class ProjectOutcome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    outcome_type = db.Column(db.String(50), nullable=False, default='dichotomous')  # future: continuous, etc.

    def __repr__(self):
        return f'<ProjectOutcome {self.name} ({self.outcome_type})>'


class StudyContinuousOutcome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'), nullable=False)
    outcome_name = db.Column(db.String(200), nullable=False)
    mean_intervention = db.Column(db.Float, nullable=True)
    sd_intervention = db.Column(db.Float, nullable=True)
    n_intervention = db.Column(db.Integer, nullable=True)
    mean_control = db.Column(db.Float, nullable=True)
    sd_control = db.Column(db.Float, nullable=True)
    n_control = db.Column(db.Integer, nullable=True)

    study = db.relationship('Study', backref=db.backref('continuous_outcomes', lazy='dynamic', cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<StudyContinuousOutcome {self.outcome_name} for Study {self.study_id}>'
