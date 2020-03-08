from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo


class RegistrationForm(FlaskForm):
    name = StringField('Имя:', validators=[DataRequired()])
    email = StringField('E-mail:', validators=[DataRequired(), Email('Некорректный адрес')])
    password = PasswordField('Пароль:', validators=[DataRequired()])
    check_password = PasswordField('Повторите пароль:',
                                   validators=[EqualTo(fieldname='password', message='Пароли должны совпадать!')])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = StringField('E-mail:', validators=[DataRequired(), Email('Некорректный адрес')])
    password = PasswordField('Пароль:', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class CreateGroupForm(FlaskForm):
    name = StringField('Имя группы:', validators=[DataRequired()])
    max_members = IntegerField('Максимальное число участников:', validators=[DataRequired()])
    submit = SubmitField('Создать')
