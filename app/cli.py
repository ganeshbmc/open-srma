import click
from app import db, app as flask_app
from app.models import User, Project, ProjectMembership


@flask_app.cli.command('create-user')
@click.option('--name', prompt=True, help='Full name')
@click.option('--email', prompt=True, help='Email address')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@click.option('--admin', is_flag=True, default=False, help='Create as admin')
def create_user(name, email, password, admin):
    """Create a new user (optionally admin)."""
    em = (email or '').strip().lower()
    if not em:
        click.echo('Email is required')
        return
    existing = User.query.filter(db.func.lower(User.email) == em).first()
    if existing:
        click.echo('User already exists')
        return
    u = User(name=name.strip(), email=em, is_admin=bool(admin))
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    click.echo(f'Created user {u.id}: {u.email} (admin={u.is_admin})')


@flask_app.cli.command('promote-admin')
@click.argument('email')
def promote_admin(email):
    """Promote an existing user to admin by email."""
    em = (email or '').strip().lower()
    u = User.query.filter(db.func.lower(User.email) == em).first()
    if not u:
        click.echo('User not found')
        return
    u.is_admin = True
    db.session.commit()
    click.echo(f'User {u.email} promoted to admin')


@flask_app.cli.command('add-membership')
@click.argument('email')
@click.argument('project_id', type=int)
@click.argument('role', type=click.Choice(['owner', 'member'], case_sensitive=False))
def add_membership(email, project_id, role):
    """Add or update a project membership for a user."""
    em = (email or '').strip().lower()
    u = User.query.filter(db.func.lower(User.email) == em).first()
    if not u:
        click.echo('User not found')
        return
    p = Project.query.get(project_id)
    if not p:
        click.echo('Project not found')
        return
    pm = ProjectMembership.query.filter_by(user_id=u.id, project_id=p.id).first()
    if pm:
        pm.role = role.lower()
        db.session.commit()
        click.echo(f'Updated membership: {u.email} -> Project {p.id} as {pm.role}')
    else:
        pm = ProjectMembership(user_id=u.id, project_id=p.id, role=role.lower(), status='active')
        db.session.add(pm)
        db.session.commit()
        click.echo(f'Added membership: {u.email} -> Project {p.id} as {pm.role}')
