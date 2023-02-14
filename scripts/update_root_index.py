"""
Update root 'index.html' to ensure that all and only the subfolders under 'web/' are listed.
"""

from os import path
from lxml import etree, html
from json import load

root_index = path.join(path.curdir, "index.html")
build_folder = path.join(path.curdir, "build")
deployments = path.join(build_folder, "deployments.json")
presentation_link_id = "presentation-links"


def ensure_paths():
    """Throw on missing paths"""
    print(build_folder, deployments, root_index)
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

    if broken_links := next(
        filter(lambda rel: not path.exists(path.join(build_folder, rel)), rel_links),
        None,
    ):
        raise FileExistsError(broken_links)

    return [f"/{u}" for u in rel_links]


def add_to(parent, to_add: list[str], urls_in_index: list[str], parser):
    """Add to div"""
    for i, url in enumerate(sorted(to_add + urls_in_index)):
        if url in to_add:
            el = html.fromstring(
                f"<a class='web_subfolder' href='{url}'>{url[1:]}</a>",
                parser=parser,
            )
            parent.insert(i, el)


def remove_from(parent, to_remove: list[str]):
    """Remove from div"""
    for el in parent:
        url = el.get("href")
        if url in to_remove:
            parent.remove(el)


def build_modified_tree(expected_subdirs: list[str]) -> str:
    """Edit tree"""
    parser = etree.HTMLParser()
    tree = etree.parse(root_index, parser=parser)
    root = tree.getroot()
    divs = root.xpath("//div[@id = '%s']" % presentation_link_id)
    presentations_div = divs[0]
    links_in_index = presentations_div.xpath("//a/@href")
    to_add = [u for u in expected_subdirs if not u in links_in_index]
    to_remove = [u for u in links_in_index if not u in expected_subdirs]

    add_to(presentations_div, to_add, links_in_index, parser)
    remove_from(presentations_div, to_remove)

    new_tree = etree.tostring(root, pretty_print=True, method="html")  # type: ignore
    return new_tree.decode("utf-8")


def save_to_disk(tree_output: str):
    with open(root_index, "w") as fh:
        fh.write(tree_output)


def main():
    ensure_paths()
    expected_subdirs = get_expected_subdirs()
    print(f"Expected subdirs: {expected_subdirs}")
    new_tree = build_modified_tree(expected_subdirs)
    save_to_disk(new_tree)
    print("Tree rebuilt.")


if __name__ == "__main__":
    main()
