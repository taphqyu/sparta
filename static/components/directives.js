angular.module('myApp.directives', [])
    .directive('fileDiff', [function() {
        function render(scope, round, merge_base, branch_tip, element) {
            element.addClass('diff-view');

            diffoutputdiv = element[0];
            contextSize = null;
            inlinediff = false;

            base = difflib.stringAsLines(merge_base.contents || '');
            newtxt = difflib.stringAsLines(branch_tip.contents || '');

            var opcodes = [];

            if (merge_base.contents && !branch_tip.contents)
            {
                // deleted
                for (var i = 0; i < base.length; ++i) { opcodes.push(['delete', i, i+1, 0, 0]); }
            }
            else if (!merge_base.contents && branch_tip.contents)
            {
                // added
                for (var i = 0; i < newtxt.length; ++i) { opcodes.push(['insert', 0, 0, i, i+1]); }
            }
            else
            {
                // changed
                var sm = new difflib.SequenceMatcher(base, newtxt);
                opcodes = sm.get_opcodes();
            }

            while (diffoutputdiv.firstChild) diffoutputdiv.removeChild(diffoutputdiv.firstChild);
            contextSize = contextSize ? contextSize : null;

            // build the diff view and add it to the current DOM
            diffoutputdiv.appendChild(diffview.buildView({
                baseTextLines: (merge_base.contents ? base : null),
                newTextLines: (branch_tip.contents ? newtxt : null),
                opcodes: opcodes,
                baseTextName: merge_base.path + ' from ' + round.merge_base_branch + '@' + round.merge_base_commit.slice(0,7),
                newTextName: branch_tip.path + ' from ' + round.branch_tip_name + '@' + round.branch_tip_commit.slice(0,7),
                contextSize: contextSize,
                viewType: inlinediff
            }));
        }

        return {
            restrict: 'A',
            // scope: {
            //     merge_base: '=merge_base',
            //     branch_tip: '=branch_tip'
            // },
            link: function(scope, element, attrs) {
                scope.$watch('data', function(data) {
                    if (angular.isDefined(data.round) && data.round.$resolved &&
                        angular.isDefined(data.base_file) && data.base_file.$resolved &&
                        angular.isDefined(data.new_file) && data.new_file.$resolved)
                    {
                        render(scope, data.round, data.base_file, data.new_file, element);
                    }
                }, true);
            },
            replace: true
        };
    }])
    .directive('validateReviewBranches', [function() {
        return {
            restrict: 'A',
            require: 'ngModel',
            link: function(scope, ele, attrs, ctrl) {
                scope.$watchGroup(['base_branch', 'review_branch'], function() {
                    var exists = scope.review_branch && scope.base_branch;
                    var valid = scope.review_branch != scope.base_branch;
                    ctrl.$setValidity('review_delta', !exists || valid);
                });
            }
        };
    }])
;
