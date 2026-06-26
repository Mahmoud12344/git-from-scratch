from gitObjects import *

# Tree format :
# [mode] space [path] 0x00 [sha-1]


def tree_parse(raw):
    """this is the parent parser that will be use in deserialization ,
    and it's just calling the tree_parse_one
    """
    pos = 0
    max_ = len(raw)
    ret = list()

    while pos < max_:
        pos, data = tree_parse_one(pos, raw)
        ret.append(data)

    return ret


def tree_parse_one(raw, start=0):
    """Parsing a single unit of [mode] space [path] 0x00 [sha-1]
    Execution steps :
    1- find the space terminator of the mode,
    2-red from the start to the end of the mode ,
    2.1-normalize to 6 bits if needed,
    3-find the null delimiter of the path,
    4-read the path,
    5-read the sha:
    5.1-normalize if needed
    """
    # 1
    sp = raw.find(b" ", start)
    assert sp - start == 5 or sp - start == 6
    # 2
    mode = raw[start:sp]
    # 2.1
    if len(mode) == 5:
        mode = b"0" + mode
    # 3
    ndl = raw.find(b"\x00", sp)
    # 4
    path = raw[sp + 1 : ndl]
    raw_sha = int.from_bytes(raw[ndl + 1 : ndl + 21], "big")
    # 5
    sha = format(raw_sha, "040x")
    return ndl + 21, GitTreeLeaf(mode, path.decode("utf8"), sha)


class GitTreeLeaf(object):
    """This is a single object wrapper for a single record
    [mode] space [path] 0x00 [sha-1]
    """

    def __init__(self, mode, path, sha):
        self.mode = mode
        self.path = path
        self.sha = sha


def _tree_leaf_sort_key(leaf: GitTreeLeaf):
    """this is a helper function used in the sorting
    , only job is adding a '/' to end of the direct"""

    if leaf.mode.startswith(b"4"):
        return leaf.path + "/"

    else:
        return leaf.path


def tree_serialize(obj: GitTree):
    """build the tree format again which is
    mode space path null sha
    """
    obj.items.sort(key=_tree_leaf_sort_key)
    ret = b""
    for i in obj.items:
        ret += i.mode
        ret += b" "
        ret += i.path.encode("utf8")
        ret += b"\x00"
        sha = int(i.sha, 16)
        ret += sha.to_bytes(20, byteorder="big")

        return ret


def ls_tree(repo, ref, recursive=None, prefix=""):
    """Execution steps:
    1-find the full name of the ref,
    2-read the object ,
    3-loop for the items in the tree,
    check for the length of the mode to and check if it's 5 or i's not
    to know the type of the current object in the tree,
    4- match the type
    5- branch if it's a leaf print and terminate ,
    else make a recursive call
    """
    # 1
    sha = object_find(repo, ref, fmt=b"tree")
    # 2
    obj = object_read(repo, sha)
    # 3
    for item in obj.items:
        if len(item.mode) == 5:
            _type = item.mode[0:1]
        else:
            _type = item.mode[0:2]
        match _type:
            case b"04":
                _type = "tree"
            case b"10":
                _type = "blob"  # < regular file
            case b"12":
                _type = "blob"  # <symlink,
            case b"16":
                _type = "commit"
            case _:
                raise Exception(f"Weird tree leaf mode {item.mode}")

        if not (recursive and type == "tree"):  # This is a leaf
            print(
                f"{'0' * (6 - len(item.mode)) + item.mode.decode('ascii')} {type} {item.sha}\t{os.path.join(prefix, item.path)}"
            )
        else:  # This is a branch, recurse
            ls_tree(repo, item.sha, recursive, os.path.join(prefix, item.path))


class GitTree(GitObject):
    fmt = b"tree"

    def deserialize(self, data):
        self.items = tree_parse(data)

    def serialize(self):
        return tree_serialize(self)

    def init(self):
        self.items = list()
