import functools
import os
import shutil
from psycopg2 import sql
from datetime import datetime 

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

from SPH_SS_App.team_auth_bp.team_auth_bp import team_login_required
from SPH_SS_App.db import get_db
from SPH_SS_App.db import close_db

team_dashboard_bp = Blueprint('team_dashboard_bp', __name__, url_prefix='/teamDashboard', template_folder='templates', static_folder='static')

@team_dashboard_bp.route('/home')
@team_login_required
def team_dashboard_home():
	db = get_db()
	cur = db.cursor()
	cur.execute(
		'SELECT * FROM teamHome(%s);', (session['team_id'],)
		)
	teamHomeData = cur.fetchall()
	cur.close()
	close_db()

	return render_template('team_dashboard_bp/team_dashboard_home.html', teamHomeData=teamHomeData)

@team_login_required
@team_dashboard_bp.app_errorhandler(413)
def requestEntityTooLargeError(e):
	return render_template('team_dashboard_bp/413.html'), 413

# a function that checks if the given name of project already exists for a team 
def ifProjectNameExists(inputProjName):
	db = get_db()
	cur = db.cursor()
	sameNameFlag = 1 # 1 --> no same name | 0 --> same name

	# step 1: extracting all the projectIds associated with a team 
	cur.execute(
		'SELECT project_id FROM associated_with WHERE team_id = %s;', (session['team_id'],)
		)
	tupleListProjectIds = cur.fetchall()

	if tupleListProjectIds is not None: # checking that the project id list is not empty
		projIds = []
		for i in range(len(tupleListProjectIds)):
			projIds.append(tupleListProjectIds[i][0])

		# step 2: extracting the project names with the corresposding ids
		projNames = []
		for i in range(len(projIds)):
			cur.execute(
				'SELECT project_name FROM projects WHERE project_id = %s;', (projIds[i],)
				) 	
			projNamesTuple = cur.fetchone()
			projNames.append(projNamesTuple[0])

		# step 3 comparing the names with the input name  
		for i in range(len(projNames)):
			if inputProjName == projNames[i]:
				sameNameFlag = 0
	else:
		sameNameFlag = 0

	if sameNameFlag == 0:
		return True # same name exist
	else:
		return False # same name does not exist 		

