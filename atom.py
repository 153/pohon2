import time
from flask import Blueprint
import settings

atom = Blueprint("atom", __name__)

tstring = "%Y-%m-%dT%H:%M:%S+00:00"
url = settings.url

feed_temp = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">

<title>{title}</title>
<author><name>Anonymous</name></author>
<id>{url}</id>
<link rel="self" href="{link}" />
<updated>{published}</updated>

"""

entry_temp = """
<entry>
<title>{title}</title>
<link rel="alternate" href="{url}" />
<id>{url}</id>
<published>{published}</published>
<updated>{updated}</updated>
<content type="html">
{content}
</content>
</entry>"""

def unix2atom(unix):
    atom = time.strftime(tstring, time.localtime(int(unix)))
    return atom

@atom.route("/atom/")
def atom_index():
    page = """<pre>

- <a href='/atom/threads'>/atom/threads</a> \tAll threads
- <a href='/atom/recent'>/atom/recent</a> \t\tRecent comments

"""
    page += tag_index()
    return page

@atom.route("/atom/threads")
def threads(index=None, link=None):
    if not index:
        with open("data/index.txt") as index:
            index = index.read().splitlines()
        index = [i.split("<>") for i in index]
    index.sort(key = lambda x: x[1], reverse=True)
    publish = unix2atom(index[0][1])
    # create update replies subject
    entries = []
    for i in index:
        with open(f"data/{i[0]}.txt") as tfile:
            tfile = tfile.read().splitlines()[1]
        content = tfile.split("<>")[3]\
                       .replace("<", "&lt;")\
                       .replace(">", "&gt;")
        title = i[3]
        link = url + "thread/" + i[0]
        published = unix2atom(i[0])
        updated = unix2atom(i[1])
        entry = entry_temp.format(title=title, url=link,
                                  published=published,
                                  updated=updated,
                                  content=content)
        entries.append(entry)
    entries = "\n".join(entries)
    if not link:
        link = url + "/atom/threads"
    output = feed_temp.format(title=settings.title,
                              url=link, link=link,
                              published=publish)
    output += entries
    output += "\n\n</feed>"
    return output

@atom.route("/atom/tag/")
def tag_index():
    with open("data/tags.txt") as index:
        index = index.read().splitlines()
    index = [i.split(" ") for i in index]
    output = ["<pre>"]
    for i in index:
        url = "/atom/tag/" + i[0]
        output.append(f"- <a href='{url}'>{url}</a> \t- #{i[0]}")
    output = "\n".join(output)
    return output
    
@atom.route("/atom/tag/<tag>")
def tag_feed(tag):
    with open("data/tags.txt") as tagi:
        tagi = tagi.read().splitlines()
    tagi = [t.split(" ") for t in tagi]
    tagi = {t[0]: t[1:] for t in tagi}
    if tag not in tagi:
        return
    index = tagi[tag]
    
    with open("data/index.txt") as threadi:
        threadi = threadi.read().splitlines()
    threadi = [t.split("<>") for t in threadi]
    index = [t for t in threadi if t[0] in index]
    link = url + "/atom/tag/" + tag
    return threads(index, link)

@atom.route("/atom/recent")
def recent_feed():
    with open("data/log.txt") as log:
        log = log.read().splitlines()[::-1]
    log = [l.split("<>") for l in log][:30]
    
    published = unix2atom(log[0][2])
    entries = []
    for l in log:
        # title url published updated content
        # "New post" /post/l[1]/l[3] l[2] l[2] l[4]
        title = "New reply"
        if len(l[5]):
            title = l[5]
        link = f"{settings.url}thread/{l[1]}/#{l[3]}"
        published = unix2atom(l[2])
        content = l[4].replace("<", "&lt;").replace(">", "&gt;")
        entry = entry_temp.format(title=title, url=link,
                                  published=published,
                                  updated=published,
                                  content=content)
        entries.append(entry)
    entries = "\n".join(entries)
    title = settings.title + ": recent posts"
    url = settings.url + "recent"
    link = settings.url + "atom/recent"
    output = feed_temp.format(title=title, url=url, link=link,
                              published=published)
    output += entries
    output += "\n\n</feed>"

    return output
    
        
        

if __name__ == "__main__":
    recent_feed()
