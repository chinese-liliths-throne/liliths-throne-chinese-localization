from pathlib import Path
from typing import List, Dict, Optional
import json
import shutil
import asyncio
import re
import copy

from data import WholeDictionary, SingleDictionary
from const import OUTDATE_DIR_NAME, PREVIOUS_GAME_VERSION
from logger import logger


class Updater:
    def __init__(
        self, old_dict_path: Path, new_dict_path: Path, new_data: WholeDictionary
    ) -> None:
        self.old_dict_path: Path = old_dict_path
        self.new_dict_path: Path = new_dict_path
        self.new_data: WholeDictionary = new_data
        self.old_data: WholeDictionary = {}
        self.file_with_missing_entry: List[Path] = []

    def update_dict(
        self,
        new_data: WholeDictionary,
        ignore_untranslated: bool = False,
    ):
        loop = asyncio.get_event_loop()

        new_outdated_dir = self.new_dict_path / OUTDATE_DIR_NAME
        old_outdated_dir = self.old_dict_path / OUTDATE_DIR_NAME

        # 迁移旧版本过时词条
        if old_outdated_dir.exists():
            shutil.move(old_outdated_dir, new_outdated_dir)

        # 获取所有json文件
        old_dict_files: List[Path] = list(self.old_dict_path.glob("**/*.json"))

        file_pairs = [
            (
                old_dict_file,
                new_data.get(
                    old_dict_file.relative_to(self.old_dict_path).as_posix(), None
                ),
                new_outdated_dir / old_dict_file.relative_to(self.old_dict_path),
            )
            for old_dict_file in old_dict_files
        ]

        tasks = [
            self.update_dict_file(
                old_dict_file, new_data, outdated_file, ignore_untranslated
            )
            for old_dict_file, new_data, outdated_file in file_pairs
        ]

        loop.run_until_complete(asyncio.gather(*tasks))

    async def update_dict_file(
        self,
        old_dict_file: Path,
        new_dict_data: Optional[SingleDictionary],
        outdated_file: Path,
        ignore_untranslated: bool = False,
    ):
        with open(old_dict_file, "r", encoding="utf-8") as old_dict:
            old_dict_data: List[Dict] = json.load(old_dict)
            
        path_key = old_dict_file.relative_to(self.old_dict_path).as_posix()

        hashed_old_dict_data: SingleDictionary = {}
        for old_dict_item in old_dict_data:
            hashed_old_dict_data[old_dict_item["key"]] = old_dict_item

        self.old_data[
            old_dict_file.relative_to(self.old_dict_path).as_posix()
        ] = hashed_old_dict_data

        no_file = False
        # 若在新提取中该文件已不存在
        if new_dict_data is None:
            logger.info("在新提取中该文件已不存在：%s", old_dict_file)
            outdated_data = hashed_old_dict_data
            no_file = True
        else:
            outdated_data, self.new_data[path_key] = await self.update_data(
                copy.deepcopy(hashed_old_dict_data), new_dict_data
            )

            if ignore_untranslated:
                # result_dict_data = list(filter(lambda entry: entry["stage"] != 0, new_dict_data))
                result_dict_data = new_dict_data
            else:
                result_dict_data = new_dict_data

            if len(outdated_data) > 0:
                logger.info("在新提取中该文件存在遗失条目：%s", old_dict_file)
                self.file_with_missing_entry.append(old_dict_file.relative_to(self.old_dict_path).as_posix())
                print([key for key, data in outdated_data.items()])

        # 过时条目融合
        if outdated_file.exists():
            with open(outdated_file, "r", encoding="utf-8") as f:
                prev_outdated_data_raw = json.load(f)
            hashed_prev_outdated_data: SingleDictionary = {}
            for prev_outdated_item in prev_outdated_data_raw:
                hashed_prev_outdated_data[
                    prev_outdated_item["key"]
                ] = prev_outdated_item
            prev_outdated_data = hashed_prev_outdated_data
        else:
            prev_outdated_data = {}

        if len(outdated_data) > 0:
            _, prev_outdated_data = await self.update_data(outdated_data, prev_outdated_data, version=PREVIOUS_GAME_VERSION)
        
        if len(prev_outdated_data) <= 0:
            if no_file:
                logger.warning(" - 文件不再包含任何条目：%s", outdated_file)
            return

        if not outdated_file.parent.exists():
            outdated_file.parent.mkdir(parents=True)

        with open(outdated_file, "w", encoding="utf-8") as f:
            json.dump(list(prev_outdated_data.values()), f, ensure_ascii=False, indent=4)

    async def update_data(
        self,
        old_dict_data: SingleDictionary,
        new_dict_data: SingleDictionary,
        version: str = "",
    ) -> SingleDictionary:
        new_dict_map: Dict[str, List[str]] = {}  # [原文文本, new_dict_data词典中对应的key]
        old_dict_map: Dict[str, List[str]] = {}  # [原文文本, old_dict_data词典中对应的key]
        
        # sort the new data and old data
        new_dict_data = dict(sorted(new_dict_data.items(), key=lambda x: x[1]["key"]))
        old_dict_data = dict(sorted(old_dict_data.items(), key=lambda x: x[1]["key"]))

        for key, data in new_dict_data.items():
            original = data["original"].strip()
            if not new_dict_map.get(original):
                new_dict_map[original] = [key]
            else:
                new_dict_map[original].append(key)

        for key, data in old_dict_data.items():
            if data["stage"] == 0:
                old_dict_data[key] = None
                continue
            original = data["original"]
            # 是否为xml文件
            if not data["key"][0].isdigit():
                original = original.replace("\\n", "\n")
            original = original.strip()
            if not old_dict_map.get(original):
                old_dict_map[original] = [key]
            else:
                old_dict_map[original].append(key)
        
        # check = False
        # if "00555" in old_dict_data:
        #     check = True

        for ori, keys in old_dict_map.items():
            new_idx_list = new_dict_map.get(ori)
            # if check and "down against [npc2.her] [npc2.lips+]" in key:
            #     with open("test.json", "w") as f:
            #         json.dump(new_dict_map, f, indent=2)
            #     for _k, _v in new_dict_map.items():
            #         if "down against [npc2.her] [npc2.lips+]" in _k:
            #             print(_k, _v)
            #     print(key)
            #     print(value, new_idx_list)
            #     input()
            # outdated file merge
            if version != "":
                for idx, old_key in enumerate(keys):
                    # 若旧字典的汉化与原文一致（即无需汉化）则无视
                    if (
                        old_dict_data[old_key]["original"]
                        == old_dict_data[old_key]["translation"]
                    ):
                        continue
                    if new_idx_list is None or len(new_idx_list) == 0 or idx >= len(new_idx_list):
                        new_dict_data[f"{old_key}"] = old_dict_data[old_key]
                        new_dict_data[f"{old_key}"]["key"] = f"{old_key}_{version}"
                        new_dict_data[f"{old_key}"]["stage"] = 9 # locked
                        continue
                    new_dict_data[new_idx_list[idx]]["translation"] = old_dict_data[
                        old_key
                    ]["translation"].strip()
                    new_dict_data[new_idx_list[idx]]["stage"] = 9 # locked

                    if "." in new_dict_data[new_idx_list[idx]]["key"].split("_")[-1]:
                        new_dict_data[new_idx_list[idx]]["key"] = "_".join(
                            new_dict_data[new_idx_list[idx]]["key"].split("_")[:-1]
                            + [f"_{version}"]
                        )
                    else:
                        new_dict_data[new_idx_list[idx]]["key"] += f"_{version}"
            else:
                if new_idx_list is None:
                    continue
                for idx, old_key in enumerate(
                    keys[: min(len(keys), len(new_idx_list))]
                ):
                    # 保留汉化内容及当前阶段
                    translation = old_dict_data[old_key]["translation"]

                    translation = translation_process(
                        translation, old_dict_data[old_key]["key"]
                    )

                    new_dict_data[new_idx_list[idx]]["translation"] = translation
                    new_dict_data[new_idx_list[idx]]["stage"] = old_dict_data[old_key][
                        "stage"
                    ]
                    # 移除被迁移的旧词条
                    old_dict_data[old_key] = None

        to_delete = [key for key, value in old_dict_data.items() if value is None]
        for key in to_delete:
            old_dict_data.pop(key)

        return old_dict_data, new_dict_data


ZH_CHARACTER = r"[一-龟]"


def translation_process(translation: str, key: str) -> str:
    # 引号使用中文双引号，括号使用半角括号
    if not ("effects" in key or "preParsingEffects" in key):
        translation = re.sub(rf"'({ZH_CHARACTER}+?)'", r"“\1”", translation)

    translation = re.sub(r"（", "(", translation)
    translation = re.sub(r"）", ")", translation)
    translation = re.sub("\t *", "\t", translation)
    # 中文与markup代码之间
    translation = re.sub(rf"\] ({ZH_CHARACTER})", r"]\1", translation)
    translation = re.sub(rf"({ZH_CHARACTER}) \[", r"\1[", translation)
    translation = re.sub(r"\] \[", r"][", translation)
    # <>左右
    translation = re.sub(r" <(i|b)", r"<\1", translation)
    translation = re.sub(r"(i|b)> ", r"\1>", translation)

    return translation