@team_dashboard_bp.route('/addProject', methods=['POST'])
@team_login_required
def teamAddProject():
	if request.method == 'POST':
		projName = str(request.form['proj-name'].strip().lower())
		projDuration = str(request.form['proj-duration'].strip())
		projPresentation = request.files['proj-pres']
		projReport = request.files['proj-report']
		projRepoLink = str(request.form['proj-repo-link'].strip())
		projPresSubDate = datetime.now()
		projRepoSubDate = datetime.now()

		db = get_db()
		cur = db.cursor()
		error = None
		msg = None

		if not projName:
			error = 'Project Name is required.'
		elif not projDuration:
			error = 'Project duration is required.'

		if error is None:
			projNameFlag = ifProjectNameExists(projName)
			if projNameFlag == True:
				error = 'Project Name already exists.'
				flash(error)
			else:
				# insert the required fields into the DB 
				cur.execute(
					'INSERT INTO projects (project_name, project_duration) VALUES (%s, %s);', (projName, projDuration,)
					)
				cur.close()
				db.commit()
				
				# get the generated project id 				
				cur = db.cursor()
				cur.execute(
					'SELECT project_id FROM projects ORDER BY project_id DESC;'
					)
				projIdGen = cur.fetchone()[0]
				
				# enter data into associated_with table 
				cur.execute(
					'INSERT INTO associated_with (project_id, team_id) VALUES (%s, %s);', (projIdGen, session['team_id'],)
					)

				# enter project repo link in the database 
				if projRepoLink:
					cur.execute(
						'UPDATE projects SET proj_repo_link = %s WHERE project_id = %s;', (projRepoLink, projIdGen,)
						)
					cur.close()
					db.commit()

				# processing the file input projPresentation 
				try:
					if projPresentation: # ensuring it exists 
						# extracting and validating file extension 
						ext = os.path.splitext(projPresentation.filename)[1].lower()

						fileExtFlag = 1
						if ext not in SPH_SS_App.config['ALLOWED_PRES_EXTENSIONS']:
							error = 'Presentation file does not obey the extension requirements.'
							fileExtFlag = 0
							flash(error)
						
						# if file extension is correct than processing further 	
						if fileExtFlag != 0:
							# checking and/or creating team and project and presentation folders 
							teamFolderName = 'Team' + str(session['team_id'])
							teamFolderPath = os.path.join(SPH_SS_App.config['PROJ_REPORT_PRES_UPLOAD_DIRECTORY'], teamFolderName)
							if os.path.isdir(teamFolderPath) == False:
								os.mkdir(teamFolderPath)

							projectFolderName = 'Proj' + str(projIdGen)
							projectFolderPath = os.path.join(teamFolderPath, projectFolderName)
							if os.path.isdir(projectFolderPath) == False:
								os.mkdir(projectFolderPath)

							presentationFolderName = 'presentation'	
							presentationFolderPath = os.path.join(projectFolderPath, presentationFolderName)
							if os.path.isdir(presentationFolderPath) == False:
								os.mkdir(presentationFolderPath)

							# uploading the file 	
							upload_path = os.path.join(presentationFolderPath, secure_filename(projPresentation.filename))
							projPresentation.save(upload_path)

							# saving the upload_path in the database
							cur = db.cursor()
							cur.execute(
								'UPDATE projects SET project_presentation = %s, proj_pres_sub_date = %s WHERE project_id = %s;', (upload_path, projPresSubDate, projIdGen,)
								)			
							cur.close()
							db.commit()
				except RequestEntityTooLarge:
					error = f'Presentation file is larger than 20 MB limit.'
					flash(error)

				# processing the file input projReport 
				try:
					if projReport: # ensuring it exists 
						# extracting and validating file extension 
						ext = os.path.splitext(projReport.filename)[1].lower()

						fileExtFlag = 1
						if ext not in SPH_SS_App.config['ALLOWED_PRES_EXTENSIONS']:
							error = 'Report file does not obey the extension requirements.'
							fileExtFlag = 0
							flash(error)
						
						# if file extension is correct than processing further 	
						if fileExtFlag != 0:
							# checking and/or creating team and project and report folders 
							teamFolderName = 'Team' + str(session['team_id'])
							teamFolderPath = os.path.join(SPH_SS_App.config['PROJ_REPORT_PRES_UPLOAD_DIRECTORY'], teamFolderName)
							if os.path.isdir(teamFolderPath) == False:
								os.mkdir(teamFolderPath)

							projectFolderName = 'Proj' + str(projIdGen)
							projectFolderPath = os.path.join(teamFolderPath, projectFolderName)
							if os.path.isdir(projectFolderPath) == False:
								os.mkdir(projectFolderPath)

							reportFolderName = 'report'
							reportFolderPath = os.path.join(projectFolderPath, reportFolderName)
							if os.path.isdir(reportFolderPath) == False:
								os.mkdir(reportFolderPath)

							# uploading the file 	
							upload_path = os.path.join(reportFolderPath, secure_filename(projReport.filename))
							projReport.save(upload_path)

							# saving the upload_path in the database
							cur = db.cursor()
							cur.execute(
								'UPDATE projects SET project_report = %s, proj_rep_sub_date = %s WHERE project_id = %s;', (upload_path, projRepoSubDate, projIdGen,)
								)			
							cur.close()
							db.commit()
				except RequestEntityTooLarge:
					error = f'Report file is larger than 20 MB limit.'
					flash(error)

				# logic for assigning guide to the project 
				cur = db.cursor()
				cur.execute(
					'SELECT guide_id FROM guides WHERE guide_id NOT IN (SELECT DISTINCT guide_id FROM assigned_to);'
					)
				neverAssgGuidesListTuple = cur.fetchall()
				neverAssgGuides = []

				if neverAssgGuidesListTuple: # checking if neverAssgGuidesListsTuple exists 
					for i in range(len(neverAssgGuidesListTuple)):
						neverAssgGuides.append(neverAssgGuidesListTuple[i][0])	

					# select one guide from the list 	
					oneGuide = neverAssgGuides[0]

					cur.execute(
						'SELECT first_name, last_name FROM guides WHERE guide_id = %s;', (oneGuide,)
						)
					compResult = cur.fetchone()
					guideFName, guideLName = compResult[0], compResult[1]

					cur.execute(
						'INSERT INTO assigned_to (guide_id, project_id) VALUES (%s, %s);', (oneGuide, projIdGen,)
						)
					cur.close()
					db.commit()
					msg = guideFName + ' ' + guideLName + ' assigned as guide for project.'
					flash(msg) 
				# if no guide exits that has not been assigned a single project 	
				else:
					# check which guide has been assigned the least projects
					cur = db.cursor()
					cur.execute(
						'SELECT guide_id FROM guidesNoOfProjAssigned ORDER BY no_of_proj_assigned ASC'
						)
					# select one guide from the list 	
					compResult = cur.fetchone()
					oneGuide = compResult[0]

					cur.execute(
						'SELECT first_name, last_name FROM guides WHERE guide_id = %s;', (oneGuide,)
						)
					compResult = cur.fetchone()
					guideFName, guideLName = compResult[0], compResult[1]

					cur.execute(
						'INSERT INTO assigned_to (guide_id, project_id) VALUES (%s, %s);', (oneGuide, projIdGen,)
						)
					cur.close()
					db.commit()
					msg = guideFName + ' ' + guideLName + ' assigned as guide for project.'
					flash(msg) 
	
		cur.close()
		close_db()
	if msg:
		flash(msg)
	if error:
		flash(error)	
	return redirect(url_for('team_dashboard_bp.team_dashboard_home'))			

