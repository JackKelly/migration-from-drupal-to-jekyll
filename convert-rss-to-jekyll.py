from lxml import etree as ET
from datetime import datetime
from os.path import join
import pypandoc
from copy import deepcopy
import html

RSS_FILENAME = "rss.xml"
OUTPUT_PATH = "_posts"

DATETIME_FORMAT = '%a, %d %b %Y %H:%M:%S %z'

JUNK_FRONT = '<div class="field field-name-body field-type-text-with-summary field-label-above"><div class="field-label"></div><div class="field-items"><div class="field-item even" property="content:encoded">'
JUNK_TAIL = '</div></div></div>'

LOG_FILE = "dumps/logfile.txt"
fh = open(LOG_FILE, 'w')
fh.close()

def fix_flickr(content_html, link):
    #content_html = content_html.replace("<em></p>", "</p>")
    #content_html = content_html.replace("<p></em>", "<p>")
    content_html = content_html.replace("allowfullscreen", 'allowfullscreen="1"')
    content_html = content_html.replace("&CategoryID=1", "")
    content_html = content_html.replace("&nbsp;", "<br/>")
    
    parser = ET.XMLParser(encoding='utf-8', recover=True)
    tree = ET.fromstring(content_html, parser=parser)

    if parser.error_log:
        print("Parsing error for", link)
        print(parser.error_log)
        with open(LOG_FILE, 'a') as fh:
            fh.write(str(parser.error_log))
        with open('dumps/' + link + 'dump.html', 'w') as dump_file:
            dump_file.write(content_html)
        

    # Fix flickr
    for span in tree.findall('div/div/p/span'):
        for subspan in span.findall('span'):
            if subspan.attrib['class'] == 'flickr-credit':
                span.remove(subspan)
                print("Removed flickr junk")

    # Get rid of spurious <div>s
    new_tree = ET.Element('p')
    for div in tree.iter('div'):
        if div.attrib['class'] == 'field-item even':
            new_tree.extend(div.getchildren())
            break

    return str(ET.tostring(new_tree)).replace("b'", "")


def extract_dict(item):
    item_dict = {}
    item_dict['title'] = item.findtext('title')

    # Date
    datetime_str = item.findtext('pubDate')
    dt = datetime.strptime(datetime_str, DATETIME_FORMAT)
    item_dict['date'] = dt.strftime('%Y-%m-%d %H:%M:%S %z')

    # Filename
    link = item.findtext('link').replace('http://jack-kelly.com/', '')
    for subdir in ['blog/', 'notes/']:
        if subdir in link:
            link = link.replace(subdir, "")
            filename = dt.strftime('%Y-%m-%d') + '-' + link
            item_dict['filename'] = filename + '.md'
            item_dict['permalink'] = '/' + subdir + filename
            break
    else:
        item_dict['filename'] = dt.strftime('%Y-%m-%d') + '-' + link + '.md'
        item_dict['permalink'] = ""

    # Content
    content_html = item.findtext('description')
    content_html = content_html.replace("Body:&nbsp;", "")
    if 'flickr-credit' in content_html:
        content_html = fix_flickr(content_html, link)
    else:
        content_html = content_html.replace(JUNK_FRONT, '').replace(JUNK_TAIL, '')
    content_md = pypandoc.convert_text(content_html, 'md', format='html')
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
print("Extracted", len(items), "posts.  Now to save them as Jekyll files...")

for item in items:
    item_dict = extract_dict(item)
    save_to_file(item_dict)

print("Done!")
