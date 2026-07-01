from gitObjects import *
from gitrepo import *


def ref_resolve(repo, ref):
    """takes a ref and resolve it recursively"""
    path = repo_file(repo, ref)

    if not os.path.isfile(path):
        return None

    with open(path, "r") as f:

        data = f.read()[:-1]

        if data.startswith("ref: "):
            return ref_resolve(repo, data[5:])
        else:
            return data


def ref_list(repo, path=None):
    """list all the references in repo sorted ,
    Execution Steps:
        1- check the path if it's a real or not , if not direct the path to start in the refs/
        2- init the dict
        3- for every ref in the path :
            we check if it's a ref for a dir or a file if it's for a
            dire we make a recursive call else we append it to the dict
    """

    if not path:
        path = repo_dir(repo, "refs")

    ret = dict()

    for f in sorted(os.listdir(path)):
        can = os.path.join(path, f)

        if os.path.isdir(can):
            ret[f] = ref_list(repo, can)
        else:
            ret[f] = ref_resolve(repo, can)


def show_ref(repo, refs, with_hash=True, prefix=""):
    if prefix:
        prefix = prefix + "/"
    for k, v in refs.items():
        if type(v) == str and with_hash:
            print(f"{v} {prefix}{k}")
        elif type(v) == str:
            print(f"{prefix}{k}")
        else:
            show_ref(repo, v, with_hash=with_hash, prefix=f"{prefix}{k}")


def ref_create(repo, ref_name, sha):
    """create the ref file in path refs/ and saves the sha to it"""
    with open(repo_file(repo, "refs/" + ref_name), "w") as f:
        f.write(sha + "\n")
