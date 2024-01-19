import datetime
import tree
import settings

def get_meta(number):
    with open(f"./data/{number}.txt", "r") as meta:
        meta = meta.readlines()
    meta = [*meta[0].split("<>"), len(meta) -1]
    return meta

def parse_tree(thread,parent=""):
    with open(f"./data/{thread}.txt", "r") as topic:
        topic = topic.read().splitlines()
    meta = topic[0].split("<>")
    topic = [t.split("<>") for t in topic[1:]]
    skeleton = {}
    for t in topic:
        t[1] = datetime.datetime.fromtimestamp(int(t[1]))
        t[1] = t[1].strftime("%Y-%m-%d %H:%M")
        repnum = t[2]
        repchain = [t[2]]
        if ":" in repnum:
            repchain = repnum.split(":")
            repnum = repnum.split(":")[-1]
        mkanchor = f"<a id='{t[2]}' href='/post/{thread}/{repnum}' title='{t[1]}'>&#128337; {repnum}.</a>"
        if parent and parent in repchain:
            pos = repchain.index(parent)
            repchain = ":".join(repchain[pos:])
            t[2] = repchain
            skeleton[t[2]] = [mkanchor, t[4], t[3]]
        if not parent:
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
    ccount = len(comments) - 1
    for n, comment in enumerate(comments):
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
        if n == ccount:
            postnum += "<a id='bottom'></a>"
        comment[3] = fmtpost(comment[3])
        comment = template.format(subject=comment[4],
                                  postnum=postnum,
                                  pubdate=pubdate,
                                  author=comment[5],
                                  comment=comment[3])
        output.append(comment)
    output = "<p>".join(output)
    return output

def fmtpost(comment):
    comment = comment.split("<br>")
    output = []
    for line in comment:
        test = line
        if "%" in line and not (test.count("%") % 2):
            test = test.split("%")
            result = []
            tagopen = 0
            for n, t in enumerate(test):
                result.append(t)
                if not (n % 2):
                    tagopen = 1
                    result.append("<span class='spoiler'>")
                else:
                    tagopen = 0
                    result.append("</span>")
            if tagopen:
                result.append("</span>")
            line = "".join(result)
        test = line.strip()
        if test.startswith("&gt;") or test.startswith(">"):
            output.append("<span class='quote'>" + line + "</span>")
        elif test.startswith("&lt;"):
            output.append("<span class='quote2'>" + line + "</span>")
        elif test.startswith("^"):
            output.append("<span class='quote3'>" + line + "</span>")
        else:
            output.append(line)
    comment = "<br>".join(output)
    return comment
