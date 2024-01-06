import datetime
import tree
import settings

def get_meta(number):
    with open(f"./data/{number}.txt", "r") as meta:
        meta = meta.readlines()
    meta = [*meta[0].split("<>"), len(meta) -1]
    return meta

def parse_tree(thread):
    with open(f"./data/{thread}.txt", "r") as topic:
        topic = topic.read().splitlines()
    meta = topic[0].split("<>")
    topic = [t.split("<>") for t in topic[1:]]
    skeleton = {}
    for t in topic:
        t[1] = datetime.datetime.fromtimestamp(int(t[1]))
        t[1] = t[1].strftime("%Y-%m-%d %H:%M")
        repnum = t[2]
        if ":" in repnum:
            repnum = repnum.split(":")[-1]
        mkanchor = f"<a id='{t[2]}' href='/post/{thread}/{repnum}' title='{t[1]}'>&#128337; {repnum}.</a>"
        skeleton[t[2]] = [mkanchor, t[4], t[3]]
    return tree.fmt_tree(skeleton)

def parse_thread(thread):
    output = []
    with open(f"data/{thread}.txt") as topic:
        topic = topic.read().splitlines()
    with open(f"html/comment.html") as template:
        template = template.read()
    meta = topic[0].split("<>")
    comments = [t.split("<>") for t in topic[1:]]
    for comment in comments:
        sage = False
        if len(comment) > 6:
            sage = True
        pubdate = datetime.datetime.fromtimestamp(int(comment[1]))
        pubdate = pubdate.strftime("%Y-%m-%d [%a] %H:%M")
        if len(comment[5]) == 0:
            comment[5] = settings.anon
        if sage:
            comment[5] = f"<span class='sage'>{comment[5]}</span>"
        postnum = comment[2]
        reply = ""
        if postnum != "1":
            postnum = postnum.split(":")
            if postnum[-2] != "1":
                chain = ":".join(postnum[:-1])
                reply = f"<a href='#{chain}'>&gt;&gt;{postnum[-2]}</a><br>"
            postnum = postnum[-1]
        comment[3] = reply + comment[3]
        postnum = f"<a href='/post/{thread}/{postnum}' id='{comment[2]}'>#{postnum}.</a>"
        comment = template.format(subject=comment[4],
                                  postnum=postnum,
                                  pubdate=pubdate,
                                  author=comment[5],
                                  comment=comment[3])
        output.append(comment)
    output = "<p>".join(output)
    return output
        
                                  
