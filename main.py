import asyncio
import time
import shutil
import os

from extractor import Extractor
from applier import Applier
from repo_dump import Repo

from const import *
from update import *
from logger import logger


PARATRANZ_ACCESS_TOKEN = ""

def main():
    new_dict_dir = Path(NEW_DICT_DIR)
    old_dict_dir = Path(OLD_DICT_DIR)

    logger.info("==== 正在移除临时文件 ====")
    shutil.rmtree(new_dict_dir, ignore_errors=True)
    shutil.rmtree(old_dict_dir, ignore_errors=True)

    repo = Repo("dev", PARATRANZ_ACCESS_TOKEN)
    logger.info("==== 正在下载最新版本游戏源码 ====")
    # repo.fetch_latest_version()
    logger.info("==== 正在解压最新版本游戏源码 ====")
    # repo.unzip_latest_version()

    root = repo.source_dir
    
    extractor = Extractor(root, new_dict_dir)
    applier = Applier(root, new_dict_dir)

    logger.info("==== 正在提取翻译条目 ====")
    extractor.extract()

    logger.info("==== 正在下载最新字典文件 ====")
    # repo.fetch_latest_dict()
    logger.info("==== 正在解压最新字典文件 ====")
    repo.unzip_latest_dict()

    logger.info("==== 正在合并字典 ====")
    update_dict(old_dict_dir, new_dict_dir)

    logger.info("==== 正在应用字典 ====")
    # applier.apply()


if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    logger.info(f"===== 总耗时 {end - start}s =====")
