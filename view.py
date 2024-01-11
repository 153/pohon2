import time
import datetime
import os
from flask import Blueprint, request
import parse
import post
import settings
import whitelist as wl

view = Blueprint("view", __name__)

def header():
    """Return page header boilerplate"""
    with open("html/head.html", "r") as page:
        page = page.read()
    output = page.format(title=settings.title)
    return output

def footer():
    """Return page footer boilerplate"""
    with open("html/footer.html", "r") as page:
        page = page.read()
    output = page.format(title=settings.title)
    return output

def ld_page(fn):
    with open(f'./html/{fn}.html', "r") as data:
        data = data.read()
    return data

def mk_page(content=None):
    """Return a page, wrapping it in the header and footer"""
    page = header()
    page += content
    page += footer()
    return page

def mk_tagbox():
    """Make checkboxes of tags for OP to use when creating a thread"""
    tags = settings.tags
    template = """<label for="{0}"><input type="checkbox" name="tag"
id="{0}" value="{0}">{0}</label>"""
    taglist = []
    with open("html/tagbox.html") as tagbox:
        tagbox = tagbox.read()
    for t in tags:
        checkbox = template.format(t)
        if t == "random":
            checkbox = checkbox.replace("checkbox\"", "checkbox\" checked")
        taglist.append(checkbox)
    taglist = "\n".join(taglist)
    tagbox = tagbox.format(taglist)
    return tagbox

def tag_list():
    """Return a simple list of tags with the number of threads they have"""
    with open("data/tags.txt") as tags:
        tags = tags.read().splitlines()
    tags = [t.split(" ") for t in tags]
    tags = [[t[0], len(t[1:])] for t in tags]
    tags.sort(key = lambda x: x[1], reverse = True)
    return tags

def thread_head(thread):
    """Create a thread header, showing replies and tags"""
    modes = {"0": "", "1": "", "2": "(saged)", "3": "(closed)",
             "4": "(closed)"}
    with open(f"data/{thread}.txt") as data:
        data = data.read().splitlines()
    meta = data[0].split("<>")
    
    subject = meta[1]
    
    # get the mode... 
    mode = ""
    if len(meta) > 2:
        mode = modes[meta[2]]

    # set the tags
    tags = meta[0]
    if " " in tags:
        tags = tags.split(" ")
        tags = [f" <i><a href='/tags/{t}/'>#{t}</a></i>" for t in tags]
        tags = "".join(tags)
    else:
        tags = f" <i><a href='/tags/{tags}'>#{tags}</a></i>"

    # count replies
    replies = len(data) - 1
    if replies != 1:
        replies = f"{replies} replies"
    else:
        replies = "1 reply"
    template = ld_page("thread_head")
    
    return template.format(thread=thread, subject=subject,
                           replies=replies, tags=tags,
                           mode=mode)

@view.route('/')
def homepage():
    """Show the homepage and basic post statistics"""
    
    with open("data/index.txt") as index:
        index = index.read().splitlines()
    index = [i.split("<>") for i in index]

    pcount = 0
    tcount = str(len(index))
    for p in index:
        pcount += int(p[2])
    pcount = str(pcount)
    return mk_page(ld_page("index").format(thread=tcount,
                                           post=pcount))

@view.route('/about/')
def about():
    """Show an about page"""
    return mk_page(ld_page("about"))

@view.route('/rules/')
def rules():
    """Show a rules page"""
    return mk_page(ld_page("rules"))

@view.route('/tags/')
def show_tags():
    """Format a tag list for users"""
    tags = tag_list()
    page = ["<ul>"]
    for t in tags:
        if t[1] == 0:
            continue
        line = f"<li><a href='/tags/{t[0]}/'>#{t[0]}</a> - {t[1]} "
        if t[1] > 1:
            line += "threads"
        else:
            line += "thread"
        page.append(line)
    page.append("</ul>")
    page = "\n".join(page)
    return mk_page(page)

