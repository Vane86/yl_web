from flask import Flask, render_template, redirect, abort, request
from sqlalchemy.exc import IntegrityError
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

from orm.models import User, Group, Task
import forms


from orm import db_session


app = Flask(__name__)
app.config['SECRET_KEY'] = 'TOPSECRET'

db_session.global_init('database/db.sqlite')
login_manager = LoginManager(app)
login_manager.login_view = '/login'


@login_manager.user_loader
def load_user(user_id):
    user = db_session.global_session.query(User).filter(User.id == user_id).first()
    return user


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    logout_user()
    message = ''
    form = forms.LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        user = db_session.global_session.query(User).filter(User.email == email).first()
        if not user:
            message = 'Такого пользователя не существует!'
        elif not user.check_password(form.password.data):
            message = 'Неверный пароль!'
        else:
            login_user(user, remember=form.remember_me.data)
            return redirect('/private')
    return render_template('login.html', title='Вход в Famtam', form=form, message=message)


@app.route('/register', methods=['GET', 'POST'])
def registration_page():
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        user = User(form.name.data,
                    form.email.data,
                    form.password.data)
        try:
            db_session.global_session.add(user)
            db_session.global_session.commit()
        except IntegrityError:
            return render_template('register.html', title='Регистрация', form=form, message='Пользователь с таким E-mail уже существует!')
        except Exception as e:
            print(e)
            return render_template('register.html', title='Регистрация', form=form, message='Произошла неизвестная ошибка.')
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/')
@app.route('/private')
@login_required
def private_page():
    return render_template('private.html', title='Личный кабинет', len=len)


@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group_page():
    form = forms.CreateGroupForm()
    if form.validate_on_submit():
        group = Group(form.name.data,
                      form.max_members.data,
                      current_user.id)
        group.users.append(current_user)
        db_session.global_session.commit()
        return redirect('/private')
    return render_template('private_create_group.html', title='Создание группы', form=form)


@app.route('/join_group', methods=['GET', 'POST'])
@login_required
def join_group_page():
    form = forms.JoinGroupForm()
    if form.validate_on_submit():
        if not form.id.data.isdigit():
            return render_template('private_join_group.html', title='Присоединиться к группе', form=form, message='ID должен быть целым числом!')
        group = db_session.global_session.query(Group).filter(Group.id == int(form.id.data)).first()
        if not group:
            return render_template('private_join_group.html', title='Присоединиться к группе', form=form, message='Такой группы не существует!')
        if len(group.users) == group.max_members:
            return render_template('private_join_group.html', title='Присоединиться к группе', form=form, message='В группе достигнуто максимальное количество участников!')
        if current_user in group.users:
            return render_template('private_join_group.html', title='Присоединиться к группе', form=form, message='Вы уже состоите в этой группе!')
        group.users.append(current_user)
        db_session.global_session.commit()
        return redirect('/private')
    return render_template('private_join_group.html', title='Присоединиться к группе', form=form)


@app.route('/group/<int:group_id>')
@login_required
def group_page(group_id):
    group = db_session.global_session.query(Group).filter(Group.id == group_id).first()
    if not group:
        abort(404)
    return render_template('private_group.html', title=group.name, group=group, len=len, STATUS_TO_STR=forms.STATUS_TO_STR)


@app.route('/group/<int:group_id>/create_task', methods=['GET', 'POST'])
@login_required
def create_task_page(group_id):
    group = db_session.global_session.query(Group).filter(Group.id == group_id).first()
    if not group:
        abort(404)
    form = forms.CreateTaskForm()
    form.performer_id.choices = [(user.id, f'{user.name} (id: {user.id})') for user in group.users if user.id != current_user.id]
    if form.validate_on_submit():
        # TODO:
        # Check all possible inputs
        task = Task(name=form.name.data, author_id=current_user.id, performer_id=form.performer_id.data,
                    group_id=group_id, priority=form.priority.data, description=form.description.data)
        db_session.global_session.add(task)
        db_session.global_session.commit()
        return redirect('/group/{{group_id}}')
    return render_template('private_create_edit_task.html', title='Создание задачи', group=group, form=form, edit=False)


@app.route('/group/<int:group_id>/task/<int:task_id>')
@login_required
def task_page(group_id, task_id):
    group = db_session.global_session.query(Group).filter(Group.id == group_id).first()
    if not group or task_id not in set(task.id for task in group.tasks):
        abort(404)
    task = db_session.global_session.query(Task).filter(Task.id == task_id).first()
    return render_template('private_task.html', title=f'Задача: {task.name}', group=group, task=task, STATUS_TO_STR=forms.STATUS_TO_STR)


@app.route('/group/<int:group_id>/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task_page(group_id, task_id):
    group = db_session.global_session.query(Group).filter(Group.id == group_id).first()
    if not group or task_id not in set(task.id for task in group.tasks):
        abort(404)

    task = db_session.global_session.query(Task).filter(Task.id == task_id).first()
    if current_user.id != task.author_id:
        abort(403)
    form = forms.CreateTaskForm()
    form.performer_id.choices = [(user.id, f'{user.name} (id: {user.id})') for user in group.users if user.id != current_user.id]
    if request.method == 'GET':
        form.name.data = task.name
        form.performer_id.data = task.performer_id
        form.priority.data = task.priority
        form.description.data = task.description
    if form.validate_on_submit():
        task.name = form.name.data
        task.performer_id = form.performer_id.data
        task.priority = form.priority.data
        task.description = form.description.data
        task.status = form.status.data
        db_session.global_session.commit()
        return redirect(f'/group/{group_id}')
    return render_template('private_create_edit_task.html', title='Редактирование задачи', group=group, form=form, edit=True)


@app.route('/group/<int:group_id>/finish_task/<int:task_id>')
@login_required
def finish_task(group_id, task_id):
    group = db_session.global_session.query(Group).filter(Group.id == group_id).first()
    if not group or task_id not in set(task.id for task in group.tasks):
        abort(404)

    task = db_session.global_session.query(Task).filter(Task.id == task_id).first()
    if current_user.id != task.performer_id:
        abort(403)

    task.status = 2
    db_session.global_session.commit()
    return redirect(f'/group/{group_id}')


app.run('localhost', 8080, debug=True)
