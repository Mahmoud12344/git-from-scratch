import argparse
import grp
import pwd

# from libwyag import *
# from gitObjects import
from gitIndex import index_read
from gitTree import *
from gitRef import *
from gitTag import *


def parse_args(argv):

    argparser = argparse.ArgumentParser(description="this is a small git reblica")

    argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
    argsubparsers.required = True

    # init parser
    init_parser = argsubparsers.add_parser("init", help="init")
    init_parser.add_argument(
        "path",
        metavar="directory",
        nargs="?",
        default=".",
        help="Where to create the repository.",
    )

    # cat-file parser
    cat_file_parser = argsubparsers.add_parser(
        "cat-file", help="Provide content of repository objects"
    )

    cat_file_parser.add_argument(
        "type",
        metavar="type",
        choices=["blob", "commit", "tag", "tree"],
        help="Specify the type",
    )
    cat_file_parser.add_argument(
        "object", metavar="object", help="The object to Display"
    )

    # hash-object parser
    hash_object_parser = argsubparsers.add_parser(
        "hash-object", help="Computes IDs and optionally creates a blob from a file"
    )

    hash_object_parser.add_argument(
        "-t",
        metavar="type",
        dest="type",
        choices=["blob", "commit", "tag", "tree"],
        help="Specify the type",
    )
    hash_object_parser.add_argument(
        "-w",
        dest="write",
        action="store_true",
        help="Wire the object into the repo database",
    )
    hash_object_parser.add_argument("path", help="Read object from a file")
    # log-parser
    log_parser = argsubparsers.add_parser(
        "log", help="show the history of the commits "
    )
    log_parser.add_argument(
        "commit",
        default="HEAD",
        nargs="?",
        help="Commit to start ",
    )

    ## ls-tree
    ls_tree_parser = argsubparsers.add_parser("ls-tree", help="Display the Tree Object")
    ls_tree_parser.add_argument(
        "-r",
        dest="recursive",
        action="store_true",
        help="Recurse into subTrees",
    )

    ls_tree_parser.add_argument(
        "tree",
        help="A tree-ish Object. ",
    )

    # checkout parser
    checkout_parser = argsubparsers.add_parser(
        "checkout", help="checkout a commit inside a directory"
    )
    checkout_parser.add_argument(
        "commit",
        help="the commit or the tree to checkout",
    )
    checkout_parser.add_argument(
        "path",
        help="The EMPTY directory to checkon",
    )

    # show-ref parser
    show_ref_parser = argsubparsers.add_parser(
        "show-ref",
        help="List references",
    )
    # tag parser
    tag_parser = argsubparsers.add_parser(
        "tag",
        help="List and create tags",
    )
    tag_parser.add_argument(
        "-a",
        action="store_true",
        dest="create_object",
        help="whether to create tag",
    )
    tag_parser.add_argument(
        "object",
        default="HEAD",
        nargs="?",
        help="The object the new tag will point to",
    )
    tag_parser.add_argument(
        "name",
        nargs="?",
        help="new tag's name",
    )

    # rev-parse parser
    rev_parse_parser = argsubparsers.add_parser(
        "rev-parse",
        help="Parse revision or other objects identifiers",
    )
    rev_parse_parser.add_argument(
        "--wyag-type",
        metavar="type",
        dest="type",
        choices=["blob", "commit", "tag", "tree"],
        default=None,
        help="Specify the expected type",
    )
    rev_parse_parser.add_argument(
        "name",
        help="The name to parse",
    )

    # ls-files parser
    ls_files_parser = argsubparsers.add_parser(
        "ls-files",
        help="list all the staged files",
    )

    ls_files_parser.add_argument(
        "--verbose",
        action="store_true",
        help="show everything ",
    )
    # check-ignore parser
    check_ignore = argsubparsers.add_parser(
        "check-ignore",
        help="check ignored files against ignore rules ,",
    )
    check_ignore.add_argument(
        "path",
        nargs="+",
        help="paths to check",
    )

    return argparser.parse_args(argv)


## commands calling


def cmd_init(args):
    """
    The Repo init logic
    1-receive the command as a path.command in the main matcher
    2 this function "cmd-init(args)" gets called and calles repo_creat(args.path)

    """
    repo_create(args.path)


# wyag cat-file TYPE OBJECT
def cmd_cat_file(args):
    repo = repo_find()

    cat_file(repo, args.object, fmt=args.type.encode())


