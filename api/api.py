import flask_restful as rest

import files
import projects
import reviews
import rounds

api = None

def init(app):
    global api
    api = rest.Api(app)

    api.add_resource(projects.ProjectList,  '/api/v1/projects')
    api.add_resource(projects.BranchList,   '/api/v1/projects/<int:project_id>/branches')
    api.add_resource(projects.BranchDiff,   '/api/v1/projects/<int:project_id>/branches/<string:commit1>/<string:commit2>')

    api.add_resource(reviews.ReviewList,    '/api/v1/reviews')
    api.add_resource(reviews.Review,        '/api/v1/reviews/<int:review_id>')
    api.add_resource(rounds.SingleRound,    '/api/v1/rounds/<int:round_id>')
    api.add_resource(files.FileContents,    '/api/v1/files/<int:file_id>')

    return api
