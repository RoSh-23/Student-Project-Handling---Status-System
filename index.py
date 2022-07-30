import functools

from flask import Blueprint
from flask import render_template
from flask import url_for


bp = Blueprint('index', __name__)


@bp.route('/')
def index():
	return render_template('index/index.html')