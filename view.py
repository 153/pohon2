from flask import Blueprint, request
import parse
import post
import settings

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

@view.route('/')
def homepage():
    return mk_page(ld_page("index"))

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
    with open("threads/tags.txt") as tags:
        tags = tags.read().splitlines()
    tags = [t.split(" ") for t in tags]
    tags = [[t[0], len(t[1:])] for t in tags]
    tags.sort(key = lambda x: x[1], reverse = True)
    return tags

@view.route('/tags')
def show_tags():
    """Format the tag list for users"""
    tags = tag_list()
    page = ["<ul>"]
    for t in tags:
        if t[1] == 0:
            continue
        line = f"<li>{t[0]} - {t[1]} "
        if t[1] > 1:
            line += "threads"
        else:
            line += "thread"
        page.append(line)
    page = "\n".join(page)
    return mk_page(page)

def thread_head(thread):
    """Create a thread header, showing replies and tags"""
    meta = parse.get_meta(thread)
    subject = meta[1]
    tags = meta[0].split(" ")
    replies = meta[2] -1
    if replies != 1:
        replies = f"{replies} replies"
    else:
        replies = "1 reply"
    return str([subject, tags, replies])

@view.route('/tree')
def tree_index():
    """Show a list of threads; clicking threads renders them as trees"""
    with open("threads/index.txt") as index:
        index = index.read().splitlines()
    index = [i.split("<>") for i in index]
    index = [f"<a href='/tree/{i[0]}'>{i[3]}</a> ({i[2]} comments)"
             for i in index]
    index = "<li>" + "<li>".join(index)
    page = f"<ul>{index}</ul>"
    return mk_page(page)

@view.route('/thread')
def thread_index():
    """Show a list of threads; clicking threads renders them as lists"""
    with open("threads/index.txt") as index:
        index = index.read().splitlines()
    index = [i.split("<>") for i in index]
    index = [f"<a href='/thread/{i[0]}'>{i[3]}</a> ({i[2]} comments)"
             for i in index]
    index = "<li>" + "<li>".join(index)
    page = f"<ul>{index}</ul>"
    return mk_page(page)

@view.route('/tree/<thread>')
def view_tree(thread, view="tree"):
    """View a thread in tree mode"""
    with open("html/tree.html", "r") as page:
        page = page.read()
    with open(f"threads/{thread}.txt", "r") as data:
        data = data.read().splitlines()
    replycnt = len(data) - 2
    
    if replycnt != 1:
        replycnt = f"({replycnt} replies)"
    else:
        replycnt = "(1 reply)"
        
    meta = parse.get_meta(thread)
    tags = meta[0]    
    subject = meta[1]
    if " " in tags:
        tags = tags.split(" ")
        tags = [f" <a href='#'>#{t}</a>" for t in tags]
        tags = "".join(tags)
    # change parse_thread to parse_tree
    tree = parse.parse_tree(thread)
    page = page.format(subject=subject, replycnt=replycnt,
                       tags=tags, tree=tree, )
    return mk_page(page)

@view.route('/post/<thread>/<reply>')
def view_reply(thread, reply="1"):
    # Show the target post, its parents, its children, and
    # a new reply box.
    
    replychain = reply.split(":")
    with open(f"threads/{thread}.txt") as comments:
        comments = comments.read().splitlines()
    comments = [c.split("<>") for c in comments]
    replychain = [comments[int(r)][1:] for r in replychain]
    for r in replychain:
        print(r[1:])
    return "ok"

@view.route('/thread/<thread>')
def view_thread(thread):
    """View a thread in list mode"""
    page = parse.parse_thread(thread)
    return mk_page(page)

# post.new_thread(subject, comment, author, tags)
@view.route('/create', methods = ["POST", "GET"])
def create_thread():
    """Allow a user to create a new thread"""
    if request.method == "GET":
        with open("html/new_thread.html") as tform:
            tform = tform.read()
        tform = tform.format(mk_tagbox())
        return mk_page(tform)
    data = request.form
    tags = request.form.getlist("tag")
    if not len(tags):
        tags = "random"
    tags = [t for t in tags if t in settings.tags]
    if not len(tags):
        tags = ["random"]
    result = post.new_thread(data["subject"], data["comment"],
                             data["author"], tags)
    return "Thread posted"

if __name__ == "__main__":
    show_tags()
#print(mk_page(view_thread("1660449790")))
