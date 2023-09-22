from pathlib import Path
from typing import List, Dict
import json
import shutil
import asyncio

from const import *
from logger import logger


def update_dict(old_dict_path: Path, new_dict_path: Path):
    loop = asyncio.get_event_loop()

    new_outdated_dir = Path(new_dict_path) / OUTDATE_DIR_NAME
    old_outdated_dir = Path(old_dict_path) / OUTDATE_DIR_NAME

    # 迁移旧版本过时词条
    if old_outdated_dir.exists():
        shutil.move(old_outdated_dir, new_outdated_dir)

    # 获取所有json文件
    old_dict_files: List[Path] = list(old_dict_path.glob('**/*.json'))

    file_pairs = [
        (
            old_dict_file,
            new_dict_path / old_dict_file.relative_to(old_dict_path),
            new_outdated_dir / old_dict_file.relative_to(old_dict_path)
        )
        for old_dict_file in old_dict_files
    ]

    tasks = [
        update_dict_file(old_dict_file, new_dict_file, outdated_file)
        for old_dict_file, new_dict_file, outdated_file in file_pairs
    ]

    loop.run_until_complete(asyncio.gather(*tasks))

async def update_dict_file(old_dict_file: Path, new_dict_file: Path, outdated_file: Path):
    with open(old_dict_file, 'r') as old_dict:
        old_dict_data: List[Dict] = json.load(old_dict)

    # 若在新提取中该文件已不存在
    if not new_dict_file.exists():
        await update_outdated_file(old_dict_data, outdated_file)
        return

    with open(new_dict_file, 'r') as new_dict:
        new_dict_data: List[Dict] = json.load(new_dict)

    await update_data(old_dict_data, new_dict_data)

    with open(new_dict_file, 'w') as new_dict:
        json.dump(new_dict_data, new_dict, indent=4, ensure_ascii=False)

    old_dict_data = list(filter(lambda entry: entry is not None, old_dict_data))
    await update_outdated_file(old_dict_data, outdated_file)


async def update_outdated_file(entries_remained: List[Dict[str, str]], outdated_file: Path):
    if len(entries_remained) <= 0:
        return

    
    if outdated_file.exists():
        with open(outdated_file, "r", encoding="utf-8") as f:
            outdated_data = json.load(f)
    else:
        outdated_data = []

    await update_data(entries_remained, outdated_data, outdated=True)

    if len(outdated_data) <= 0:
        logger.warning(f" - 文件不再包含任何条目：{outdated_file}")
        return
    
    if not outdated_file.parent.exists():
        outdated_file.parent.mkdir(parents=True)

    with open(outdated_file, "w", encoding="utf-8") as f:
        json.dump(outdated_data, f, ensure_ascii=False, indent=4)


async def update_data(old_dict_data: List[Dict[str, str]], new_dict_data: List[Dict[str, str]], outdated: bool = False):
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
        original = data["original"].replace("\\n", "\n")
        if not old_dict_map.get(original):
            old_dict_map[original] = [idx]
        else:
            old_dict_map[original].append(idx)

    for key, value in old_dict_map.items():
        new_idx_list = new_dict_map.get(key)
        if outdated:
            for idx, old_idx in enumerate(value):
                # 若旧字典的汉化与原文一致（即无需汉化）则无视
                if old_dict_data[old_idx]["original"] == old_dict_data[old_idx]["translation"]:
                    continue
                if new_idx_list is None:
                    new_dict_data.append(old_dict_data[old_idx])
                    continue
                new_dict_data[new_idx_list[idx]
                            ]["translation"] = old_dict_data[old_idx]["translation"]
                new_dict_data[new_idx_list[idx]
                            ]["stage"] = old_dict_data[old_idx]["stage"]
        elif new_idx_list is not None:
            for idx, old_idx in enumerate(
                value[:min(len(value), len(new_idx_list))]
            ):
                # 保留汉化内容及当前阶段
                new_dict_data[new_idx_list[idx]
                            ]["translation"] = old_dict_data[old_idx]["translation"]
                new_dict_data[new_idx_list[idx]
                            ]["stage"] = old_dict_data[old_idx]["stage"]
                # 移除被迁移的旧词条
                old_dict_data[old_idx] = None