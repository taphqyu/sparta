angular.module('myApp', ['ngRoute', 'xeditable', 'jsTag', 'myApp.controllers'])
    .config(['$routeProvider', '$locationProvider',
        function($routeProvider, $locationProvider) {
            $routeProvider
            .when('/', {
                redirectTo: '/reviews'
            })
            .when('/reviews', {
                templateUrl: '/static/partials/reviews-list.html',
                controller: 'ReviewListController'
            })
            .when('/reviews/new', {
                templateUrl: '/static/partials/create-review.html',
                controller: 'CreateReviewController'
            })
            .when('/reviews/:review_id', {
                templateUrl: '/static/partials/single-review.html',
                controller: 'ReviewController',
                reloadOnSearch: false
            })

            .when('/projects/new', {
                templateUrl: '/static/partials/add-project.html',
                controller: 'AddProjectController'
            })

            .when('/reviews/:review_id/change/:round_id/:merge_base-:branch_tip', {
                templateUrl: '/static/partials/diff.html',
                controller: 'DiffController'
            })
            .when('/reviews/:review_id/change/:round_id/-:branch_tip', {
                templateUrl: '/static/partials/diff.html',
                controller: 'DiffController'
            })
            .when('/reviews/:review_id/change/:round_id/:merge_base-', {
                templateUrl: '/static/partials/diff.html',
                controller: 'DiffController'
            })

            .otherwise({
                templateUrl: '/static/partials/debug.html',
                controller: 'DebugController'
            })
            ;

        $locationProvider.html5Mode(true);
    }])
    .run(function(editableOptions) {
        editableOptions.theme = 'bs3';
    })
;
