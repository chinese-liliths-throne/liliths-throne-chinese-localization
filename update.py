from pathlib import Path
from typing import List, Dict
import json
import shutil
import asyncio
import re

from const import OUTDATE_DIR_NAME
from logger import logger


def update_dict(
    old_dict_path: Path, new_dict_path: Path, ignore_untranslated: bool = False
):
    loop = asyncio.get_event_loop()

    new_outdated_dir = Path(new_dict_path) / OUTDATE_DIR_NAME
    old_outdated_dir = Path(old_dict_path) / OUTDATE_DIR_NAME

    # 迁移旧版本过时词条
    if old_outdated_dir.exists():
        shutil.move(old_outdated_dir, new_outdated_dir)

    # 获取所有json文件
    old_dict_files: List[Path] = list(old_dict_path.glob("**/*.json"))

    file_pairs = [
        (
            old_dict_file,
            new_dict_path / old_dict_file.relative_to(old_dict_path),
            new_outdated_dir / old_dict_file.relative_to(old_dict_path),
        )
        for old_dict_file in old_dict_files
    ]

    tasks = [
        update_dict_file(
            old_dict_file, new_dict_file, outdated_file, ignore_untranslated
        )
        for old_dict_file, new_dict_file, outdated_file in file_pairs
    ]

    loop.run_until_complete(asyncio.gather(*tasks))


async def update_dict_file(
    old_dict_file: Path,
    new_dict_file: Path,
    outdated_file: Path,
    ignore_untranslated: bool = False,
):
    with open(old_dict_file, "r", encoding="utf-8") as old_dict:
        old_dict_data: List[Dict] = json.load(old_dict)

    no_file = False
    # 若在新提取中该文件已不存在
    if not new_dict_file.exists():
        logger.info("在新提取中该文件已不存在：%s", old_dict_file)
        outdated_data = old_dict_data
        no_file = True
    else:
        with open(new_dict_file, "r", encoding="utf-8") as new_dict:
            new_dict_data: List[Dict] = json.load(new_dict)

        old_dict_data.sort(key=lambda item: item["key"])
        new_dict_data.sort(key=lambda item: item["key"])

        old_dict_data = await update_data(old_dict_data, new_dict_data)

        if ignore_untranslated:
            # result_dict_data = list(filter(lambda entry: entry["stage"] != 0, new_dict_data))
            result_dict_data = new_dict_data
        else:
            result_dict_data = new_dict_data

        with open(new_dict_file, "w", encoding="utf-8") as new_dict:
            json.dump(result_dict_data, new_dict, indent=4, ensure_ascii=False)

        outdated_data = list(filter(lambda entry: entry is not None, old_dict_data))
        if len(outdated_data) > 0:
            logger.info("在新提取中该文件存在遗失条目：%s", old_dict_file)
            print([entry["key"] for entry in outdated_data])

    # 过时条目融合
    if outdated_file.exists():
        with open(outdated_file, "r", encoding="utf-8") as f:
            prev_outdated_data = json.load(f)
    else:
        prev_outdated_data = []

    await update_data(outdated_data, prev_outdated_data, version="0.4.8.9")

    if len(prev_outdated_data) <= 0:
        if no_file:
            logger.warning(" - 文件不再包含任何条目：%s", outdated_file)
        return

    if not outdated_file.parent.exists():
        outdated_file.parent.mkdir(parents=True)

    with open(outdated_file, "w", encoding="utf-8") as f:
        json.dump(prev_outdated_data, f, ensure_ascii=False, indent=4)


async def update_data(
    old_dict_data: List[Dict[str, str]],
    new_dict_data: List[Dict[str, str]],
    version: str = "",
) -> List[Dict[str, str]]:
    new_dict_map: Dict[str, List[int]] = {}  # [原文文本, new_dict_data列表中对应序号]
    old_dict_map: Dict[str, List[int]] = {}  # [原文文本, old_dict_data列表中对应序号]

    for idx, data in enumerate(new_dict_data):
        original = data["original"]
        if not new_dict_map.get(original):
            new_dict_map[original] = [idx]
        else:
            new_dict_map[original].append(idx)

    for idx, data in enumerate(old_dict_data):
        if data["stage"] == 0:  # 旧字典无汉化
            old_dict_data[idx] = None
            continue
        original = data["original"]
        # 是否为xml文件
        if not data["key"][0].isdigit():
            original = original.replace("\\n", "\n")
        if not old_dict_map.get(original):
            old_dict_map[original] = [idx]
        else:
            old_dict_map[original].append(idx)

    for key, value in old_dict_map.items():
        new_idx_list = new_dict_map.get(key)
        if new_idx_list is None:
            continue
        if version != "":
            for idx, old_idx in enumerate(value):
                # 若旧字典的汉化与原文一致（即无需汉化）则无视
                if (
                    old_dict_data[old_idx]["original"]
                    == old_dict_data[old_idx]["translation"]
                ):
                    continue
                if new_idx_list is None or len(new_idx_list) == 0:
                    new_dict_data.append(old_dict_data[old_idx])
                    new_dict_data[-1]["key"] += f"_{version}"
                    continue
                new_dict_data[new_idx_list[idx]]["translation"] = old_dict_data[
                    old_idx
                ]["translation"]
                new_dict_data[new_idx_list[idx]]["stage"] = old_dict_data[old_idx][
                    "stage"
                ]

                if "." in new_dict_data[new_idx_list[idx]]["key"].split("_")[-1]:
                    new_dict_data[new_idx_list[idx]]["key"] = "_".join(
                        new_dict_data[new_idx_list[idx]]["key"].split("_")[:-1]
                        + [f"_{version}"]
                    )
                else:
                    new_dict_data[new_idx_list[idx]]["key"] += f"_{version}"
        else:
            for idx, old_idx in enumerate(value[: min(len(value), len(new_idx_list))]):
                # 保留汉化内容及当前阶段
                translation = old_dict_data[old_idx]["translation"]

                # 引号使用中文双引号，括号使用半角括号
                zh_character = r"[一-龟]"
                if not (
                    "effects" in old_dict_data[old_idx]["key"]
                    or "preParsingEffects" in old_dict_data[old_idx]["key"]
                ):
                    translation = re.sub(rf"'({zh_character}+?)'", r"“\1”", translation)
                translation = re.sub(r"（", "(", translation)
                translation = re.sub(r"）", ")", translation)
                translation = re.sub("\t *", "\t", translation)
                # 中文与markup代码之间
                translation = re.sub(rf"\] ({zh_character})", r"]\1", translation)
                translation = re.sub(rf"({zh_character}) \[", r"\1[", translation)
                translation = re.sub(r"\] \[", r"][", translation)
                # <>左右
                translation = re.sub(r" <(i|b)", r"<\1", translation)
                translation = re.sub(r"(i|b)> ", r"\1>", translation)

                new_dict_data[new_idx_list[idx]]["translation"] = translation
                new_dict_data[new_idx_list[idx]]["stage"] = old_dict_data[old_idx][
                    "stage"
                ]
                # 移除被迁移的旧词条
                old_dict_data[old_idx] = None
    return old_dict_data
