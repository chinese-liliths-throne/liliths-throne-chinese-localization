import re
from typing import List, Optional, Dict
from pathlib import Path
import json
import asyncio

from lxml import etree

from data import XmlEntry, CodeEntry, FilePair, WholeDictionary, SingleDictionary
from const import BLACKLIST_FILE, BLACKLIST_HTMLCONTENT
from util import split_htmlContent, get_element_CDATA


def try_xml_entry_attrib(
    file: str, element: etree._Element, attr: str
) -> Optional[XmlEntry]:
    if element.attrib.get(attr):
        return XmlEntry(
            file=file,
            original=element.attrib.get(attr),
            translation="",
            node_tag=element.tag,
            attribute=attr,
            stage=0,
            node_idx=0,
        )
    else:
        return None


def try_xml_entry_text(file: str, element: etree._Element) -> Optional[XmlEntry]:
    text = get_element_CDATA(element)

    if text is None:
        return None

    return XmlEntry(
        file=file,
        original=text,
        translation="",
        node_tag=element.tag,
        attribute=None,
        stage=0,
        node_idx=0,
    )


def get_splited_htmlContent(file: Path, element: etree._Element) -> List[XmlEntry]:
    if element.text is None:
        return []

    if element.text.strip() == "":
        return []

    attr = element.get("tag")
    if attr is None:
        raise ValueError("htmlContent tag is None")
    if attr in [x["tag"] for x in BLACKLIST_HTMLCONTENT if file.name in x["file"]]:
        return [
            XmlEntry(
                file=file.as_posix(),
                original=element.text,
                translation="",
                node_tag=element.tag,
                attribute=attr.replace("_", "-"),
                stage=0,
                node_idx=0,
            )
        ]

    extracted_blocks = split_htmlContent(element.text)

    return [
        XmlEntry(
            file=file.as_posix(),
            original=block,
            translation="",
            node_tag=element.tag,
            attribute=attr.replace("_", "-"),
            stage=0,
            node_idx=0,
        )
        for idx, block in enumerate(extracted_blocks)
    ]


