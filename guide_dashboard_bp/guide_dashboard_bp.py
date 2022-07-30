import functools
import os
import shutil
from datetime import datetime 
from psycopg2 import sql

from flask import Blueprint
from flask import request
from flask import flash
from flask import redirect
from flask import session
from flask import g
from flask import abort
from flask import render_template
from flask import url_for
from flask import send_from_directory
from flask import current_app as SPH_SS_App

from jinja2 import TemplateNotFound

from werkzeug.utils import secure_filename 
from werkzeug.exceptions import RequestEntityTooLarge


from SPH_SS_App.guide_auth_bp.guide_auth_bp import guide_login_required
from SPH_SS_App.db import get_db
from SPH_SS_App.db import close_db

guide_dashboard_bp = Blueprint('guide_dashboard_bp', __name__, url_prefix='/guideDashboard', template_folder='templates', static_folder='static')

@guide_dashboard_bp.route('/home')
@guide_login_required
def guide_dashboard_home():
	db = get_db()
	cur = db.cursor()

	cur.execute(
		'SELECT * FROM guideHomeData(%s);', (session['guide_id'],)
		)
	guideHomeData = cur.fetchall()

	return render_template('guide_dashboard_bp/guide_dashboard_home.html', guideHomeData=guideHomeData)


@guide_dashboard_bp.route('/serveFile', methods=['GET'])
@guide_login_required	
def serveFile():
	inputPID = request.args.get('inputPID', None)
	file_reqd = request.args.get('file_reqd', None)
	db = get_db()
	cur = db.cursor()

	cur.execute(
		'SELECT team_id FROM associated_with WHERE project_id = %s;', (inputPID,)
		)

	teamID = cur.fetchone()

	cur.execute(
		'SELECT guide_id FROM assigned_to WHERE project_id = %s;', (inputPID,)
		)
	guideID_ret = cur.fetchone()

	if guideID_ret:
		guideID_ret = guideID_ret[0]
		if guideID_ret != session['guide_id']:
			return redirect(url_for('guide_dashboard_bp.guide_dashboard_home'))

	if teamID:
		teamID = teamID[0]
		cur.execute(
			'SELECT  pid, ppres, preport FROM teamHome(%s);', (teamID,)
			)
		teamHomeData = cur.fetchall()
		cur.close()
		close_db()

		projPresPath = None
		projRepoPath = None
		for i in range(len(teamHomeData)):
			if teamHomeData[i][0] == int(inputPID):
				projPresPath = teamHomeData[i][1]
				projRepoPath = teamHomeData[i][2]

		if file_reqd == str(1):
			if projPresPath:
				file_name = os.path.basename(projPresPath) 			
				location = os.path.dirname(projPresPath)   
				return send_from_directory(location, file_name)
			else:
				return render_template('guide_dashboard_bp/fileNotUploadedError.html')
		elif file_reqd == str(2):
			if projRepoPath:
				file_name = os.path.basename(projRepoPath) 			
				location = os.path.dirname(projRepoPath)    
				return send_from_directory(location, file_name)
			else:				
				return render_template('guide_dashboard_bp/fileNotUploadedError.html')
		else:
			return redirect(url_for('guide_dashboard_bp.guide_dashboard_home'))
	else:				
		return redirect(url_for('guide_dashboard_bp.guide_dashboard_home'))

@guide_dashboard_bp.route('/getMembersDetail/<inputPID>')
@guide_login_required
def getMembersDetail(inputPID):
	db = get_db()
	cur = db.cursor()
	teamName = None
	teamMembersData = None

	cur.execute(
		'SELECT guide_id FROM assigned_to WHERE project_id = %s;', (inputPID,)
		)

	guideID = cur.fetchone()

	if guideID:
		guideID = guideID[0]
		if guideID == session['guide_id']:
			cur.execute(
				'SELECT aw.team_id, tp.username FROM associated_with as aw, team_passwords AS tp WHERE aw.project_id = %s AND aw.team_id = tp.team_id;', (inputPID,)
				)
			queryData = cur.fetchone()

			if queryData:
				teamID = queryData[0]
				teamName = queryData[1]

				cur.execute(
					'SELECT * FROM teamMembers(%s);', (teamID,)
					)
				teamMembersData = cur.fetchall()
			else:
				return render_template('guide_dashboard_bp/guide_dashboard_proj_members_error.html')
		else:
			return render_template('guide_dashboard_bp/guide_dashboard_proj_members_error.html')
	else:		
		return render_template('guide_dashboard_bp/guide_dashboard_proj_members_error.html')		
			
	cur.close()
	db.close()
	
	return render_template('guide_dashboard_bp/guide_dashboard_proj_members.html', teamName=teamName, teamMembersData=teamMembersData)		


@guide_dashboard_bp.route('/Profile', methods=['GET'])
@guide_login_required
def guideProfile():
	if request.method == 'GET':
		db = get_db()
		cur = db.cursor()

		cur.execute(
			'SELECT first_name, last_name, email FROM guides WHERE guide_id = %s;', (session['guide_id'],)
			)

		guideData = cur.fetchone()

		return render_template('guide_dashboard_bp/guideProfile.html', guideData=guideData)


