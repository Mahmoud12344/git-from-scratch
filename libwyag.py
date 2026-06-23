import cli

## this is the module used for parsing the input and makes the help/use menuses
import argparse

# this is used to read and write config files
import configparser
from datetime import datetime
import grp, pwd, os, sys, re

# this is a standard library used to match filenames  will be used for gitignore
from fnmatch import fnmatch

# for the hash i think this will be used for the commit hashes
import hashlib
from math import ceil

# i think this is a zib thing we will see :)
import zlib

argparser = argparse.ArgumentParser(description="this is a small git reblica")

argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True


"""
- Execution steps 
1- the  entry point is the ./wyag with the subcommans 
2-the main gits called form the wyag 
3- main function has the grgv from command line arguments we take every thing expt the fitst argument 
4 we parse the input 
5 -match the cmd function 
"""


def main(argv=sys.argv[1:]):
    args = cli.parse_args(argv)

    match args.command:
        # case 'add': cmd_add(args)
        # # case 'cat-file':cmd_cat_file(a)
        # case 'check-gitignore':cmd_check_gitignore(args)
        # case 'checkout':cmd_checkout(args)
        # # case 'commit':cmd_commit(args)
        # case "hash-object"  : cmd_hash_object(args)
        case "init":
            cmd_init(args)
        # case "log"          : cmd_log(args)
        # case "ls-files"     : cmd_ls_files(args)
        # case "ls-tree"      : cmd_ls_tree(args)
        # case "rev-parse"    : cmd_rev_parse(args)
        # case "rm"           : cmd_rm(args)
        # case "show-ref"     : cmd_show_ref(args)
        # case "status"       : cmd_status(args)
        # case "tag"          : cmd_tag(args)
        # case _              : print("Bad command.")


class GitRepository(object):
    """A git repo"""

    worktree = None
    gitdire = None
    conf = None

    def __init__(self, path, force=False):

        self.worktree = path
        self.gitdire = os.path.join(path, ".mygit")

        if not (force or os.path.isdir(self.gitdire)):
            raise Exception(f"not a git repo {path}")

        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("conf file is missing")

        if not force:
            verse = int(self.conf.get("core", "repositoryformatversion"))
            if verse != 0:
                raise Exception(f"unsupported repoformatversion {verse}")


def repo_path(repo, *path):
    """compute path under repo's gitdir,"""

    return os.path.join(repo.gitdire, *path)


# this makes sure that the parent for a file exist
def repo_file(repo, *path, mkdir=False):
    """Same as repo_path, but create dirname(*path) if absent.  For
    example, repo_file(r, \"refs\", \"remotes\", \"origin\", \"HEAD\") will create
    .gitmy/refs/remotes/origin."""

    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)


def repo_dir(repo, *path, mkdir=False):
    """same as repo_path , but mkdir *Path if absent if mkdir"""

    path = repo_path(repo, *path)

    if os.path.exists(path):
        if os.path.isdir(path):
            return path
        else:
            raise Exception(f"Not a directory {path}")

    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None


def repo_create(path):
    """create a new repo at path
    execution steps :
    1-instantiation of the GitRepo obj ,
    2.1-checking if the path is not a path to a directory
    2.2-if the .mygit exists raise exception
    2.3-if all of this does not satisfy , we creat the work tree
    3 - creates the skeleton of the .mygit
    4- make the head
    5- make the default config file"""

    repo = GitRepository(path, True)

    ## check if the repo exist of it's an empty dir

    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception(f"{path} is not a dire ")
        if os.path.exists(repo.gitdire):
            raise Exception(f" {path} is not Empty")

    else:
        os.makedirs(repo.worktree)

    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    # .mygit/description
    with open(repo_file(repo, "description "), "w") as f:
        f.write('un named repo , open file "description"  to name the repo\n ')
    # .mygit/HEAD

    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/master\n")

    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)

    return repo


def repo_default_config():
    ret = configparser.ConfigParser()
    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")
    return ret


def cmd_init(args):
    """
    The Repo init logic
    1-receive the command as a path.command in the main matcher
    2 this function "cmd-init(args)" gets called and calles repo_creat(args.path)

    """
    repo_create(args.path)


def repo_find(path=".", required=True):
    """This function is used to find where is the .mygit repo and returning the absoulute path to it
    excution steps
    1-we check this path if it contains this .mygit
    1.1-if it existt we return a GitRepo obj
    2- if this path doesn't have the the .mygit we go back up one level 'parent'
    2.1- we check if this parent is the root if so it's required we raise an exception if not we return None
    3 - we recurse this function again"""

    path = os.path.realpath(path)
    if os.path.isdir(os.path.join(path, ".mygit")):
        return GitRepository(path)
    pr = os.path.realpath(os.path.join(path, ".."))

    # base case we've reached the root
    if pr == path:
        if required:
            raise Exception("Not a GitRepo")
        else:
            return None

    return repo_find(pr, required)


class GitObject(object):

    def __init__(self, data=None):

        if data != None:
            self.deserialize(data)
        else:
            self.init()

    def serialize(self, repo):
        """must be implemented by a subclass to make a bitString imp for the data"""
        raise Exception("UnImplemented")

    def deserialize(self, data):

        raise Exception("UnImplemented")

    def init(self):
        pass


def object_read(repo, sha):
    """this reads a git sha-1 hash and return the exact object
    1-read the path by repo_file
    1.1-check the file type

    2- open the file as a binary type
    3-decompress the obj to the a redable format type space size null content
    4 read the obj type
    5-read and validate the obj size
    6-pick the constructor
    7- return"""

    path = repo_file(repo, "object", sha[:2], sha[2:])

    if not os.path.isfile(path):
        return None

    with open(path, "fb") as f:
        raw = zlib.decompress(f.read())
        ## the obj type plop commit ,,,
        x = raw.find(b" ")
        fmt = raw[0:x]

        ## reading the size

        y = raw.find(b"\x00", x)
        size = int(raw[x:y].decode("ascii"))

        if size != len(raw) - y - 1:
            raise Exception(f"Mall formed obj {sha}:bad length")

        match fmt:
            case b"commit":
                c = GitCommit
            case b"blob":
                c = GitBlob
            case b"tree":
                c = GitTree
            case b"tag":
                c = GitTag
            case _:
                raise Exception(f"Unknown type {fmt.decode('ascii')} for object {sha}")

    return c(raw[y + 1 :])


def object_write(obj, repo=None):
    """this is a util function used to write the git objects to there correct place,
    1- use the repecteve searialization method in the obj
    2-make the raw header,
    3-hash it ,
    4-compute the path and wite the file"""

    data = obj.serialize()
    result = obj.fmt + b" " + str(len(data)).encode() + b"\x00" + data
    sha = hashlib.sha1(result).hexdigest()
    if repo:
        path = repo_file(repo, "objects", sha[0:2], sha[2:], mkdir=True)

        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(zlib.compress(result))

    return sha


class GitBlob(GitObject):
    fmt = b"blob"

    def serialize(self):
        return self.blobdata

    def deserialize(self, data):
        self.blobdata = data
