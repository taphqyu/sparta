import os
import subprocess

GIT_ADDED = 'A'
GIT_COPIED = 'C'
GIT_DELETED = 'D'
GIT_MODIFIED = 'M'
GIT_RENAMED = 'R'
GIT_TYPE_CHANGED = 'T'
GIT_UNCHANGED = 'U' # TODO: ligitimize: git really uses this to mean unmerged

def update_project_cache(project_id, fetch_path):
    cache_dir = cached_project_path(project_id)
    if os.path.exists(cache_dir):
        subprocess.check_output(['git', 'fetch'], cwd=cache_dir)
    else:
        os.makedirs(cache_dir)
        subprocess.check_output(['git', 'clone', '--mirror', fetch_path, cache_dir])

def cached_project_path(project_id):
    return os.path.join('sparta_project_cache', str(project_id))

def merge_base(project_id, first, second):
    project_path = cached_project_path(project_id)
    return subprocess.check_output(['git', 'merge-base', first, second], cwd=project_path).strip()

def show_file(project_id, commit, path):
    project_path = cached_project_path(project_id)
    return subprocess.check_output(['git', 'show', '%s:%s' % (commit, path)], cwd=project_path)

def branch_list(project_id):
    project_path = cached_project_path(project_id)
    results = []

    for line in subprocess.check_output(['git', 'branch', '--list', '-v', '--no-abbrev'], cwd=project_path).splitlines():
        pieces = line.split()

        if pieces[0] == '*':
            pieces = pieces[1:]

        results.append({
            'name': pieces[0],
            'commit': pieces[1],
            'commit_subject': ' '.join(pieces[2:])
        })

    return results

def rev_count_between(project_id, commit1, commit2):
    project_path = cached_project_path(project_id)
    commit1_heritage = subprocess.check_output(['git', 'rev-list', '--count', commit1, '^%s' % commit2], cwd=project_path)
    commit2_heritage = subprocess.check_output(['git', 'rev-list', '--count', commit2, '^%s' % commit1], cwd=project_path)
    return (int(commit1_heritage.strip()), int(commit2_heritage.strip()))

def rev_list_authors(project_id, commit1, commit2):
    project_path = cached_project_path(project_id)
    commits = subprocess.check_output(['git', 'rev-list', '--format=%aN', commit2, '^%s' % commit1], cwd=project_path).splitlines()
    authors = set()

    # output is one line of the commit hash and then one of the format spec for each commit.
    # since the format spec includes the commit, skip the commit header line
    for line in commits:
        if not line.startswith('commit '):
            authors.add(line.strip())

    return authors

def status_exists_in_preimage(status):
    return status in [GIT_DELETED, GIT_MODIFIED, GIT_RENAMED, GIT_TYPE_CHANGED, GIT_UNCHANGED]

def status_exists_in_postimage(status):
    return status in [GIT_ADDED, GIT_COPIED, GIT_MODIFIED, GIT_RENAMED, GIT_TYPE_CHANGED, GIT_UNCHANGED]

def parse_name_status(git_diff_name_status_z_output):
    results = []

    # Fields are separated by NULs in the output of `git diff --name-status -z`.
    pieces = git_diff_name_status_z_output.split('\0')

    # Each record consists of either two pieces (usually) or three pieces (if the preimage and
    # postimage paths are different, i.e. for copies and renames).
    # Loop while len > 1 instead of len > 0 because there's an extra empty field at the end.
    while len(pieces) > 1:
        # status contains the percent similarity for copies and renames, which we don't care about;
        # just grab the status name.
        status = pieces[0][0]

        # Preimage path is next.
        preimage_path = pieces[1]

        # For copies and renames, postimage path is next. Otherwise, postimage path is the same as
        # preimage path, and is not listed.
        if status in [GIT_COPIED, GIT_RENAMED]:
            postimage_path = pieces[2]
            pieces = pieces[3:]
        else:
            postimage_path = preimage_path
            pieces = pieces[2:]

        # For adds, there is no preimage file. For deletes, these is no postimage file.
        if not status_exists_in_preimage(status):
            preimage_path = None
        if not status_exists_in_postimage(status):
            postimage_path = None

        results.append((status, preimage_path, postimage_path))

    return results

def diff_name_status(project_id, merge_base, branch_tip):
    project_path = cached_project_path(project_id)
    return parse_name_status(subprocess.check_output(['git', 'diff', '-z', '--find-renames',
                                                      '--name-status', merge_base, branch_tip], cwd=project_path))
