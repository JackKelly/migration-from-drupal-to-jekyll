import xml.etree.ElementTree as ET
from datetime import datetime
from os.path import join
import pypandoc
from copy import deepcopy
import re
from progress.bar import Bar

RSS_FILENAME = "rss.xml"
OUTPUT_PATH = "_posts"

DATETIME_FORMAT = '%a, %d %b %Y %H:%M:%S %z'

JUNK_FRONT = '<div class="field field-name-body field-type-text-with-summary field-label-above"><div class="field-label">Body:&nbsp;</div><div class="field-items"><div class="field-item even" property="content:encoded">'
JUNK_TAIL = '</div></div></div>'


def delete(string, targets):
    for target in targets:
        string = string.replace(target, '')
    return string


def replace_between(string, start, stop, replacement):
    pattern = '{}.*?{}'.format(start, stop)
    return re.sub(pattern, replacement, string, flags=re.DOTALL)


def delete_between(string, start, stop):
    return replace_between(string, start, stop, '')


def extract_dict(item):
    item_dict = {}
    item_dict['title'] = item.findtext('title')

    # Date
    datetime_str = item.findtext('pubDate')
    dt = datetime.strptime(datetime_str, DATETIME_FORMAT)
    item_dict['date'] = dt.strftime('%Y-%m-%d %H:%M:%S %z')

    # Filename
    link = item.findtext('link').replace('http://jack-kelly.com', '')
    item_dict['permalink'] = link
    link_stripped = delete(link[1:], ['blog/', 'notes/'])
    item_dict['filename'] = dt.strftime('%Y-%m-%d') + '-' + link_stripped + '.md'

    # Content
    content_html = item.findtext('description')

    if "haunted" in item_dict['title']:
        with open("haunted.html", "w") as f:
            f.write(content_html)

    content_html = delete(
        content_html,
        [JUNK_FRONT, JUNK_TAIL, 'class="flickr-photo-img"', 'class=" flickr-img-wrap"',
         'style="width:800px;"'])
    content_html = delete_between(
        content_html, '<span class="flickr-credit">', '</a>.</span></span>')
    content_html = replace_between(
        content_html, '<img width', 'src="http://farm', '<img src="http://farm')
    content_html = content_html.replace('iframe width="690" height="388"',
                                        'iframe width="740" height="416"')

    content_md = pypandoc.convert_text(
        content_html, 'md', format='html', extra_args=['--parse-raw'])
    content_md = content_md.replace("CO~2~", "CO<sub>2</sub>")

    item_dict['content'] = content_md

    # Tags
    categories = []
    for category in item.findall('category'):
        category_text = '"' + list(category.itertext())[0] + '"'
        categories.append(category_text)
    item_dict['categories'] = "[" + ", ".join(categories) + "]"

    return item_dict


def save_to_file(item_dict):
    item_dict = deepcopy(item_dict)
    item_dict['title'] = item_dict['title'].replace(r"'", r"\'").replace(r'"', r'\"')
    
    text = """---
title: "{title}"
date: {date}
categories: {categories}
permalink: {permalink}
---
{content}
""".format(**item_dict)
    filename = join(OUTPUT_PATH, item_dict['filename'])
    with open(filename, 'w') as f:
        f.write(text)


tree = ET.parse(RSS_FILENAME)
items = tree.findall("channel/item")
print("Extracted", len(items), "posts.  Now to save them as Jekyll files...\n")
bar = Bar('Files', max=len(items))

for item in items:
    bar.next()
    item_dict = extract_dict(item)
    save_to_file(item_dict)

bar.finish()
print("Done!")
