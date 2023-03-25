"""
Build root 'index.html' to ensure that all and only the subfolders are listed.
"""

from os import path
import chevron
from json import load

build_folder_name = "build"
build_folder = path.join(path.curdir, build_folder_name)
index_template = path.join(path.curdir, build_folder, "index.html")
root_index = path.join(path.curdir, "index.html")
deployments = path.join(build_folder, "deployments.json")
talk = "talk", 
teaching = "teaching"


def ensure_paths():
    """Throw on missing paths"""
    if missing := next(
        filter(lambda f: not path.exists(f), [index_template, build_folder, deployments]),
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


def strip_prefix(url: str) -> str:
    """E.g. example-presentation"""
    return url.partition('-')[2]


def generate_keys_from_dirnames(prefix, dirs: list[str]):
    return [{"url": d, "title": strip_prefix(d)} for d in dirs if d[1:].startswith(prefix)]


def generate_template_data(expected_subdirs: list[str]):
    talk_presentations = generate_keys_from_dirnames(talk, expected_subdirs)
    teaching_presentations = generate_keys_from_dirnames(teaching, expected_subdirs)
    return {
        "is_root": True,
        "pageTitle": "Presentations",
        "has_talk_presentations": bool(talk_presentations),
        "talk_presentations": talk_presentations,
        "has_teaching_presentations": bool(teaching_presentations),
        "teaching_presentations": teaching_presentations,
    }


def save_to_disk(file: str, html: str):
    with open(file, "w") as fh:
        fh.write(html)


def generate_root_html(template, data):
    with open(template, 'r') as f:
        return chevron.render(f, data)


def main():
    ensure_paths()
    expected_subdirs = get_expected_subdirs()
    print(f"Expected subdirs: {expected_subdirs}")
    data = generate_template_data(expected_subdirs)
    html_str = generate_root_html(index_template, data)
    save_to_disk(root_index, html_str)
    print("Root index.html updated.")


if __name__ == "__main__":
    main()