def thread_index_sort(index=[]):
    """Sort an index of threads, and also show thread's special mode (if any)"""
    modes = {"sticky": "<img src='/sticky.png' title='pinned'>",
             "lock": "<img src='/lock.png' title='closed'>",
             "sage": "<img src='/ghost.png' title='permasage'>"}
    if not index:
        with open("data/index.txt") as index:
            index = index.read().splitlines()
        index = [i.split("<>") for i in index]
        index.sort(key = lambda x: x[1], reverse=True)
    tmode = []
    for n, i in enumerate(index):
        if len(i) >= 5 and i[4] in ["1", "4"]:
            index.insert(0, index.pop(n))        
    for n, i in enumerate(index):
        if len(i) < 5:
            tmode.append("")
            continue
        elif i[4] == "0":
            tmode.append("")
            continue
        if i[4] == "1":
            tmode.append(modes["sticky"])
        elif i[4] == "2":
            tmode.append(modes["sage"])
        elif i[4] == "3":
            tmode.append(modes["lock"])
        elif i[4] == "4":
            tmode.append(modes["sticky"] + modes["lock"])
    return tmode, index

@view.route('/tags/<tags>/')
@view.route('/tags/<tags>/<badtags>/')
def tag_index(tags, badtags=None):
    """Show a list of threads with specific tag/tags"""
    atoms = " <link rel='alternate' type='application/atom+xml'"
    atoms += f" href='/atom/tag/{tags[0]}'>"
    title = ""
    if badtags:
        if "+" in badtags:
            badtags = badtags.split("+")
        elif " " in badtags:
            badtags = badtags.split(" ")
        else:
            badtags = [badtags]
    else:
        badtags = []
        
    if not tags or tags == " ":
        tags = settings.tags
        title ="<h3>All tags"
    elif "+" in tags:
        tags = tags.split("+")
    elif " " in tags:
        tags = tags.split(" ")
    else:
        tags = [tags]
        
    if not len(tags) and not len(badtags):
        return show_tags()
    
    negate = ""
    if badtags:
        negate = "-" + " -".join(badtags)
    
    with open("data/tags.txt") as tagdb:
        tagdb = tagdb.read().splitlines()
    tagdb = [t.split(" ") for t in tagdb]
    tagdb = {t[0]: t[1:] for t in tagdb}
    
    with open("data/index.txt") as threaddb:
        threaddb = threaddb.read().splitlines()
    threaddb = [t.split("<>") for t in threaddb]
    threaddb = {t[0]: t[1:] for t in threaddb}
    
    results = {}

    output = []

    try:
        if badtags:
            badtags = [tagdb[i] for i in badtags]
            badtags = list(set([c for b in badtags for c in b]))
    except:
        badtags = []

    poscnt = []
    negcnt = []
    for t in tags:
        if t in tagdb:
            for t2 in tagdb[t]:
                poscnt.append(t2)
                if t2 in badtags:
                    negcnt.append(t2)
                    continue
                results[t2] = [*threaddb[t2]]
                
    poscnt = len(set(poscnt))
    negcnt = len(set(negcnt))
    if negcnt > poscnt: negcnt = poscnt
    tags = " ".join([f"+{tag}" for tag in tags])
    results = [[t, *results[t]] for t in results]
    results.sort(key = lambda x: x[1], reverse=True)
    tmode, index = thread_index_sort(results)
    outstring = "<a href='/thread/{0}/'>{1}</a> ({2} comments)"
    for n, r in enumerate(results):
        newline = tmode[n] + outstring.format(r[0], r[3], r[2])
        output.append(newline)
    if len(output) == 0:
        output = ["Zero entries for tag query"]
    output = "\n<li>" + "\n<li>".join(output)
    output = atoms + "\n<ul>" + output + "\n</ul>"
    if len(title) == 0:
        title = f"<h3>{tags} ({poscnt} threads)</h3>"
    else:
        title += f" ({poscnt} threads)</h3>"
    if badtags:
        title += f"<h3>{negate} ({negcnt} threads)</h3>"
    output = title + output + "<p>"
    
    return mk_page(output)

