"""
Update root 'index.html' to ensure that all and only the subfolders under 'web/' are listed.
"""

from os import listdir, path
from lxml import etree

web_folder = path.relpath("web")
root_index = path.relpath("index.html")
presentation_link_id = "presentation-links"


def ensure_paths():
    # Throw on missing paths
    if missing := next(
        filter(lambda f: not path.exists(f), [web_folder, root_index]), None
    ):
        raise FileExistsError(missing)


def add_to(body, to_add: list[str], urls_in_index: list[str], parser):
    # Add to body
    for url in sorted(to_add + urls_in_index):
        if url in to_add:
            el = etree.fromstring(
                f"<a class='web_subfolder' name='link to {url}' href='{url}'>{url[1:]}</a>",
                parser=parser,
            )
            print(f"Appending {url}")
            body.append(el)


def remove_from(body, to_remove: list[str]):
    # Remove from body
    for el in body:
        url = el.get("href")
        if url in to_remove:
            print(f"Removing {url}")
            body.remove(el)


def parse(listed_subdirs: list[str]):
    parser = etree.HTMLParser()
    tree = etree.parse(root_index, parser=parser)
    root = tree.getroot()
    div_elems = root.xpath("//div[@id = '%s']" % presentation_link_id)
    div = div_elems[0]
    links = div.xpath("//a/@href")
    to_remove = [u for u in links if not u in listed_subdirs]
    to_add = [f"/{u}" for u in listed_subdirs if not u in links]

    add_to(div, to_add, links, parser)
    remove_from(div, to_remove)

    print("Done modifying the tree:\n***\n")
    print(etree.tostring(root, pretty_print=True, method="html"))  # type: ignore


def main():
    ensure_paths()
    listed_subdirs = listdir(web_folder)

    if not listed_subdirs:
        raise ValueError(
            f"Found empty {web_folder}! The continuous integration must have failed you earlier."
        )

    parse(listed_subdirs)


if __name__ == "__main__":
    main()
