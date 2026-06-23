import argparse


def parse_args(argv):

    argparser = argparse.ArgumentParser(description="this is a small git reblica")

    argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
    argsubparsers.required = True

    init_parser = argsubparsers.add_parser("init", help="init")

    init_parser.add_argument(
        "path",
        metavar="directory",
        nargs="?",
        default=".",
        help="Where to create the repository.",
    )

    return argparser.parse_args(argv)
