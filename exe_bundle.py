from lxml import etree
from pathlib import Path

import os

from const import *


def add_plugin(pom_path: Path, plugin_path: Path):
    """
    Add a plugin to the pom.xml
    """

    if not pom_path.exists():
        raise FileNotFoundError(f"{pom_path} does not exist")

    if not plugin_path.exists():
        raise FileNotFoundError(f"{plugin_path} does not exist")

    pom_tree: etree._ElementTree = etree.parse(pom_path)
    plugin_tree: etree._ElementTree = etree.parse(plugin_path)

    namespace = pom_tree.getroot().nsmap

    pom_plugins = list(pom_tree.iterfind("//plugins", namespaces=namespace))
    
    # find version
    plugin_version = list(pom_tree.iterfind("//version", namespaces=namespace))[0].text

    padding = max(0, 4 - len(plugin_version.split('.')))
    plugin_version = f"${{project.version}}{''.join(['.0'] * padding)}"
    
    plugin_tree.getroot().find(".//fileVersion").text = plugin_version
    plugin_tree.getroot().find(".//productVersion").text = plugin_version

    if len(pom_plugins) > 0:
        pom_plugins[0].append(plugin_tree.getroot())
    else:
        raise Exception("No plugins element found in pom.xml")

    pom_tree.write(pom_path, pretty_print=True, encoding="utf-8")


if __name__ == "__main__":
    pom_path = Path(SOURCE_DIR["main"]) / "pom.xml"
    plugin_path = Path(EXE_PLUGIN_PATH)

    add_plugin(pom_path, plugin_path)