# wyag hash-object [-w] [-t TYPE] FILE
def cmd_hash_object(args):
    """it reads a file, computes its hash as an object,
    either storing it in the repository (if the -w flag is passed)
    or just printing its hash."""
    if args.write:
        repo = repo_find()
    else:
        repo = None
    with open(args.path, "rb") as fd:
        sha = object_hash(fd, args.type.encode(), repo)
        print(sha)


def cmd_log(args):
    repo = repo_find()

    print("digraph wyaglog{")
    print("  node[shape=rect]")
    log_graphviz(repo, object_find(repo, args.commit), set())
    print("}")


def cmd_ls_tree(args):
    repo = repo_find()
    ls_tree(repo, args.tree, args.recursive)


def cmd_checkout(args):
    """Execution steps
    1- find the repo
    2-read the object,
    3.if the object is a commit we grab it's tree,
    4-check for the path if it's exit and empty or does not exit and make it,
    5- call the checkout func
    """
    # 1
    repo = repo_find()
    # 2
    obj = object_read(repo, object_find(repo, args.commit))
    # 3
    if obj.fmt == b"commit":
        obj = object_read(repo, obj.kvlm[b"tree"].decode("ascii"))
    # 4
    if os.path.exists(args.path):
        if not os.path.isdir(args.path):
            raise Exception(f"Not A Directory :--> {args.path}")
        if os.listdir(args.path):
            raise Exception(f"Not Empty :--> {args.path}!")
    else:
        os.makedirs(args.path)

    tree_checkout(repo, obj, os.path.realpath(args.path))


def cmd_show_ref(args):
    repo = repo_find()
    refs = ref_list(repo)
    show_ref(repo, refs, prefix="refs")


def cmd_tag(args):
    repo = repo_find()

    if args.name:
        tag_create(
            repo,
            args.name,
            args.object,
            create_object=args.create_object,
        )
    else:
        refs = (ref_list(repo),)
        show_ref(repo, refs["tags"], with_hash=False)


def cmd_rev_parse(args):
    if args.type:
        fmt = args.type.encode()
    else:
        fmt = None

    repo = repo_find()
    print(object_find(repo, args.name, fmt, follow=True))


def cmd_ls_files(args):
    repo = repo_find()
    index = index_read(repo)
    if args.verbose:
        print(
            f"Index file format v{index.version}, containing {len(index.entries)} entries."
        )

    for e in index.entries:
        print(e.name)
        if args.verbose:
            entry_type = {
                0b1000: "regular file",
                0b1010: "symlink",
                0b1110: "git link",
            }[e.mode_type]
            print(f"  {entry_type} with perms: {e.mode_perms:o}")
            print(f"  on blob: {e.sha}")
            print(
                f"  created: {datetime.fromtimestamp(e.ctime[0])}.{e.ctime[1]}, modified: {datetime.fromtimestamp(e.mtime[0])}.{e.mtime[1]}"
            )
            print(f"  device: {e.dev}, inode: {e.ino}")
            try:
                print(
                    f"  user: {pwd.getpwuid(e.uid).pw_name} ({e.uid})  group: {grp.getgrgid(e.gid).gr_name} ({e.gid})"
                )
            except NameError:
                # These modules are not available on Windows, so just use the less-nice info.
                print(f"  user: {e.uid}  group: {e.gid}")
            print(f"  flags: stage={e.flag_stage} assume_valid={e.flag_assume_valid}")


def cmd_check_ignore(args):
    repo = repo_find()
    rules = gitignore_read(repo)
    for path in args.path:
        if check_ignore(rules, path):
            print("-->", path)


def log_graphviz(repo, sha, seen):

    if sha in seen:
        return
    seen.add(sha)

    commit = object_read(repo, sha)
    assert commit.fmt == b"commit"

    message = commit.kvlm[None].decode("utf8").strip()
    message = message.replace("\\", "\\\\")
    message = message.replace('"', '\\"')

    if "\n" in message:  # Keep only the first line
        message = message[: message.index("\n")]

    print(f'  c_{sha} [label="{sha[0:7]}: {message}"]')

    if b"parent" not in commit.kvlm:
        # Base case: the initial commit.
        return

    parents = commit.kvlm[b"parent"]

    if not isinstance(parents, list):
        parents = [parents]

    for p in parents:
        p = p.decode("ascii")
        print(f"  c_{sha} -> c_{p};")
        log_graphviz(repo, p, seen)