class Extractor:
    def __init__(self, target: str, root: str, new_dict_path: str, commit_sha: str):
        self.target = target
        self.root = Path(root)
        self.target_dir = Path(new_dict_path)
        self.new_data: WholeDictionary = {}

        if not self.root.is_dir():
            raise NotADirectoryError("Invalid root directory")
        if not self.target_dir.is_dir():
            self.target_dir.mkdir()

    def extract(self):
        self.extract_res()
        if self.target == "main":
            self.extract_src()

    def extract_res(self):
        loop = asyncio.get_event_loop()

        if self.target == "main":
            res_path = self.root.joinpath("res")
        elif self.target == "mod":
            res_path = self.root

        file_pairs: List[FilePair] = []

        # 递归获取所有后缀为xml的文件
        for file in res_path.glob("**/*.xml"):
            result_path = self.target_dir.joinpath(
                file.relative_to(self.root)
            ).with_suffix(".json")
            file_pairs.append(FilePair(file, result_path))
            # if not result_path.parent.exists():
            #     result_path.parent.mkdir(parents=True)

        tasks = [
            self.extract_xml_gather(file.original_file, file.entry_file)
            for file in file_pairs
        ]

        loop.run_until_complete(asyncio.gather(*tasks))

    async def extract_xml_gather(self, xml_path, entry_path):
        entry_dict = await self.extract_xml(xml_path)
        if len(entry_dict) <= 0:
            return

        self.new_data[entry_path.relative_to(self.target_dir).as_posix()] = entry_dict

        # with open(entry_path, "w", encoding="utf-8") as f:
        #     json.dump(entry_list, f, ensure_ascii=False, indent=4)

    async def extract_xml(self, xml_path: Path) -> List[Dict[str, XmlEntry]]:
        entry_dict: SingleDictionary = {}
        entry_cluster: Dict[str, Dict[str, int]] = {}

        def insert_entry(entry: Optional[XmlEntry]):
            if entry is None:
                return
            tag = entry.node_tag
            attrib = entry.attribute if entry.attribute is not None else "text"

            entry_json = entry.to_json()
            if entry_cluster.get(tag) is None:
                entry_cluster[tag] = {attrib: 0}
            elif entry_cluster[tag].get(attrib) is None:
                entry_cluster[tag][attrib] = 0
            else:
                entry_cluster[tag][attrib] += 1

            entry_json["key"] += "_" + str(entry_cluster[tag][attrib])
            entry_dict[entry_json["key"]] = entry_json

        file = xml_path.as_posix()

        parser = etree.XMLParser(strip_cdata=False)

        root = etree.parse(file, parser)

        # exportedCharacter
        for name in root.iter("name"):
            # e = try_xml_entry_attrib(file, name, "nameAndrogynous")
            # insert_entry(e)
            # e = try_xml_entry_attrib(file, name, "nameFeminine")
            # insert_entry(e)
            # e = try_xml_entry_attrib(file, name, "nameMasculine")
            # insert_entry(e)
            parent = name.getparent()
            if parent is not None and parent.tag == "formattingNames":
                continue
            e = try_xml_entry_text(file, name)
            insert_entry(e)

        for namePlural in root.iter("namePlural"):
            e = try_xml_entry_text(file, namePlural)
            insert_entry(e)

        # for surname in root.iter("surname"):
        #     e = try_xml_entry_attrib(file, surname, "value")
        #     insert_entry(e)

        # for genericName in root.iter("genericName"):
        #     e = try_xml_entry_attrib(file, genericName, "value")
        #     insert_entry(e)

        for description in root.iter("description"):
            # e = try_xml_entry_attrib(file, description, "value")
            # insert_entry(e)
            e = try_xml_entry_text(file, description)
            insert_entry(e)

        # for clothing in root.iter("clothing"):
        #     e = try_xml_entry_attrib(file, clothing, "name")
        #     insert_entry(e)
        # for weapon in root.iter("weapon"):
        #     e = try_xml_entry_attrib(file, weapon, "name")
        #     insert_entry(e)

        # clothing
        for determiner in root.iter("determiner"):
            e = try_xml_entry_text(file, determiner)
            insert_entry(e)

        for _self in root.iter("self"):
            e = try_xml_entry_text(file, _self)
            insert_entry(e)
        for other in root.iter("other"):
            e = try_xml_entry_text(file, other)
            insert_entry(e)
        for otherRough in root.iter("otherRough"):
            e = try_xml_entry_text(file, otherRough)
            insert_entry(e)

        for clothingAuthorTag in root.iter("clothingAuthorTag"):
            e = try_xml_entry_text(file, clothingAuthorTag)
            insert_entry(e)
        for authorTag in root.iter("authorTag"):
            e = try_xml_entry_text(file, authorTag)
            insert_entry(e)

        ## sticker related
        for stickerName in root.iter("stickerName"):
            e = try_xml_entry_text(file, stickerName)
            insert_entry(e)
        for namePrefix in root.iter("namePrefix"):
            e = try_xml_entry_text(file, namePrefix)
            insert_entry(e)
        for namePostfix in root.iter("namePostfix"):
            e = try_xml_entry_text(file, namePostfix)
            insert_entry(e)
        for descriptionModification in root.iter("descriptionModification"):
            e = try_xml_entry_text(file, descriptionModification)
            insert_entry(e)

        # combat move nodes
        for availabilityDescription in root.iter("availabilityDescription"):
            e = try_xml_entry_text(file, availabilityDescription)
            insert_entry(e)

        for criticalDescription in root.iter("criticalDescription"):
            e = try_xml_entry_text(file, criticalDescription)
            insert_entry(e)

        for movePredictionDescriptionWithTarget in root.iter(
            "movePredictionDescriptionWithTarget"
        ):
            e = try_xml_entry_text(file, movePredictionDescriptionWithTarget)
            insert_entry(e)

        for movePredictionDescriptionNoTarget in root.iter(
            "movePredictionDescriptionNoTarget"
        ):
            e = try_xml_entry_text(file, movePredictionDescriptionNoTarget)
            insert_entry(e)

        for execute in root.iter("execute"):
            e = try_xml_entry_text(file, execute)
            insert_entry(e)

        for critDescription in root.iter("critDescription"):
            e = try_xml_entry_text(file, critDescription)
            insert_entry(e)

        for critEffectDescription in root.iter("critEffectDescription"):
            e = try_xml_entry_text(file, critEffectDescription)
            insert_entry(e)

        # dialogueNodes
        for title in root.iter("title"):
            e = try_xml_entry_text(file, title)
            insert_entry(e)

        for responseTitle in root.iter("responseTitle"):
            e = try_xml_entry_text(file, responseTitle)
            insert_entry(e)

        for responseTooltip in root.iter("responseTooltip"):
            e = try_xml_entry_text(file, responseTooltip)
            insert_entry(e)

        for effects in root.iter("effects"):
            parent = effects.getparent()
            if parent is not None and parent.tag == "response":
                e = try_xml_entry_text(file, effects)
                insert_entry(e)

        for preParsingEffects in root.iter("preParsingEffects"):
            e = try_xml_entry_text(file, preParsingEffects)
            insert_entry(e)

        for combatant in root.iter("combatant"):
            e = try_xml_entry_text(file, combatant)
            insert_entry(e)

        # encounter
        # name

        # item
        # determiner
        # name
        # namePlural
        # description

        for useDescriptor in root.iter("useDescriptor"):
            e = try_xml_entry_text(file, useDescriptor)
            insert_entry(e)

        for potionDescriptor in root.iter("potionDescriptor"):
            e = try_xml_entry_text(file, potionDescriptor)
            insert_entry(e)

        # effectTooltipLines
        for line in root.iter("line"):
            e = try_xml_entry_text(file, line)
            insert_entry(e)

        for applyEffects in root.iter("applyEffects"):
            e = try_xml_entry_text(file, applyEffects)
            insert_entry(e)

        # useDescriptor
        for selfUse in root.iter("selfUse"):
            e = try_xml_entry_text(file, selfUse)
            insert_entry(e)
        for otherUse in root.iter("otherUse"):
            e = try_xml_entry_text(file, otherUse)
            insert_entry(e)

        # placeType
        # name
        for tooltipDescription in root.iter("tooltipDescription"):
            e = try_xml_entry_text(file, tooltipDescription)
            insert_entry(e)
        for virginityLossDescription in root.iter("virginityLossDescription"):
            e = try_xml_entry_text(file, virginityLossDescription)
            insert_entry(e)

        # worldType
        # name
        for sexBlockedReason in root.iter("sexBlockedReason"):
            e = try_xml_entry_text(file, sexBlockedReason)
            insert_entry(e)

        # outfit
        # name
        # description

        # pattern
        # name

        # race
        # name
        # namePlural
        # nameFeral.name
        # nameFeralPlural.name

        for defaultTransformName in root.iter("defaultTransformName"):
            e = try_xml_entry_text(file, defaultTransformName)
            insert_entry(e)

        # racialBody
        # no

        # subspecies
        # bookName
        for bookName in root.iter("bookName"):
            e = try_xml_entry_text(file, bookName)
            insert_entry(e)
        # name
        # namePlural
        for singularMaleName in root.iter("singularMaleName"):
            e = try_xml_entry_text(file, singularMaleName)
            insert_entry(e)
        for singularFemaleName in root.iter("singularFemaleName"):
            e = try_xml_entry_text(file, singularFemaleName)
            insert_entry(e)
        for pluralMaleName in root.iter("pluralMaleName"):
            e = try_xml_entry_text(file, pluralMaleName)
            insert_entry(e)
        for pluralFemaleName in root.iter("pluralFemaleName"):
            e = try_xml_entry_text(file, pluralFemaleName)
            insert_entry(e)
        for nameSillyMode in root.iter("nameSillyMode"):
            e = try_xml_entry_text(file, nameSillyMode)
            insert_entry(e)
        for namePluralSillyMode in root.iter("namePluralSillyMode"):
            e = try_xml_entry_text(file, namePluralSillyMode)
            insert_entry(e)
        for nameHalfDemon in root.iter("nameHalfDemon"):
            e = try_xml_entry_text(file, nameHalfDemon)
            insert_entry(e)
        for namePluralHalfDemon in root.iter("namePluralHalfDemon"):
            e = try_xml_entry_text(file, namePluralHalfDemon)
            insert_entry(e)
        for singularMaleNameHalfDemon in root.iter("singularMaleNameHalfDemon"):
            e = try_xml_entry_text(file, singularMaleNameHalfDemon)
            insert_entry(e)
        for singularFemaleNameHalfDemon in root.iter("singularFemaleNameHalfDemon"):
            e = try_xml_entry_text(file, singularFemaleNameHalfDemon)
            insert_entry(e)
        for pluralMaleNameHalfDemon in root.iter("pluralMaleNameHalfDemon"):
            e = try_xml_entry_text(file, pluralMaleNameHalfDemon)
            insert_entry(e)
        for pluralFemaleNameHalfDemon in root.iter("pluralFemaleNameHalfDemon"):
            e = try_xml_entry_text(file, pluralFemaleNameHalfDemon)
            insert_entry(e)

        # description
        for feralName in root.iter("feralName"):
            e = try_xml_entry_text(file, feralName)
            insert_entry(e)
        for feralNamePlural in root.iter("feralNamePlural"):
            e = try_xml_entry_text(file, feralNamePlural)
            insert_entry(e)
        for feralSingularMaleName in root.iter("feralSingularMaleName"):
            e = try_xml_entry_text(file, feralSingularMaleName)
            insert_entry(e)
        for feralSingularFemaleName in root.iter("feralSingularFemaleName"):
            e = try_xml_entry_text(file, feralSingularFemaleName)
            insert_entry(e)
        for feralPluralMaleName in root.iter("feralPluralMaleName"):
            e = try_xml_entry_text(file, feralPluralMaleName)
            insert_entry(e)
        for feralPluralFemaleName in root.iter("feralPluralFemaleName"):
            e = try_xml_entry_text(file, feralPluralFemaleName)
            insert_entry(e)

        for statusEffectDescription in root.iter("statusEffectDescription"):
            e = try_xml_entry_text(file, statusEffectDescription)
            insert_entry(e)

        # coveringType
        # determiner
        # name
        # namePlural

        # bookText
        for htmlContent in root.iter("htmlContent"):
            # 将htmlContent拆分成小段
            e_list = get_splited_htmlContent(xml_path, htmlContent)
            for e in e_list:
                insert_entry(e)

            # 保留大段文本
            # e = try_xml_entry_text(file, htmlContent)
            # insert_entry(e)

        # Bodyparts
        # name
        # namePlural
        for transformationName in root.iter("transformationName"):
            e = try_xml_entry_text(file, transformationName)
            insert_entry(e)
        for transformationDescription in root.iter("transformationDescription"):
            e = try_xml_entry_text(file, transformationDescription)
            insert_entry(e)
        for bodyDescription in root.iter("bodyDescription"):
            e = try_xml_entry_text(file, bodyDescription)
            insert_entry(e)
        for crotchBoobsTransformationDescription in root.iter(
            "crotchBoobsTransformationDescription"
        ):
            e = try_xml_entry_text(file, crotchBoobsTransformationDescription)
            insert_entry(e)
        for crotchBoobsBodyDescription in root.iter("crotchBoobsBodyDescription"):
            e = try_xml_entry_text(file, crotchBoobsBodyDescription)
            insert_entry(e)
        # fluid.namesFeminine.name
        # fluid.namesMusculine.name
        # fluid.descriptorsMasculine.name
        # fluid.descriptorsFeminine.name
        # hair.determiner
        for descriptor in root.iter("descriptor"):
            e = try_xml_entry_text(file, descriptor)
            insert_entry(e)

        for handName in root.iter("handName"):
            e = try_xml_entry_text(file, handName)
            insert_entry(e)
        for handNamePlural in root.iter("handNamePlural"):
            e = try_xml_entry_text(file, handNamePlural)
            insert_entry(e)
        for fingerName in root.iter("fingerName"):
            e = try_xml_entry_text(file, fingerName)
            insert_entry(e)
        for fingerNamePlural in root.iter("fingerNamePlural"):
            e = try_xml_entry_text(file, fingerNamePlural)
            insert_entry(e)
        for noseName in root.iter("noseName"):
            e = try_xml_entry_text(file, noseName)
            insert_entry(e)
        for tipName in root.iter("tipName"):
            e = try_xml_entry_text(file, tipName)
            insert_entry(e)
        for tipNamePlural in root.iter("tipNamePlural"):
            e = try_xml_entry_text(file, tipNamePlural)
            insert_entry(e)

        # setBonus
        # name

        # sexAction
        # title
        for tooltip in root.iter("tooltip"):
            e = try_xml_entry_text(file, tooltip)
            insert_entry(e)
        for text in root.iter("text"):
            e = try_xml_entry_text(file, text)
            insert_entry(e)

        # sexManager
        for deskName in root.iter("deskName"):
            e = try_xml_entry_text(file, deskName)
            insert_entry(e)
        for wallName in root.iter("wallName"):
            e = try_xml_entry_text(file, wallName)
            insert_entry(e)
        for startingDescription in root.iter("startingDescription"):
            e = try_xml_entry_text(file, startingDescription)
            insert_entry(e)

        # statusEffect
        # name
        # description
        for effect in root.iter("effect"):
            parent = effect.getparent()
            if parent is not None and parent.tag == "statusEffects":
                continue
            e = try_xml_entry_text(file, effect)
            insert_entry(e)

        # tatto
        # name
        # description
        for bodyOverviewDescription in root.iter("bodyOverviewDescription"):
            e = try_xml_entry_text(file, bodyOverviewDescription)
            insert_entry(e)

        # txt / dialogue
        # htmlContent
        for tab in root.iter("tab"):
            e = try_xml_entry_text(file, tab)
            insert_entry(e)

        # weapon
        # determiner
        # name
        # namePlural
        # description
        for attackDescriptor in root.iter("attackDescriptor"):
            e = try_xml_entry_text(file, attackDescriptor)
            insert_entry(e)
        for attackTooltipDescription in root.iter("attackTooltipDescription"):
            e = try_xml_entry_text(file, attackTooltipDescription)
            insert_entry(e)
        for equipText in root.iter("equipText"):
            e = try_xml_entry_text(file, equipText)
            insert_entry(e)
        for unequipText in root.iter("unequipText"):
            e = try_xml_entry_text(file, unequipText)
            insert_entry(e)
        for hitText in root.iter("hitText"):
            e = try_xml_entry_text(file, hitText)
            insert_entry(e)
        for criticalHitText in root.iter("criticalHitText"):
            e = try_xml_entry_text(file, criticalHitText)
            insert_entry(e)
        for missText in root.iter("missText"):
            e = try_xml_entry_text(file, missText)
            insert_entry(e)
        for onCriticalHitEffect in root.iter("onCriticalHitEffect"):
            e = try_xml_entry_text(file, onCriticalHitEffect)
            insert_entry(e)

        # names
        for fem in root.iter("fem"):
            e = try_xml_entry_text(file, fem)
            insert_entry(e)
        for _and in root.iter("and"):
            e = try_xml_entry_text(file, _and)
            insert_entry(e)
        for mas in root.iter("mas"):
            e = try_xml_entry_text(file, mas)
            insert_entry(e)

        return entry_dict

    def extract_src(self):
        loop = asyncio.get_event_loop()

        src_path = self.root.joinpath("src")

        file_pairs: List[FilePair] = []

        # 递归获取所有后缀为xml的文件
        for file in src_path.glob("**/*.java"):
            result_path = self.target_dir.joinpath(
                file.relative_to(self.root)
            ).with_suffix(".json")
            file_pairs.append(FilePair(file, result_path))
            # if not result_path.parent.exists():
            #     result_path.parent.mkdir(parents=True)

        tasks = [
            self.extract_java_gather(file.original_file, file.entry_file)
            for file in file_pairs
        ]

        loop.run_until_complete(asyncio.gather(*tasks))

    async def extract_java_gather(self, java_path: Path, entry_path: Path):
        entry_dict = await self.extract_java(java_path)
        if len(entry_dict) <= 0:
            return
        self.new_data[entry_path.relative_to(self.target_dir).as_posix()] = entry_dict
        # with open(entry_path, "w", encoding="utf-8") as f:
        #     json.dump(entry_list, f, ensure_ascii=False, indent=4)

    async def extract_java(self, file: Path):
        if file.name in BLACKLIST_FILE:
            return []
        java_extractor = JavaExtractor()
        entry_dict: SingleDictionary = {}

        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for idx, line in enumerate(lines):
            line = line.strip()
            original_line = line

            line = java_extractor.process_comment(line)
            line = line.strip()

            if len(line) == 0:
                continue

            # controller\eventListeners\tooltips
            if file.parent.name == "tooltips":
                java_extractor.parse_tooltips(line)
            # game\character\attributes
            elif file.parent.name == "attributes":
                java_extractor.parse_attributes(line)
            # game\character\body
            elif file.parent.name == "body" or file.parent.parent.name == "body":
                java_extractor.parse_body(line)
            # game\character\effects
            elif file.parent.name == "effects":
                java_extractor.parse_effects(file.name, line)
            # game\character\fetishes
            elif file.parent.name == "fetishes":
                java_extractor.parse_fetishs(line)
            # game\character\npc
            elif "npc" in file.parent.as_posix():
                java_extractor.parse_npc(file.name, line)
            # game\character\race
            elif file.parent.name == "race":
                java_extractor.parse_race(line)
            # game\combat\moves
            elif file.parent.name == "moves":
                java_extractor.parse_moves(line)
            # game\iventory\clothing
            elif file.parent.name == "clothing":
                java_extractor.parse_clothing(line)
            # game\iventory\enchanting
            elif file.parent.name == "enchanting":
                java_extractor.parse_enchanting(line)
            # game\iventory\item
            elif file.parent.name == "item":
                java_extractor.parse_item(line)
            # main
            elif file.parent.name == "main":
                java_extractor.parse_main(line)
            # rendering
            elif file.parent.name == "rendering":
                java_extractor.parse_rendering(line)
            # utils\colours
            elif file.parent.name == "colours":
                java_extractor.parse_colours(line)
            # world\population
            elif file.parent.name == "population":
                java_extractor.parse_population(line)
            # world no sub
            elif file.parent.name == "world":
                java_extractor.parse_world(line)
            # rest in controller\
            elif "controller" in file.parent.as_posix():
                java_extractor.parse_controller(line)
            # game\sex\positions
            elif "positions" in file.parent.as_posix():
                java_extractor.parse_positions(line)
            # rest in game\sex\
            elif "sex" in file.parent.as_posix():
                java_extractor.parse_sex(file.name, line)
            # rest in game\character\
            elif "character" in file.parent.as_posix():
                java_extractor.parse_character(file.name, line)
            # rest in game\dialogue\
            elif "dialogue" in file.parent.as_posix():
                java_extractor.parse_dialogue(file.name, line)
            # rest in game\
            elif "game" in file.parent.as_posix():
                java_extractor.parse_game(file.name, line)
            # rest in world\places
            elif "places" in file.parent.as_posix():
                java_extractor.parse_places(file.name, line)

            java_extractor.parse_normal(line)

            if java_extractor.general_string_parse(line):
                entry = CodeEntry(
                    file=file.as_posix(),
                    original=original_line,
                    translation="",
                    line=idx,
                    stage=0,
                )
                entry_json = entry.to_json()
                entry_dict[entry_json["key"]] = entry_json

        return entry_dict


