import re
from typing import List, Optional, Dict
from pathlib import Path
import json
import asyncio

from lxml import etree

from data import XmlEntry, CodeEntry, FilePair


def try_xml_entry_attrib(file: str, element: etree._Element, attr: str) -> Optional[XmlEntry]:
    if element.attrib.get(attr):
        return XmlEntry(
            file=file,
            original=element.attrib.get(attr),
            translation="",
            node_tag=element.tag,
            attribute=attr,
            stage=0
        )
    else:
        return None


def try_xml_entry_text(file: str, element: etree._Element) -> Optional[XmlEntry]:
    if element.text is None:
        return None

    if element.text.strip() == "":
        return None

    return XmlEntry(
        file=file,
        original=element.text,
        translation="",
        node_tag=element.tag,
        attribute=None,
        stage=0
        )


class Extractor:
    def __init__(self, root: str, new_dict_path: str):
        self.root = Path(root)
        self.target_dir = Path(new_dict_path)

        if not self.root.is_dir():
            raise Exception("Invalid root directory")
        if not self.target_dir.is_dir():
            self.target_dir.mkdir()

    def extract(self):
        self.extract_res()
        self.extract_src()

    def extract_res(self):
        loop = asyncio.get_event_loop()

        res_path = self.root.joinpath("res")

        file_pairs: List[FilePair] = []

        # 递归获取所有后缀为xml的文件
        for file in res_path.glob("**/*.xml"):
            result_path = self.target_dir.joinpath(
                file.relative_to(self.root)).with_suffix(".json")
            file_pairs.append(FilePair(file, result_path))
            if not result_path.parent.exists():
                result_path.parent.mkdir(parents=True)

        tasks = [
            self.extract_xml_gather(file.original_file, file.entry_file) for file in file_pairs
        ]

        loop.run_until_complete(asyncio.gather(*tasks))

    async def extract_xml_gather(self, xml_path, entry_path):
        entry_list = await self.extract_xml(xml_path)
        if len(entry_list) <= 0:
            return
        with open(entry_path, "w", encoding="utf-8") as f:
            json.dump(entry_list, f, ensure_ascii=False, indent=4)

    async def extract_xml(self, xml_path: Path) -> Dict[str, XmlEntry]:
        entry_list = []

        def insert_entry(entry: Optional[XmlEntry]):
            if entry is None:
                return
            entry_json = entry.to_json()
            entry_json['key'] += "_" + str(len(entry_list))
            entry_list.append(entry_json)

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
        for AuthorTag in root.iter("AuthorTag"):
            e = try_xml_entry_text(file, AuthorTag)
            insert_entry(e)

        # combat move nodes
        for availabilityDescription in root.iter("availabilityDescription"):
            e = try_xml_entry_text(file, availabilityDescription)
            insert_entry(e)

        for criticalDescription in root.iter("criticalDescription"):
            e = try_xml_entry_text(file, criticalDescription)
            insert_entry(e)

        for movePredictionDescriptionWithTarget in root.iter("movePredictionDescriptionWithTarget"):
            e = try_xml_entry_text(file, movePredictionDescriptionWithTarget)
            insert_entry(e)

        for movePredictionDescriptionNoTarget in root.iter("movePredictionDescriptionNoTarget"):
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
            e = try_xml_entry_text(file, htmlContent)
            insert_entry(e)

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
        for crotchBoobsTransformationDescription in root.iter("crotchBoobsTransformationDescription"):
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
        # no

        # statusEffect
        # name
        # description
        for effect in root.iter("effect"):
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

        return entry_list

    def extract_src(self):
        loop = asyncio.get_event_loop()

        src_path = self.root.joinpath("src")

        file_pairs: List[FilePair] = []

        # 递归获取所有后缀为xml的文件
        for file in src_path.glob("**/*.java"):
            result_path = self.target_dir.joinpath(
                file.relative_to(self.root)).with_suffix(".json")
            file_pairs.append(FilePair(file, result_path))
            if not result_path.parent.exists():
                result_path.parent.mkdir(parents=True)

        tasks = [
            self.extract_java_gather(file.original_file, file.entry_file) for file in file_pairs
        ]

        loop.run_until_complete(asyncio.gather(*tasks))

    async def extract_java_gather(self, java_path, entry_path):
        entry_list = await self.extract_java(java_path)
        if len(entry_list) <= 0:
            return
        with open(entry_path, "w", encoding="utf-8") as f:
            json.dump(entry_list, f, ensure_ascii=False, indent=4)

    async def extract_java(self, file: Path):
        java_extractor = JavaExtractor()
        entry_list = []

        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for idx, line in enumerate(lines):
            line = line.strip()
            extract_flag = False

            if file.parent.name == "tooltips":
                java_extractor.parse_tooltips(line)
            elif file.parent.name == "controller":
                java_extractor.parse_controller(line)
            elif file.parent.name == "attributes":
                java_extractor.parse_attributes(line)
            elif file.parent.name == "body" or file.parent.parent.name == "body":
                java_extractor.parse_body(line)
            elif file.parent.name == "effects":
                java_extractor.parse_effects(line)
            elif file.parent.name == "fetishs":
                java_extractor.parse_fetishs(line)
            elif file.parent.name == "npc":
                java_extractor.parse_npc(line)
            elif file.parent.name == "race":
                java_extractor.parse_race(line)
            elif file.parent.name == "character":
                java_extractor.parse_character(line)
            elif file.parent.name == "moves":
                java_extractor.parse_moves(line)
            elif file.parent.name == "dialogue" or file.parent.parent.name == "dialogue":
                java_extractor.parse_dialogue(line)
            elif file.parent.name == "clothing":
                java_extractor.parse_clothing(line)
            elif file.parent.name == "enchanting":
                java_extractor.parse_enchanting(line)
            elif file.parent.name == "item":
                java_extractor.parse_item(line)
            elif file.parent.name == "positions" or file.parent.parent.name == "positions":
                java_extractor.parse_positions(line)
            elif file.parent.name == "main":
                java_extractor.parse_main(line)
            elif file.parent.name == "rendering":
                java_extractor.parse_rendering(line)
            elif file.parent.name == "colours":
                java_extractor.parse_colours(line)
            elif file.parent.name == "places":
                java_extractor.parse_places(line)
            elif file.parent.name == "population":
                java_extractor.parse_population(line)
            elif file.parent.name == "world":
                java_extractor.parse_world(line)

            java_extractor.parse_normal(line)

            if java_extractor.general_string_parse(line):
                extract_flag = True

            if extract_flag:
                entry_list.append(
                    CodeEntry(
                        file=file,
                        original=line, 
                        translation="", 
                        line=idx,
                        stage=0
                    ).to_json()
                )

        return entry_list


