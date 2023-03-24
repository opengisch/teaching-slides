"""
Update root 'index.html' to ensure that all and only the subfolders under 'web/' are listed.
Update presentation subfolders 'index.html' to conform with the styling.
"""

from os import path, symlink, unlink
from lxml import etree, html
from json import load

root_index = path.join(path.curdir, "index.html")
build_folder_name = "build"
build_folder = path.join(path.curdir, build_folder_name)
deployments = path.join(build_folder, "deployments.json")
presentation_types = ["talk", "teaching"]
a_bootstrap_classes = "list-group-item list-group-item-action"


def ensure_paths():
    """Throw on missing paths"""
    if missing := next(
        filter(lambda f: not path.exists(f), [root_index, build_folder, deployments]),
        None,
    ):
        raise FileExistsError(missing)


def get_expected_subdirs() -> list[str]:
    """
    Read list of build candidates from '.build/deployments.json'
    """
    with open(deployments, "r") as fh:
        dict_json = load(fh)

    if not "to_deploy" in dict_json:
        raise KeyError(
            "Your '.build/deployments.json' file misses an essential key: 'to_deploy'. Aborting."
        )

    rel_links = dict_json["to_deploy"]
    rel_links_paths = [path.join(build_folder, rel) for rel in rel_links]

    if broken_links := next(
        filter(lambda rel: not path.isdir(rel), rel_links_paths),
        None,
    ):
        raise FileExistsError(
            f"'{broken_links}' does not exist or is not a folder! Aborting."
        )

    return [f"/{u}" for u in rel_links]

 
def slug(url: str) -> str:
    """E.g. talk-example-presentation"""
    return url.split("/")[-1]


def slug_without_prefix(url: str) -> str:
    """E.g. example-presentation"""
    return url.partition('-')[2]


def remove_symlink(sym_link):
    # remove symbolic link
    if path.exists(sym_link):
        unlink(sym_link)


def create_a_tag(parser, url, text):
    return html.fromstring(
        f"<a class='{a_bootstrap_classes}' title='{text}' href='{url}'>{text}</a>",
        parser=parser,
    )


def add_to_root_index(parent, to_add: list[str], urls_in_index: list[str], parser):
    """Add to div"""
    for i, url in enumerate(sorted(to_add + urls_in_index)):
        if url in to_add:
            # add symbolic link for nicer url
            dirname = slug(url)
            sym_link = path.join(path.curdir, dirname)
            target_dir = path.join(build_folder, dirname)
            remove_symlink(sym_link)
            symlink(target_dir, sym_link, target_is_directory = True)
            a_tag = create_a_tag(parser, url, slug_without_prefix(url))
            parent.insert(i, a_tag)


def remove_from_root_index(parent, to_remove: list[str]):
    """Remove from div"""
    for el in parent:
        url = el.get("href")
        if url in to_remove:
            parent.remove(el)
            sym_link = path.join(path.curdir, slug(url))
            remove_symlink(sym_link)


def parse_index_html_template():
    parser = etree.HTMLParser()
    tree = etree.parse(root_index, parser=parser)
    return parser, tree.getroot()
   

def print_html(tree_root) -> str:
    new_tree = etree.tostring(tree_root, pretty_print=True, method="html")  # type: ignore
    return new_tree.decode("utf-8")

def adapt_root_index_html(parser, root, expected_subdirs: list[str]) -> tuple[list[str], str]:
    """Edit tree"""
    to_add = []
    for presentation_type in presentation_types:
        divs = root.xpath(f"//div[@id = 'presentation-links-{presentation_type}']")
        # in html: "presentation-links-talk" or "presentation-links-teaching"
        presentations_div = divs[0]
        links_in_index = presentations_div.xpath("//a/@href")
        to_add = [d for d in expected_subdirs if d[1:].startswith(presentation_type) and not d in links_in_index]
        to_remove = [href for href in links_in_index if not href in expected_subdirs]

        add_to_root_index(presentations_div, to_add, links_in_index, parser)
        remove_from_root_index(presentations_div, to_remove)
    
    return to_add, print_html(root)


def get_subdir_a_tags_attrs(parser, subdir_index) -> list[list[str]]: # [href, title][]
    tree = etree.parse(subdir_index, parser=parser)
    presentation_links = tree.xpath("//a")
    return [[a.get("href"), a.get("title")] for a in presentation_links]


def adapt_subdir_index_html(parser, root, subdir_index,  dirname: str):
    parent = root.xpath(f"//a[@id = 'presentation-links']")[0]
    for i, el in enumerate(parent):
        if i == 0:
            # Change content title
            el.text = slug_without_prefix(dirname)
        else:
            # Remove following links
            parent.remove(el)
    # Insert presentation links
    for i, (href, title) in enumerate(get_subdir_a_tags_attrs(parser, subdir_index)):
        a_tag = create_a_tag(parser, href, title)
        parent.insert(i, a_tag)
    return print_html(root)


def save_to_disk(file: str, tree_output: str):
    with open(file, "w") as fh:
        fh.write(tree_output)


def main():
    ensure_paths()
    expected_subdirs = get_expected_subdirs()
    print(f"Expected subdirs: {expected_subdirs}")
    parser, root = parse_index_html_template()
    added, root_index_html = adapt_root_index_html(parser, root, expected_subdirs)
    save_to_disk(root_index, root_index_html)
    print("Root index.html updated.")

    for dirname in added:
        subdir_index = path.join(build_folder, dirname, "index.html")
        subdir_index_html = adapt_subdir_index_html(parser, root, subdir_index, dirname)
        save_to_disk(root_index, subdir_index_html)
    print("Presentation subfolders index.html updated.")


if __name__ == "__main__":
    main()