@view.route('/tree/')
def tree_index():
    """Show a list of threads; clicking threads renders them as trees"""
    atoms = " <link rel='alternate' type='application/atom+xml'"
    atoms += f" href='/atom/threads'>\n"
    tmode, index = thread_index_sort()

    for n, i in enumerate(index):
        index[n] = tmode[n] + f" <a href='/tree/{i[0]}/'>{i[3]}</a> ({i[2]} replies)"
    index = "<li>" + "<li>".join(index)
    page = atoms + f"<ul>{index}</ul>"
    return mk_page(page)

@view.route('/thread/')
def thread_index():
    """Show a list of threads; clicking threads renders them as lists"""
    atoms = " <link rel='alternate' type='application/atom+xml'"
    atoms += f" href='/atom/threads'>\n"
    tmode, index = thread_index_sort()

    for n, i in enumerate(index):
        index[n] = tmode[n] + f" <a href='/thread/{i[0]}/'>{i[3]}</a> ({i[2]} replies)"
    index = "\n<li>" + "\n<li>".join(index)
    page = atoms + f"<ul>{index}\n</ul>\n"
    return mk_page(page)

@view.route('/tree/<thread>/')
@view.route('/tree/<thread>/<parent>')
def view_tree(thread, view="tree", parent=""):
    """View a thread in tree mode"""
    page = ld_page("tree")
    try:
        with open(f"data/{thread}.txt", "r") as data:
            data = data.read().splitlines()
    except:
        return mk_page("404")
    
    replycnt = len(data) - 2

    tree = parse.parse_tree(thread, parent)
    template = ld_page("tree")
    page = thread_head(thread)
    page += template.format(tree=tree, )
    return mk_page(page)

@view.route('/post/')
def post_null():
    return '<meta http-equiv="refresh" content="0;URL=/">'

@view.route('/post/<thread>/<reply>')
def view_reply(thread, reply="1"):
    """Show a reply to a thread, a new reply box, and the reply's parents"""
    sage = False
    reply = int(reply)
    try:
        with open(f"data/{thread}.txt") as comments:
            comments = comments.read().splitlines()
    except:
        return mk_page("404")
    
    if (reply < 1) or (reply > len(comments)):
        return mk_page("404")
    
    comments = [c.split("<>") for c in comments]
    template = ld_page("comment")
    thread_subject = comments[0][1]
    mode = 0
    if len(comments[0]) > 2:
        mode = comments[0][2]

    comment = comments[reply]
    if len(comment) > 6:
        sage = True
    anc = comment[2]
    replychain = [1]
    if ":" in comment[2]:
        replychain = [int(i) for i in comment[2].split(":")][::-1]
    replys = []

    for r in replychain:
        comment = comments[r]
        postnum = "1"
        if ":" in comment[2]:
            postnum = comment[2].split(":")[-1]
        postnum = f"<a href='/post/{thread}/{postnum}'>#{postnum}.</a> "
        pubdate = datetime.datetime.fromtimestamp(int(comment[1]))
        pubdate = pubdate.strftime("%Y-%m-%d [%a] %H:%M")
        if len(comment[5]) == 0:
            comment[5] = settings.anon
        if sage:
            comment[5] = f"<span class='sage'>{comment[5]}</span>"

        replys.append(template.format(subject=comment[4],
                           postnum=postnum,
                           pubdate=pubdate,
                           author=comment[5],
                           comment=comment[3]))

    page = f"<h2><a href='/thread/{thread}'>{thread_subject}</a></h3>"
    page += f"Go back: <a href='/thread/{thread}#{anc}'>thread mode</a> "
    page += f"| <a href='/tree/{thread}#{anc}'>tree mode</a> "
    page += f"| <a href='/tree/{thread}/{str(reply)}'>sub tree</a><p>" 
    page += replys[0] + "<p>"
    if not wl.approve():
        page += ld_page("reply_captcha").format(wl.show_captcha(1, f"/post/{thread}/{reply}"))
    elif mode in ["3", "4"]:
        page += ld_page("closed_box")
    else:
        page += ld_page("reply_thread").format(
            anon=settings.anon, thread=thread, parent=anc,
            subject = str(settings.length["subject"]),
            name = str(settings.length["name"]),
            comment = str(settings.length["long"])
        )
    page += "<hr>"
    page += "<h3>Parents</h3>"
    page += "<p>".join(replys[1:])
    return mk_page(page)

