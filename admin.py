import datetime
from flask import Blueprint, request, make_response
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
    if checkpass != settings.password:
        return "<meta http-equiv='refresh' content='0;URL=/admin'>"

@admin.route('/admin/', methods=["POST", "GET"])
def login():
    checkpass = request.cookies.get("admin")
    if request.method == "GET":
        if checkpass != settings.password:
            return mk_page(ld_page("login"))
        return "<meta http-equiv='refresh' content='0;URL=/admin/menu'>"
    
    data = request.form.copy()
    if data["pw"] != settings.password:
        return "Fail"
    response = make_response(redirect('/admin/'))
    response.set_cookie("admin", data["pw"])
    return response

@admin.route('/admin/menu/')
def menu():
    check_login()
    return mk_page(ld_page("admin_menu"))

@admin.route('/admin/threads/')
def threads():
    with open("threads/index.txt") as index:
        index = index.read().splitlines()
    index = [i.split("<>") for i in index]
    page = ""
    page += "<ul>"
    for i in index:
        page += f"<li><a href='./{i[0]}/'>{i[3]}</a>"
        page += f" - {i[2]} replies"
    page += "</ul>"
    return mk_page(page)
