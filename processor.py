import json
import os
import shutil

from pathlib import Path
from typing import Dict, Union, List, Tuple

from logger import logger
from data import XmlEntry, CodeEntry
from const import ENTRY_DIFF_DIR, TRANS_DIFF_DIR

JsonEntry = Dict


class Processor:
    def __init__(
        self, target: str, dict_path: Path, old_dict_path: Path, pt_token: str
    ):
        self.target = target
        self.dict_path = dict_path
        self.old_dict_path = old_dict_path
        self.pt_token = pt_token
        self.upgrade_files = set()
        self.translated: Dict[str, JsonEntry] = {}
        self.untranslated: Dict[str, JsonEntry] = {}
        self.new_data: Dict[Path, Dict[str, JsonEntry]] = {}
        self.old_data: Dict[Path, Dict[str, JsonEntry]] = {}

    def load(self):
        for file in self.dict_path.glob("**/*.json"):
            if "过时词条" in file.as_posix():
                continue

            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for index, entry in enumerate(data):
                if entry["stage"] != 0:
                    self.translated[file.as_posix() + ":" + str(index)] = entry
                else:
                    self.untranslated[file.as_posix() + ":" + str(index)] = entry
                rel_file = file.relative_to(self.dict_path)
                if self.new_data.get(rel_file, None) is None:
                    self.new_data[rel_file] = {entry["key"]: entry}
                else:
                    self.new_data[rel_file][entry["key"]] = entry

        for file in self.old_dict_path.glob("**/*.json"):
            if file.parent == self.old_dict_path:
                continue

            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for index, entry in enumerate(data):
                rel_file = file.relative_to(self.old_dict_path)
                if self.old_data.get(rel_file, None) is None:
                    self.old_data[rel_file] = {entry["key"]: entry}
                else:
                    self.old_data[rel_file][entry["key"]] = entry

    def process(self):
        self.load()
        self.check_same()
        self.filter_changed()

    def filter_changed(self):
        shutil.rmtree(ENTRY_DIFF_DIR[self.target], ignore_errors=True)
        shutil.rmtree(TRANS_DIFF_DIR[self.target], ignore_errors=True)

        entry_diff: List[Path] = []
        trans_diff: Dict[Path, List[JsonEntry]] = {}

        for file, entries in self.new_data.items():
            if self.old_data.get(file, None) is None:
                entry_diff.append(file)
                continue
            if len(entries) != len(self.old_data[file]):
                entry_diff.append(file)

            file_trans_diff: List[JsonEntry] = []

            for key, entry in entries.items():
                old_entry = self.old_data[file].get(key, None)
                if old_entry is None:
                    if entry["translation"] != "":
                        print(key, self.old_data[file])
                        file_trans_diff.append(entry)
                    continue
                if entry["translation"] != old_entry["translation"]:
                    file_trans_diff.append(entry)

            if len(file_trans_diff) > 0:
                trans_diff[file] = file_trans_diff

        logger.info(f"共有{len(entry_diff)}个文件原词条发生变动！")
        logger.info(f"共有{len(trans_diff)}个文件翻译发生变动！")

        for path in entry_diff:
            out_path = Path(ENTRY_DIFF_DIR[self.target], path)
            os.makedirs(out_path.parent, exist_ok=True)
            shutil.copy(path, out_path)

        for path, entries in trans_diff.items():
            out_path = Path(TRANS_DIFF_DIR[self.target], path)
            os.makedirs(out_path.parent, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)

    def check_same(self):
        same_checker: Dict[str, str] = {}  # Dict[original_text, first_key]
        res_dict: Dict[
            str, List[Tuple[int, str]]
        ] = {}  # Dict[file_path, List[Tuple[entry_index, trans_key]]]

        for key, value in self.translated.items():
            if same_checker.get(value["original"], None) is None:
                same_checker[value["original"]] = key

        for key, value in self.untranslated.items():
            if same_checker.get(value["original"], None):
                path, entry_index = key.split(":")
                if res_dict.get(path, None) is None:
                    res_dict[path] = [
                        (int(entry_index), same_checker[value["original"]])
                    ]
                else:
                    res_dict[path].append(
                        (int(entry_index), same_checker[value["original"]])
                    )

        logger.info(f"共有{sum([len(v) for v in res_dict.values()])}个词条会被填充！")
        self.upgrade_files = self.upgrade_files.union(res_dict.keys())

        for path, modify_list in res_dict.items():
            with open(path, "r", encoding="utf-8") as f:
                data: List[Dict] = json.load(f)
            memory_data = self.new_data[Path(path).relative_to(self.dict_path)]
            for index, trans_key in modify_list:
                translation = self.translated[trans_key]["translation"]
                data[index]["translation"] = translation
                data[index]["stage"] = 2
                key = data[index]["key"]
                memory_data[key]["translation"] = translation
                memory_data[key]["stage"] = 2
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    # def update_pt_dict(self):
    # 	post_url = PARATRANZ_API_BASE_URL + "/projects/" + PARATRANZ_PROJECT_ID + "/files/" +
