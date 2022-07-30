DROP TABLE IF EXISTS membership;
DROP TABLE IF EXISTS team_passwords;
DROP TABLE IF EXISTS guide_passwords;
DROP TABLE IF EXISTS associated_with;
DROP TABLE IF EXISTS assigned_to;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS guides;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS projects; 

CREATE TABLE students(
	student_id SERIAL NOT NULL,
	first_name VARCHAR(50) NOT NULL,
	last_name VARCHAR(50) NOT NULL,
	stream VARCHAR(5) NOT NULL,
	section VARCHAR(2) NOT NULL,
	email VARCHAR(80) NOT NULL,
	mobile_no NUMERIC(10, 0) NOT NULL, 
	UNIQUE (student_id),
	UNIQUE (email), 
	UNIQUE (mobile_no),
	PRIMARY KEY (student_id)
);

CREATE TABLE teams(
	team_id SERIAL NOT NULL,
	num_of_mem INT NOT NULL,
	leader_id INT NOT NULL,
	UNIQUE (team_id),
	UNIQUE (leader_id),
	PRIMARY KEY (team_id),
	FOREIGN KEY (leader_id) REFERENCES students (student_id)
);

CREATE TABLE projects(
	project_id SERIAL NOT NULL,
	project_name  VARCHAR(50) NOT NULL,
	project_duration VARCHAR(20) NOT NULL,
	project_presentation VARCHAR(250), 
	project_report VARCHAR(250),
	proj_pres_sub_date TIMESTAMP WITH TIME ZONE,
	proj_rep_sub_date TIMESTAMP WITH TIME ZONE,
	proj_repo_link VARCHAR(180),
	UNIQUE (project_id),
	PRIMARY KEY (project_id)	
);


CREATE TABLE guides(
	guide_id SERIAL NOT NULL,
	first_name VARCHAR(50) NOT NULL,
	last_name VARCHAR(50) NOT NULL,
	email VARCHAR(80) NOT NULL, 
	UNIQUE (guide_id),
	UNIQUE (email),
	PRIMARY KEY (guide_id)
);

CREATE TABLE membership(
	team_id INT NOT NULL,
	student_id INT NOT NULL,
	UNIQUE (student_id),
	PRIMARY KEY (team_id, student_id),
	FOREIGN KEY (team_id) REFERENCES teams (team_id),
	FOREIGN KEY (student_id) REFERENCES students (student_id)
);

CREATE TABLE associated_with(
	project_id INT NOT NULL,
	team_id INT NOT NULL,
	UNIQUE (project_id),
	PRIMARY KEY (project_id, team_id),
	FOREIGN KEY (project_id) REFERENCES projects (project_id),
	FOREIGN KEY (team_id) REFERENCES teams (team_id)
);

CREATE TABLE assigned_to(
	guide_id INT NOT NULL, 
	project_id INT NOT NULL,
	PRIMARY KEY (guide_id, project_id),
	UNIQUE (project_id),
	FOREIGN KEY (guide_id) REFERENCES guides (guide_id),
	FOREIGN KEY (project_id) REFERENCES projects (project_id)
);

CREATE TABLE team_passwords(
	team_id INT NOT	NULL, 
	username VARCHAR(50),
	password VARCHAR(120),
	UNIQUE (team_id),
	UNIQUE (username),
	PRIMARY KEY (team_id),
	FOREIGN KEY (team_id) REFERENCES teams (team_id)
);

CREATE TABLE guide_passwords(
	guide_id INT NOT NULL, 
	username VARCHAR(80),
	password VARCHAR(120),
	UNIQUE (guide_id),
	UNIQUE (username),
	PRIMARY KEY (guide_id),
	FOREIGN KEY (guide_id) REFERENCES guides (guide_id), 
	FOREIGN KEY (username) REFERENCES guides (email) ON UPDATE CASCADE 
);