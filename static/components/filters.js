angular.module('myApp.filters', [])
    .filter('sort_by_filepath', function(){
        return function(input) {
            return input.sort(function(a, b) {
                if (a.branch_tip_file) {
                    a = a.branch_tip_file.path;
                } else if (a.prev_tip_file) {
                    a = a.prev_tip_file.path;
                } else if (a.merge_base_file) {
                    a = a.merge_base_file.path;
                } else {
                    a = null;
                }

                if (b.branch_tip_file) {
                    b = b.branch_tip_file.path;
                } else if (b.prev_tip_file) {
                    b = b.prev_tip_file.path;
                } else if (b.merge_base_file) {
                    b = b.merge_base_file.path;
                } else {
                    b = null;
                }

                return a.localeCompare(b);
            });
        };
    })
;
