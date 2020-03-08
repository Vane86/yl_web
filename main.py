from flask import Flask, render_template, redirect
from sqlalchemy.exc import IntegrityError
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

from orm.models import User, Group
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
    return render_template('login.html', form=form, message=message)


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
            return render_template('register.html', form=form, message='Пользователь с таким E-mail уже существует!')
        except Exception:
            return render_template('register.html', form=form, message='Произошла неизвестная ошибка.')
        return redirect('/login')
    return render_template('register.html', form=form)


@app.route('/')
@app.route('/private')
@login_required
def private_page():
    return render_template('private.html', title='Личный кабинет', len=len)


@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    form = forms.CreateGroupForm()
    if form.validate_on_submit():
        group = Group(form.name.data,
                      form.max_members.data,
                      current_user.id)
        group.users.append(current_user)
        db_session.global_session.commit()
        return redirect('/private')
    return render_template('private_create_group.html', form=form)


@app.route('/join_group')
@login_required
def join_group():
    return '<h1>Войти в группу!</h1>'


app.run('localhost', 8080, debug=True)
