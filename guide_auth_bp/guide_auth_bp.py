import functools
import psycopg2

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask import abort
from jinja2 import TemplateNotFound
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from SPH_SS_App.db import get_db
from SPH_SS_App.db import close_db

guide_auth_bp = Blueprint('guide_auth_bp', __name__, url_prefix='/guideAuth', template_folder='templates', static_folder='static')


@guide_auth_bp.route('/signup', methods=('GET', 'POST'))
def guideSignup():
	if request.method == 'POST':
		firstName = request.form['fn'].strip()
		lastName = request.form['ln'].strip()
		email = request.form['email'].strip()
		password = request.form['cnf-pwd'].strip()
		db = get_db()
		cur = db.cursor()
		error = None 

		if not firstName:
			error = 'First Name is required.'
		elif not lastName:
			error = 'Last Name is required.'
		elif not email:
			error = 'Email is required.'
		elif not password:
			error = 'Password is required.'

		if error is None:
			try:
				cur.execute(
					'INSERT INTO guides (first_name, last_name, email) VALUES (%s, %s, %s);',
					(firstName, lastName, email)
					)
				cur.close()
				db.commit()
				db = get_db()
				cur = db.cursor()
				cur.execute(
					'SELECT guide_id FROM guides WHERE email LIKE %s;', (email,)
					)
				guide_id = cur.fetchone()
				cur.execute(
					'INSERT INTO guide_passwords (guide_id, username, password) VALUES (%s, %s, %s);', (guide_id, email, generate_password_hash(password)), 
					)
				cur.close()
				db.commit()
			except db.IntegrityError:
				error = f'User {email} is already registered.'
			else:
				credentialsMsg = 'Your username is ' + email + '.'
				flash(credentialsMsg)
				return redirect(url_for('guide_auth_bp.guideSignin'))
		cur.close()
		close_db()			
		flash(error)
	try:
		return render_template('guide_auth_bp/guide_sign_up.html')
	except TemplateNotFound:
		abort(404)			


@guide_auth_bp.route('/signin', methods=('GET', 'POST'))
def guideSignin():
	if request.method == 'POST':
		username = request.form['uname']
		password = request.form['pwd']
		db = get_db()
		error = None 
		cur = db.cursor()
		cur.execute(
			'SELECT * FROM guide_passwords WHERE username LIKE %s;', (username,)
		)

		guide = cur.fetchone()

		if guide is None:
			error = 'Incorrect username.'
		elif not check_password_hash(guide[2], password):
			error = 'Incorrect password.'

		if error is None:
			session.clear()
			session['guide_id'] = guide[0]
			session['guide_username'] = guide[1]
			return redirect(url_for('guide_dashboard_bp.guide_dashboard_home'))	

		flash(error)	
		cur.close()
		close_db()

	try:
		return render_template('guide_auth_bp/guide_sign_in.html')			
	except TemplateNotFound:
		abort(404)	

@guide_auth_bp.before_app_request
def load_logged_in_guide():
	guide_id = session.get('guide_id')

	if guide_id is None:
		g.guide = None 
	else:
		db = get_db()
		cur = db.cursor() 
		cur.execute(
			'SELECT * FROM guide_passwords WHERE guide_id = %s;', (guide_id,)
			)
		g.guide = cur.fetchone()
		cur.close()
		close_db()

@guide_auth_bp.route('/guideLogout')
def guideLogout():
	session.clear()
	return redirect(url_for('index.index'))


# a function that ensures that the user is logged in to view any content that requires authentication 
def guide_login_required(view):
	@functools.wraps(view)
	def wrapped_view(**kwargs):
		if g.guide is None:
			return redirect(url_for('index.index'))

		return view(**kwargs)

	return wrapped_view	

@guide_auth_bp.after_app_request
def after_app_request(response):
	response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	return response