from gitObjects import GitObject

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


class GitTree(GitObject):
    fmt = b"tree"

    def deserialize(self, data):
        self.items = tree_parse(data)

    def serialize(self):
        return tree_serialize(self)

    def init(self):
        self.items = list()
