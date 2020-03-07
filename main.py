from flask import Flask, render_template, redirect

from sqlalchemy.exc import IntegrityError
from orm.models import User
import forms


from orm import db_session


app = Flask(__name__)
app.config['SECRET_KEY'] = 'TOPSECRET'

db_session.global_init('database/db.sqlite')

@app.route('/', methods=['GET', 'POST'])
def login_page():
    form = forms.LoginForm()
    if form.validate_on_submit():
        return '<h1>Успех!</h1>'
    return render_template('login.html', form=form)


@app.route('/registration', methods=['GET', 'POST'])
def registration_page():
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        user = User(form.name.data,
                    form.email.data,
                    form.password.data)
        sess = db_session.create_session()
        try:
            sess.add(user)
            sess.commit()
        except IntegrityError:
            return render_template('register.html', form=form, message='Пользователь с таким E-mail уже существует!')
        sess.close()
        return redirect('/')
    return render_template('register.html', form=form)


app.run('localhost', 8080, debug=True)
