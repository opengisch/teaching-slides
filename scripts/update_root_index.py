"""
Update root 'index.html' to ensure that all and only the subfolders under 'web/' are listed.
"""

from sys import argv
from os import path
from lxml import etree, html
from json import dumps

web_folder = path.relpath("web")
root_index = path.relpath("index.html")
presentation_link_id = "presentation-links"


def ensure_paths():
    # Throw on missing paths
    if missing := next(filter(lambda f: not path.exists(f), [root_index]), None):
        raise FileExistsError(missing)


def get_inputs() -> tuple[list[str], list[str]]:
    # Get valid input
    if not argv[1] or argv[2]:
        raise ValueError("This Python scripts requires 2 arguments")

    to_include = argv[1].split("\n")
    # Expecting 'Opted-out: val1 val2 val3...'
    to_exclude = argv[2].split(":")[1].split(" ")

    if not to_include:
        raise ValueError("This Python scripts requires at least one list as input!")

    return to_include, to_exclude


def add_to(parent, to_add: list[str], urls_in_index: list[str], parser):
    # Add to div
    for i, url in enumerate(sorted(to_add + urls_in_index)):
        if url in to_add:
            el = html.fromstring(
                f"<a class='web_subfolder' name='link to {url}' href='{url}'>{url[1:]}</a>",
                parser=parser,
            )
            parent.insert(i, el)


def remove_from(parent, to_remove: list[str]):
    # Remove from div
    for el in parent:
        url = el.get("href")
        if url in to_remove:
            parent.remove(el)


def build_modified_tree(to_include: list[str], to_exclude: list[str]) -> str:
    # Edit tree
    parser = etree.HTMLParser()
    tree = etree.parse(root_index, parser=parser)
    root = tree.getroot()
    divs = root.xpath("//div[@id = '%s']" % presentation_link_id)
    presentations_div = divs[0]
    links = presentations_div.xpath("//a/@href")
    to_add = [f"/{u}" for u in to_include if not u in links]
    to_remove = [f"/{u}" for u in to_exclude]

    add_to(presentations_div, to_add, links, parser)
    remove_from(presentations_div, to_remove)

    new_tree = etree.tostring(root, pretty_print=True, method="html")  # type: ignore
    return new_tree.decode("utf-8")


def save_to_disk(tree_output: str):
    with open(root_index, "w") as fh:
        fh.write(tree_output)


def main():
    ensure_paths()
    to_include, to_exclude = get_inputs()
    new_tree = build_modified_tree(to_include, to_exclude)
    save_to_disk(new_tree)
    print(dumps(to_exclude))


if __name__ == "__main__":
    main()