SB_REGEX = r"([sS][bB]|StringBuilder)(\(\))?"
ADJ_REGEX = r"[a|A]djectives?"
TEXT_REGEX = r"[t|T]exts?"
NAME_REGEX = r"[n|N]ames?"
TITLE_REGEX = r"[t|T]itles?"
DESC_REGEX = r"[d|D]esc(ription|riptor)?s?"
DETER_REGEX = r"[d|D]eterminers?"
STRING_REGEX = r"[s|S]trings?"
PREFIX_REGEX = r"[p|P]refixe?s?"
SUFFIX_REGEX = r"[s|S]uffixe?s?"
EFFECT_REGEX = r"[e|E]ff(ect)?s?"
MOD_REGEX = r"[m|M]od(ifier)?s?"

ASSIGN_REGEX = r"\s*\+?=\s*"
ADD_REGEX = r"(List)?.add"


class JavaExtractor:
    def __init__(self):
        self.interest_line: bool = False
        self.comment: bool = False

    def parse_normal(self, line: str):
        if self.interest_line:
            return

        if "return" in line:
            self.interest_line = True
        elif (
            re.search(
                rf"({SB_REGEX}|{DESC_REGEX}|{TEXT_REGEX}|{STRING_REGEX}|[o|O]utput)\.append",
                line,
            )
            is not None
        ):
            self.interest_line = True
        elif "new Response" in line:
            self.interest_line = True
        elif ".setInformation" in line:
            self.interest_line = True
        elif (
            re.search(
                rf"({SB_REGEX}|{ADJ_REGEX}|{TEXT_REGEX}|{NAME_REGEX}|{TITLE_REGEX}|{DESC_REGEX}|returnValue|{PREFIX_REGEX}|{SUFFIX_REGEX}|{STRING_REGEX}|{DETER_REGEX}|[o|O]utput){ASSIGN_REGEX}",
                line,
            )
            is not None
        ):
            self.interest_line = True
        elif (
            re.search(
                rf"({ADJ_REGEX}|{TEXT_REGEX}|{NAME_REGEX}(Plural)?|{TITLE_REGEX}|{DESC_REGEX}|{EFFECT_REGEX}|{MOD_REGEX}){ADD_REGEX}",
                line,
            )
            is not None
        ):
            self.interest_line = True
        elif "list.add" in line or "list2.add" in line:
            self.interest_line = True
        elif "Names.contains" in line:
            self.interest_line = True
        # elif "System.err.println" in line:
        #     self.interest_line = True
        elif "new Value<>" in line:
            self.interest_line = True
        elif "public enum" in line:  # 枚举项
            self.interest_line = True
        elif re.search(r"^\s*[A-Z_0-9]+\(", line) is not None:  # 枚举项
            self.interest_line = True
        elif "new String[]" in line or "static String[]" in line:
            self.interest_line = True
        elif "super(" in line or "this(" in line:
            self.interest_line = True
        elif "new TattooWriting" in line:
            self.interest_line = True
        elif "setName" in line or "setSurname" in line or "setGenericName" in line:
            self.interest_line = True
        elif "setDescription" in line:
            self.interest_line = True
        elif "new NameTriplet" in line:
            self.interest_line = True
        elif (
            "UtilText.parse" in line
            or "Util.capitaliseSentence" in line
            or "UtilText.returnStringAtRandom" in line
            or "Util.randomItemFromValues" in line
        ):
            self.interest_line = True
        elif "new EventLogEntry" in line:
            self.interest_line = True
        elif "new DialogueNode" in line:
            self.interest_line = True
        elif ".flashMessage" in line:
            self.interest_line = True
        elif ".addSpecialParsingString" in line:
            self.interest_line = True
        elif "spawnDomGloryHoleNPC" in line or "spawnSubGloryHoleNPC" in line:
            self.interest_line = True
        elif "getTooltipText" in line:
            self.interest_line = True
        elif "appendToTextEndStringBuilder" in line:
            self.interest_line = True
        elif line.strip().startswith('"'):
            self.interest_line = True

    def parse_tooltips(self, line: str):
        if "tooltipSB.append" in line:
            self.interest_line = True

        elif ".setTooltipContent" in line:
            self.interest_line = True

    def parse_controller(self, line: str):
        if "tooltipDescriptionSB.append" in line:
            self.interest_line = True
        elif "getTextStartStringBuilder()" in line:
            self.interest_line = True
        elif "verb = " in line:
            self.interest_line = True

    def parse_attributes(self, line: str):
        if "new AbstractAttribute" in line:
            self.interest_line = True

    def parse_body(self, line: str):
        if "new BodyCoveringTemplate" in line:
            self.interest_line = True
        elif "new AbstractBodyCoveringType" in line:
            self.interest_line = True
        elif re.search(r"new Abstract\w+Type", line) is not None:
            self.interest_line = True
        elif "faceBodyDescriptionFeral = " in line:
            self.interest_line = True
        elif "stage = " in line or "areaEgged = " in line:
            self.interest_line = True
        elif "extraEffectsLsit.add" in line:
            self.interest_line = True

    def parse_effects(self, filename: str, line: str):
        if filename == "AbstractStatusEffect.java":
            if "stringBuilderToAppendTo.append" in line:
                self.interest_line = True
        elif filename == "StatusEffect.java":
            if "from1 = " in line or "from2 = " in line:
                self.interest_line = True
            elif "orificesRecovering.add" in line:
                self.interest_line = True
        if "new AbstractPerk" in line:
            self.interest_line = True
        elif "new AbstractStatusEffect" in line:
            self.interest_line = True

    def parse_fetishs(self, line: str):
        if "new AbstractFetish" in line:
            self.interest_line = True
        elif "perkRequirementsList.add" in line:
            self.interest_line = True

    def parse_npc(self, filename: str, line: str):
        if filename == "NPCOffspring.java":
            if "result = " in line:
                self.interest_line = True
        if "new PossibleItemEffect" in line:
            self.interest_line = True
        elif "FlavorText" in line:
            self.interest_line = True
        elif "getSurname().endsWith" in line:
            self.interest_line = True
        elif "speech.add" in line:
            self.interest_line = True

    def parse_race(self, line: str):
        if "new AbstractRace" in line:
            self.interest_line = True
        elif "new AbstractSubspecies" in line:
            self.interest_line = True
        elif "Modified.add" in line:
            self.interest_line = True
        elif "names.put" in line:
            self.interest_line = True

    def parse_character(self, filename: str, line: str):
        if filename == "StatusEffect.java":
            if "tooDeep.add" in line or "stretching.add" in line:
                self.interest_line = True
        elif filename == "GameCharacter.java":
            if "target = " in line:
                self.interest_line = True
            elif "additional = " in line:
                self.interest_line = True
        elif filename == "Litter.java":
            if "entries.add" in line:
                self.interest_line = True
        elif filename == "Heather.java":
            if "ingredientMap.put" in line:
                self.interest_line = True
        elif filename == "Angelixx.java":
            if "adjectivesUsed =" in line:
                self.interest_line = True
        if re.search(r"writing\s*=\s*", line) is not None:
            self.interest_line = True
        elif "new GenderAppearance" in line:
            self.interest_line = True
        elif "_CALCULATION = " in line:
            self.interest_line = True
        elif "newArrayListOfValues" in line:
            self.interest_line = True

    def parse_moves(self, line: str):
        if "new AbstractCombatMove" in line:
            self.interest_line = True
        elif "formatAttackOutcome" in line:
            self.interest_line = True
        elif "reason = " in line:
            self.interest_line = True

    def parse_dialogue(self, filename: str, line: str):
        if filename == "PrologueDialogue.java":
            if "demonstoneImages = " in line or "demonstoneEnergy = " in line:
                self.interest_line = True
        elif filename == "PhoneDialogue.java":
            if "clothingSlotCategories.put" in line:
                self.interest_line = True
        elif filename == "ClothingEmporium.java":
            if "descriptionStart = " in line:
                self.interest_line = True
        elif filename == "SuccubisSecrets.java":
            if "entry.getValue().getValue().add" in line:
                self.interest_line = True
        elif filename == "RoomPlayer.java":
            if ".add" in line:
                self.interest_line = True
        elif filename == "SlaveAuctionBidder.java":
            if "Comments = " in line:
                self.interest_line = True
        elif filename == "SlaverAlleyDialogue.java":
            if "Availability.add" in line:
                self.interest_line = True
        elif filename == "EnforcerWarehouse.java":
            if "dangerousDirections.add" in line:
                self.interest_line = True
        elif filename == "OptionsDialogue.java":
            if "disabledMsg = " in line:
                self.interest_line = True
        elif filename == "KaysWarehouse.java":
            if "KaySexResponse(" in line:
                self.interest_line = True
        elif filename == "UtilText.java":
            if "new ParserCommand" in line:
                self.interest_line = True
        elif filename == "SlaveDialogue.java":
            if "legsSpreading = " in line:
                self.interest_line = True
        elif filename == "DominionExpress.java":
            if "new MuleReward" in line:
                self.interest_line = True

        if "purchaseAvailability.append" in line:
            self.interest_line = True
        elif re.search(r"(Cry|Reaction|Speech)\s*=\s*", line) is not None:
            self.interest_line = True
        elif "new AbstractParserTarget" in line:
            self.interest_line = True
        elif "OffspringHeaderDisplay" in line:
            self.interest_line = True
        elif "map.put" in line:
            self.interest_line = True
        elif "responses.add" in line:
            self.interest_line = True
        elif "failEffects" in line:
            self.interest_line = True

    def parse_clothing(self, line: str):
        if "new AbstractClothingType" in line:
            self.interest_line = True

    def parse_enchanting(self, line: str):
        if "new AbstractItemEffectType" in line:
            self.interest_line = True
        elif "area = " in line:
            self.interest_line = True

    def parse_item(self, line: str):
        if "new AbstractItemType" in line:
            self.interest_line = True
        elif "Util.newArrayListOfValues" in line:
            self.interest_line = True
        elif "parsed.add" in line:
            self.interest_line = True
        elif "new AbstractStatusEffect" in line:
            self.interest_line = True

    def parse_positions(self, line: str):
        if "new AbstractSexPosition" in line:
            self.interest_line = True
        elif "new SexSlot" in line:
            self.interest_line = True

    def parse_sex(self, filename: str, line: str):
        if filename == "SadisticActions.java":
            if "tailSpecial1 = " in line or "tailSpecial2 = " in line:
                self.interest_line = True
        elif filename == "PenisAnus.java":
            if "assTargeting = " in line:
                self.interest_line = True
        elif filename == "GenericOrgasms.java":
            if "breasts = " in line:
                self.interest_line = True
            elif "areas.add" in line:
                self.interest_line = True

    def parse_main(self, line: str):
        if re.search(r"disclaimer\s*=\s*", line) is not None:
            self.interest_line = True

    def parse_rendering(self, line: str):
        if "equippedPanelSB.append" in line:
            self.interest_line = True
        elif "panelSB.append" in line:
            self.interest_line = True

    def parse_colours(self, line: str):
        if "new Colour" in line:
            self.interest_line = True

    def parse_places(self, filename: str, line: str):
        if "new AbstractPlaceType" in line:
            self.interest_line = True
        elif "new AbstractPlaceUpgrade" in line:
            self.interest_line = True
        elif "new AbstractGlobalPlaceType" in line:
            self.interest_line = True

    def parse_population(self, line: str):
        if "new AbstractPopulationType" in line:
            self.interest_line = True

    def parse_world(self, line: str):
        if "new AbstractWorldType" in line:
            self.interest_line = True

    def parse_game(self, filename: str, line: str):
        if filename == "Game.java":
            if "corruptionGains = " in line:
                self.interest_line = True
        elif filename == "Combat.java":
            if "Content.put" in line or "Content.get" in line:
                self.interest_line = True
            elif "critText.append" in line:
                self.interest_line = True
        elif filename == "Spell.java":
            if "cost = " in line:
                self.interest_line = True

    def general_string_parse(self, line: str) -> bool:
        if not self.interest_line:
            return False

        if line.strip().endswith(";"):
            self.interest_line = False
        elif "@Override" in line:  # 有效？
            self.interest_line = False

        if (
            re.search(r"(getMandatoryFirstOf|getAllOf|parseFromXMLFile)", line)
            is not None
        ):
            return False
        elif "SVGImageSB.append" in line:
            return False
        elif "System.err.println" in line:  # 暂不翻译报错信息
            return False

        if re.search(r"\"[^\"]+\"(?!\")", line) is not None:
            return True
        return False

    def process_comment(self, line: str) -> str:
        """
        处理多行注释
        """
        if re.search(r"^/\*", line) is not None:
            if "*/" not in line:
                self.comment = True
            else:
                return line[: line.find("/*")]
        elif self.comment and "*/" in line:
            self.comment = False
            return line[: line.find("*/")]

        # 处于多行注释内部则返回空字符串
        if self.comment:
            return ""

        # 移除单行注释
        if line.find(r"//") != -1:
            match = re.search(r"(?<!s:)//", line)
            if match is not None:
                return line[: match.start()]

        # 返回原字符串
        return line
