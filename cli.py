import argparse
from libwyag import *
from gitObjects import *


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
    cat_file(repo, args.obj, fmt=args.type.encode())


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


# TODO understand in details how this function works and , know what is 'graphviz 'lib
def log_graphviz(repo, sha, seen):

    if sha in seen:
        return
    seen.add(sha)

    commit = object_read(repo, sha)
    message = commit.kvlm[None].decode("utf8").strip()
    message = message.replace("\\", "\\\\")
    message = message.replace('"', '\\"')

    if "\n" in message:  # Keep only the first line
        message = message[: message.index("\n")]

    print(f'  c_{sha} [label="{sha[0:7]}: {message}"]')
    assert commit.fmt == b"commit"

    if not b"parent" in commit.kvlm.keys():
        # Base case: the initial commit.
        return

    parents = commit.kvlm[b"parent"]

    if type(parents) != list:
        parents = [parents]

    for p in parents:
        p = p.decode("ascii")
        print(f"  c_{sha} -> c_{p};")
        log_graphviz(repo, p, seen)
