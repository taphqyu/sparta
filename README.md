What?
=====

Code review tool for git designed for a highly iterative workflow and a rebase/fast-forward-merge
branching model.

Why?
====

I couldn't find a code review tool with all of the following features:

 * Robust defect/conversation tracking across multiple iterations (including rebases).
 * View changes since the last "accepted" version of a file.

Setup
=====

1. Install [https://www.npmjs.com/](npm).
2. Install [http://bower.io/](bower).
3. Set up sparta:

```
$ bower install
$ python init_database.py
```

4. Run sparta in debug mode:

```
$ python app.py
```

Reset
=====

```
rm -f sparta.db
rm -rf sparta_project_cache/
python init_database.py
```
