import flask
import flask_restful as rest
import logging

import db
import git
import model

logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_round(review, base_branch, base_commit, review_branch, review_commit):

    # helper function to record the contents of a file at a specific commit
    def create_file(info):
        if info is None:
            return None

        if isinstance(info, model.File):
            return info

        (commit, path) = info
        contents = git.show_file(review.project_id, commit, path)
        result = model.File.find_or_create(db.session(), path, contents)
        db.session().add(result)
        return result

    def change_model_to_tuple(change):
        return (change.status_from_base,
                change.merge_base_file.path if change.merge_base_file is not None else None,
                change.branch_tip_file.path if change.branch_tip_file is not None else None)

    def map_path_forward(path, changes):
        if path is None:
            return None
        for change in changes:
            if path == change[1]:
                return change[2] or change[1]
        return path

    def map_path_backward(path, changes):
        if path is None:
            return None
        for change in changes:
            if path == change[2]:
                return change[1] or change[2]
        return path

    # there are four sets of changes which must be considered:
    #   1. current branch to current base
    #   2. current branch to previous branch
    #   3. previous branch to previous base
    #   4. current base to previous base
    # (1) and (2) are stored in the database, and (3) and (4) are used to inform them, e.g. by
    # identifying reverted files or files renamed upstream.

    if len(review.rounds) > 0:
        prev_round = review.rounds[-1]
        prev_branch = prev_round.branch_tip_name
        prev_commit = prev_round.branch_tip_commit
        changes_to_prev = git.diff_name_status(review.project_id, prev_commit, review_commit)
        #base_changes_to_prev_base = git.diff_name_status(review.project_id, prev_round.merge_base_commit, base_commit)
    else:
        prev_round = None
        prev_branch = None
        prev_commit = None
        changes_to_prev = []
        #base_changes_to_prev_base = None

    changes_to_base = git.diff_name_status(review.project_id, base_commit, review_commit)
    prev_changes_to_prev_base = [change_model_to_tuple(change) for change in prev_round.changes] if prev_round is not None else []

    paths_in_review = [change[2] or change[1] for change in changes_to_base]
    paths_in_review += [map_path_forward(change[2] or change[1], changes_to_prev) for change in prev_changes_to_prev_base]

    paths_in_review = set(paths_in_review)

    print '-------------------------------------------------------------------------------------'
    print paths_in_review

    round = model.Round(review=review,
                        round_index=len(review.rounds)+1,
                        merge_base_branch=base_branch,
                        merge_base_commit=base_commit,
                        branch_tip_name=review_branch,
                        branch_tip_commit=review_commit,
                        prev_tip_name=prev_branch,
                        prev_tip_commit=prev_commit)
    db.session().add(round)

    for current_path in paths_in_review:
        base_path = map_path_backward(current_path, changes_to_base)
        prev_path = map_path_backward(current_path, changes_to_prev)

        base_candidates = [change for change in changes_to_base if current_path == change[1] or current_path == change[2]]
        prev_candidates = [change for change in changes_to_prev if current_path == change[1] or current_path == change[2]]

        # changed from base   changed from prev   meaning
        # ----------------------------------------------------------------------------------------------------------
        # yes                 yes                 change on this branch which was changed since the last round
        # yes                 no                  change on this branch which is the same since the last round
        # no                  yes                 change originally on this branch which was committed upstream
        # no                  no                  change originally on this branch which was committed upstream before last round

        if len(base_candidates) == 1 and len(prev_candidates) == 1:
            # change on this branch which was changed since the last round
            status_from_base = base_candidates[0][0]
            status_from_prev = prev_candidates[0][0]
            branch_tip_file = (review_commit, current_path) if git.status_exists_in_postimage(status_from_base) else None
            merge_base_file = (base_commit, base_path) if git.status_exists_in_preimage(status_from_base) else None
            prev_tip_file = (prev_commit, prev_path) if git.status_exists_in_preimage(status_from_prev) else None

        elif len(base_candidates) == 1 and len(prev_candidates) == 0:
            # change on this branch which is the same since the last round
            status_from_base = base_candidates[0][0]
            status_from_prev = 'U'
            branch_tip_file = (review_commit, current_path) if git.status_exists_in_postimage(status_from_base) else None
            merge_base_file = (base_commit, base_path) if git.status_exists_in_preimage(status_from_base) else None
            prev_tip_file = branch_tip_file

        elif len(base_candidates) == 0 and len(prev_candidates) == 1:
            # change originally on this branch which was reverted or committed upstream
            status_from_base = 'U'
            status_from_prev = prev_candidates[0][0]
            branch_tip_file = (review_commit, current_path) if git.status_exists_in_postimage(status_from_prev) else None
            merge_base_file = branch_tip_file
            prev_tip_file = (prev_commit, prev_path) if git.status_exists_in_preimage(status_from_prev) else None

        elif len(base_candidates) == 0 and len(prev_candidates) == 0:
            # change originally on this branch which was reverted or committed upstream before last round
            ghost_candidates = [change for change in prev_changes_to_prev_base if map_path_forward(change[2] or change[1], changes_to_prev) == current_path]
            assert(len(ghost_candidates) == 1)

            status_from_base = 'U'
            status_from_prev = 'U'
            branch_tip_file = ghost_candidates[0].branch_tip_file
            merge_base_file = ghost_candidates[0].branch_tip_file
            prev_tip_file = ghost_candidates[0].branch_tip_file

        else:
            logger.error('illegal number of (base, prev) candidates (%d, %d) for current path %s',
                         len(base_candidates),
                         len(prev_candidates),
                         current_path)
            continue

        merge_base_file = create_file(merge_base_file)
        branch_tip_file = create_file(branch_tip_file)
        prev_tip_file = create_file(prev_tip_file)

        change = model.Change(round=round,
                              status_from_base=status_from_base,
                              status_from_prev=status_from_prev,
                              merge_base_file=merge_base_file,
                              branch_tip_file=branch_tip_file,
                              prev_tip_file=prev_tip_file)
        db.session().add(change)
        logger.debug('Adding change: %s %s %s //// %s %s %s',
                     merge_base_file.path if merge_base_file else None,
                     status_from_base,
                     branch_tip_file.path if branch_tip_file else None,
                     prev_tip_file.path if prev_tip_file else None,
                     status_from_prev,
                     branch_tip_file.path if branch_tip_file else None)

    return round


