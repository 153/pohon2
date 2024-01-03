from flask import request
import time
import settings as s
import parse
import whitelist as wl

def clean(msg, limit):
    msg = msg.replace("&", "&amp;").replace("<", "&lt;")\
                    .replace("\n","<br>").replace("\r","")
    return msg[:limit]

def new_thread(subject="", comment="", author="", tags=None):
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
    author = clean(author, s.length["short"])
    subject = clean(subject, s.length["short"])
    
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

def update_log(ip, thread, time_reply, replynum,
               comment, subject, author):
    line = "<>".join([ip, thread, time_reply, replynum,
                      comment, subject, author])
    line = line + "\n"
    with open("data/log.txt", "a") as log:
        log.write(line)

def update_index(thread, time_reply):    
    with open("data/index.txt") as indexf:
        indexf = indexf.read().splitlines()
    indexf = [i.split("<>") for i in indexf if len(i.strip())]
    indexdic = {i[0]: i[1:] for i in indexf}
    indexdic[thread][0] = time_reply    
    indexdic[thread][1] = str(int(indexdic[thread][1]) + 1)
    indexf = "\n".join(["<>".join([i[0], *indexdic[i[0]]]) for i in indexf])
    with open("data/index.txt", "w") as index:
        index.write(indexf)

def update_thread(thread, ipaddr, time_reply, replynum,
                  comment, subject, author):
    t_line = "<>".join([ipaddr, time_reply, replynum,
                        comment, subject, author])
    t_line = t_line + "\n"
    with open(f"data/{thread}.txt", "a") as t_file:
        t_file.write(t_line)

def update_tags(thread, tags):
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

def new_reply(thread, comment, parent, author="", subject=""):
    if wl.flood("comment"):
        return False
    now = str(int(time.time()))

    ipaddr = wl.get_ip()
    if not author:
        author = s.anon
    comment = clean(comment, s.length["long"])
    author = clean(author, s.length["short"])
    subject = clean(subject, s.length["short"])
    
    replynum = mk_replynum(thread, parent)

    update_log(ipaddr, thread, now, replynum, comment, subject, author)
    update_index(thread, now)
    update_thread(thread, ipaddr, now, replynum, comment, subject, author)
