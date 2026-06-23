import cli
from cli import *
from gitObjects import *
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

argparser = argparse.ArgumentParser(description="this is a small git reblica")

argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True


"""
- Execution steps 
1- the  entry point is the ./wyag with the subcommans 
2-the main gits called form the wyag 
3- main function has the grgv from command line arguments we take every thing expt the fitst argument 
4 we parse the input 
5 -match the cmd function 
"""


def main(argv=sys.argv[1:]):
    args = cli.parse_args(argv)

    match args.command:
        # case 'add': cmd_add(args)
        # # case 'cat-file':cmd_cat_file(a)
        # case 'check-gitignore':cmd_check_gitignore(args)
        # case 'checkout':cmd_checkout(args)
        # # case 'commit':cmd_commit(args)
        # case "hash-object"  : cmd_hash_object(args)
        case "init":
            cmd_init(args)
        # case "log"          : cmd_log(args)
        # case "ls-files"     : cmd_ls_files(args)
        # case "ls-tree"      : cmd_ls_tree(args)
        # case "rev-parse"    : cmd_rev_parse(args)
        # case "rm"           : cmd_rm(args)
        # case "show-ref"     : cmd_show_ref(args)
        # case "status"       : cmd_status(args)
        # case "tag"          : cmd_tag(args)
        # case _              : print("Bad command.")
