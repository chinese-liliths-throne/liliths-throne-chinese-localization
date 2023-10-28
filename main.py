import time
import shutil
import os
import argparse

from extractor import Extractor
from applier import Applier
from processor import Processor
from repo_dump import Repo

from const import *
from update import *
from logger import logger


argparser = argparse.ArgumentParser()
argparser.add_argument("--branch", type=str, default="dev",
                       help="the specific branch name of the repo")
argparser.add_argument("--pt_token", type=str, default="",
                       help="paratranz token used to download dictionary, will be override by environment variale")
argparser.add_argument("--udpate_repo", type=bool,
                       default=True, help="whether to update repo file")
argparser.add_argument("--udpate_dict", type=bool,
                       default=True, help="whether to update dictionary file")
argparser.add_argument("--special_process", action='store_true',
                       help="whether to do special process")

def main():
    args = argparser.parse_args()

    branch = args.branch
    pt_token = args.pt_token if os.environ.get(
        'PARATRANZ_TOKEN') is None else os.environ.get('PARATRANZ_TOKEN')

    new_dict_dir = Path(NEW_DICT_DIR)
    old_dict_dir = Path(OLD_DICT_DIR)

    logger.info("==== 正在移除临时文件 ====")
    shutil.rmtree(new_dict_dir, ignore_errors=True)
    shutil.rmtree(old_dict_dir, ignore_errors=True)

    repo = Repo(branch, pt_token)
    if args.udpate_repo:
        logger.info("==== 正在下载最新版本游戏源码 ====")
        repo.fetch_latest_version()
    logger.info("==== 正在解压最新版本游戏源码 ====")
    repo.unzip_latest_version()

    root = repo.source_dir

    extractor = Extractor(root, new_dict_dir, repo.latest_commit)
    applier = Applier(root, new_dict_dir)
    processor = Processor(new_dict_dir)

    logger.info("==== 正在提取翻译条目 ====")
    extractor.extract()

    if args.udpate_dict:
        logger.info("==== 正在下载最新字典文件 ====")
        repo.fetch_latest_dict()
    logger.info("==== 正在解压最新字典文件 ====")
    repo.unzip_latest_dict()

    logger.info("==== 正在合并字典 ====")
    update_dict(old_dict_dir, new_dict_dir)
    
    if args.special_process:
        logger.info("==== 正在应用特殊处理 ====")
        processor.process()

    logger.info("==== 正在应用字典 ====")
    applier.apply()


if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    logger.info(f"===== 总耗时 {end - start}s =====")
