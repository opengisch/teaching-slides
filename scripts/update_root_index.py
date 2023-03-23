"""
Update root 'index.html' to ensure that all and only the subfolders under 'web/' are listed.
"""

from os import path, symlink, unlink
from lxml import etree, html
from json import load

root_index = path.join(path.curdir, "index.html")
build_folder_name = "build"
build_folder = path.join(path.curdir, build_folder_name)
deployments = path.join(build_folder, "deployments.json")
presentation_types = ["talk", "teaching"]


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

 
def get_subdir_from_href(url) -> str:
    return url.split("/")[-1]


def remove_symlink(sym_link):
    # remove symbolic link
    if path.exists(sym_link):
        unlink(sym_link)


def add_to(parent, to_add: list[str], urls_in_index: list[str], parser):
    """Add to div"""
    a_bootstrap_classes = "list-group-item list-group-item-action"
    for i, url in enumerate(sorted(to_add + urls_in_index)):
        if url in to_add:
            # add symbolic link for nice url
            dirname = url[1:]
            sym_link = path.join(path.curdir, dirname)
            target_dir = path.join(build_folder, dirname)
            remove_symlink(sym_link)
            symlink(target_dir, sym_link, target_is_directory = True)
            el = html.fromstring(
                f"<a class='{a_bootstrap_classes}' href='{url}'>{url.partition('-')[2]}</a>",
                parser=parser,
            )
            parent.insert(i, el)


def remove_from(parent, to_remove: list[str]):
    """Remove from div"""
    for el in parent:
        url = el.get("href")
        if url in to_remove:
            parent.remove(el)
            sym_link = path.join(path.curdir, get_subdir_from_href(url))
            remove_symlink(sym_link)


def build_modified_tree(expected_subdirs: list[str]) -> str:
    """Edit tree"""
    parser = etree.HTMLParser()
    tree = etree.parse(root_index, parser=parser)
    root = tree.getroot()
    for presentation_type in presentation_types:
        divs = root.xpath(f"//div[@id = 'presentation-links-{presentation_type}']")
        # in html: "presentation-links-talk" or "presentation-links-teaching"
        presentations_div = divs[0]
        links_in_index = presentations_div.xpath("//a/@href")
        to_add = [d for d in expected_subdirs if d[1:].startswith(presentation_type) and not d in links_in_index]
        to_remove = [href for href in links_in_index if not href in expected_subdirs]

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
