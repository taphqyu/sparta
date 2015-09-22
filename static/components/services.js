angular.module('myApp.services', ['ngResource'])
    .factory('Project', function($resource) {
        return $resource('/api/v1/projects/:project_id', {'project_id': '@project_id'});
    })
    .factory('Branches', function($resource) {
        return $resource('/api/v1/projects/:project_id/branches', {'project_id': '@project_id'});
    })
    .factory('BranchDiffs', function($resource) {
        return $resource('/api/v1/projects/:project_id/branches/:commit1/:commit2');
    })
    .factory('Review', function($resource) {
        return $resource('/api/v1/reviews/:review_id', {'review_id': '@review_id'});
    })
    .factory('SingleRound', function($resource) {
        return $resource('/api/v1/rounds/:round_id', {'round_id': '@round_id'});
    })
    .factory('FileContents', function($resource) {
        return $resource('/api/v1/files/:file_id', {'file_id': '@file_id'});
    })
    .value('version', '0.1');
