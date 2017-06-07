import yaml
from os.path import join


OUTPUT_PATH = "../jekyll/_taxonomy/"


with open('taxonomy_term_data.yml', 'r') as f:
    taxonomy = yaml.load(f)

for relation in taxonomy:
    filename = str(relation['tid']) + '.md'
    category = relation['name']
    category_underscored = category.replace(' ', '_')
    body = """---
redirect_to: "/categories/#{category}"
redirect_from:
  - "/tags/{category_underscored}"
""".format(category=category, category_underscored=category_underscored)
    if category_underscored != category_underscored.lower():
        body += """  - "/tags/{}"
""".format(category_underscored.lower())
    body += """---"""
    with open(join(OUTPUT_PATH, filename), 'w') as f:
        f.write(body)

print("Done")
