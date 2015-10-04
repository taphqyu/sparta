angular.module('myApp.controllers', ['jsTag', 'myApp.services', 'myApp.directives', 'myApp.filters'])
    .controller('CreateReviewController', ['$scope', '$location', 'JSTagsCollection', 'Project', 'Review', 'Branches', 'BranchDiffs', function CreateReviewController($scope, $location, JSTagsCollection, Project, Review, Branches, BranchDiffs) {
        $scope.data = {};

        if (angular.isDefined($location.search().project))
        {
            $scope.review_project_id = $location.search().project;
        }

        // to be selected by the user
        $scope.base_branch = 'master';
        $scope.review_branch = null;

        $scope.review_project = null;
        $scope.data.projects = Project.query();

        $scope.$watch('base_branch', function () {
            console.log($scope.base_branch);
        });

        $scope.$watch('review_project_id', function () {
            if ($scope.review_project_id)
            {
                console.log($scope.review_project_id);
                // to be queried when the user selects branches
                $scope.data.branch_diff = null;
                $scope.data.branches = Branches.get({'project_id': $scope.review_project_id});
            }
            else
            {
                $scope.data.branch_diff = null;
                $scope.data.branches = null;
            }
        });

        $scope.reviewers = new JSTagsCollection();
        $scope.observers = new JSTagsCollection();

        // used by jsTag
        $scope.reviewerTagOptions = {
            'edit': false,
            'tags': $scope.reviewers,
            'texts': {
                'inputPlaceHolder': 'type to add reviewers'
            }
        };

        $scope.observerTagOptions = {
            'edit': false,
            'tags': $scope.observers,
            'texts': {
                'inputPlaceHolder': 'type to add observers'
            }
        };

        $scope.$watchGroup(['base_branch', 'review_branch'], function() {
            $scope.data.branch_diff = null;

            if (!$scope.data.branches || !$scope.base_branch || !$scope.review_branch)
            {
                return;
            }

            BranchDiffs.get({
                'project_id': $scope.review_project_id,
                'commit1': $scope.data.branches[$scope.base_branch].commit,
                'commit2': $scope.data.branches[$scope.review_branch].commit
            }, function(response) {
                $scope.data.branch_diff = response;
            });;
        });

        $scope.create_review = function() {
            var review = new Review();

            review.title = $scope.review_title;
            review.project = {
                project_id: $scope.review_project_id
            };
            review.latest_round = {
                merge_base_branch: $scope.base_branch,
                merge_base_commit: $scope.data.branches[$scope.base_branch].commit,
                branch_tip_name: $scope.review_branch,
                branch_tip_commit: $scope.data.branches[$scope.review_branch].commit,
            };

            review.reviewers = _.pluck($scope.reviewers.tags, 'value');
            review.observers = _.pluck($scope.observers.tags, 'value');

            review.$save(function(response) {
                console.log(response);
                if (angular.isDefined(response.review_id)) {
                    $location.path('/reviews/' + response.review_id);
                    $location.search('project', null);
                }
            });
        };
    }])
    .controller('AddProjectController', ['$scope', '$location', 'Project', function AddProjectController($scope, $location, Project) {
        $scope.add_project = function() {
            var project = new Project();

            project.name           = $scope.project_name;
            project.fetch_url      = $scope.fetch_url;
            project.branchlink_url = $scope.branchlink_url;
            project.commitlink_url = $scope.commitlink_url;

            project.$save(function(response) {
                console.log(response);
                if (angular.isDefined(response.project_id)) {
                    $location.path('/reviews/new');
                    $location.search('project', response.project_id);
                }
            });
        }
    }])
    .controller('ReviewListController', ['$scope', 'Review', function ReviewListController($scope, Review) {
        $scope.data = {};
        $scope.data.reviews = Review.query();
    }])
    .controller('ReviewController', ['$scope', '$location', '$routeParams', '$http', 'Review', 'BranchDiffs', 'SingleRound', 'FileContents', function ReviewController($scope, $location, $routeParams, $http, Review, BranchDiffs, SingleRound, FileContents) {
        $scope.change_status_names = {
            'A': 'added',
            'C': 'copied',
            'D': 'deleted',
            'M': 'modified',
            'R': 'modified', // map these to the same string
            'T': 'modified'  // map these to the same string
        };

        $scope.change_status_symbols = {
            'A': 'A',
            'C': 'C',
            'D': 'D',
            'M': 'M',
            'R': 'R',
            'T': 'T',
            'U': '-'
        };

        queryReview = function() {
            Review.get({'review_id': $routeParams.review_id}, function (response) {
                // assign in the callback instead of assigning the return value directly to prevent
                // flickering when this function gets called when a new round is updated.
                $scope.data.review = response;

                BranchDiffs.get({
                    'project_id': $scope.data.review.project.project_id,
                    'commit1': $scope.data.review.latest_round.branch_tip_commit,
                    'commit2': $scope.data.review.latest_round.branch_tip_name
                }, function (response) {
                    // assign in the callback instead of assigning the return value directly to prevent
                    // flickering when this function gets called when a new round is updated.
                    $scope.data.branch_age = response;
                });

                BranchDiffs.get({
                    'project_id': $scope.data.review.project.project_id,
                    'commit1': $scope.data.review.latest_round.merge_base_commit,
                    'commit2': $scope.data.review.latest_round.merge_base_branch
                }, function (response) {
                    // assign in the callback instead of assigning the return value directly to prevent
                    // flickering when this function gets called when a new round is updated.
                    $scope.data.base_age = response;
                });
            });
        };

        $scope.data = {};
        queryReview();

        $scope.saveReviewTitle = function() {
            // TODO: how to use $resource for this? or at least take routing info from it.
            $http.patch('/api/v1/reviews/' + $scope.data.review.review_id,
                        {'title': $scope.data.review.title});
        };

        $scope.setReviewStatus = function(status) {
            $scope.data.review.status = status;
            // TODO: how to use $resource for this? or at least take routing info from it.
            $http.patch('/api/v1/reviews/' + $scope.data.review.review_id,
                        {'status': $scope.data.review.status});
        };

        $scope.updateReviewToLatest = function() {
            $http.put('/api/v1/reviews/' + $scope.data.review.review_id, {
                'merge_base_branch': $scope.data.review.latest_round.merge_base_branch,
                'branch_tip_name': $scope.data.review.latest_round.branch_tip_name
            }).then(function (response) {
                queryReview();
            });
        };

        $scope.viewDiff = function(round_id, base_file_id, new_file_id) {
            $scope.data.round = SingleRound.get({'round_id': round_id});

            if ($routeParams.base_file != '') {
                $scope.data.base_file = FileContents.get({'file_id': base_file_id});
            }

            if ($routeParams.new_file_id != '') {
                $scope.data.new_file = FileContents.get({'file_id': new_file_id});
            }
        }

        $scope.showFileList = function() {
            $('#rounds-container').show();
            $('#filelist-show').hide();
            $('#filelist-hide').show();
            $('#diff-container').removeClass('col-sm-10');
            $('#diff-container').addClass('col-sm-7');
        }

        $scope.hideFileList = function() {
            $('#rounds-container').hide();
            $('#filelist-show').show();
            $('#filelist-hide').hide();
            $('#diff-container').addClass('col-sm-10');
            $('#diff-container').removeClass('col-sm-7');
        }
    }])
    .controller('DebugController', ['$scope', '$location', function DebugController($scope, $location) {
        $scope.location = $location;
    }])
;
