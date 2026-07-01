from gitIndex import GitIndexEntry
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
        pos, data = tree_parse_one(raw, pos)
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


def tree_checkout(repo, tree, path):
    """Execution  steps:
    for each item in the tree
    1-read the received object ,
    2-identify the dest path which is the path + the object internal path,
    3 - branch :
        if the received object is a tree : recurse
        elif write this fle

    """
    for item in tree.items:
        obj = object_read(repo, item.sha)
        dest = os.path.join(path, item.path)
        if obj.fmt == b"tree":
            os.mkdir(dest)
            tree_checkout(repo, obj, dest)
        elif obj.fmt == b"blob":
            with open(dest, "wb") as fb:
                fb.write(obj.blobdata)


def tree_to_dict(repo, ref, prefix="")->dict:
    """A recursive function to convert a full
    tree into a dic with full paths,"""
    ret = dict()
    tree_sha = object_find(repo, ref, fmt=b"tree")
    tree = object_read(repo, tree_sha)
    for leaf in tree.items:
        full_path=os.path.join(prefix,leaf.path)
        is_subtree=leaf.mode.startswith(b'04')
        
        if is_subtree:
            ret.update(tree_to_dict(repo,leaf.sha,full_path))
        else:
            ret[full_path]=leaf.sha
            
    return ret
class GitTree(GitObject):
    fmt = b"tree"

    def deserialize(self, data):
        self.items = tree_parse(data)

    def serialize(self):
        return tree_serialize(self)

    def init(self):
        self.items = list()


def branch_git_active(repo):

    with open(repo_file(repo, "HEAD"), "r") as f:
        head = f.read()
        if head.startswith("ref: refs/heads/"):
            return head[16:-1]
        else:
            return False

def tree_from_index(repo, index):
    contents = dict()
    contents[""] = list()

    # Enumerate entries, and turn them into a dictionary where keys
    # are directories, and values are lists of directory contents.
    for entry in index.entries:
        dirname = os.path.dirname(entry.name)

        # We create all dictonary entries up to root ("").  We need
        # them *all*, because even if a directory holds no files it
        # will contain at least a tree.
        key = dirname
        while key != "":
            if not key in contents:
                contents[key] = list()
            key = os.path.dirname(key)

        # For now, simply store the entry in the list.
        contents[dirname].append(entry)

    # Get keys (= directories) and sort them by length, descending.
    # This means that we'll always encounter a given path before its
    # parent, which is all we need, since for each directory D we'll
    # need to modify its parent P to add D's tree.
    sorted_paths = sorted(contents.keys(), key=len, reverse=True)

    # This variable will store the current tree's SHA-1.  After we're
    # done iterating over our dict, it will contain the hash for the
    # root tree.
    sha = None

    # We go through the sorted list of paths (dict keys)
    for path in sorted_paths:
        # Prepare a new, empty tree object
        tree = GitTree()

        # Add each entry to our new tree, in turn
        for entry in contents[path]:
            # An entry can be a normal GitIndexEntry read from the
            # index, or a tree we've created.
            if isinstance(entry, GitIndexEntry): # Regular entry (a file)

                # We transcode the mode: the entry stores it as integers,
                # we need an octal ASCII representation for the tree.
                leaf_mode = f"{entry.mode_type:02o}{entry.mode_perms:04o}".encode("ascii")
                leaf = GitTreeLeaf(mode = leaf_mode, path=os.path.basename(entry.name), sha=entry.sha)
            else: # Tree.  We've stored it as a pair: (basename, SHA)
                leaf = GitTreeLeaf(mode = b"040000", path=entry[0], sha=entry[1])

            tree.items.append(leaf)

        # Write the new tree object to the store.
        sha = object_write(tree, repo)

        # Add the new tree hash to the current dictionary's parent, as
        # a pair (basename, SHA)
        parent = os.path.dirname(path)
        base = os.path.basename(path) # The name without the path, eg main.go for src/main.go
        contents[parent].append((base, sha))

    return sha
