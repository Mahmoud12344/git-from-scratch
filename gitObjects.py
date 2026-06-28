# from  import *
# from cli import *
from repository import *
from gitRef import ref_resolve

# from gitBlob import GitBlob
# import gitBlob
# from gitCommit import GitCommit

# this is used to read and write config files
from datetime import datetime
import os, sys, re

# this is a standard library used to match filenames  will be used for gitignore
from fnmatch import fnmatch

# for the hash i think this will be used for the commit hashes
import hashlib
from math import ceil

# i think this is a zib thing we will see :)
import zlib


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

    path = repo_file(repo, "objects", sha[:2], sha[2:])
    if not os.path.isfile(path):
        return None

    with open(path, "rb") as f:
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
                from gitCommit import GitCommit

                c = GitCommit
            case b"blob":
                from gitBlob import GitBlob

                c = GitBlob
            case b"tree":
                from gitTree import GitTree

                c = GitTree
            case b"tag":
                from gitTag import GitTag

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


def object_resolve(repo, name):
    """Resolve the name to an object hash in repo

    This function is aware of :
    - the HEAD literal
        -short and long hashes
        -tags,
        branches,
        remote branches,
    Execution Steps:
        1-creates a list of the candidates;
        2-make the compiled regex obj to find the sha ,
        3- check if the name is empty,
        4-if the name is HEAD we resolve the reference directly
        if it's a hex:
        check
            4.1- as ref,
            4.2-as tag,
            4.3- as branch
            4.4-as remote_branch

    """
    # 1
    cand = list()
    # 2
    hashRE = re.compile(r"^[0-9A-Fa-f]{4,40}$")
    # 3
    if not name.strip():
        return None
    # 4
    if name == "HEAd":
        return [ref_resolve(repo, "HEAD")]

    if hashRE.match(name):
        name = name.lower()
        pref = name[0:2]
        path = repo_dir(repo, "objects", pref, mkdir=False)
        if path:
            rem = name[2:]
            for f in os.listdir(path):
                if f.startswith(rem):
                    cand.append(pref + f)
    # 4.2
    as_tag = ref_resolve(repo, "refs/tags" + name)
    if as_tag:
        cand.append(as_tag)
    # 4.3
    as_branch = ref_resolve(repo, "refs/heads/" + name)
    if as_branch:
        cand.append(as_branch)

    # 4.4
    as_remote_branch = ref_resolve(repo, "refs/remotes/" + name)
    if as_remote_branch:  # Did we find a remote branch?
        cand.append(as_remote_branch)

    return cand


def object_find(repo, name, fmt=None, follow=True):
    """Search for an object in the repo:
    Execution steps :
    1-If we have a tag and fmt is anything else, we follow the tag.
    2-If we have a commit and fmt is tree, we return this commit's tree object
    3-In all other situations, we bail out: nothing else makes sense.
    """

    # this is a list of references
    sha = object_resolve(repo, name)
    if not sha:
        raise Exception(f"NO such a ref -> {name}")
    if len(sha) > 1:
        raise Exception(
            f"Ambiguous reference {name}: Candidates are:\n - {'\n - '.join(sha)}."
        )

    sha = sha[0]
    if not fmt:
        return sha

    while True:
        obj = object_read(repo, sha)
        if obj.fmt == fmt:
            return sha
        if not follow:
            return None
        if obj.fmt == b"tag":
            sha = obj.klvm[b"object"].decode("ascii")
        elif obj.fmt == b"commit" and fmt == b"tree":
            sha = obj.klvm[b"tree"].decode("ascii")
        else:
            return None

    #   wyag cat-file TYPE OBJECT


def cat_file(repo, obj, fmt=None):
    """imply prints the raw contents of an object to stdout,
    uncompressed and without the git header"""

    obj = object_read(repo, object_find(repo, obj, fmt=fmt))
    print(f"in cat_file the obj is --> {obj}")

    sys.stdout.buffer.write(obj.serialize())


def object_hash(fd, fmt, repo=None):
    data = fd.read()
    match fmt:
        case b"commit":
            from gitCommit import GitCommit

            obj = GitCommit(data)
        case b"tree":
            from gitTree import GitTree

            obj = GitTree(data)
        case b"blob":
            from gitBlob import GitBlob

            obj = GitBlob(data)
        case b"tag":
            from gitTag import GitTag

            obj = GitTag(data)
        case _:
            raise Exception(f"Unknown Type {fmt}!")

    return object_write(obj, repo=repo)
