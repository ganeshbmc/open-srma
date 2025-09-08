from flask import render_template, flash, redirect, url_for
from app import app, db
from app.forms import ProjectForm, StudyForm
from app.models import Project, Study

@app.route('/')
def index():
    projects = Project.query.all()
    return render_template('index.html', projects=projects)

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(name=form.name.data, description=form.description.data)
        db.session.add(project)
        db.session.commit()
        flash('Project created successfully!')
        return redirect(url_for('index'))
    return render_template('add_project.html', form=form)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    studies = project.studies.all()
    return render_template('project_detail.html', project=project, studies=studies)

@app.route('/project/<int:project_id>/add_study', methods=['GET', 'POST'])
def add_study(project_id):
    project = Project.query.get_or_404(project_id)
    form = StudyForm()
    if form.validate_on_submit():
        study = Study(title=form.title.data, author=form.author.data, year=form.year.data, project=project)
        db.session.add(study)
        db.session.commit()
        flash('Study added successfully!')
        return redirect(url_for('project_detail', project_id=project.id))
    return render_template('add_study.html', form=form, project=project)