@guide_dashboard_bp.route('/guideEdit', methods=['GET', 'POST'])
@guide_login_required
def guideEdit():
	if request.method == 'POST':
		firstName = request.form['fn'].strip()
		lastName = request.form['ln'].strip()
		email = request.form['email'].strip()
		error = None

		if firstName == '':
			error = 'First Name required.'
		elif lastName == '':
			error = 'Last Name required.'
		elif email == '':
			error = 'Email is required.'
		else:
			db = get_db()
			cur = db.cursor()
			cur.execute(
				'SELECT first_name, last_name, email FROM guides WHERE guide_id = %s;', (session['guide_id'],)
				)

			guideExistingData = cur.fetchone()
			existingFirstName = guideExistingData[0]
			existingLastName = guideExistingData[1]
			existingEmail = guideExistingData[2]

			if existingFirstName != firstName:
				cur.execute(
					'UPDATE guides SET first_name = %s WHERE guide_id = %s;', (firstName, session['guide_id'],) 
					)
				db.commit()

			if existingLastName != lastName:
				cur.execute(
					'UPDATE guides SET last_name = %s WHERE guide_id = %s;', (lastName, session['guide_id'],) 
					)
				db.commit()

			if existingEmail != email:
				cur.execute(
					'SELECT email FROM guides WHERE email = %s;', (email,)
					)
				emailFound = cur.fetchone()
				if emailFound:
					error = 'Email already exists.'
				else:
					cur.execute(
					'UPDATE guides SET email = %s WHERE guide_id = %s;', (email, session['guide_id'],) 
					)

		db = get_db()
		cur = db.cursor()
		cur.execute(
			'SELECT first_name, last_name, email FROM guides WHERE guide_id = %s;', (session['guide_id'],)
			)
		guideData = cur.fetchone()					

		cur.close()			
		db.commit()	
		close_db()
		if error != None:		
			flash(error)
		
		return render_template('guide_dashboard_bp/guideProfile.html', guideData=guideData)			

@guide_dashboard_bp.route('/guideCommunications', methods=['GET', 'POST'])
@guide_login_required
def guideCommunications():
	db = get_db()
	cur = db.cursor()
	associatedTeams = None
	communicationData = None

	# find the details of the teams associated with the current guide 
	cur.execute(
		'SELECT team_id, username FROM teamGuides WHERE guide_id = %s;', (session['guide_id'],)
		)
	associatedTeams = cur.fetchall()

	if associatedTeams:	# check if the data exists 
		# create the tables for storing the communication if not already exists 
		tableNames = []
		communicationData = []
		for i in range(len(associatedTeams)):
			tableNames.append('teamGuide_' + str(associatedTeams[i][0]) + str(session['guide_id']))

		for i in range(len(associatedTeams)):
			cur.execute(
				sql.SQL(
					"""
					CREATE TABLE IF NOT EXISTS {}(
					comm_id SERIAL NOT NULL, 
					team_id INT NOT NULL, 
					guide_id INT NOT NULL, 
					comment VARCHAR(250) NOT NULL, 
					direction INT, timeInfo TIMESTAMP WITH TIME ZONE, 
					PRIMARY KEY (comm_id), 
					FOREIGN KEY (team_id) REFERENCES teams (team_id), 
					FOREIGN KEY (guide_id) REFERENCES guides (guide_id));
					"""
				).format(sql.Identifier(tableNames[i])),
			)
		cur.close()
		db.commit()

		# select some past comments to present on the frontend 
		cur = db.cursor()

		for i in range(len(associatedTeams)):
			cur.execute(
				sql.SQL(
					""" 
					SELECT team_id, comment, direction, timeInfo 
					FROM {} 
					ORDER BY timeInfo DESC LIMIT 1;
					"""
				).format(sql.Identifier(tableNames[i])),
			)
			if cur.description:
				data = cur.fetchone()
				communicationData.append(data)

	cur.close()
	close_db()				

	return render_template('guide_dashboard_bp/guideCommunications.html', associatedTeams=associatedTeams, communicationData=communicationData)


@guide_dashboard_bp.route('/guideCommunications<inputTID>', methods=['GET', 'POST'])
@guide_login_required
def guideSpecificCommunication(inputTID):
	db = get_db()
	cur = db.cursor()
	fullCommData = None
	inputTID = inputTID 

	# find team name  
	cur.execute(
		'SELECT username FROM teamGuides WHERE team_id = %s;', (inputTID,)
		)
	teamName = cur.fetchone()


	if teamName:
		teamName = teamName[0]
		tableName = 'teamGuide_' + str(inputTID) + str(session['guide_id'])
		try:
			cur.execute(
						sql.SQL
						(
							""" 
							SELECT comment, direction, timeInfo 
							FROM {}
							ORDER BY timeInfo DESC;
							"""
						).format(sql.Identifier(tableName)),
					)

			if 	cur.description:
				fullCommData = cur.fetchall()	
		except Exception as e:
			return redirect(url_for('guide_dashboard_bp.guide_dashboard_home'))
	else:
		flash('Does Not exist.')
		return redirect(url_for('guide_dashboard_bp.guide_dashboard_home'))
				

	return render_template('guide_dashboard_bp/guideSpecificCommunication.html', fullCommData=fullCommData, teamName=teamName, inputTID=inputTID )


@guide_dashboard_bp.route('/communicationAdd<inputTID>', methods=['GET', 'POST'])
@guide_login_required	
def communicationAdd(inputTID):
	if request.method == 'POST':
		comment = request.form['cmt-area']
		timeInfo = datetime.now()
		db = get_db()
		cur = db.cursor()
		error = None

		if not comment:
			error = "Comment is required."
		
		# direction of 0 implies communication from team to guide and 1 for vice versa	
		if error is None:
			tableName = 'teamGuide_' + str(inputTID) + str(session['guide_id'])
			cur.execute(
						sql.SQL
						(
							""" 
							INSERT INTO {} (team_id, guide_id, comment, direction, timeInfo) VALUES (%s, %s, %s, %s, %s);"""   
						).format(sql.Identifier(tableName)),[inputTID, session['guide_id'], comment, 1, timeInfo]
					)
			cur.close()
			db.commit()
			close_db()

			if error:
				flash(error)

	return redirect(url_for('guide_dashboard_bp.guideSpecificCommunication', inputTID=inputTID))
