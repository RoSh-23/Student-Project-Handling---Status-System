import psycopg2

import click 
from flask import current_app
from flask import g 
from flask.cli import with_appcontext 


# this function creates the database if does not exit and connects 
def get_db():
	if 'db' not in g:
		g.db = psycopg2.connect(dbname='*****', user='*****', host='*****', password='*****')

	return g.db

# this function closes the connection to the database 
def close_db(e=None):
	db = g.pop('db', None)

	if db is not None:
		db.close()	

# This function initializes the database 
def init_db():
	db = get_db()

	cursor = db.cursor()

	with current_app.open_resource('schema.sql') as file:
		cursor.execute(file.read().decode('utf8'))

	db.commit()	
	cursor.close()	


@click.command('init-db')
@with_appcontext
def init_db_command():
	''' Clear Existing data and create new tables. '''
	init_db()
	click.echo('Initialized the database.')

def init_app(app):
	app.teardown_appcontext(close_db)
	app.cli.add_command(init_db_command)
