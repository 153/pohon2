import time
import settings
import parse

def new_thread(subject="", comment="", author="", tags=""):
    if None in [subject, comment]:
        return False
    if not tags:
        tags = "random"
    ipaddr = "0.0"
    thread = str(int(time.time()))
    if not author:
        author = settings.anon
    comment = comment.replace("&", "&amp;").replace("<", "&lt;")
    comment = comment.replace("\n","<br>").replace("\r","")
    meta = "<>".join([tags, subject])
    post = "<>".join([ipaddr, thread, "1", comment, subject, author])

    # Write the thread file....
    tfile = "\n".join([meta, post])
    with open(f"threads/{thread}.txt", "w") as threadfile:
        threadfile.write(tfile)

    # Update the index....
    iline = "<>".join([thread, thread, "1", subject])
    with open("threads/index.txt", "r") as index:
        index = index.read()
    index = "\n".join([iline, index])
    with open("threads/index.txt", "w") as newindex:
        newindex.write(index)

    # Update the log...
    update_log(ipaddr, thread, thread, "1", comment, subject, author)
    return "Thread posted successfully" 

def update_log(ip, thread, time_reply, replynum,
               comment, subject, author):
    line = "<>".join([ip, thread, time_reply, replynum,
                      comment, subject, author])
    line = line + "\n"
    with open("threads/log.txt", "a") as log:
        log.write(line)

def update_index(thread, time_reply):    
    with open("threads/index.txt") as indexf:
        indexf = indexf.read().splitlines()
    indexf = [i.split("<>") for i in indexf if len(i.strip())]
    indexdic = {i[0]: i[1:] for i in indexf}
    indexdic[thread][0] = time_reply    
    indexdic[thread][1] = str(int(indexdic[thread][1]) + 1)
    indexf = "\n".join(["<>".join([i[0], *indexdic[i[0]]]) for i in indexf])
    with open("threads/index.txt", "w") as index:
        index.write(indexf)

def update_thread(thread, ipaddr, time_reply, replynum,
                  comment, subject, author):
    t_line = "<>".join([ipaddr, time_reply, replynum,
                        comment, subject, author])
    t_line = t_line + "\n"
    with open(f"threads/{thread}.txt", "a") as t_file:
        t_file.write(t_line)

def mk_replynum(thread, parent="1"):
    with open(f"threads/{thread}.txt") as tfile:
        tfile = tfile.read().splitlines()
    replynum = str(len(tfile))
    return ":".join([parent, replynum])

def new_reply(thread, comment, parent, author="", subject=""):
    now = str(int(time.time()))
    # get real ipaddr later on...
    ipaddr = "0.0"
    if not author:
        author = settings.anon
        
    replynum = mk_replynum(thread, parent)

    update_log(ipaddr, thread, now, replynum, comment, subject, author)
    update_index(thread, now)
    update_thread(thread, ipaddr, now, replynum, comment, subject, author)

def test_thread():
    subject = "can this write threads"
    comment = "hello world round two"
    author = "dev"
    tags = "tech spam web"
    new_thread(subject, comment, author, tags)
    
def test_reply():
    thread = "1688203002"
    comment = "blah blah blah..."
    parent = "1"
    author = "Anon"
    new_reply(thread, comment, parent, author)

#test_reply()
#test_thread()
#new_reply("1687588142", "It's just a fun place to hang out", "1:3")
#new_reply("1688203002", "Testing the first comment now that tree/thread views are working.<br><br>Hello world!", "1", "Archduke", "Making progress")
