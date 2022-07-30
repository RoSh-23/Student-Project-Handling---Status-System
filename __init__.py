import os

from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request

def pageNotFound(e):
    # if a request comes from our team URL space 
    if request.path.startswith('/teamDashboard/'):
        return render_template('team_dashboard_bp/404.html'), 404
    elif request.path.startswith('/guideDashboard/'):
        return render_template('guide_dashboard_bp/404.html'), 404   
    else:
        return render_template('errors/404.html'), 404

def create_app(test_config=None):
    # create and configure the app
    SPH_SS_App = Flask(__name__, instance_relative_config=True)
    SPH_SS_App.config.from_mapping(
        SECRET_KEY = 'dev' 
    )    

    SPH_SS_App.config['PROJ_REPORT_PRES_UPLOAD_DIRECTORY'] = "E:\\Projects_College_UG_BCA_Official\\SEM_6\\BCA_Sem6_Project\\projRepoPresUploads\\"
    SPH_SS_App.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024; # 20MB
    SPH_SS_App.config['ALLOWED_REPORT_EXTENSIONS'] = ['.doc', '.docx', '.pdf', '.pages', '.odt']
    SPH_SS_App.config['ALLOWED_PRES_EXTENSIONS'] = ['.pdf', '.ppt', '.pptx', '.odp', '.key']

    if test_config is None:
        # load the instance config, if it exists, when not testing
        SPH_SS_App.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        SPH_SS_App.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(SPH_SS_App.instance_path)
    except OSError:
        pass

    from SPH_SS_App import db 

    db.init_app(SPH_SS_App)

    SPH_SS_App.register_error_handler(404, pageNotFound)
    

    from SPH_SS_App.guide_auth_bp import guide_auth_bp
    from SPH_SS_App.team_auth_bp import team_auth_bp
    from SPH_SS_App import index
    from SPH_SS_App.guide_dashboard_bp import guide_dashboard_bp
    from SPH_SS_App.team_dashboard_bp import team_dashboard_bp

    
    SPH_SS_App.register_blueprint(team_auth_bp.team_auth_bp)
    SPH_SS_App.register_blueprint(guide_auth_bp.guide_auth_bp)
    SPH_SS_App.register_blueprint(index.bp)
    SPH_SS_App.register_blueprint(team_dashboard_bp.team_dashboard_bp)
    SPH_SS_App.register_blueprint(guide_dashboard_bp.guide_dashboard_bp)

    return SPH_SS_App