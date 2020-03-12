from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange


STATUS_TO_STR = ['На исполнении', 'Выполнено', 'Ждет проверки']


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
    max_members = IntegerField('Максимальное число участников:', validators=[DataRequired(), NumberRange(2, 50, 'Число должно быть от 2 до 50!')])
    submit = SubmitField('Создать')


class JoinGroupForm(FlaskForm):
    id = StringField('Уникальный ID группы:', validators=[DataRequired()])
    submit = SubmitField('Войти')


class CreateTaskForm(FlaskForm):
    name = StringField('Название:', validators=[DataRequired()])
    performer_id = SelectField('Исполнитель:', coerce=int, validators=[DataRequired()])  # choices must be filled in creation time!
    priority = SelectField('Приоритет:', choices=[(0, 'Высокий'), (1, 'Средний'), (2, 'Низкий')], coerce=int, default=1)
    description = TextAreaField('Описание:', validators=[DataRequired()])
    status = SelectField('Статус:', choices=[(0, STATUS_TO_STR[0]), (1, STATUS_TO_STR[1]), (2, STATUS_TO_STR[2])], coerce=int, default=0)
    submit = SubmitField('Применить')
