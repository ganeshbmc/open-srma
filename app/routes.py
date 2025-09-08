from flask import render_template, flash, redirect, url_for
from app import app, db
from app.forms import ProjectForm
from app.models import Project

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
