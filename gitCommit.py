from gitObjects import GitObject


class GitCommit(GitObject):
    fmt = "commit"

    def deserialize(self, data):
        self.kvlm = kvlm_parse(data)

    def serialize(self):
        return kvlm_serialize(self.kvlm)

    def init(self):
        self.kvlm = dict()


def kvlm_parse(raw, start=0, dct=None):
    """this is a parser for the commit message object works on the key/value space newLine delimiters.
    this function is recursive and it reads a key/value pair and call itself in the new position
    Execution steps:
    1-we innit the dect if it's not initialized yet,
    2-we search for the next space and the next new line ,
    3- Check if the space appears before the new line I's a keyword else it's the commit message , and we Read to the end of the file ,
    -- base case for the recursion :
        if the newline appears first or there is no space atall the find fun returns -1, and we assume a Blank line ,
        Blank Line : means that the reminder of the data is the message itself ,
    4 we store it in the dct with a None key and the data as the value , and we return ,

    5 - the Recursive code ,
    5.1- we read a key/value pair and recurse for the next,find the end of the value ,
    as the continuation lines begin with a space , So we loop until we find a \n not followed by a space

    5.2 grab the values And drop the leading space on the continuation lines
    5.3 making sure Not to overwrite existing data ,

    """
    # 1
    if not dct:
        dct = dict()
    # 2
    spc = raw.find(b" ", start)
    nl = raw.find(b"\n", start)
    # 3
    if (spc < 0) or (nl < spc):
        assert nl == start
        # 4
        dct[None] = raw[start + 1]
        return dct
    # 5
    key = raw[start:spc]
    end = start
    # 5.1
    while True:
        end = raw.find(b"\n", end + 1)
        if raw[end + 1] != ord(" "):
            break
    # 5.2
    value = raw[spc + 1 : end].replace(b"\n ", b"\n")

    # 5.3
    if key in dct:
        if type(dct[key]) == list:
            dct[key].append(value)
        else:
            dct[key] = [dct[key], value]
    else:
        dct[key] = value

    return kvlm_parse(raw, start=end + 1, dct=dct)


def kvlm_serialize(kvlm):
    ret = b""

    # Output fields
    for k in kvlm.keys():
        # Skip the message itself
        if k == None:
            continue
        val = kvlm[k]
        # Normalize to a list
        if type(val) != list:
            val = [val]

        for v in val:
            ret += k + b" " + (v.replace(b"\n", b"\n ")) + b"\n"

    # Append message
    ret += b"\n" + kvlm[None]

    return ret
