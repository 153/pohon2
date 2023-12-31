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

    updates = [""]
    tags = request.form.getlist("tag")
    deletes = request.form.getlist("d")
    updates.append(edit_tags(thread, tags))
    updates.append(delete_comments(thread, deletes))
    print(data)
#    return(str(data))
    updates = "<ul>" + "<li>".join(updates) + "</ul>"
    updates += f"<meta http-equiv='refresh' content='5;URL=/admin/threads/{thread}/'>"
    updates += f"<p><a href='/admin/threads/{thread}'>return in 5 seconds</a>"
    return mk_page(updates)

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

    table = ["<p><table><tr border-bottom='4px solid black'>",
             "<th><th>D<th>D+B<th>IP<th>Time<th>Comment"]
    row = ld_page("mod_comments")
    for n, c in enumerate(comments):
        n += 1
        comment = c[3].replace("<br>", "")[:50]
        table.append(row.format(n, c[0], timestamp(c[1]), comment, thread))
    table.append("</table>")
    table = "\n".join(table)

    # render page
    output = ld_page("edit_thread")\
        .format(thread=thread, subject=meta[1], replies=meta[2],
                tags=tags)
    output += table
    return mk_page(output)

def delete_thread(thread):
    with open("threads/index.txt") as index:
        index = index.read().splitlines()
    with open("threads/tags.txt") as tags:
        tags = tags.read().splitlines()

    # remove thread from index
    index = [i.split("<>") for i in index]
    index2 = ["<>".join(i) for i in index if i[0] != thread]
    index2 = "\n".join(index2) + "\n"
    
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
    if len(ntags) == 0:
        ntags = ["random"]
        
    with open(f"threads/{thread}.txt") as convo:
        convo = convo.read().splitlines()
    convo[0] = convo[0].split("<>")

    # turn old and new tag lists into sets
    tags = convo[0][0]
    if " " in tags:
        tags = set(tags.split(" "))
    else:
        tags = set([tags])
    ntags = set(ntags)

    # see what threads need to be added or removed
    add_list = ntags - tags
    del_list = tags - ntags
    if add_list == del_list:
        return "No tags modified"

    with open("threads/tags.txt", "r") as tlist:
        tlist = tlist.read().splitlines()
    tlist = [t.split(" ") for t in tlist]
    tlist = {t[0]: t[1:] for t in tlist}

    # apply changes to big thread list
    for t in add_list:
        if t not in tlist:
            tlist[t] = []
        tlist[t].append(thread)
    for t in del_list:
        if t not in tlist:
            continue
        tlist[t].remove(thread)
    tlist = "\n".join([" ".join([t, *tlist[t]]) for t in tlist])

    # apply changes to thread file
    ntags = " ".join(ntags)
    convo[0][0] = ntags
    convo[0] = "<>".join(convo[0])
    convo = "\n".join(convo) + "\n"

    with open(f"threads/{thread}.txt", "w") as newfile:
        newfile.write(convo)
    with open("threads/tags.txt", "w") as newfile:
        newfile.write(tlist)
    return f"{len(add_list) + len(del_list)} tags modified"

def delete_comments(thread, deletes):
    with open(f'threads/{thread}.txt', "r") as convo:
        convo = convo.read().splitlines()
    convo = [c.split("<>") for c in convo]
    deletes = [int(d) for d in deletes]
    if len(deletes) == 0:
        return "No comments deleted"
    for d in deletes:
        convo[d][3] = "<i>Message removed</i>"
        convo[d][4] = ""
        convo[d][5] = "</b><i>Deleted</i><b>"
    convo = "\n".join(["<>".join(c) for c in convo]) + "\n"
    with open(f'threads/{thread}.txt', "w") as output:
        output = output.write(convo)
    return f"{len(deletes)} comments deleted"
