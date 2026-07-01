import os, configparser


class GitRepository(object):
    """A git repo"""

    worktree = None
    gitdire = None
    conf = None

    def __init__(self, path, force=False):

        self.worktree = path
        self.gitdire = os.path.join(path, ".mygit")

        if not (force or os.path.isdir(self.gitdire)):
            raise Exception(f"not a git repo {path}")

        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("conf file is missing")

        if not force:
            verse = int(self.conf.get("core", "repositoryformatversion"))
            if verse != 0:
                raise Exception(f"unsupported repoformatversion {verse}")


def repo_path(repo, *path):
    """compute path under repo's gitdir,"""

    return os.path.join(repo.gitdire, *path)


# this makes sure that the parent for a file exist
def repo_file(repo, *path, mkdir=False):
    """Same as repo_path, but create dirname(*path) if absent.  For
    example, repo_file(r, \"refs\", \"remotes\", \"origin\", \"HEAD\") will create
    .gitmy/refs/remotes/origin."""

    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)


def repo_dir(repo, *path, mkdir=False):
    """same as repo_path , but mkdir *Path if absent if mkdir"""

    path = repo_path(repo, *path)

    if os.path.exists(path):
        if os.path.isdir(path):
            return path
        else:
            raise Exception(f"Not a directory {path}")

    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None


def repo_create(path):
    """create a new repo at path
    execution steps :
    1-instantiation of the GitRepo obj ,
    2.1-checking if the path is not a path to a directory
    2.2-if the .mygit exists raise exception
    2.3-if all of this does not satisfy , we creat the work tree
    3 - creates the skeleton of the .mygit
    4- make the head
    5- make the default config file"""

    repo = GitRepository(path, True)

    ## check if the repo exist of it's an empty dir

    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception(f"{path} is not a dire ")
        if os.path.exists(repo.gitdire):
            raise Exception(f" {path} is not Empty")

    else:
        os.makedirs(repo.worktree)

    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    # .mygit/description
    with open(repo_file(repo, "description "), "w") as f:
        f.write('un named repo , open file "description"  to name the repo\n ')
    # .mygit/HEAD

    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/master\n")

    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)

    return repo


def repo_default_config():
    ret = configparser.ConfigParser()
    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")
    return ret


def repo_find(path=".", required=True):
    """This function is used to find where is the .mygit repo and returning the absoulute path to it
    excution steps
    1-we check this path if it contains this .mygit
    1.1-if it existt we return a GitRepo obj
    2- if this path doesn't have the the .mygit we go back up one level 'parent'
    2.1- we check if this parent is the root if so it's required we raise an exception if not we return None
    3 - we recurse this function again"""

    path = os.path.realpath(path)
    if os.path.isdir(os.path.join(path, ".mygit")):
        return GitRepository(path)
    pr = os.path.realpath(os.path.join(path, ".."))

    # base case we've reached the root
    if pr == path:
        if required:
            raise Exception("Not a GitRepo")
        else:
            return None

    return repo_find(pr, required)


def gitconfig_read():
    xdg_config_home = (
        os.environ["XDG_CONFIG_HOME"]
        if "XDG_CONFIG_HOME" in os.environ
        else "~/.config"
    )
    configfiles = [
        os.path.expanduser(os.path.join(xdg_config_home, "git/config")),
        os.path.expanduser("~/.gitconfig"),
    ]

    config = configparser.ConfigParser()
    config.read(configfiles)
    return config


def gitconfig_user_get(config):
    if "user" in config:
        if "name" in config["user"] and "email" in config["user"]:
            return f"{config['user']['name']} <{config['user']['email']}>"
    return None
