from gitObjects import *


class GitBlob(GitObject):
    """git blob is a git object represents a File in the git slang"""

    fmt = b"blob"

    def serialize(self):
        return self.blobdata

    def deserialize(self, data):
        self.blobdata = data
