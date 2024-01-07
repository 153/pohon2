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
    meta = parse.get_meta(thread)
    tags = meta[0]
    subject = meta[1]
    if " " in tags:
        tags = tags.split(" ")
        tags = [f" <i><a href='/tags/{t}/'>#{t}</a></i>" for t in tags]
        tags = "".join(tags)
    else:
        tags = f" <i><a href='/tags/{tags}'>#{tags}</a></i>"
        
    replies = meta[2]
    if replies != 1:
        replies = f"{replies} replies"
    else:
        replies = "1 reply"
    template = ld_page("thread_head")
    return template.format(thread=thread, subject=subject,
                           replies=replies, tags=tags, cnt=meta[2])

@view.route('/')
def homepage():
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
    return mk_page(ld_page("about"))

@view.route('/tags/')
def show_tags():
    """Format the tag list for users"""
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

@view.route('/tags/<tags>/')
def tag_index(tags):
    tags = tags.split("+")
    
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
    for t in tags:
        if t in tagdb:
            for t2 in tagdb[t]:
                results[t2] = [*threaddb[t2]]

    tags = " ".join([f"+{tag}" for tag in tags])
    results = [[t, *results[t]] for t in results]
    results.sort(key = lambda x: x[1], reverse=True)
    outstring = "<li> <a href='/thread/{0}/'>{1}</a> ({2} comments)"
    for r in results:
        output.append(outstring.format(r[0], r[3], r[2]))
    output = "<ul>\n" + "\n".join(output) + "\n</ul>"
    output = f"<h3>{tags} ({len(results)} threads)</h3>" + output
    
    return mk_page(output)

@view.route('/tree/')
def tree_index():
    """Show a list of threads; clicking threads renders them as trees"""
    with open("data/index.txt") as index:
        index = index.read().splitlines()
    index = [i.split("<>") for i in index]
    index.sort(key = lambda x: x[1], reverse=True)    
    index = [f"<a href='/tree/{i[0]}/'>{i[3]}</a> ({i[2]} replies)"
             for i in index]
    index = "<li>" + "<li>".join(index)
    page = f"<ul>{index}</ul>"
    return mk_page(page)

@view.route('/thread/')
def thread_index():
    """Show a list of threads; clicking threads renders them as lists"""
    with open("data/index.txt") as index:
        index = index.read().splitlines()
    index = [i.split("<>") for i in index]
    index.sort(key = lambda x: x[1], reverse=True)
    index = [f"<a href='/thread/{i[0]}/'>{i[3]}</a> ({i[2]} replies)"
             for i in index]
    index = "\n<li>" + "\n<li>".join(index)
    page = f"<ul>{index}\n</ul>\n"
    return mk_page(page)

@view.route('/tree/<thread>/')
def view_tree(thread, view="tree"):
    """View a thread in tree mode"""
    page = ld_page("tree")
    try:
        with open(f"data/{thread}.txt", "r") as data:
            data = data.read().splitlines()
    except:
        return mk_page("404")
    
    replycnt = len(data) - 2

    # change parse_thread to parse_tree
    tree = parse.parse_tree(thread)
    template = ld_page("tree")
    page = thread_head(thread)
    page += template.format(tree=tree, )
    return mk_page(page)

@view.route('/post/')
def post_null():
    return '<meta http-equiv="refresh" content="0;URL=/">'

@view.route('/post/<thread>/<reply>')
def view_reply(thread, reply="1"):
    # Show the target post, its parents, its children, and
    # a new reply box.

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

    page = f"<h2>&#9939; <a href='/thread/{thread}'>{thread_subject}</a></h3>"
    page += f"Go back: <a href='/thread/{thread}#{anc}'>thread mode</a> | <a href='/tree/{thread}#{anc}'>tree mode</a><p>" 
    page += replys[0] + "<p>"
    if wl.approve():
        page += ld_page("reply_thread").format(
            anon=settings.anon, thread=thread, parent=anc,
            subject = str(settings.length["subject"]),
            name = str(settings.length["name"]),
            comment = str(settings.length["long"])
        )
    else:
        page += ld_page("reply_captcha").format(wl.show_captcha(1, f"/post/{thread}/{reply}"))
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
    with open("data/log.txt") as posts:
        posts = posts.read().splitlines()[::-1]
    posts = [p.split("<>") for p in posts]
    output = ["<h3>Last 30 posts</h3>"]
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
    
    return mk_page("\n".join(output))
        
