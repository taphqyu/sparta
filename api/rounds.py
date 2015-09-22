import flask_restful as rest

import db
import model

class SingleRound(rest.Resource):
    @db.noresult_is_404
    def get(self, round_id):
        return db.session().query(model.Round).filter_by(round_id=round_id).one().to_dict(
            include=['files'],
            childargs={
                'files': {
                    'include': ['merge_base_file', 'branch_tip_file'],
                    'exclude': ['tie_id', 'round_id', 'merge_base_file_id', 'branch_tip_file_id'],
                    'childargs': {
                        'merge_base_file': {'exclude': ['content_hash', 'file_contents']},
                        'branch_tip_file': {'exclude': ['content_hash', 'file_contents']},
                    }
                }
            })