@view.route('/thread/<thread>/')
def view_thread(thread):
    """View a thread in list mode"""
    if not os.path.exists(f"data/{thread}.txt"):
        return mk_page("404")
    page = ""
    page += thread_head(thread)
    page += parse.parse_thread(thread)
    return mk_page(page)

@view.route('/create/', methods = ["POST", "GET"])
def create_thread():
    """Allow a user to create a new thread"""
    if request.method == "GET":
        if wl.approve():
            tform = ld_page("new_thread")
            tform = tform.format(tags=mk_tagbox(),
                        author=settings.anon,
                        subject = str(settings.length["subject"]),
                        name = str(settings.length["name"]),
                        comment = str(settings.length["long"])
                                 )
            return mk_page(tform)
        else:
            return wl.show_captcha(0, "/create/")
            return "<meta http-equiv='refresh' content='0;URL=/captcha'>"
    data = request.form
    tags = request.form.getlist("tag")
    if not len(tags):
        tags = "random"
    tags = [t for t in tags if t in settings.tags]
    if not len(tags):
        tags = ["random"]
    if wl.flood("thread"):
        return mk_page(wl.flood("thread"))
    result = post.new_thread(data["subject"], data["comment"],
                             data["author"], tags)
    if len(result) > 20:
        return mk_page(result)
    output = ld_page("redirect").format(thread=result)
    return mk_page(output)

@view.route('/post', methods = ["POST"])
def reply_thread():
    """Post a reply to a thread"""
    sage = False
    data = request.form.copy()
    if None in [data["thread"], data["comment"]]:
        return None
    if "parent" not in data:
        parent = "1"
    if "author" not in data:
        data["author"] = settings.anon
    if "subject" not in data:
        data["subject"] = ""
    if "sage" in data:
        sage = True
    if wl.flood("comment"):
        return mk_page(wl.flood("comment"))
    error = post.new_reply(data["thread"], data["comment"],
                           data["parent"], data["author"],
                           data["subject"], sage)
    if error:
        return mk_page(error)
    output = ld_page("redirect").format(thread=data["thread"] + "#bottom")
    return mk_page(output)

@view.route('/recent/')
def recent_posts():
    """View x recent posts"""
    atoms = " <link rel='alternate' type='application/atom+xml'"
    atoms += f" href='/atom/recent'>\n"
    with open("data/log.txt") as posts:
        posts = posts.read().splitlines()[::-1]
    posts = [p.split("<>") for p in posts]
    output = [atoms]
    output.append(f"<h3>Last {settings.length['recent']} posts</h3>")
    ctemp = ld_page("comment")
    for p in posts:
        if len(p) > 7:
            continue
        pubdate = time.strftime("%Y-%m-%d [%a] %H:%M",
                                time.gmtime(int(p[2])))
        replynum = p[3]
        parent = ""
        if ":" in replynum:
            replynum = replynum.split(":")
            if replynum[-2] != "1":
                parent = replynum[-2]
                parentnum = ":".join(replynum[:-1])
                parent = f"<a href='/thread/{p[1]}#{parentnum}'>&gt;&gt;{parent}</a><br>"
                p[4] = parent + p[4]
            replynum = replynum[-1]
        postnum = f"<a href='/thread/{p[1]}#{p[3]}'>{replynum}.</a>"
        post = ctemp.format(postnum=postnum, subject=p[5],
                            pubdate=pubdate, author=p[6],
                            comment=p[4])
        output.append(post)
    output = output[:settings.length["recent"]+1]
    
    return mk_page("\n".join(output))
        
