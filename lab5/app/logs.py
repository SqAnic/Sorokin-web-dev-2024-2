from functools import wraps
from check_rights import CheckRights
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask import Blueprint, render_template, redirect, send_file, url_for, request,flash
from app import db
from math import ceil
import io
from auth import checkRole

bp = Blueprint('logs', __name__, url_prefix='/logs')

PER_PAGE = 5

@bp.route("/visits")
@login_required
def show_user_logs():
    page = int(request.args.get('page', 1))
    if current_user.is_admin():
        query = ('SELECT vl.*, u.first_name, u.second_name, u.middle_name '
                 'FROM visit_logs vl LEFT JOIN users u ON vl.user_id = u.id '
                 'ORDER BY vl.created_at DESC LIMIT %s OFFSET %s')
        query_count = ('SELECT COUNT(*) as count FROM visit_logs')
        params = (PER_PAGE, (page - 1) * PER_PAGE)
    else:
        query = ('SELECT vl.*, u.first_name, u.second_name, u.middle_name '
                 'FROM visit_logs vl LEFT JOIN users u ON vl.user_id = u.id '
                 'WHERE vl.user_id = %s ORDER BY vl.created_at DESC LIMIT %s OFFSET %s')
        query_count = ('SELECT COUNT(*) as count FROM visit_logs WHERE user_id = %s')
        params = (current_user.id, PER_PAGE, (page - 1) * PER_PAGE)
        
    with db.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(query, params)
        logs = cursor.fetchall()
    
    with db.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(query_count, (current_user.id,) if not current_user.is_admin() else ())
        count = cursor.fetchone().count

    return render_template("log/visits.html", logs=logs, count=ceil(count / PER_PAGE), page=page)


@bp.route("/users")
@login_required
@checkRole('view_logs')
def show_count_logs():
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT user_id, COUNT(*) as count FROM visit_logs GROUP BY user_id')
        cursor.execute(query)
        logs = cursor.fetchall()
    return render_template("log/users.html", logs=logs)

@bp.route("/page")
@login_required
@checkRole('view_logs')
def show_page_logs():
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT path, COUNT(*) as count FROM visit_logs GROUP BY path')
        cursor.execute(query)
        logs = cursor.fetchall()
    return render_template("log/page.html", logs=logs)


@bp.route("/export_csv")
@login_required
def export_csv():
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT * FROM logs')
        cursor.execute(query)
        logs=cursor.fetchall()
    data = load_data(logs, ['user_id','path', 'created_at'])
    return send_file(data, as_attachment=True,download_name='download.csv')

def load_data(records, fields):
    csv_data=", ".join(fields)+"\n"
    for record in records:
        csv_data += ", ".join([str(getattr(record, field, '')) for field in fields]) + "\n"
    f = io.BytesIO()
    f.write(csv_data.encode('utf-8'))
    f.seek(0)
    return f