from flask import Blueprint, request
import post
import parse
import settings

view = Blueprint("view", __name__)

def header():
    with open("html/head.html", "r") as page:
        page = page.read()
    output = page.format(title=settings.title)
    return output

def footer():
    with open("html/footer.html", "r") as page:
        page = page.read()
    output = page.format(title=settings.title)
    return output

def mk_page(content):
    page = header()
    page += content
    page += footer()
    return page

def thread_head(thread):
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

@view.route('/thread/<thread>')
def view_thread(thread):
    page = parse.parse_thread(thread)
    return mk_page(page)

# post.new_thread(subject, comment, author, tags)
@view.route('/create', methods = ["POST", "GET"])
def create_thread():
    if request.method == "GET":
        with open("html/new_thread.html") as tform:
            tform = tform.read()
        return mk_page(tform)
    data = request.form
    result = post.new_thread(data["subject"], data["comment"],
                             data["author"], data["tags"])
    return "Thread posted"
    
#print(mk_page(view_thread("1660449790")))
