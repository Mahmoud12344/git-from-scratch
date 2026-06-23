# from  import *
from cli import *
from repository import *

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
    """this function specifies how to serialize the blob obj"""

    fmt = b"blob"

    def serialize(self):
        return self.blobdata

    def deserialize(self, data):
        self.blobdata = data
