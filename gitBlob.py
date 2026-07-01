import os

from gitIndex import GitIndexEntry, index_read, index_write
from gitObjects import GitObject, object_hash


class GitBlob(GitObject):
    """git blob is a git object represents a File in the git slang"""

    fmt = b"blob"

    def serialize(self):
        return self.blobdata

    def deserialize(self, data):
        self.blobdata = data


def rm(repo, paths, delete=True, skip_missing=False):
    index = index_read(repo)
    worktree = os.path.realpath(repo.worktree)
    abspathes = set()
    for path in paths:
        abspathe = os.path.realpath(path)
        if os.path.commonpath([worktree, abspathe]) != worktree:
            raise Exception(
                f"Can't remove a path outside the working tree{repo.worktree}",
                f"\n{paths}",
            )
        abspathes.add(abspathe)
    keptent = list()
    remove = list()
    matched = set()

    for ent in index.entries:
        full_path = os.path.realpath(os.path.join(repo.worktree, ent.name))
        matched_target = None
        for abspathe in abspathes:
            if full_path == abspathe or full_path.startswith(abspathe + os.sep):
                matched_target = abspathe
                break

        if matched_target:
            remove.append(full_path)
            matched.add(matched_target)
        else:
            keptent.append(ent)

    missing = abspathes - matched
    if len(missing) > 0 and not skip_missing:
        raise Exception(f"Cannot remove paths not in the index: {missing}")

    # Physically delete paths from filesystem.
    if delete:
        for path in remove:
            os.unlink(path)

    # Update the list of entries in the index, and write it back.
    index.entries = keptent
    index_write(repo, index)


def add(repo, paths, delete=True, skip_missing=False):

    # First remove all paths from the index, if they exist.
    rm(repo, paths, delete=False, skip_missing=True)

    worktree = os.path.realpath(repo.worktree)

    # Convert the paths to pairs: (absolute, relative_to_worktree).
    # Also delete them from the index if they're present.
    clean_paths = set()
    for path in paths:
        abspath = os.path.realpath(path)
        if os.path.commonpath([worktree, abspath]) != worktree:
            raise Exception(f"Not a file, or outside the worktree: {paths}")
        if os.path.isfile(abspath):
            relpath = os.path.relpath(abspath, repo.worktree)
            clean_paths.add((abspath, relpath))
        elif os.path.isdir(abspath):
            for root, dirs, files in os.walk(abspath):
                dirs[:] = [
                    d
                    for d in dirs
                    if os.path.realpath(os.path.join(root, d)) != repo.gitdire
                ]
                for filename in files:
                    full_path = os.path.realpath(os.path.join(root, filename))
                    relpath = os.path.relpath(full_path, repo.worktree)
                    clean_paths.add((full_path, relpath))
        else:
            raise Exception(f"Not a file, or outside the worktree: {paths}")

    index = index_read(repo)

    for abspath, relpath in sorted(clean_paths, key=lambda item: item[1]):
        with open(abspath, "rb") as fd:
            sha = object_hash(fd, b"blob", repo)

            stat = os.stat(abspath)

            ctime_s = int(stat.st_ctime)
            ctime_ns = stat.st_ctime_ns % 10**9
            mtime_s = int(stat.st_mtime)
            mtime_ns = stat.st_mtime_ns % 10**9

            entry = GitIndexEntry(
                ctime=(ctime_s, ctime_ns),
                mtime=(mtime_s, mtime_ns),
                dev=stat.st_dev,
                ino=stat.st_ino,
                mode_type=0b1000,
                mode_perms=0o644,
                uid=stat.st_uid,
                gid=stat.st_gid,
                fsize=stat.st_size,
                sha=sha,
                flag_assume_valid=False,
                flag_stage=False,
                name=relpath,
            )
            index.entries.append(entry)

    # Write the index back
    index_write(repo, index)
