import flask
import sqlalchemy

db = None

def get():
    return db

def session():
    return db.session

def init(app):
    global db
    db = flask.ext.sqlalchemy.SQLAlchemy(app)

def noresult_is_404(func):
    def helper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlalchemy.orm.exc.NoResultFound:
            flask.abort(404)
    return helper
