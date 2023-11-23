import json

from pathlib import Path
from typing import Dict, Union, List, Tuple

from logger import logger
from data import XmlEntry, CodeEntry
from const import *


class Processor:
    def __init__(self, dict_path: Path, pt_token: str):
        self.dict_path = dict_path
        self.pt_token = pt_token
        self.upgrade_files = set()
        self.translated: Dict[str, Union[XmlEntry, CodeEntry]] = {}
        self.untranslated: Dict[str, Union[XmlEntry, CodeEntry]] = {}

    def load(self):
        for file in self.dict_path.glob("**/*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for index, entry in enumerate(data):
                if "src" in file.as_posix():
                    e = CodeEntry.from_json(file, entry)
                else:
                    e = XmlEntry.from_json(file, entry)
                if entry["stage"] != 0:
                    self.translated[file.as_posix() + ":" + str(index)] = e
                else:
                    self.untranslated[file.as_posix() + ":" + str(index)] = e

    def process(self):
        self.load()
        self.check_same()

    def check_same(self):
        same_checker: Dict[str, str] = {}  # Dict[original_text, first_key]
        res_dict: Dict[
            str, List[Tuple[int, str]]
        ] = {}  # Dict[file_path, List[Tuple[entry_index, trans_key]]]

        for key, value in self.translated.items():
            if same_checker.get(value.original, None) is None:
                same_checker[value.original] = key

        for key, value in self.untranslated.items():
            if same_checker.get(value.original, None):
                path, entry_index = key.split(":")
                if res_dict.get(path, None) is None:
                    res_dict[path] = [(int(entry_index), same_checker[value.original])]
                else:
                    res_dict[path].append(
                        (int(entry_index), same_checker[value.original])
                    )

        logger.info(f"共有{sum([len(v) for v in res_dict.values()])}个词条会被填充！")
        self.upgrade_files = self.upgrade_files.union(res_dict.keys())

        for path, modify_list in res_dict.items():
            with open(path, "r", encoding="utf-8") as f:
                data: List[Dict] = json.load(f)
            for index, trans_key in modify_list:
                translation = self.translated[trans_key].translation
                data[index]["translation"] = translation
                data[index]["stage"] = 2
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    # def update_pt_dict(self):
    # 	post_url = PARATRANZ_API_BASE_URL + "/projects/" + PARATRANZ_PROJECT_ID + "/files/" +
