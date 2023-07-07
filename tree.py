import copy

example = {
    "1": ["15:22", "Nameless", "I shaved my cat today."],
    "1:2": ["15:30", "Curious", "Why did you do that?"],
    "1:3": ["15:34", "Purrvert", "Post shaved pussy pics!"],
    "1:2:4": ["15:45", "Nameless", "Her hair grows pretty long and she likes to play outside."],
    "1:5": ["15:50", "Anon", "What is your cat named?"],
    "1:3:6": ["15:55", "Nameless", "Get a life, you freak!!"],
    "1:5:7": ["16:20", "Nameless", "She is named Kelly and she is 4 years old."],
    "1:3:6:8": ["16:22", "Purrvert", "No. :3"]
    }

chars = {
    "diamond": "&#9670;",
    "square": "&#9632;",
    "line": "&boxv;",
    "dash": "&boxh;",
    "cross": "&boxvr;",
    "corner": "&boxur;"
}

def mklvl(treed):
    array = []
    head = []
    for n, t in enumerate(treed):
        item = treed[t]
        level = item[0]
        parent = item[-1]
        children = item[-2]
        if level == 0 and children > 0:
            array = [3]
        elif level == 0 and children == 0:
            array = [0]
        else:
            while len(array) < (level + 1):
                array.append(0)
            cont = treed[parent][-2] - treed[parent].index(t)
            if not cont:
                array[level-1] = 2
            else:
                array[level-1] = 1
            if children:
                array[level] = 3
        head.append(copy.deepcopy(array))

    for n, c in enumerate(head):
        for m, x in enumerate(c):
            if x == 2 and not (head[n-1][m] % 2):
                head[n][m] = 0
    for y in range(len(array)-1):
        for n, x in enumerate(head):
            if head[n][-1] == 0:
                head[n] = head[n][:-1]
    body = [[y%2 for y in x] for x in head]
    return [head, body]

def parse(tree):
    tree = sorted(tree)
    tree_dic = {}
    for t in tree:
        lev = t.count(":")
        children = [x for x in tree if t in x][1:]
        children = [x for x in children if x.count(":") == lev+1]
        if lev > 0:
            parent = ":".join(t.split(":")[:-1])
        else:
            parent = ""
        tree_dic[t] = [lev, *children, len(children), parent]
    lines = mklvl(tree_dic)
    return [tree, *lines]

# head: tree[1], date, name
# body: tree[2], message, tree[2]
        
def mktree(tree):
    # tree[1] shows what leftmargin the first line of the post need
    # tree[2] shows what leftmargin the rest lines of the post need
    
    # tree[1] + meta information "datetime, author" 
    # tree[2] + "comment" + tree[2] + "comment" ...

    if type(tree) is dict:
        tree = tree.keys()
    tree = parse(tree)
    for m, i in enumerate(tree[1]):
        if tree[1][m][-1] == 3:
            tree[1][m].pop()
        if len(tree[1][m]) == 0:
            continue
        if tree[1][m][-1] == 2:
            tree[1][m][-1] = chars["corner"]
        elif tree[1][m][-1] == 1:
            tree[1][m][-1] = chars["cross"]
        for n, j in enumerate(tree[1][m]):
            if j == 0:
                tree[1][m][n] = "&emsp;"
            elif j == 1:
                tree[1][m][n] = chars["line"]
        middle = [" ", chars["line"]]
        tree[2][m] = [middle[x] for x in tree[2][m]]
    tree[2][0] = [chars["line"]]
    return tree

def branch(node, comment, test=1):
    # comment: date, subject, comment
    head = "&emsp;".join(node[1])
    if len(node[1]) > 0:
        head += chars['dash']

    tail = comment[2]
    if "<br>" in tail:
        tail = tail.split("<br>")
    else:
        tail = [tail]
        
    # If no subject (comment[1]), try to load the first comment
    # if len(comment[1]) == 0:
    #     comment[1] = tail.pop(0)
    # if len(tail) == 0:
    #     tail.append("")
        
    head += chars['square'] + "&emsp;" \
         + comment[0] + " " + comment[1]

    for n, t in enumerate(tail):
        if "boxur" in head and not head.startswith("&boxur;"):
            if not node[2][-1] == "&boxv;":
                t = "&emsp;" + t

        tail[n] = "&emsp;".join(node[2]) \
            + "&emsp;" + t \
            + "\n" + "&emsp;".join(node[2])
    tail = "".join(tail)
    return "\n".join([head, tail])
        
    if "boxur" in head and not head.startswith("&boxur;"):
        if not node[2][-1] == "&boxv;":
            comment[2] = "&emsp;" + comment[2]

    # Make a loop for multiline comments
    tail = "&emsp;".join(node[2]) \
        + "&emsp;" + comment[2] \
        + "\n" + "&emsp;".join(node[2])
    return "\n".join([head, tail])

def fmt_tree(tree):
    skeleton = mktree(tree)
    output = []
    for n, i in enumerate(skeleton[0]):
        output.append([skeleton[0][n], skeleton[1][n], skeleton[2][n]])
    for n, i in enumerate(output):
        message = tree[i[0]]
        output[n] = branch(i, message)
    return "\n".join(output)

def fmt_list(tree):
    for i in tree:
        print(chars["square"],
              f"<a class='title'>#{i.split(':')[-1]}</a>",
              example[i][1] + ", at",  example[i][0])
        print(chars["line"])
        if len(i.split(":")) > 2:
            print(chars["line"], f"<a href=''>>>{i.split(':')[-2]}</a>")
        while example[i][2].startswith("&emsp;"):
            example[i][2] = example[i][2][6:].strip()
        print(chars["line"], example[i][2])
        print(chars["line"])

if __name__ == "__main__":
    with open("threads/1660449790.txt") as example:
        example = example.read().splitlines()[1:]
    example = [t.split("<>") for t in example]
    skeleton = {t[2]: ["1", t[4], t[3]] for t in example}
    fmt_tree(skeleton)
    
#print(fmt_tree(example))
#print("<hr>")
#fmt_list(example)
