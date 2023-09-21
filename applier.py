from pathlib import Path
from lxml import etree
from typing import List, Dict
import json
import re

from data import XmlEntry, CodeEntry
from logger import logger


class Applier:
    def __init__(self, root: str, dict_dir: str) -> None:
        self.root = Path(root)
        self.dict_dir = Path(dict_dir)

    def apply(self) -> None:
        self.apply_res()
        self.apply_src()

    def apply_res(self) -> None:
        original_files = [file for file in self.root.glob("**/*.xml")]
        dict_fils = [self.dict_dir.joinpath(file.relative_to(
            self.root)).with_suffix('.json') for file in original_files]

        for original_file, dict_file in zip(original_files, dict_fils):
            if not dict_file.exists():  # 不存在对应字典文件
                continue

            self.apply_xml(original_file, dict_file)

    def apply_xml(self, original_file: Path, dict_file: Path) -> None:
        with open(dict_file, "r", encoding="utf-8") as f:
            entry_list = json.load(f)

        entry_list = [XmlEntry.from_json(
            original_file, entry) for entry in entry_list]
        
        parser = etree.XMLParser(strip_cdata=False)

        tree: etree._Element = etree.parse(str(original_file), parser)

        entry_dict: Dict[str, List[XmlEntry]] = {}
        for entry in entry_list:
            if entry_dict.get(entry.node_tag) is None:
                entry_dict[entry.node_tag] = [entry]
            else:
                entry_dict[entry.node_tag].append(entry)

        for tag, entry_cluster in entry_dict.items():
            nodes: List[etree._Element] = list(tree.iter(tag))
            nodes = list(filter(lambda node: not(node.text is None or len(node.text.strip())==0) , nodes))
            if len(entry_cluster) != len(nodes):
                logger.warning(f"\t****{original_file.relative_to(self.root)}: 节点{tag}数量({len(nodes)})与字典数量({len(entry_cluster)})不匹配")
                continue
            for entry, node in zip(entry_cluster, nodes):
                if len(entry.translated_text) <= 0 or entry.translated_text == entry.original_text:  # 暂无汉化或无需修改
                    continue

                if entry.attribute is not None:
                    node.set(entry.attribute, entry.translated_text)
                else:
                    node.text = entry.translated_text
                    node.text = etree.CDATA(node.text)

        

        tree.write(original_file.as_posix(), encoding="utf-8",
                   xml_declaration=True, pretty_print=True, standalone=False)

    def apply_src(self) -> None:
        original_files = [file for file in self.root.glob("**/*.java")]
        dict_fils = [self.dict_dir.joinpath(file.relative_to(
            self.root)).with_suffix('.json') for file in original_files]

        for original_file, dict_file in zip(original_files, dict_fils):
            if not dict_file.exists():  # 不存在对应字典文件
                continue

            self.apply_java(original_file, dict_file)
            
    def apply_java(self, original_file: Path, dict_file: Path) -> None:
        with open(dict_file, "r", encoding="utf-8") as f:
            entry_list = json.load(f)
        with open(original_file, "r", encoding="utf-8") as f:
            text = f.readlines()

        entry_list = [CodeEntry.from_json(
            original_file, entry) for entry in entry_list]
        
        for entry in entry_list:
            line_text = text[entry.line]
            applied_text = self.apply_java_line(line_text, entry.original_text, entry.translated_text)
            text[entry.line] = applied_text
        
        with open(original_file, "w", encoding="utf-8") as f:
            f.writelines(text)


    def apply_java_line(self, text: str, original_text: str, translated_text: str) -> str:
        if len(translated_text) <= 0:
            return text
        index = text.find(original_text)
        if index == -1:
            logger.warning("\t****原文本无匹配！")
            return text
        else:
            text = text[:index] + translated_text + text[index + len(original_text):]
            return text