class ReviewList(rest.Resource):
    def get(self):
        results = []

        for review in db.session().query(model.Review).all():
            review_dict = review.to_dict(include=['project'], exclude=['project_id'])

            if len(review.rounds) > 0:
                review_dict['latest_round'] = review.rounds[-1].to_dict(exclude=['review_id'])
            else:
                review_dict['latest_round'] = None

            results.append(review_dict)

        return results

    def post(self):
        review_req = flask.request.json
        print review_req

        try:
            project = review_req['project']
            title = review_req.get('title', '')
            latest_round = review_req['latest_round']

            project_id = project['project_id']
            base_branch = latest_round['merge_base_branch']
            base_commit = latest_round['merge_base_commit']
            review_branch = latest_round['branch_tip_name']
            review_commit = latest_round['branch_tip_commit']
            reviewers = review_req.get('reviewers', []) or []
            observers = review_req.get('observers', []) or []

        except KeyError as e:
            flask.abort(400, str(e))

        # TODO: make sure there isn't already a review with these specs

        # find common ancestor
        base_commit = git.merge_base(project_id, base_commit, review_commit)
        authors = list(git.rev_list_authors(project_id, base_commit, review_commit))
        reviewers = list(set(reviewers))
        observers = list(set(observers))

        logger.debug('Creating review from %s@%s -> %s@%s; title=%s',
                     review_branch,
                     review_commit[0:7],
                     base_branch,
                     base_commit[0:7],
                     title)

        review = model.Review(project_id=project_id, status='new', title=title, authors=authors, reviewers=reviewers, observers=observers)
        db.session().add(review)

        round = create_round(review, base_branch, base_commit, review_branch, review_commit)
        db.session().add(round)

        db.session().commit()

        logger.debug('Review %d: created.', review.review_id)
        return {'review_id': review.review_id}

class Review(rest.Resource):
    @db.noresult_is_404
    def get(self, review_id):
        review = db.session().query(model.Review).filter_by(review_id=review_id).one()
        result = review.to_dict(
            include=['project', 'rounds'],
            exclude=['project_id'],
            childargs={
                'rounds': {
                    'include': ['changes'],
                    'exclude': ['review_id'],
                    'childargs': {
                        'changes': {
                            'include': ['merge_base_file', 'branch_tip_file', 'prev_tip_file'],
                            'exclude': ['merge_base_file_id', 'branch_tip_file_id', 'prev_tip_file_id'],
                            'childargs': {
                                'merge_base_file': {'exclude': ['content_hash', 'contents']},
                                'branch_tip_file': {'exclude': ['content_hash', 'contents']},
                                'prev_tip_file': {'exclude': ['content_hash', 'contents']},
                            }
                        }
                    }
                }
            })

        if len(review.rounds) > 0:
            result['latest_round'] = review.rounds[-1].to_dict(exclude=['review_id'])
        else:
            result['latest_round'] = None

        return result

    def patch(self, review_id):
        # for editing minor properties like titles
        print flask.request.json
        review = db.session().query(model.Review).filter_by(review_id=review_id).one()

        for (k, v) in flask.request.json.iteritems():
            if hasattr(review, k):
                setattr(review, k, v)

        db.session().commit()

        return self.get(review_id)

    def put(self, review_id):
        # for adding rounds
        print flask.request.json

        review = db.session().query(model.Review).filter_by(review_id=review_id).one()
        branches = git.branch_list(review.project_id)

        # extract and validate arguments
        base_branch = flask.request.json.get('merge_base_branch')
        review_branch = flask.request.json.get('branch_tip_name')

        base_commit = [branch for branch in branches if branch['name'] == base_branch]
        review_commit = [branch for branch in branches if branch['name'] == review_branch]

        if review_branch is None or len(base_commit) != 1 or len(review_commit) != 1:
            flask.abort(400)

        base_commit = base_commit[0]['commit']
        review_commit = review_commit[0]['commit']

        # replace HEAD of base branch with merge-base of the two branches
        base_commit = git.merge_base(review.project_id, base_commit, review_commit)

        # if this is the same as the latest round, don't add it
        latest_round = review.rounds[-1]

        if (latest_round.merge_base_branch == base_branch and
            latest_round.merge_base_commit == base_commit and
            latest_round.branch_tip_name == review_branch and
            latest_round.branch_tip_commit == review_commit):
            return self.get(review_id)

        # create round from base to branch
        round = create_round(review, base_branch, base_commit, review_branch, review_commit)
        db.session().add(round)

        db.session().commit()

        return self.get(review_id)