@team_dashboard_bp.route('/serveFile', methods=['GET'])
@team_login_required
def serveFile():
	inputPID = request.args.get('inputPID', None)
	file_reqd = request.args.get('file_reqd', None)
	db = get_db()
	cur = db.cursor()
	cur.execute(
		'SELECT  pid, ppres, preport FROM teamHome(%s);', (session['team_id'],)
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
			return render_template('team_dashboard_bp/fileNotUploadedError.html')
	elif file_reqd == str(2):
		if projRepoPath:
			file_name = os.path.basename(projRepoPath) 			
			location = os.path.dirname(projRepoPath)    
			return send_from_directory(location, file_name)
		else:				
			return render_template('team_dashboard_bp/fileNotUploadedError.html')
	else:
		return redirect(url_for('team_dashboard_bp.team_dashboard_home'))

@team_dashboard_bp.route('/editProject/<inputPID>', methods=['GET', 'POST'])
@team_login_required
def teamEditProject(inputPID):
	inputPID = int(inputPID)
	if request.method == 'POST':
		projName = str(request.form['proj-name'].strip().lower())
		projDuration = str(request.form['proj-duration'].strip())
		projPresentation = request.files['proj-pres']
		projReport = request.files['proj-report']
		projRepoLink = str(request.form['proj-repo-link'].strip())
		projPresSubDate = datetime.now()
		projRepoSubDate = datetime.now()

		db = get_db()
		cur = db.cursor()
		error = None
		msg = None

		if not projName:
			error = 'Project Name is required.'
		elif not projDuration:
			error = 'Project duration is required.'

		cur.execute(
			'SELECT team_id FROM associated_with WHERE project_id = %s;', (inputPID,)
			)
		teamID = cur.fetchone()[0]

		if teamID == session['team_id']:
			if error is None:
				cur.execute(
					'SELECT project_name FROM projects WHERE project_id = %s;', (inputPID,)
					)
				existingProjName = cur.fetchone()[0]
				projNameFlag = False
				if existingProjName != projName:
					projNameFlag = ifProjectNameExists(projName)
				if projNameFlag == True:
					error = 'Project Name already exists.'
					flash(error)
				else:
					# update the fields in the DB 
					cur.execute(
						'UPDATE projects SET project_name = %s, project_duration = %s WHERE project_id = %s;', (projName, projDuration, inputPID)
						)
					cur.close()
					db.commit()

					# update project repo link in the database 
					cur = db.cursor()
					if projRepoLink == '':
						cur.execute(
							'UPDATE projects SET proj_repo_link = NULL WHERE project_id = %s;', (inputPID,)
							)
						cur.close()
						db.commit()

					if projRepoLink == 'None' or projRepoLink == 'none' or projRepoLink == 'NULL':
						cur.execute(
							'UPDATE projects SET proj_repo_link = NULL WHERE project_id = %s;', (inputPID,)
							)
						cur.close()
						db.commit()
					elif projRepoLink:
						cur.execute(
							'UPDATE projects SET proj_repo_link = %s WHERE project_id = %s;', (projRepoLink, inputPID,)
							)
						cur.close()
						db.commit()

					# processing the file input projPresentation 
					try:
						if projPresentation: # ensuring it exists 
							# extracting and validating file extension 
							ext = os.path.splitext(projPresentation.filename)[1].lower()

							fileExtFlag = 1
							if ext not in SPH_SS_App.config['ALLOWED_PRES_EXTENSIONS']:
								error = 'Presentation file does not obey the extension requirements.'
								fileExtFlag = 0
								flash(error)
							
							# if file extension is correct than processing further 	
							if fileExtFlag != 0:
								# checking and/or creating team and project and presentation folders 
								teamFolderName = 'Team' + str(session['team_id'])
								teamFolderPath = os.path.join(SPH_SS_App.config['PROJ_REPORT_PRES_UPLOAD_DIRECTORY'], teamFolderName)
								if os.path.isdir(teamFolderPath) == False:
									os.mkdir(teamFolderPath)

								projectFolderName = 'Proj' + str(inputPID)
								projectFolderPath = os.path.join(teamFolderPath, projectFolderName)
								if os.path.isdir(projectFolderPath) == False:
									os.mkdir(projectFolderPath)

								presentationFolderName = 'presentation'	
								presentationFolderPath = os.path.join(projectFolderPath, presentationFolderName)
								if os.path.isdir(presentationFolderPath) == False:
									os.mkdir(presentationFolderPath)
								else:
									for fN in os.listdir(presentationFolderPath):
									    file_path = os.path.join(presentationFolderPath, fN)
									    try:
									        if os.path.isfile(file_path) or os.path.islink(file_path):
									            os.unlink(file_path)
									        elif os.path.isdir(file_path):
									            shutil.rmtree(file_path)
									    except Exception as e:
									        flash('Failed to delete %s. Reason: %s' % (file_path, e))
									os.rmdir(presentationFolderPath) # deleting the existing folder containing the file
									os.mkdir(presentationFolderPath)

								# uploading the file 	
								upload_path = os.path.join(presentationFolderPath, secure_filename(projPresentation.filename))
								projPresentation.save(upload_path)

								# saving the upload_path in the database
								cur = db.cursor()
								cur.execute(
									'UPDATE projects SET project_presentation = %s, proj_pres_sub_date = %s WHERE project_id = %s;', (upload_path, projPresSubDate, inputPID,)
									)			
								cur.close()
								db.commit()
					except RequestEntityTooLarge:
						error = f'Presentation file is larger than 20 MB limit.'
						flash(error)

					# processing the file input projReport 
					try:
						if projReport: # ensuring it exists 
							# extracting and validating file extension 
							ext = os.path.splitext(projReport.filename)[1].lower()

							fileExtFlag = 1
							if ext not in SPH_SS_App.config['ALLOWED_PRES_EXTENSIONS']:
								error = 'Report file does not obey the extension requirements.'
								fileExtFlag = 0
								flash(error)
							
							# if file extension is correct than processing further 	
							if fileExtFlag != 0:
								# checking and/or creating team and project and report folders 
								teamFolderName = 'Team' + str(session['team_id'])
								teamFolderPath = os.path.join(SPH_SS_App.config['PROJ_REPORT_PRES_UPLOAD_DIRECTORY'], teamFolderName)
								if os.path.isdir(teamFolderPath) == False:
									os.mkdir(teamFolderPath)

								projectFolderName = 'Proj' + str(inputPID)
								projectFolderPath = os.path.join(teamFolderPath, projectFolderName)
								if os.path.isdir(projectFolderPath) == False:
									os.mkdir(projectFolderPath)

								reportFolderName = 'report'
								reportFolderPath = os.path.join(projectFolderPath, reportFolderName)
								if os.path.isdir(reportFolderPath) == False:
									os.mkdir(reportFolderPath)
								else:
									for fN in os.listdir(reportFolderPath):
									    file_path = os.path.join(reportFolderPath, fN)
									    try:
									        if os.path.isfile(file_path) or os.path.islink(file_path):
									            os.unlink(file_path)
									        elif os.path.isdir(file_path):
									            shutil.rmtree(file_path)
									    except Exception as e:
									        flash('Failed to delete %s. Reason: %s' % (file_path, e))
									os.rmdir(reportFolderPath)
									os.mkdir(reportFolderPath)

								# uploading the file 	
								upload_path = os.path.join(reportFolderPath, secure_filename(projReport.filename))
								projReport.save(upload_path)

								# saving the upload_path in the database
								cur = db.cursor()
								cur.execute(
									'UPDATE projects SET project_report = %s, proj_rep_sub_date = %s WHERE project_id = %s;', (upload_path, projRepoSubDate, inputPID,)
									)			
								cur.close()
								db.commit()
					except RequestEntityTooLarge:
						error = f'Report file is larger than 20 MB limit.'
						flash(error)
		cur.close()
		close_db()
	if error:
		flash(error)
	else:
		flash('Project details updated successfully.')	
	return redirect(url_for('team_dashboard_bp.team_dashboard_home'))

@team_dashboard_bp.route('/deleteProject/<inputPID>', methods=['GET', 'POST'])
@team_login_required
def teamDeleteProject(inputPID):
	inputPID = int(inputPID)
	db = get_db()
	cur = db.cursor()
	# delete information from associated_with table in DB
	cur.execute(
		'DELETE FROM associated_with WHERE project_id = %s;', (inputPID,)
		)

	# delete information from assigned_to table in DB
	cur.execute(
		'DELETE FROM assigned_to WHERE project_id = %s;', (inputPID,)
		)
	cur.close()
	db.commit()

	# delete the file resources associated with the project stored in the file system if exists 
	teamFolderName = 'Team' + str(session['team_id'])
	teamFolderPath = os.path.join(SPH_SS_App.config['PROJ_REPORT_PRES_UPLOAD_DIRECTORY'], teamFolderName)

	if os.path.isdir(teamFolderPath):
		projectFolderName = 'Proj' + str(inputPID)
		projectFolderPath = os.path.join(teamFolderPath, projectFolderName)

		if os.path.isdir(projectFolderPath):
			for fN in os.listdir(projectFolderPath):
			    file_path = os.path.join(projectFolderPath, fN)
			    try:
			        if os.path.isfile(file_path) or os.path.islink(file_path):
			            os.unlink(file_path)
			        elif os.path.isdir(file_path):
			            shutil.rmtree(file_path)
			    except Exception as e:
			        print('Failed to delete %s. Reason: %s' % (file_path, e))
			os.rmdir(projectFolderPath)

	# delete information from projects table in DB
	cur = db.cursor()
	cur.execute(
		'DELETE FROM projects WHERE project_id = %s;', (inputPID,)
		)
	
	cur.close()
	db.commit()
	close_db()

	return redirect(url_for('team_dashboard_bp.team_dashboard_home'))

@team_dashboard_bp.route('/manageMembers')
@team_login_required
def manageMembers():
	db = get_db()
	cur = db.cursor()

	cur.execute(
		'SELECT * FROM teamMembers(%s);', (session['team_id'],)
		)
	teamMembersData = cur.fetchall()

	cur.execute(
		'SELECT leader_id FROM teams WHERE team_id = %s;', (session['team_id'],)
		)
	leadID = cur.fetchone()[0]
	leadName = None 

	for i in range(len(teamMembersData)):
		if teamMembersData[i][0] == leadID:
			leadName = teamMembersData[i][1]

	cur.close()
	close_db()

	return render_template('team_dashboard_bp/manageMembers.html', teamMembersData=teamMembersData, leadName=leadName)

@team_dashboard_bp.route('/editMembers/<inputMID>', methods=['POST', 'GET'])
@team_login_required
def teamEditMember(inputMID):
	if request.method == 'POST':
		email = str(request.form['email'].strip())
		mobileNo = int(request.form['mobno'].strip())

		db = get_db()
		cur = db.cursor()
		error = None 

		cur.execute(
			'SELECT email, mobile_no FROM students WHERE student_id = %s;', (inputMID,)
			)

		existData = cur.fetchone()
		existEmail = existData[0]
		existMobNo = existData[1]

		if existEmail != email:
			try:
				cur.execute(
					'UPDATE students SET email=%s WHERE student_id=%s;', (email, inputMID,)
					)
				cur.close()
				db.commit()
			except db.IntegrityError:
				error = f'Email already exists.'
				flash(error)

		if existMobNo != mobileNo:
			try:
				cur = db.cursor(

					)
				cur.execute(
					'UPDATE students SET mobile_no=%s WHERE student_id=%s;', (mobileNo, inputMID,)
					)
				cur.close()
				db.commit()
			except db.IntegrityError:
				error = f'Mobile Number already exists.'
				flash(error)

		cur.close()
		db.commit()
		close_db()

		flash(error)

	

	return redirect(url_for('team_dashboard_bp.manageMembers'))

@team_dashboard_bp.route('/guideDetails', methods=['GET'])
@team_login_required
def guideDetails():
	if request.method == 'GET':
		db = get_db()
		cur = db.cursor()
		cur.execute(
			'SELECT * FROM guideDetailsTeamDashboard(%s);', (session['team_id'],)
			)
		teamGuideData = cur.fetchall()
		cur.close()
		close_db()

		return render_template('team_dashboard_bp/teamGuideDetails.html', teamGuideData=teamGuideData)

@team_dashboard_bp.route('/teamCommunicate')
@team_login_required
def teamCommunicate():
	db = get_db()
	cur = db.cursor()
	associatedGuides = None
	communicationData = None

	# find the details of the guides associated with the current team 
	cur.execute(
		'SELECT guide_id, gname FROM teamGuides WHERE team_id = %s;', (session['team_id'],)
		)
	associatedGuides = cur.fetchall()

	if associatedGuides:	# check if the data exists 
		# create the tables for storing the communication 
		tableNames = []
		communicationData = []
		for i in range(len(associatedGuides)):
			tableNames.append('teamGuide_' + str(session['team_id']) + str(associatedGuides[i][0]))

		for i in range(len(associatedGuides)):
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

		for i in range(len(associatedGuides)):
			cur.execute(
				sql.SQL(
					""" 
					SELECT guide_id, comment, direction, timeInfo 
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

	return render_template('team_dashboard_bp/teamCommunication.html', associatedGuides=associatedGuides, communicationData=communicationData)	

@team_dashboard_bp.route('/teamCommunicate/<inputGID>', methods=['GET', 'POST'])
@team_login_required
def teamSpecificCommunication(inputGID):
	db = get_db()
	cur = db.cursor()
	fullCommData = None
	inputGID = inputGID

	# find guide name  
	cur.execute(
		'SELECT gname FROM teamGuides WHERE guide_id = %s;', (inputGID,)
		)
	guideName = cur.fetchone()

	if guideName:
		guideName = guideName[0]
		tableName = 'teamGuide_' + str(session['team_id']) + str(inputGID)
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
			return redirect(url_for('team_dashboard_bp.team_dashboard_home'))
	else:
		return redirect(url_for('team_dashboard_bp.team_dashboard_home'))

	return render_template('team_dashboard_bp/teamSpecificCommunication.html', fullCommData=fullCommData, guideName=guideName, inputGID=inputGID)


@team_dashboard_bp.route('/communicationAdd/<inputGID>', methods=['GET', 'POST'])
@team_login_required
def communicationAdd(inputGID):
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
			tableName = 'teamGuide_' + str(session['team_id']) + str(inputGID)
			cur.execute(
						sql.SQL
						(
							""" 
							INSERT INTO {} (team_id, guide_id, comment, direction, timeInfo) VALUES (%s, %s, %s, %s, %s);"""   
						).format(sql.Identifier(tableName)),[session['team_id'], inputGID, comment, 0, timeInfo]
					)
			cur.close()
			db.commit()
			close_db()

			if error:
				flash(error)

	return redirect(url_for('team_dashboard_bp.teamSpecificCommunication', inputGID=inputGID))

				