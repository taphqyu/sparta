import flask_restful as rest

import db
import model

class FileContents(rest.Resource):
    @db.noresult_is_404
    def get(self, file_id):
        return db.session().query(model.File).filter_by(file_id=file_id).one().to_dict()
