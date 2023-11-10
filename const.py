PROXY_URL = "https://ghproxy.com/"

REPO_BASE_URL = "https://github.com/Innoxia/liliths-throne-public"
REPO_API_URL = "https://api.github.com/repos/Innoxia/liliths-throne-public"

REPO_BRANCH = "dev"

PARATRANZ_API_BASE_URL = "https://paratranz.cn/api"
PARATRANZ_PROJECT_ID = "8288"
PARATRANZ_API_URL = PARATRANZ_API_BASE_URL + "/projects/" + PARATRANZ_PROJECT_ID

GITHUB_PUBLIC_ACCESS_TOKEN = "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"


DOWNLOAD_DIR = "./downloads"
ROOT_DIR = "./"
SOURCE_DIR = "./liliths-throne-public-"
NEW_DICT_DIR = "./new_dict"
OLD_DICT_DIR = "./old_dict"
FONT_DIR = "./font"
FONT_TARGET_DIR = "./res/fonts"

EXE_PLUGIN_PATH = "./exe-plugin.xml"

OUTDATE_DIR_NAME = "过时词条"
FONT_DIR_NAME = "Source Han"


BLACKLIST_FILE = ["SexActionManager.java"]

BLACKLIST_HTMLCONTENT = [
    {
        "file": "res/txt/dsg/encounters/fields/elis/eisek_mob_hideout.xml",
        "tag": "CONFRONT",
    },
    {"file": "res/txt/encounters/dominion/prostitute.xml", "tag": "ALLEY_PROSTITUTE"},
    {
        "file": "res/txt/places/dominion/lilayasHome/lab.xml",
        "tag": "LILAYA_EXPLAINS_ESSENCES_3",
    },
    {
        "file": "res/txt/places/dominion/slaverAlley/genericDialogue.xml",
        "tag": "PUBLIC_STOCKS_SEAN_TALK",
    },
    {
        "file": "res/txt/places/submission/submissionPlaces.xml",
        "tag": "CLAIRE_INFO_TELEPORTATION",
    },
]

__all__ = [
    "PROXY_URL",
    "REPO_BASE_URL",
    "REPO_API_URL",
    "REPO_BRANCH",
    "PARATRANZ_API_BASE_URL",
    "PARATRANZ_PROJECT_ID",
    "PARATRANZ_API_URL",
    "GITHUB_PUBLIC_ACCESS_TOKEN",
    "DOWNLOAD_DIR",
    "ROOT_DIR",
    "SOURCE_DIR",
    "NEW_DICT_DIR",
    "OLD_DICT_DIR",
    "FONT_DIR",
    "FONT_TARGET_DIR",
    "EXE_PLUGIN_PATH",
    "OUTDATE_DIR_NAME",
    "FONT_DIR_NAME",
    "BLACKLIST_FILE",
    "BLACKLIST_HTMLCONTENT",
]
