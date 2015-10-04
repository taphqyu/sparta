What?
=====

Sparta is a web-based code review tool for git. It's designed for a highly iterative workflow and a
rebase/fast-forward-merge branching model.

Why?
====

I couldn't find a code review tool with all of the following features:

 * Robust defect/conversation tracking across many iterations.
  * Including when the branch under review is rebased or otherwise rewritten.
  * Including when the code changes under the comment.
  * Including long conversations that obscure the code if rendered inline.
 * View diffs against the target branch or against the last-reviewed version of a file.
  * Without this, it's difficult to spot small changes in the latest iteration of a large review.
 * Change the source or target branch midway through a review.
  * If you're reviewing **feature/widget** against **release/1.0**, but **release/1.0** gets merged
    to **master** before the review is complete, you can update the existing review to contain
    **feature/widget** against **release/1.1** without losing history/conversation/defects.

Setup
=====

Prerequisites: bower, python, pip.

```
$ bower install
$ pip install -r requirements.txt
$ python init_database.py
```

Run
===

Debug mode:

```
$ python app.py
```

Production mode:

TBD

Reset
=====

```
$ rm -f sparta.db
$ rm -rf sparta_project_cache/
$ python init_database.py
```
