import os

from gitIndex import index_read
from gitObjects import object_read


class GitIgnore(object):
    scoped = None
    absolute = None

    def __init__(self, absolute: list, scoped: list):
        self.absolute = absolute
        self.scoped = scoped


def check_ignore1(rules, path):
    """matches the paths against set of rules and
    return True False or None if Nothing matches"""
    res = None
    for pattern, val in rules:
        import fnmatch

        if fnmatch(path, pattern):
            res = val

    return res


def check_ignore_scoped(rules, path):
    """match against the dictionary of scoped rules
    (the various .gitignore files). It just starts
    at the path’s directory then moves up to the parent
    directory, recursively, until it has tested root."""

    parent = os.path.dirname(path)

    while True:
        if parent in rules:
            res = check_ignore1(rules[parent], path)
            if res != None:
                return res
        if parent == "":
            break
        parent = os.path.dirname(parent)

    return None


def check_ignore_absolute(rules, path):
    """match against the absolute path"""
    parent = os.path.dirname(path)
    for ruleset in rules:
        result = check_ignore1(ruleset, path)
        if result != None:
            return result
    return False


def check_ignore(rules, path):
    """the main function to check against the paths"""
    if os.path.isabs(path):
        raise Exception(
            "This function requires path to be relative to the repository's root"
        )

    result = check_ignore_scoped(rules.scoped, path)
    if result != None:
        return result

    return check_ignore_absolute(rules.absolute, path)


def gitignore_read(repo):
    """Reads all the .gitignore anywhere on the system ,global and local,scoped ;
    Execution Steps :
    1-instantiate the GitIgnore and build it step by step
    2- reads the local conf in .git/info/exclude
    3- reads the glob conf

    """

    gi = GitIgnore(absolute=list(), scoped=list())
    # local
    repo_file = os.path.join(repo.gitdire, "info/exclude")
    if os.path.exists(repo_file):
        with open(repo_file, "r") as f:
            gi.absolute.append(gitignore_parse(f.readlines))
    # globe
    if "XD_CONFIG_HOME" in os.environ:
        config_home = os.environ["XD_CONFIG_HOME"]
    else:
        config_home = os.path.expanduser("~/.config")
    global_file = os.path.join(config_home, "git/ignore")
    if os.path.exists(global_file):
        with open(global_file, "r") as f:
            gi.absolute.append(gitignore_parse(f.readlines()))
    # index
    index = index_read(repo)
    for ent in index.entries:
        if ent.name == ".gitignore" or ent.name.endswith("./gitignore"):
            dir_name = os.path.dirname(ent.name)
            contents = object_read(repo, ent.sha)
            lines = contents.blobdata.decode("utf8").splitlines()
            gi.scoped[dir_name] = gitignore_parse(lines)  # type: ignore
    return gi


def gitignore_parse1(raw):
    """reads a single pattern and return a pair of the pattern itself
    and wither or not to include it
    Execution steps:
    1-remove the spaces
    2-check for hash # if it exits it's a comment return None ,
    3-check for \\ as a scape SEQUENCE if it's we return (path,False)
    else return (path,true)
    """
    raw = raw.strip()
    if not raw or raw[0] == "#":
        return None
    elif raw[0] == "!":
        return (raw[1:], False)
    elif raw[0] == "\\":
        return (raw[1:], True)
    else:
        return (raw, True)


def gitignore_parse(lines) -> list[str]:
    """gitignore parse used to scan the files for the patters and return a list of them"""
    res = list()

    for line in lines:
        parsed = gitignore_parse1(line)
        if parsed:
            res.append(parsed)

    return res
