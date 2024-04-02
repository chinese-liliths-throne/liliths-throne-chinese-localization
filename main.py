import time
import shutil
import os
import argparse

from pathlib import Path

from extractor import Extractor
from applier import Applier
from processor import Processor
from repo_dump import Repo
from update import Updater
from const import NEW_DICT_DIR, OLD_DICT_DIR, REPO_BRANCH
from logger import logger
from util import dict_update_splited_htmlContent


argparser = argparse.ArgumentParser()
argparser.add_argument(
    "--pt-token",
    type=str,
    default="",
    help="paratranz token used to download dictionary, will be override by environment variale",
)
argparser.add_argument(
    "--no-update-repo",
    action="store_true",
    default=False,
    help="whether to update repo file",
)
argparser.add_argument(
    "--no-download-dict",
    action="store_true",
    default=False,
    help="whether to download latest dictionary file (you must ensure that there is a dictionary zip)",
)
argparser.add_argument(
    "--special-process", action="store_true", help="whether to do special process"
)
argparser.add_argument(
    "--ignore-untranslated",
    action="store_true",
    help="whether to ignore untranslated entries",
)

argparser.add_argument(
    "--target",
    type=str,
    default="main",
    choices=["main", "mod"],
    help="determine which project to localize",
)


def main():
    args = argparser.parse_args()

    target = args.target

    pt_token = (
        args.pt_token
        if os.environ.get("PARATRANZ_TOKEN") is None
        else os.environ.get("PARATRANZ_TOKEN")
    )
    if pt_token == "":
        pt_token = input(
            "请输入Paratranz的Acccess Token，\t或选择设置环境变量“PARATRANZ_TOKEN”/在main.py文件夹中修改--pt-token的default值："
        )

    new_dict_dir = Path(NEW_DICT_DIR[target])
    old_dict_dir = Path(OLD_DICT_DIR[target])

    logger.info("==== 正在移除临时文件 ====")
    shutil.rmtree(new_dict_dir, ignore_errors=True)
    shutil.rmtree(old_dict_dir, ignore_errors=True)

    new_dict_dir.mkdir(parents=True, exist_ok=True)
    # old_dict_dir.mkdir(parents=True, exist_ok=True) # will be created by unzip_latest_dict

    repo = Repo(target, REPO_BRANCH[target], pt_token)
    root = repo.source_dir

    if not args.no_update_repo:
        logger.info("==== 正在下载最新版本游戏源码 ====")
        repo.fetch_latest_version()
        logger.info("==== 正在解压最新版本游戏源码 ====")
        repo.unzip_latest_version()

    extractor = Extractor(target, root, new_dict_dir, repo.latest_commit)

    logger.info("==== 正在提取翻译条目 ====")
    extractor.extract()

    new_data = extractor.new_data

    if not args.no_download_dict:
        logger.info("==== 正在下载最新字典文件 ====")
        repo.fetch_latest_dict()
    if not old_dict_dir.exists():
        logger.info("==== 正在解压最新字典文件 ====")
        repo.unzip_latest_dict(old_dict_dir)

    updater = Updater(old_dict_dir, new_dict_dir, new_data)

    logger.info("==== 正在合并字典 ====")
    updater.update_dict(new_data, args.ignore_untranslated)

    old_data = updater.old_data

    processor = Processor(
        target, new_dict_dir, old_dict_dir, pt_token, new_data, old_data
    )

    if args.special_process:
        logger.info("==== 正在应用特殊处理 ====")
        processor.process()

    dump(new_data, new_dict_dir)

    applier = Applier(target, root, new_dict_dir, new_data)

    logger.info("==== 正在应用字典 ====")
    applier.apply()


def dump(new_data, new_dict_dir):
    import json

    for path, new_dict in new_data.items():
        (new_dict_dir / path).parent.mkdir(parents=True, exist_ok=True)
        with open(new_dict_dir / path, "w", encoding="utf-8") as f:
            json.dump(list(new_dict.values()), f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    logger.info("===== 总耗时 %ss =====", end - start)
