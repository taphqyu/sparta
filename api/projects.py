import flask
import flask_restful as rest
import logging

import db
import git
import model

from sqlalchemy.exc import IntegrityError

logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ProjectList(rest.Resource):
    def get(self):
        results = []

        for project in db.session().query(model.Project).all():
            results.append(project.to_dict())

        return results

    def post(self):
        project_req = flask.request.json
        print project_req

        try:
            project_name = project_req['name']
            fetch_url = project_req['fetch_url']
            branchlink_url = project_req.get('branchlink_url', '')
            commitlink_url = project_req.get('commitlink_url', '')

        except KeyError as e:
            flask.abort(400, str(e))

        logger.debug('Creating project "%s" -> %s', project_name, fetch_url)

        project = model.Project(name=project_name,
                                fetch_url=fetch_url,
                                branchlink_url=branchlink_url,
                                commitlink_url=commitlink_url)

        db.session().add(project)

        try:
            db.session().commit()
        except IntegrityError:
            db.session().rollback();
            return {'error': 'A project named "%s" already exists.' % project_name}

        logger.info('Updating cache for project "%s" (%d)...', project.name, project.project_id)
        git.update_project_cache(project.project_id, project.fetch_url)

        return {'project_id': project.project_id}

class BranchList(rest.Resource):
    def get(self, project_id):
        return dict((branch['name'], branch) for branch in git.branch_list(project_id))

class BranchDiff(rest.Resource):
    def get(self, project_id, commit1, commit2):
        divergence = git.rev_count_between(project_id, commit1, commit2)
        return {
            'base': divergence[0],
            'branch': divergence[1]
        }
