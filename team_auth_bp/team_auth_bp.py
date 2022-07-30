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

team_auth_bp = Blueprint('team_auth_bp', __name__, url_prefix='/teamAuth', template_folder='templates', static_folder='static')

@team_auth_bp.route('/signup', methods=('GET', 'POST'))
def teamSignup():
	if request.method == 'POST':
		noOfMem = int(request.form['no-of-mem'].strip())
		# creating an array of entered roll numbers 
		memRollNos = []
		for i in range(noOfMem):
			formIdentifier = 'roll-no' + str(i + 1)
			memRollNos.append(int(request.form[formIdentifier].strip()))

		leaderRollNo = request.form['roll-no1'].strip()	
		username = str(request.form['uname'].strip())
		password = str(request.form['cnf-pwd'].strip())

		db = get_db()
		cur = db.cursor()
		error = None

		if not noOfMem:
			error = 'Number of Members is required.'
		elif not username:
			error = 'Username is required.'
		elif not password:
			error = 'Password is required.'	
		else:
			for i in range(noOfMem):
				if not memRollNos[i]:
					error = 'Member' + str(i + 1) + ' Roll Number is required.'	

		rollNoExistsFlag = 1
		teamPartFlag = 1
		sameClassFlag = 1

		if error is None:
			try:
				# check if entered roll number(s) exists or not 
				for i in range(noOfMem):
					rollNoExistsFlag = 1; # flag = 1 -> roll no exists | flag = 0 -> roll no does not exist  
					cur.execute(
						'SELECT student_id FROM students WHERE student_id = %s;', (memRollNos[i],)
						)
					existRollNo = cur.fetchone()
					if existRollNo == None:
						rollNoExistsFlag = 0
						error = str(memRollNos[i]) + ' does not exist in the database.'
						flash(error)
					else:
						rollNoExistsFlag = 1

				if rollNoExistsFlag == 1:
					# check if entered student roll number is already part of a team or not
					for i in range(noOfMem):
						teamPartFlag = 1; # flag = 1 -> that no student is already part of a team | flag = 0 -> student is already part of a team 
						cur.execute(
							'SELECT team_id FROM membership WHERE student_id = %s;', (memRollNos[i],)
							)
						existTeamId = cur.fetchone()
						if existTeamId != None:
							teamPartFlag = 0
							error = 'Member ' + str(i + 1) + ' is already a member of team.'
							flash(error)
							break
						else:
							teamPartFlag = 1

					if teamPartFlag	== 1:
						# check if all members belong to the same class
						classRecords = []
						sameClassFlag = 1; # flag = 1 -> members belong to the same class | flag = 0 -> member do not belong to the same class
						for i in range(noOfMem):
							cur.execute(
								'SELECT stream, section FROM students WHERE student_id = %s;', (memRollNos[i],)
								)
							classRec = cur.fetchone()
							streamSec = classRec[0] + classRec[1]
							classRecords.append(streamSec)

						for i in range(noOfMem):
							for j in range(noOfMem):
								if classRecords[i] == classRecords[j]:
									sameClassFlag = 1;
								else:
									sameClassFlag = 0;
									break

						if sameClassFlag == 0:
							error = 'Members do not belong to the same class.'
							flash(error)
			except db.IntegrityError:
				error = f'Username already exists.'	

		if error is None:
			try:
				# insert the records in the database 
				cur.execute(
					'INSERT INTO teams (num_of_mem, leader_id) VALUES (%s, %s);', (noOfMem, leaderRollNo),
					)
				cur.close()
				db.commit()
				cur = db.cursor()
				cur.execute(
					'SELECT team_id FROM teams WHERE leader_id = %s;', (leaderRollNo,)
					)
				team_id = cur.fetchone()
				cur.execute(
					'INSERT INTO team_passwords (team_id, username, password) VALUES (%s, %s, %s);', (team_id, username, (generate_password_hash(password)),)
					)
				for i in range(noOfMem):
					cur.execute(
						'INSERT INTO membership (team_id, student_id) VALUES (%s, %s);', (team_id, memRollNos[i],)
						)					
				cur.close()
				db.commit()

				credentialsMsg = 'Your username is ' + username + '.'
				flash(credentialsMsg)
				return redirect(url_for('team_auth_bp.teamSignin'))
				flash(error)
			except  db.IntegrityError:
				error = f'Username already exists.'
				flash(error)
		cur.close()
		close_db()		
	try:
		return render_template('team_auth_bp/team_sign_up.html')
	except TemplateNotFound:
		abort(404)

@team_auth_bp.route('/signin', methods=('GET', 'POST'))
def teamSignin():
	if request.method == 'POST':
		username = request.form['uname']
		password = request.form['pwd']
		db = get_db()
		error = None 
		cur = db.cursor()
		cur.execute(
			'SELECT * FROM team_passwords WHERE username LIKE %s;', (username,)
		)
		
		team = cur.fetchone()

		if team is None:
			error = 'Incorrect username.'
		elif not check_password_hash(team[2], password):
			error = 'Incorrect password.'

		if error is None:
			session.clear()
			session['team_id'] = team[0]
			session['team_username'] = team[1]
			return redirect(url_for('team_dashboard_bp.team_dashboard_home'))	

		flash(error)	
		cur.close()
		close_db()

	try:
		return render_template('team_auth_bp/team_sign_in.html')			
	except TemplateNotFound:
		abort(404)		

@team_auth_bp.before_app_request
def load_logged_in_team():
	team_id = session.get('team_id')

	if team_id is None:
		g.team = None 
	else:
		db = get_db()
		cur = db.cursor() 
		cur.execute(
			'SELECT * FROM team_passwords WHERE team_id = %s;', (team_id,)
			)
		g.team = cur.fetchone()
		cur.close()
		close_db()

@team_auth_bp.route('/teamLogout')
def teamLogout():
	session.clear()
	return redirect(url_for('index.index'))


# a function that ensures that the user is logged in to view any content that requires authentication 
def team_login_required(view):
	@functools.wraps(view)
	def wrapped_view(**kwargs):
		if g.team is None:
			return redirect(url_for('index.index'))

		return view(**kwargs)

	return wrapped_view	


@team_auth_bp.after_app_request
def after_app_request(response):
	response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	return response