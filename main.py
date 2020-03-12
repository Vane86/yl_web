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
    s = db_session.create_session()
    user = s.query(User).filter(User.id == user_id).first()
    s.close()
    return user


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    logout_user()
    message = ''
    form = forms.LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        s = db_session.create_session()
        user = s.query(User).filter(User.email == email).first()
        if not user:
            message = 'Такого пользователя не существует!'
        elif not user.check_password(form.password.data):
            message = 'Неверный пароль!'
        else:
            login_user(user, remember=form.remember_me.data)
            resp = redirect('/private')
            s.close()
            return resp
    resp = render_template('login.html', title='Вход в Famtam', form=form, message=message)
    return resp


@app.route('/register', methods=['GET', 'POST'])
def registration_page():
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        user = User(form.name.data,
                    form.email.data,
                    form.password.data)
        s = db_session.create_session()
        try:
            s.add(user)
            s.commit()
        except IntegrityError:
            return render_template('register.html', title='Регистрация', form=form, message='Пользователь с таким E-mail уже существует!')
        except Exception as e:
            print(e)
            return render_template('register.html', title='Регистрация', form=form, message='Произошла неизвестная ошибка.')
        finally:
            s.close()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/')
@app.route('/private')
@login_required
def private_page():
    s = db_session.create_session()
    s.add(current_user)
    s.merge(current_user)
    resp = render_template('private.html', title='Личный кабинет', len=len)
    s.close()
    return resp


@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group_page():
    form = forms.CreateGroupForm()
    s = db_session.create_session()
    if form.validate_on_submit():
        group = Group(form.name.data,
                      form.max_members.data,
                      current_user.id)
        group.users.append(current_user)
        s.merge(group)
        s.commit()
        resp = redirect('/private')
        s.close()
        return resp
    s.add(current_user)
    s.merge(current_user)
    resp = render_template('private_create_group.html', title='Создание группы', form=form)
    s.close()
    return resp


@app.route('/join_group', methods=['GET', 'POST'])
@login_required
def join_group_page():
    form = forms.JoinGroupForm()
    s = db_session.create_session()
    if form.validate_on_submit():
        s.add(current_user)
        s.merge(current_user)
        if not form.id.data.isdigit():
            resp = render_template('private_join_group.html', title='Присоединиться к группе', form=form, message='ID должен быть целым числом!')
            s.close()
            return resp
        group = s.query(Group).filter(Group.id == int(form.id.data)).first()
        if not group:
            resp = render_template('private_join_group.html', title='Присоединиться к группе', form=form, message='Такой группы не существует!')
            s.close()
            return resp
        if len(group.users) == group.max_members:
            resp = render_template('private_join_group.html', title='Присоединиться к группе', form=form, message='В группе достигнуто максимальное количество участников!')
            s.close()
            return resp
        if current_user in group.users:
            resp = render_template('private_join_group.html', title='Присоединиться к группе', form=form, message='Вы уже состоите в этой группе!')
            s.close()
            return resp
        group.users.append(current_user)
        s.merge(group)
        s.commit()
        s.close()
        return redirect('/private')
    resp = render_template('private_join_group.html', title='Присоединиться к группе', form=form)
    s.close()
    return resp


@app.route('/group/<int:group_id>')
@login_required
def group_page(group_id):
    s = db_session.create_session()
    group = s.query(Group).filter(Group.id == group_id).first()
    if not group:
        s.close()
        abort(404)
    resp = render_template('private_group.html', title=group.name, group=group, len=len, STATUS_TO_STR=forms.STATUS_TO_STR)
    s.close()
    return resp


@app.route('/group/<int:group_id>/create_task', methods=['GET', 'POST'])
@login_required
def create_task_page(group_id):
    s = db_session.create_session()
    group = s.query(Group).filter(Group.id == group_id).first()
    if not group:
        s.close()
        abort(404)
    form = forms.CreateTaskForm()
    form.performer_id.choices = [(user.id, f'{user.name} (id: {user.id})') for user in group.users if user.id != current_user.id]
    if form.validate_on_submit():
        task = Task(name=form.name.data, author_id=current_user.id, performer_id=form.performer_id.data,
                    group_id=group_id, priority=form.priority.data, description=form.description.data)
        s.add(task)
        s.commit()
        s.close()
        return redirect(f'/group/{group_id}')
    resp = render_template('private_create_edit_task.html', title='Создание задачи', group=group, form=form, edit=False)
    s.close()
    return resp


@app.route('/group/<int:group_id>/task/<int:task_id>')
@login_required
def task_page(group_id, task_id):
    s = db_session.create_session()
    group = s.query(Group).filter(Group.id == group_id).first()
    if not group or task_id not in set(task.id for task in group.tasks):
        s.close()
        abort(404)
    task = s.query(Task).filter(Task.id == task_id).first()
    resp = render_template('private_task.html', title=f'Задача: {task.name}', group=group, task=task, STATUS_TO_STR=forms.STATUS_TO_STR)
    s.close()
    return resp


@app.route('/group/<int:group_id>/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task_page(group_id, task_id):
    s = db_session.create_session()
    group = s.query(Group).filter(Group.id == group_id).first()
    if not group or task_id not in set(task.id for task in group.tasks):
        s.close()
        abort(404)
    task = s.query(Task).filter(Task.id == task_id).first()
    if current_user.id != task.author_id:
        s.close()
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
        s.merge(task)
        s.commit()
        s.close()
        return redirect(f'/group/{group_id}')
    resp = render_template('private_create_edit_task.html', title='Редактирование задачи', group=group, form=form, edit=True)
    s.close()
    return resp


@app.route('/group/<int:group_id>/finish_task/<int:task_id>')
@login_required
def finish_task(group_id, task_id):
    s = db_session.create_session()
    group = s.query(Group).filter(Group.id == group_id).first()
    if not group or task_id not in set(task.id for task in group.tasks):
        s.close()
        abort(404)

    task = s.query(Task).filter(Task.id == task_id).first()
    if current_user.id != task.performer_id:
        s.close()
        abort(403)

    task.status = 2
    s.merge(task)
    s.commit()
    s.close()
    return redirect(f'/group/{group_id}')


@app.route('/private/settings', methods=['GET', 'POST'])
@login_required
def private_settings_page():
    form = forms.SettingsForm()
    s = db_session.create_session()
    if request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
    if form.validate_on_submit():
        if form.name.data:
            current_user.name = form.name.data
        if form.email.data:
            current_user.email = form.email.data
        if form.password.data:
            current_user.set_password(form.password.data)
        s.merge(current_user)
        s.commit()
        s.close()
        return redirect('/private')
    resp = render_template('private_settings.html', title='Настройки', form=form)
    s.close()
    return resp


if __name__ == '__main__':
    app.run('localhost', 8080)
