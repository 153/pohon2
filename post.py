from flask import request
import time
import crypt
import settings as s
import parse
import whitelist as wl

def clean(msg, limit):
    """Sanitize input and reduce length of input"""
    msg = msg.replace("&", "&amp;").replace("<", "&lt;")\
                    .replace("\n","<br>").replace("\r","")
    return msg[:limit]

def tripcode(author):
    """Make a tripcode from input string "user#password"""
    if "◆" in author:
        author = author.replace("◆", "&#9671;")
    if not "#" in author:
        return author
    author = author.split("#")
    if len(author) > 2:
        author[1] = "#".join(author[1:])
    if "&#9671;" in author[1]:
        author[1].replace("&#9671", "◆")
        
    pw = author[1][:8]

    trip = trip2(pw)
    trip = f"<span class='trip' title='tripcode'>{trip}</span>"
    author = "&#9670;".join([author[0], trip])
    return author

def trip2(tripkey):
    from passlib.hash import des_crypt
    from re import sub

    try:
        tripkey = bytes(tripkey, encoding='shift-jis', errors='strict')
        tripkey.decode('utf-8')
    except (UnicodeDecodeError,):
        pass
    except (UnicodeEncodeError,):
        try:
            tripkey = bytes(tripkey, encoding='utf-8', errors='strict')
        except (UnicodeEncodeError,):
            tripkey = bytes(tripkey, encoding='utf-8', errors='xmlcharrefreplace')
    else:
        pass

    salt = (tripkey + b'H.')[1:3]
    salt = sub(rb'[^\.-z]', b'.', salt)
    salt = salt.translate(bytes.maketrans(b':;<=>?@[\\]^_`', b'ABCDEFGabcdef'))

    # trip = des_crypt.hash(tripkey, salt=salt.decode('shift-jis'))
    trip = des_crypt.hash(tripkey, salt=salt.decode('utf-8'))
    trip = trip[-10:]

    return trip
    
    

def line_check(msg):
    """Make sure no lines in comments are >72 chars long"""
    if "<br>" in msg:
        msg = msg.split("<br>")
    else:
        msg = [msg]
    toolong = []
    for n, m in enumerate(msg):
        if len(m) > s.length["line"]:
            toolong.append([
                f"Line {n+1} is {len(m) - s.length['line']}"\
                f" characters too long:",
                f"{m[:s.length['line']]}",
                f"{m[s.length['line']:]}"])
    
    if not len(toolong):
        return
    with open("html/long_line.html") as longline:
        longline = longline.read()
    with open("html/long_error.html") as errorpage:
        errorpage = errorpage.read()
    toolong = "\n".join([longline.format(*m) for m in toolong])
    return errorpage.format(s.length['line'], toolong)
                           
def new_thread(subject="", comment="", author="", tags=None):
    """Create a new thread, if subject and comment are specified, with optional author/tags"""
    if None in [subject, comment]:
        return False
    if not tags:
        tags = ["random"]
    if wl.flood("thread"):
        return False
    ipaddr = wl.get_ip()
    thread = str(int(time.time()))
    if not author:
        author = s.anon
    comment = clean(comment, s.length["long"])
    check = line_check(comment)
    if check:
        return check
    author = clean(author, s.length["name"])
    author = tripcode(author)
    subject = clean(subject, s.length["subject"])
    
#    comment = comment
    meta = "<>".join([" ".join(tags), subject])
    post = "<>".join([ipaddr, thread, "1", comment, subject, author])

    # Write the thread file....
    tfile = "\n".join([meta, post]) + "\n"
    with open(f"data/{thread}.txt", "w") as threadfile:
        threadfile.write(tfile)

    # Update the index....
    iline = "<>".join([thread, thread, "1", subject])
    with open("data/index.txt", "r") as index:
        index = index.read()
    index = "\n".join([iline, index])
    with open("data/index.txt", "w") as newindex:
        newindex.write(index)

    # Update the log...
    update_log(ipaddr, thread, thread, "1", comment, subject, author)

    # Update the tags
    update_tags(thread, tags)
    
    return thread

def update_log(ip, thread, time_reply, replynum, comment, subject, author, sage=False):
    """Update the serverlog when a new thread or comment is made"""
    line = "<>".join([ip, thread, time_reply, replynum,
                      comment, subject, author])
    if sage:
        line += "<>1"
    line = line + "\n"
    with open("data/log.txt", "a") as log:
        log.write(line)

def update_index(thread, time_reply, sage=False):
    """Update index file when a reply is made"""
    with open("data/index.txt") as indexf:
        indexf = indexf.read().splitlines()
    indexf = [i.split("<>") for i in indexf if len(i.strip())]
    indexdic = {i[0]: i[1:] for i in indexf}
    if not sage:
        indexdic[thread][0] = time_reply    
    indexdic[thread][1] = str(int(indexdic[thread][1]) + 1)
    indexf = "\n".join(["<>".join([i[0], *indexdic[i[0]]]) for i in indexf])
    with open("data/index.txt", "w") as index:
        index.write(indexf)

def update_thread(thread, ipaddr, time_reply, replynum, comment, subject, author, sage=False):
    """update a thread file when a reply is made"""
    t_line = "<>".join([ipaddr, time_reply, replynum,
                        comment, subject, author])
    if sage:
        t_line += "<>1"
    t_line = t_line + "\n"
    with open(f"data/{thread}.txt", "a") as t_file:
        t_file.write(t_line)

def update_tags(thread, tags):
    """update tag list when a new thread is made"""
    with open("data/tags.txt") as taglist:
        taglist = taglist.read().splitlines()
    taglist = [t.split(" ") for t in taglist]
    tagdic = {t[0]: t[1:] for t in taglist}
    for tag in tags:
        if tag not in tagdic:
            tagdic[tag] = []
        tagdic[tag].append(thread)
    tagfile = sorted([[t, *tagdic[t]] for t in tagdic], key=len)[::-1]
    tagfile = "\n".join([" ".join(t) for t in tagfile])
    with open("data/tags.txt", "w") as taglist:
        taglist.write(tagfile)
        
def mk_replynum(thread, parent="1"):
    with open(f"data/{thread}.txt") as tfile:
        tfile = tfile.read().splitlines()
    replynum = str(len(tfile))
    return ":".join([parent, replynum])

def new_reply(thread, comment, parent, author="", subject="", sage=False):
    """Post a new reply to a thread"""
    if wl.flood("comment"):
        return False
    now = str(int(time.time()))

    with open(f"data/{thread}.txt") as tmode:
        tmode = tmode.read().splitlines()
    tmode = tmode[0].split("<>")
    if len(tmode) == 2:
        tmode = "0"
    elif tmode[2] in ["3", "4"]:
        return "Thread is closed to posting"
    elif tmode[2] == "2":
        sage = True
    
    ipaddr = wl.get_ip()
    if not author:
        author = s.anon
    comment = clean(comment, s.length["long"])
    check = line_check(comment)
    if check:
        return check
    author = clean(author, s.length["name"])
    author = tripcode(author)
    subject = clean(subject, s.length["subject"])
    
    replynum = mk_replynum(thread, parent)

    update_log(ipaddr, thread, now, replynum, comment, subject, author, sage)
    update_index(thread, now, sage)
    update_thread(thread, ipaddr, now, replynum, comment, subject, author, sage)
