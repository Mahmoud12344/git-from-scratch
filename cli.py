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
