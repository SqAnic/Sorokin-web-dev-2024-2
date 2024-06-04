from flask import Flask, render_template, redirect, url_for, request, make_response, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from my_sqldb import MyDb
import mysql.connector
import hashlib
import re

app = Flask(__name__)

app.config.from_pyfile('config.py')

db = MyDb(app)

login_manager = LoginManager();

login_manager.init_app(app);

login_manager.login_view = 'login'
login_manager.login_message = 'Доступ к данной странице есть только у авторизованных пользователей '
login_manager.login_message_category = 'warning'

def get_roles():
    connection = db.connect()
    cursor = connection.cursor(named_tuple=True)
    try:
        query = ('SELECT * FROM roles')
        cursor.execute(query)
        roles = cursor.fetchall()
    except:
        db.connect().rollback()
        flash('Неверные логин или пароль', 'danger')
    finally:
        cursor.close()


    return roles

class User(UserMixin):
    def __init__(self,user_id,user_login):
        self.id = user_id
        self.login = user_login
        

@login_manager.user_loader
def load_user(user_id):
    cursor= db.connect().cursor(named_tuple=True)
    query = ('SELECT * FROM users WHERE id=%s')
    cursor.execute(query,(user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
       return User(user.id,user.login)
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == "POST":
        login = request.form.get('login')
        password = request.form.get('password')
        remember = request.form.get('remember')
        connection = db.connect()
        cursor = connection.cursor(named_tuple=True)
        try:
            query = ('SELECT * FROM users WHERE login=%s and password_hash=SHA2(%s,256) ')
            cursor.execute(query,(login, password))
            user_data = cursor.fetchone()
            if user_data:
                login_user(User(user_data.id,user_data.login),remember=remember)
                flash('Вы успешно прошли аутентификацию', 'success')
                return redirect(url_for('index'))
        except:
            db.connect().rollback()
            flash('Неверные логин или пароль', 'danger')
        finally:
            cursor.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/list_users')
def list_users():
    connection = db.connect()
    cursor = connection.cursor(named_tuple=True)
    try:
        query = ('SELECT * FROM users')
        cursor.execute(query)
        users = cursor.fetchall()
    except:
        db.connect().rollback()
        flash('Ошибка', 'danger')
    finally:
        cursor.close()
        
    return render_template('list_users.html', users = users)

@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    form_infa = {}
    errors = {}
    if request.method == "POST": 
        first_name = request.form.get('name')
        form_infa['first_name'] = first_name
        second_name = request.form.get('lastname')
        form_infa['second_name'] = second_name
        middle_name = request.form.get('middlename')
        form_infa['middlename'] = middle_name
        login = request.form.get('login')
        form_infa['login'] = login
        password = request.form.get('password')
        
        role_id = request.form.get('role')
        
        # Проверка полей на пустоту
        if not first_name:
            errors['name'] = 'Имя не может быть пустым.'
        if not second_name:
            errors['lastname'] = 'Фамилия не может быть пустой.'
        if not middle_name:
            errors['middlename'] = 'Отчество не может быть пустым.'
        if not login:
            errors['login'] = 'Логин не может быть пустым.'
        if not password:
            errors['password'] = 'Пароль не может быть пустым.'
        
        # Валидация логина
        if login and not re.match(r'^[a-zA-Z0-9]{5,}$', login):
            errors['login'] = errors.get('login', '') + ' Логин должен состоять только из латинских букв и цифр и иметь длину не менее 5 символов.'
        
        # Валидация пароля
        if password:
            if len(password) < 8 or len(password) > 128:
                errors['password'] = errors.get('password', '') + ' Пароль должен быть не менее 8 и не более 128 символов.'
            if not re.search(r'[A-Z]', password):
                errors['password'] = errors.get('password', '') + ' Пароль должен содержать как минимум одну заглавную букву.'
            if not re.search(r'[a-z]', password):
                errors['password'] = errors.get('password', '') + ' Пароль должен содержать как минимум одну строчную букву.'
            if not re.search(r'[0-9]', password):
                errors['password'] = errors.get('password', '') + ' Пароль должен содержать как минимум одну цифру.'
            if re.search(r'\s', password):
                errors['password'] = errors.get('password', '') + ' Пароль не должен содержать пробелов.'
            if not re.match(r'^[a-zA-Zа-яА-Я0-9~!?@#$%^&*_\-+()[\]{}><\/\\|"\'.,:;]*$', password):
                errors['password'] = errors.get('password', '') + ' Пароль содержит недопустимые символы.'
        
        if errors:
            roles = get_roles()
            return render_template('create_user.html', roles=roles, errors=errors, form_infa=form_infa)
        
        try:
            connection = db.connect()
            cursor = connection.cursor(named_tuple=True)
            query = 'INSERT INTO users (login, password_hash, first_name, second_name, middle_name, role_id) values (%s, SHA2(%s,256), %s, %s, %s, %s)'
            cursor.execute(query, (login, password, first_name, second_name, middle_name, role_id))
            connection.commit()
            flash('Вы успешно зарегистрировали пользователя', 'success')
            return redirect(url_for('list_users'))
        except mysql.connector.errors.DatabaseError:
            connection.rollback()
            flash('Ошибка при регистрации', 'danger')
        finally:
            cursor.close()
            connection.close()
        
    roles = get_roles()
    return render_template('create_user.html', roles=roles, errors=errors, form_infa=form_infa)


@app.route('/show_user/<int:user_id>')
@login_required
def show_user(user_id):
    connection = db.connect()
    cursor = connection.cursor(named_tuple=True)
    try:
        query = ('SELECT users.*, roles.name as role_name FROM users LEFT JOIN roles ON users.role_id = roles.id WHERE users.id = %s')
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
    except:
        db.connect().rollback()
        flash('Ошибка при выводе списка пользователей', 'danger')
    finally:
        cursor.close()
    
    return render_template('show_user.html', user = user )


@app.route('/edit_user/<int:user_id>', methods=['GET','POST'])
@login_required
def edit_user(user_id):
    connection = db.connect()
    cursor = connection.cursor(named_tuple=True)
    try:
        query = ('SELECT users.*, roles.name as role_name FROM users LEFT JOIN roles ON users.role_id = roles.id WHERE users.id = %s')
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
    except:
        db.connect().rollback()
        flash('Ошибка при редактировании пользователя', 'danger')

    if request.method == "POST":
        first_name = request.form.get('name')
        second_name = request.form.get('lastname')
        middle_name = request.form.get('middlename')
        try:
            query = ('UPDATE users SET first_name=%s, second_name=%s, middle_name=%s where id=%s;')
            cursor.execute(query,(first_name,  second_name, middle_name, user_id))
            db.connect().commit()
            flash('Вы успешно обновили пользователя', 'success')
            return redirect(url_for('list_users'))
        except mysql.connector.errors.DatabaseError:
            db.connect().rollback()
            flash('Ошибка при обновлении', 'danger')
        finally:
            cursor.close()

    return render_template('edit_user.html', user = user)

@app.route('/delete_user/<int:user_id>', methods=["POST"])
@login_required
def delete_user(user_id):
    connection = db.connect()
    cursor = connection.cursor(named_tuple=True)
    try:
        query = ('DELETE FROM users WHERE id=%s')
        cursor.execute(query, (user_id,))
        db.connect().commit()
        flash('Удаление успешно', 'success')
    except:
        db.connect().rollback()
        flash('Ошибка при удалении пользователя', 'danger')
    finally:
        cursor.close()

    return redirect(url_for('list_users'))

@app.route('/change_pass', methods=['GET', 'POST'])
@login_required
def change_pass():
    if request.method == "POST":
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        new1_password = request.form.get('new1_password')
        msg = ''

        # Проверка нового пароля
        if len(new_password) < 8 or len(new_password) > 128 or not any(char.islower() for char in new_password) or not any(char.isupper() for char in new_password) or not any(char.isdigit() for char in new_password) or not new_password.isalnum() or ' ' in new_password:
            msg += 'Пароль должен удовлетворять всем указанным требованиям. '
        
        # Проверка совпадения паролей
        if new1_password != new_password:
            msg += 'Пароли не совпадают. '
        
        if msg != '':
            flash(msg, 'danger')
            return render_template('change_pass.html')

        try:
            conn = db.connect()  # Открываем соединение
            cursor = conn.cursor(named_tuple=True)  # Создаем курсор
            
            # Получаем login текущего пользователя
            user_login = current_user.login
            
            # Проверка старого пароля
            query = 'SELECT password_hash FROM users WHERE login=%s'
            cursor.execute(query, (user_login,))
            user = cursor.fetchone()
            
            if user is None:
                flash('Ошибка пользователя', 'danger')
                return render_template('change_pass.html')

            if user.password_hash != hashlib.sha256(old_password.encode()).hexdigest():
                flash('Старый пароль неверен', 'danger')
                return render_template('change_pass.html')

            # Обновляем пароль
            query = 'UPDATE users SET password_hash=%s WHERE login=%s'
            cursor.execute(query, (hashlib.sha256(new_password.encode()).hexdigest(), user_login))
            conn.commit()  # Фиксируем изменения

            flash('Пароль успешно изменен', 'success')
        except Exception as e:
            conn.rollback()
            flash('Ошибка при изменении пароля: ' + str(e), 'danger')
        finally:
            cursor.close()  # Закрываем курсор
            conn.close()    # Закрываем соединение

    return render_template('change_pass.html')
