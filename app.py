import flask
import flask.ext.sqlalchemy
import logging

import api

logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = flask.Flask(__name__)

def init_projects():
    import api.db as db
    import git
    import model

    for project in db.session().query(model.Project).all():
        logger.info('Updating cache for project %s (%d)...', project.short_name, project.project_id)
        git.update_project_cache(project.project_id, project.fetch_url)

@app.route('/api/<path:path>')
def unknown_api_endpoint(**kwargs):
    flask.abort(404)

@app.route('/')
@app.route('/<path:path>')
def delegate_to_angular(**kwargs):
    return app.send_static_file('app.html')

if __name__ == '__main__':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sparta.db'

    api.init_db(app)
    api.init_api(app)

    init_projects()

    app.run(debug=True)