class JavaExtractor:
    def __init__(self):
        self.interest_line: bool = False

    def parse_normal(self, line: str):
        if self.interest_line:
            return

        if "return" in line:
            self.interest_line = True
        elif re.search(r"([sS][bB]|StringBuilder)(\(\))?\.append", line) is not None:
            self.interest_line = True
        elif "new Response" in line:
            self.interest_line = True
        elif ".setInformation" in line:
            self.interest_line = True
        elif "getTextEndStringBuilder().append" in line:
            self.interest_line = True
        elif re.search(r"[d|D]escript(ion|or)\s*=\s*", line) is not None:
            self.interest_line = True
        elif re.search(r"[t|T]itle\s*=\s*", line) is not None:
            self.interest_line = True
        elif re.search(r"[n|N]ame\s*=\s*", line) is not None:
            self.interest_line = True
        elif re.search(r"[t|T]ext\s*=\s*", line) is not None:
            self.interest_line = True
        # elif "System.err.println" in line:
        #     self.interest_line = True
        elif "new Value<>" in line:
            self.interest_line = True
        elif re.search(r"^\s*[A-Z_]+\(", line):   # 枚举项
            self.interest_line = True
        elif "new String[]" in line or "static String[]" in line:
            self.interest_line = True
        elif re.search(r"returnValue\s*=\s*", line) is not None:
            self.interest_line = True
        elif "Names.add" in line or "names.add" in line:
            self.interest_line = True
        elif "Descriptions.add" in line or "descriptions.add" in line:
            self.interest_line = True
        elif "super(" in line:
            self.interest_line = True
        elif "new TattooWriting" in line:
            self.interest_line = True
        elif ".setDescription" in line:
            self.interest_line = True
        elif ".setName" in line:
            self.interest_line = True
        elif "new NameTriplet" in line:
            self.interest_line = True
        elif "Effects.add" in line:
            self.interest_line = True
        elif "Adjectives.add" in line:
            self.interest_line = True
        elif "UtilText.returnStringAtRandom" in line:
            self.interest_line = True
        elif "UtilText.parse" in line:
            self.interest_line = True
        elif "new EventLogEntry" in line:
            self.interest_line = True
        elif "new DialogueNode" in line:
            self.interest_line = True
        elif re.search(r"String\s*=\s*", line) is not None:
            self.interest_line = True

    def parse_tooltips(self, line: str):
        if "tooltipSB.append" in line:
            self.interest_line = True

        elif ".setTooltipContent" in line:
            self.interest_line = True

    def parse_controller(self, line: str):
        if "tooltipDescriptionSB.append" in line:
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

    def parse_effects(self, line: str):
        if "new AbstractPerk" in line:
            self.interest_line = True
        elif "new AbstractStatusEffect" in line:
            self.interest_line = True

    def parse_fetishs(self, line: str):
        if "new AbstractFetish" in line:
            self.interest_line = True

    def parse_npc(self, line: str):
        if "new PossibleItemEffect" in line:
            self.interest_line = True
        elif "FlavorText" in line:
            self.interest_line = True

    def parse_race(self, line: str):
        if "new AbstractRace" in line:
            self.interest_line = True
        elif "new AbstractSubspecies" in line:
            self.interest_line = True

    def parse_character(self, line: str):
        if re.search(r"writing\s*=\s*", line) is not None:
            self.interest_line = True
        elif "new GenderAppearance" in line:
            self.interest_line = True

    def parse_moves(self, line: str):
        if "new AbstractCombatMove" in line:
            self.interest_line = True
        elif "formatAttackOutcome" in line:
            self.interest_line = True

    def parse_dialogue(self, line: str):
        if "purchaseAvailability.append" in line:
            self.interest_line = True
        elif re.search(r"(Cry|Reaction|Speech)\s*=\s*", line) is not None:
            self.interest_line = True
        elif "new AbstractParserTarget" in line:
            self.interest_line = True
        elif "OffspringHeaderDisplay" in line:
            self.interest_line = True

    def parse_clothing(self, line: str):
        if "new AbstractClothingType" in line:
            self.interest_line = True

    def parse_enchanting(self, line: str):
        if "new AbstractItemEffectType" in line:
            self.interest_line = True

    def parse_item(self, line: str):
        if "new AbstractItemType" in line:
            self.interest_line = True

    def parse_positions(self, line: str):
        if "new AbstractSexPosition" in line:
            self.interest_line = True
        elif "new SexSlot" in line:
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

    def parse_places(self, line: str):
        if "new AbstractPlaceType" in line:
            self.interest_line = True
        elif "new AbstractPlaceUpgrade" in line:
            self.interest_line = True

    def parse_population(self, line: str):
        if "new AbstractPopulationType" in line:
            self.interest_line = True

    def parse_world(self, line: str):
        if "new AbstractWorldType" in line:
            self.interest_line = True

    def general_string_parse(self, line: str) -> bool:
        if not self.interest_line:
            return False

        if line.endswith(';'):
            self.interest_line = False
        elif "@Override" in line:  # 有效？
            self.interest_line = False
        
        if re.search(r"^(/\*|\*)", line) is not None:
            self.interest_line = False
            return False
        elif re.search(r"(getMandatoryFirstOf|getAllOf|getAttribute|parseFromXMLFile)", line) is not None:
            return False

        # print(line, re.search(r"\".+\"", line))
        if line.find(r"//") != -1:
            line = line[:line.find(r"//")]
        if re.search(r"\"[^\"]+\"(?!\")", line) is not None:
            return True
        return False
