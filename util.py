import re
import copy
import json
from pathlib import Path
from typing import List, Optional, Dict

from lxml import etree

from const import NEW_DICT_DIR
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

    PARAGRAPH_REGEX = r"(<p.*?>.*?</p>)"
    VAR_REGEX = r"(#VAR.*?#ENDVAR)"

    paragraph_matches = re.findall(PARAGRAPH_REGEX, text, re.DOTALL)
    var_matches = re.findall(VAR_REGEX, text, re.DOTALL)

    extracted_blocks += paragraph_matches
    extracted_blocks += var_matches

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


__all__ = ["split_htmlContent", "dict_update_splited_htmlContent"]


if __name__ == "__main__":
    count_entry(NEW_DICT_DIR)
