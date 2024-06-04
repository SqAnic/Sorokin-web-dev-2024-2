from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from my_sqldb import MyDb
import mysql.connector


app = Flask(__name__)

app.config.from_pyfile('config.py')

db = MyDb(app)

from auth import bp as bp_auth, init_login_manage
from logs import bp as bp_logs
from auth import checkRole

app.register_blueprint(bp_auth)
app.register_blueprint(bp_logs)

init_login_manage(app)

@app.before_request
def log_request_info():
    if request.endpoint=="static":
        return
    path=request.path
    user_id=getattr(current_user,"id",None)
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('INSERT INTO visit_logs (user_id,path) VALUES (%s,%s)')
        cursor.execute(query,(user_id,path))
        db.connect().commit()

def get_roles():
    with db.connect().cursor(named_tuple=True) as cursor:
            query = ('SELECT * FROM roles')
            cursor.execute(query)
            roles = cursor.fetchall()
    return roles


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/list_users')
@login_required
def list_users():
    with db.connect().cursor(named_tuple=True) as cursor:
            query = ('SELECT * FROM users')
            cursor.execute(query)
            users = cursor.fetchall()
    return render_template('list_users.html', users = users)

@app.route('/create_user', methods=['GET', 'POST'])
@login_required
@checkRole('create')
def create_user():
    if request.method == "POST":
        first_name = request.form.get('name')
        second_name = request.form.get('lastname')
        middle_name = request.form.get('middlename')
        login = request.form.get('login')
        password = request.form.get('password')
        role_id = request.form.get('role')
        try:
            with db.connect().cursor(named_tuple=True) as cursor:
                query = ('INSERT INTO users (login, password_hash, first_name, second_name, middle_name, role_id) '
                         'VALUES (%s, SHA2(%s,256), %s, %s, %s, %s)')
                cursor.execute(query, (login, password, first_name, second_name, middle_name, role_id))
                db.connect().commit()
                flash('Вы успешно зарегистрировали пользователя', 'success')
                return redirect(url_for('list_users'))
        except mysql.connector.errors.DatabaseError:
            db.connect().rollback()
            flash('Ошибка при регистрации', 'danger')

    roles = get_roles()
    return render_template('create_user.html', roles=roles, current_user=current_user)


@app.route('/show_user/<int:user_id>')
@login_required
@checkRole('show')
def show_user(user_id):
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT users.*, roles.name as role_name FROM users LEFT JOIN roles ON users.role_id = roles.id WHERE users.id = %s')
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
    return render_template('show_user.html', user=user)


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@checkRole('edit')
def edit_user(user_id):
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT users.*, roles.name as role_name FROM users LEFT JOIN roles ON users.role_id = roles.id WHERE users.id = %s')
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

    if request.method == "POST":
        first_name = request.form.get('name')
        second_name = request.form.get('lastname')
        middle_name = request.form.get('middlename')
        role_id = user.role_id  # Role cannot be changed by a regular user

        if current_user.is_admin():
            role_id = request.form.get('role')

        try:
            with db.connect().cursor(named_tuple=True) as cursor:
                query = ('UPDATE users SET first_name=%s, second_name=%s, middle_name=%s, role_id=%s WHERE id=%s')
                cursor.execute(query, (first_name, second_name, middle_name, role_id, user_id))
                db.connect().commit()
                flash('Вы успешно обновили пользователя', 'success')
                return redirect(url_for('list_users'))
        except mysql.connector.errors.DatabaseError:
            db.connect().rollback()
            flash('Ошибка при обновлении', 'danger')
    roles = get_roles()
    return render_template('edit_user.html', user=user, roles=roles, current_user=current_user)


@app.route('/delete_user/<int:user_id>', methods=["POST"])
@login_required
@checkRole('delete')
def delete_user(user_id):
    with db.connect().cursor(named_tuple=True) as cursor:
        try:
            query = ('DELETE FROM users WHERE id=%s')
            cursor.execute(query, (user_id,))
            db.connect().commit()
            flash('Удаление успешно', 'success')
        except:
            db.connect().rollback()
            flash('Ошибка при удалении пользователя', 'danger')
    return redirect(url_for('list_users'))
