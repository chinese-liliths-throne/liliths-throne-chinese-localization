import json
import os
import shutil

from pathlib import Path
from typing import Dict, Union, List, Tuple

from logger import logger
from data import JsonEntry, WholeDictionary, SingleDictionary
from const import ENTRY_DIFF_DIR, TRANS_DIFF_DIR


class Processor:
    def __init__(
        self,
        target: str,
        dict_path: Path,
        old_dict_path: Path,
        pt_token: str,
        new_data: WholeDictionary = {},
        old_data: WholeDictionary = {},
    ):
        self.target = target
        self.dict_path = dict_path
        self.old_dict_path = old_dict_path
        self.pt_token = pt_token

        self.upgrade_files = set()

        self.translated: Dict[str, JsonEntry] = {}
        self.untranslated: Dict[str, JsonEntry] = {}

        self.new_data: WholeDictionary = new_data
        self.old_data: WholeDictionary = old_data

    def load(self):
        for path, fileDict in self.new_data.items():
            for key, entry in fileDict.items():
                if entry["stage"] != 0:
                    self.translated[path + ":" + key] = entry
                else:
                    self.untranslated[path + ":" + key] = entry

    def process(self):
        self.load()
        self.check_same()
        self.filter_changed()

    def filter_changed(self):
        shutil.rmtree(ENTRY_DIFF_DIR[self.target], ignore_errors=True)
        shutil.rmtree(TRANS_DIFF_DIR[self.target], ignore_errors=True)

        entry_diff: List[str] = []
        trans_diff: Dict[str, List[JsonEntry]] = {}

        for file, entries in self.new_data.items():
            if self.old_data.get(file, None) is None:
                entry_diff.append(file)
                continue
            if len(entries) != len(self.old_data[file]) or set(entries.keys() != set(self.old_data[file].keys())) > 0:
                entry_diff.append(file)

            file_trans_diff: List[JsonEntry] = []

            for key, entry in entries.items():
                old_entry = self.old_data[file].get(key, None)
                if old_entry is None:
                    if entry["translation"] != "":
                        # print(key, self.old_data[file][key])
                        file_trans_diff.append(entry)
                        entry["stage"] = 1
                    continue
                if entry["translation"] != old_entry["translation"]:
                    file_trans_diff.append(entry)
                    entry["stage"] = 1



            if len(file_trans_diff) > 0:
                trans_diff[file] = file_trans_diff

        logger.info(f"共有{len(entry_diff)}个文件原词条发生变动！")
        logger.info(f"共有{len(trans_diff)}个文件翻译发生变动！")

        for path in entry_diff:
            out_path = Path(ENTRY_DIFF_DIR[self.target], path)
            os.makedirs(out_path.parent, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(list(self.new_data[path].values()), f, indent=2, ensure_ascii=False)

        for path, entries in trans_diff.items():
            out_path = Path(TRANS_DIFF_DIR[self.target], path)
            os.makedirs(out_path.parent, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)

    def check_same(self):
        same_checker: Dict[str, str] = {}  # Dict[original_text, first_key]

        for key, value in self.translated.items():
            if same_checker.get(value["original"], None) is None:
                same_checker[value["original"]] = key

        fill_count = 0

        for key, value in self.untranslated.items():
            translated_key = same_checker.get(value["original"])
            if translated_key is not None:
                value["translation"] = self.translated[translated_key]["translation"]
                fill_count += 1

        logger.info(f"共有{fill_count}个词条会被填充！")
