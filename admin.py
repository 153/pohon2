import datetime
import os
from flask import Blueprint, request, make_response, redirect
import view
from view import ld_page, mk_page, mk_tagbox
import settings

admin = Blueprint("admin", __name__)

def timestamp(x):
    x = datetime.datetime.fromtimestamp(int(x))
    x = x.strftime("%Y-%m-%d [%a] %H:%M")
    return x

def check_login():
    checkpass = request.cookies.get("admin")
    print(checkpass)
    if checkpass != settings.password:
        return "<meta http-equiv='refresh' content='0;URL=/admin'>"
    return None

@admin.route('/logout/')
def logout():
    response = make_response(redirect('/admin/'))
    response.set_cookie("admin", "null")
    return response

@admin.route('/admin/', methods=["POST", "GET"])
def login():
    checkpass = request.cookies.get("admin")
    if request.method == "GET":
        if checkpass != settings.password:
            return mk_page(ld_page("login"))
        return "<meta http-equiv='refresh' content='0;URL=/admin/menu'>"
    
    data = request.form.copy()
    if data["pw"] != settings.password:
        return "<meta http-equiv='refresh' content='0;URL=/admin'>"
    response = make_response(redirect('/admin/'))
    response.set_cookie("admin", data["pw"])
    return response

@admin.route('/admin/menu/')
def menu():
    if check_login():
        return check_login()
    return mk_page(ld_page("admin_menu"))

@admin.route('/admin/threads/')
def threads():
    if check_login():
        return check_login()
    with open("threads/index.txt") as index:
        index = index.read().splitlines()
    index = [i.split("<>") for i in index]
    index.sort(key = lambda x: x[1], reverse=True)
    page = ""
    page += "<ul>"
    for i in index:
        page += f"<li><a href='./{i[0]}/'>{i[3]}</a>"
        page += f" - {i[2]} replies"
    page += "</ul>"
    return mk_page(page)

@admin.route('/admin/threads/<thread>/', methods=["POST", "GET"])
def thread_edit(thread):
    data = request.form.copy()
    if request.method == "GET":
        return thread_edit_page(thread)
    
    if "mod" in data and data["mod"] == "delete":
        delete_thread(data["thread"])
        return mk_page("Thread successfully deleted. "
                       "<p><a href='/admin/threads/'>Return</a>")

    tags = request.form.getlist("tag")
    edit_tags(thread, tags)
    print(data)
#    return(str(data))

    return str(request.form)

def thread_edit_page(thread):
    with open(f"threads/{thread}.txt", "r") as data:
        data = data.read().splitlines()
    meta = data[0].split("<>")
    comments = [d.split("<>") for d in data[1:]]
    meta.append(len(comments))

    # make threadbox
    t_tags = meta[0].split(" ")
    g_tags = settings.tags

    label = "<label for='{0}'>{1} {0}</label>"
    uncheck = "<input type='checkbox' name='tag' id='{0}' value='{0}'>"
    check = "<input type='checkbox' name='tag' id='{0}' value='{0}' checked>"
    
    tagbox = []
    for tag in g_tags:
        if tag in t_tags:
            tagbox.append(label.format(tag, check.format(tag)))
        else:
            tagbox.append(label.format(tag, uncheck.format(tag)))
    tags = "\n".join(tagbox)
    tags = ld_page("tagbox").format(tags)

    # render page
    output = ld_page("edit_thread")\
        .format(thread=thread, subject=meta[1], replies=meta[2],
                tags=tags)
    output += "<pre>" + str(str(meta) + "\n" + str(comments))
    return mk_page(output)

def delete_thread(thread):
    with open("threads/index.txt") as index:
        index = index.read().splitlines()
    with open("threads/tags.txt") as tags:
        tags = tags.read().splitlines()

    # remove thread from index
    index = [i.split("<>") for i in index]
    index2 = ["<>".join(i) for i in index if i[0] != thread]
    index2 = "\n".join(index2)
    
    # remove thread from tags
    tags = [t.split(" ") for t in tags]
    for t in tags:
        if thread in t:
            t.remove(thread)
    tags = "\n".join([" ".join(t) for t in tags])

    # delete thread file, write new index and tag files
    os.remove(f"threads/{thread}.txt")
    with open("threads/tags.txt", "w") as tagfile:
        tagfile.write(tags)
    with open("threads/index.txt", "w") as indexfile:
        indexfile.write(index2)

def edit_tags(thread, ntags):
    print(ntags)
    if len(ntags) == 0:
        ntags = ["random"]
        
    with open(f"threads/{thread}.txt") as convo:
        convo = convo.read().splitlines()
    convo[0] = convo[0].split("<>")
    
    tags = convo[0][0]
    if " " in tags:
        tags = set(tags.split(" "))
    else:
        tags = set([tags])
    ntags = set(ntags)
#    if len(ntags) > 1:
#        ntags = set(ntags)
#    else:
#        ntags = set(ntags)
        
    add_list = ntags - tags
    del_list = tags - ntags
    if add_list == del_list:
        return

    with open("threads/tags.txt", "r") as tlist:
        tlist = tlist.read().splitlines()
    print("\n".join(tlist))
    tlist = [t.split(" ") for t in tlist]
    tlist = {t[0]: t[1:] for t in tlist}

    print("++", add_list)
    print("--", del_list)
    for t in add_list:
        if t not in tlist:
            tlist[t] = []
        tlist[t].append(thread)
    for t in del_list:
        if t not in tlist:
            continue
        tlist[t].remove(thread)
    
    tlist = "\n".join([" ".join([t, *tlist[t]]) for t in tlist])
    print("~~~", tlist)
    ntags = " ".join(ntags)
    convo[0][0] = ntags
    convo[0] = "<>".join(convo[0])
    convo = "\n".join(convo)

    with open(f"threads/{thread}.txt", "w") as newfile:
        newfile.write(convo)
    with open("threads/tags.txt", "w") as newfile:
        newfile.write(tlist)
