import re
import copy
import json
from pathlib import Path
from typing import List, Optional, Dict

from lxml import etree

from const import NEW_DICT_DIR
from data import XmlEntry
from logger import logger


def count_entry(dict_dir):
    dict_path = Path(dict_dir)

    total_num = 0

    for file in dict_path.glob("**/*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data: List[Dict] = json.load(f)

        total_num += len(data)

    logger.info("There are %s entries in total.", total_num)


def split_htmlContent(text: str) -> List[str]:
    extracted_blocks = []

    TAG_REGEX = r"(?:div|p)"

    PARAGRAPH_REGEX = r"(<p[^>]*?>.*?</p>)"
    TITLE_REGEX = r"(<h[1-9][^>]*?>.*?</h[1-9]>)"
    BOTH_START_P_REGEX = r"<p>\n[^<>]*?\n\s*<p>"
    BOTH_END_P_REGEX = r"</p>\n[^<>]*?\n\s*</p>"
    DIV_REGEX = r"(<div[^>]*?>.*?</div>)"
    HALF_BLOCK_F_REGEX = rf"(<{TAG_REGEX}[^>]*?>[^<>]*?\Z)"
    HALF_BLOCK_B_REGEX = rf"(\A[^<>]*?</{TAG_REGEX}>)"
    VAR_REGEX = r"(#VAR.*?#ENDVAR)"
    CUT_END_TAG_REGEX = rf"(#[A-Z]+[^<>]*?</{TAG_REGEX}>)"
    # CUT_START_TAG_REGEX = rf"(<{TAG_REGEX}[^>]*?>[^<>]*?#[A-Z]+.*?\n)"

    paragraph_matches = re.findall(PARAGRAPH_REGEX, text, re.DOTALL)
    title_regex = re.findall(TITLE_REGEX, text, re.DOTALL)
    div_matches = re.findall(DIV_REGEX, text, re.DOTALL)
    var_matches = re.findall(VAR_REGEX, text, re.DOTALL)
    half_block_f_matches = re.findall(HALF_BLOCK_F_REGEX, text, re.DOTALL)
    half_block_b_matches = re.findall(HALF_BLOCK_B_REGEX, text, re.DOTALL)
    cut_end_tag_matches = re.findall(CUT_END_TAG_REGEX, text, re.DOTALL)
    both_start_p_matches = re.findall(BOTH_START_P_REGEX, text, re.DOTALL)
    both_end_p_matches = re.findall(BOTH_END_P_REGEX, text, re.DOTALL)
    # cut_start_tag_matches = re.findall(CUT_START_TAG_REGEX, text, re.DOTALL)
    # if "Letting go of the milker, the foul rat-boy delivers a wickedly-sharp slap to her rear end, " in text:
    #     print(both_end_p_matches)
    #     input()
    
    extracted_blocks += paragraph_matches
    extracted_blocks += title_regex
    extracted_blocks += div_matches
    extracted_blocks += var_matches
    extracted_blocks += half_block_f_matches
    extracted_blocks += half_block_b_matches
    filtered_cut_end_tag_matches = filter(lambda x: not any([x in block for block in extracted_blocks]), cut_end_tag_matches)
    extracted_blocks += filtered_cut_end_tag_matches
    filtered_both_start_p_matches = filter(lambda x: not any([x in block for block in extracted_blocks]), both_start_p_matches)
    extracted_blocks += filtered_both_start_p_matches
    filtered_both_end_p_matches = filter(lambda x: not any([x in block for block in extracted_blocks]), both_end_p_matches)
    extracted_blocks += filtered_both_end_p_matches
    # extracted_blocks += cut_start_tag_matches

    if len(extracted_blocks) == 0:
        extracted_blocks.extend(text.split("<br/><br/>"))

    if len(extracted_blocks) == 0:
        extracted_blocks.append(text)

    return extracted_blocks


def dict_update_splited_htmlContent(old_dict_dir: Path):
    for file in old_dict_dir.glob("res/**/*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data: List[Dict] = json.load(f)
        splited = []
        for idx, item in enumerate(data):
            if "htmlContent" not in item["key"]:
                continue
            original_splited = split_htmlContent(item["original"])
            translation_splited = split_htmlContent(item["translation"])
            if len(original_splited) != len(translation_splited):
                logger.warning(
                    "%s has unpaired entry of key %s\n\t\tthere are %s original splits but %s splits",
                    file,
                    item["key"],
                    original_splited,
                    translation_splited,
                )
                continue
            new_items = []
            for i, original in enumerate(original_splited):
                new_item = copy.deepcopy(item)
                new_item["original"] = original
                new_item["translation"] = translation_splited[i]
                new_item["key"] = new_item["key"] + f"_{i}"
                new_items.append(new_item)
            splited.append((idx, new_items))
        if len(splited) <= 0:
            continue
        for idx, new_items in splited[::-1]:
            data.pop(idx)
        for idx, new_items in splited:
            data.extend(new_items)
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


def xml_node_replace_translation(node: etree._Element, entry: XmlEntry) -> str:
    if entry.stage == 0 or entry.translation == entry.original:  # 无需修改
        return
    # htmlContent的属性用于存储文本的对应id，并不需要替换属性文本
    if entry.attribute is not None and entry.node_tag != "htmlContent":
        node.set(entry.attribute, entry.translation)
    else:
        node.text = node.text.replace(
            entry.original,
            entry.translation.replace("\\n", "\n"),
        )
    node.text = etree.CDATA(node.text)


__all__ = ["split_htmlContent", "dict_update_splited_htmlContent"]


if __name__ == "__main__":
    count_entry(NEW_DICT_DIR)
