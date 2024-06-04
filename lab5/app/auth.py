from functools import wraps
from check_rights import CheckRights
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask import Blueprint, render_template, redirect, url_for, request,flash
from app import db


bp = Blueprint('auth', __name__, url_prefix='/auth')

ADMIN_ROLE_ID=1

def init_login_manage(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Доступ к данной странице есть только у авторизованных пользователей '
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(load_user)


class User(UserMixin):
    def __init__(self,user_id,user_login, role_id):
        self.id = user_id
        self.login = user_login
        self.role_id = role_id


    def is_admin(self):
        return ADMIN_ROLE_ID == self.role_id

    def can(self, action, record=None):
        check_rights = CheckRights(record)
        method = getattr(check_rights, action, None)
        if method:
            return method()
        return False


def load_user(user_id):
    cursor= db.connect().cursor(named_tuple=True)
    query = ('SELECT * FROM users WHERE id=%s')
    cursor.execute(query,(user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
       return User(user.id,user.login, user.role_id)
    return None


def checkRole(action):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if current_user.can(action):
                return f(*args, **kwargs)
            flash("У вас нет доступа к этой странице", "danger")
            return redirect(url_for('index'))
        return wrapper
    return decorator


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@bp.route('/login',methods=['GET','POST'])
def login():
    if request.method == "POST":
        login = request.form.get('login')
        password = request.form.get('password')
        remember = request.form.get('remember')
        with db.connect().cursor(named_tuple=True) as cursor:
            query = ('SELECT * FROM users WHERE login=%s and password_hash=SHA2(%s,256) ')
            cursor.execute(query,(login, password))
            user_data = cursor.fetchone()
            if user_data:
                    login_user(User(user_data.id,user_data.login, user_data.role_id),remember=remember)
                    flash('Вы успешно прошли аутентификацию', 'success')
                    return redirect(url_for('index'))
        flash('Неверные логин или пароль', 'danger')
    return render_template('login.html')
