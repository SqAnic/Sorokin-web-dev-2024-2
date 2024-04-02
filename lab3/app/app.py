from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
app = Flask(__name__)
application = app

# app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config.from_pyfile('configure.py')

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к этой странице нужно залогиниться'
login_manager.login_message_category = 'alert-warning'


login_manager.init_app(application)

class User(UserMixin):
    def __init__(self, login, user_id):
        self.login = login
        self.id = user_id 
    

@login_manager.user_loader
def load_user(user_id):
    users = user_list()
    for user in users:
        if user["id"] == user_id:
            return User(user["login"], user_id)
    return None

def user_list():
    return [{"id": "1", "login": "Egor", "password": "1111"}]

@app.route('/')
def index():
    msg = 'Hello'
    return render_template('index.html', qq=msg)

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":    
        name = request.form.get("login", False)
        password = request.form.get("password", False)
        remember_me = request.form.get('remember_me') == "on"
        db = user_list()
        text = "Ошибка логина"
        category = "alert-danger"
        for record in db:
            if record["login"] == name and record["password"] == password:
                user = User(record["login"], record["id"])
                login_user(user, remember=remember_me)
                flash("Успешно", "alert-success")
            
                return redirect(request.args.get("next") or url_for("index"))
            
        flash("Введены некорректные данные", "alert-danger")
        
    return render_template('flask_login.html')


@app.route('/secret')
@login_required
def secret():
    if not current_user.is_authenticated:
        flash("Для доступа к этой странице нужно залогиниться", "alert-info")
        return redirect(url_for("login")) 
    return render_template("secret.html")


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route('/counter')
def counter():
    if "counter" in session:
        session["counter"] += 1
    else:
        session["counter"] = 1 

    return render_template('counter.html')

# python3 -m venv ve
# . ve/bin/activate -- Linux
# ve\Scripts\activate -- Windows
# pip install flask python-dotenv