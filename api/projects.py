import flask_restful as rest

import db
import git
import model

class ProjectList(rest.Resource):
    def get(self):
        results = []

        for project in db.session().query(model.Project).all():
            results.append(project.to_dict())

        return results

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
