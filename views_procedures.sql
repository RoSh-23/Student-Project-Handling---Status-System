/* to remember the sequence of dropping  
DROP VIEW guidesNoOfProjAssigned;
DROP FUNCTION teamHome;
DROP FUNCTION teamMembers;
DROP FUNCTION guideDetailsTeamDashboard;
DROP VIEW teamGuides;
DELETE FROM membership; 
DELETE FROM team_passwords;
DELETE FROM guide_passwords;
DELETE FROM associated_with;
DELETE FROM assigned_to;
DELETE FROM teams;
DELETE FROM guides;
DELETE FROM students;
DELETE FROM projects;
*/

CREATE VIEW guidesNoOfProjAssigned AS 
SELECT guide_id, COUNT(project_id) AS no_of_proj_assigned 
FROM assigned_to
GROUP BY guide_id;

CREATE OR REPLACE FUNCTION teamHome (IN teamID INT)
RETURNS TABLE (
	pid INT,
	pname VARCHAR(50),
	pdur VARCHAR(20),
	gname TEXT,
	ppres VARCHAR(250),
	ppresdate TIMESTAMP WITH TIME ZONE,
	preport VARCHAR(250), 
	prepodate TIMESTAMP WITH TIME ZONE, 
	prepoLink VARCHAR(180)
) AS $$
DECLARE
BEGIN
	RETURN QUERY
	SELECT p.project_id, p.project_name, p.project_duration, g.first_name || ' ' || g.last_name, p.project_presentation, p.proj_pres_sub_date, p.project_report, p.proj_rep_sub_date, p.proj_repo_link 
	FROM projects AS p, guides AS g, assigned_to AS at, associated_with AS aw 
	WHERE p.project_id = at.project_id AND 
	      at.guide_id = g.guide_id AND 
		  aw.project_id = p.project_id AND
		  aw.team_id = teamID;
END; 
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION teamMembers (IN teamID INT)
RETURNS TABLE (
	sid INT,
	sname TEXT,
	sstream VARCHAR(5),
	ssection VARCHAR(2),
	semail VARCHAR(80),
	smobile_no NUMERIC(10, 0)
) AS $$
DECLARE
BEGIN
	RETURN QUERY
	SELECT s.student_id, s.first_name || ' ' || s.last_name, s.stream, s.section, s.email, s.mobile_no
	FROM students AS s, membership AS m 
	WHERE m.team_id = teamID AND 
		  s.student_id = m.student_id;
END; 
$$ LANGUAGE 'plpgsql';

/* A function which returns the information to be displayed on guideDetails page of team dashboard */
CREATE OR REPLACE FUNCTION guideDetailsTeamDashboard (IN teamID INT)
RETURNS TABLE (
	gid INT,
	gname TEXT,
	gemail VARCHAR(80)
) AS $$
DECLARE
BEGIN
	RETURN QUERY
	SELECT DISTINCT g.guide_id, g.first_name || ' ' || g.last_name, g.email 
	FROM guides AS g, teams AS t, projects AS p, associated_with AS aw, assigned_to AS at 
	WHERE t.team_id = teamID AND 
		  t.team_id = aw.team_id AND 
      	  aw.project_id = p.project_id AND 
	  	  p.project_id = at.project_id AND 
	  	  at.guide_id = g.guide_id;
	  	   
END; 
$$ LANGUAGE 'plpgsql';

/* Function to return the data to be presented on guide home page - project list */
CREATE OR REPLACE FUNCTION guideHomeData (IN guideID INT)
RETURNS TABLE (
	p_id INT, 
	p_name VARCHAR(50),
	s_class TEXT,
	tp_uname VARCHAR(50),
	t_noOfMembers INT,
	t_leaderName TEXT,
	p_dur VARCHAR(20),
	p_link VARCHAR(180),
	P_presDateTime TIMESTAMP WITH TIME ZONE, 
	P_repDateTime TIMESTAMP WITH TIME ZONE
) AS $$
DECLARE
BEGIN
	RETURN QUERY
	SELECT DISTINCT p.project_id, p.project_name, s.stream || ' ' || s.section, tp.username, t.num_of_mem, s.first_name || ' ' || s.last_name, p.project_duration, p.proj_repo_link, p.proj_pres_sub_date, p.proj_rep_sub_date  
	FROM students AS s, projects AS p, guides AS g, teams AS t, membership AS m, assigned_to AS at, associated_with AS aw, team_passwords AS tp
	WHERE g.guide_id = guideID AND 
	      g.guide_id = at.guide_id AND 
		  at.project_id = p.project_id AND 
		  p.project_id = aw.project_id AND 
		  aw.team_id = t.team_id AND 
		  t.team_id = m.team_id AND 
		  m.student_id = s.student_id AND 
		  s.student_id = t.leader_id AND 
		  t.team_id = tp.team_id;
END; 
$$ LANGUAGE 'plpgsql';

/* a view which lists the detials of entire guides and associated teams */
CREATE VIEW teamGuides AS 
SELECT DISTINCT tp.username, t.team_id, g.first_name || ' ' || g.last_name AS gname, at.guide_id 
FROM teams AS t, guides AS g, team_passwords AS tp, associated_with AS aw, assigned_to AS at 
WHERE t.team_id = aw.team_id AND 
	  aw.project_id = at.project_id AND 
	  g.guide_id = at.guide_id AND 
	  t.team_id = tp.team_id
ORDER BY team_id;