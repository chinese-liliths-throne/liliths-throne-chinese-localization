from pathlib import Path
from lxml import etree
from typing import List, Dict
import json
import re
import shutil

from data import XmlEntry, CodeEntry
from logger import logger
from urllib.parse import quote
from const import (
    ROOT_DIR,
    FONT_DIR,
    SVG_DIR,
    FONT_DIR_NAME,
    FONT_TARGET_DIR,
    PARATRANZ_PROJECT_ID,
)

FONT_SIZE_REGEX = r"font-size\s*:\s*(\d+)\s*(?:px|pt)"
LINE_HEIGHT_REGEX = r"line-height\s*:\s*(\d+)\s*(?:px|pt)"


def ui_value_modify(line: str, regex: str, multiplier: float) -> str:
    matches = re.search(regex, line)
    if matches is not None:
        for group in matches.groups():
            if group.isdigit():
                value = int(group)
                if value <= 16:
                    value = int(value * min(multiplier + 0.1, 1))
                else:
                    value = int(value * multiplier)
                line = line.replace(group, str(value))
            else:
                multiplier = int(multiplier * 10)
                line = line.replace(group, f"({group})*{str(multiplier)}/10")

    return line


def valid_element(element: etree._Element) -> bool:
    if element.text is None or len(element.text.strip()) == 0:
        return False
    elif element.getparent().tag == "formattingNames":
        return False
    elif element.getparent().tag == "statusEffects":
        return False

    return True


class Applier:
    def __init__(self, target: str, root: str, dict_dir: str) -> None:
        self.target = target
        self.root = Path(root)
        self.dict_dir = Path(dict_dir)

    def apply(self) -> None:
        self.apply_res()
        if self.target == "main":
            self.apply_src()
            self.apply_special()  # 对于其他优化游戏的文件进行调整

    def apply_special(self) -> None:
        self.modify_css()
        self.modify_java()
        self.modify_xml()
        self.add_files()

    def add_files(self) -> None:
        # 复制字体文件
        shutil.copytree(
            Path(ROOT_DIR) / FONT_DIR / FONT_DIR_NAME,
            self.root / FONT_TARGET_DIR / FONT_DIR_NAME,
            dirs_exist_ok=True,
        )
        shutil.copy(
            Path(ROOT_DIR) / "replace_file" / "GenderNames.java",
            self.root
            / "src"
            / "com"
            / "lilithsthrone"
            / "game"
            / "character"
            / "gender"
            / "GenderNames.java",
        )

    def modify_css(self) -> None:
        for file in self.root.glob("**/*.css"):
            with open(file, mode="r", encoding="utf-8") as f:
                lines = f.readlines()

            for idx, line in enumerate(lines):
                if line.strip().startswith(
                    "-fx-font-family"
                ) or line.strip().startswith("font-family"):
                    item = line.split(":")
                    fonts = item[1].split(",")
                    fonts.insert(0, '"Source Han Sans CN"')
                    item[1] = ",".join(fonts)
                    line = ":".join(item)

                line = ui_value_modify(line, FONT_SIZE_REGEX, 0.8)
                line = ui_value_modify(line, LINE_HEIGHT_REGEX, 0.9)

                lines[idx] = line

            with open(file, "w", encoding="utf-8") as f:
                f.writelines(lines)

    def modify_java(self) -> None:
        for file in self.root.glob("**/*.java"):
            with open(file, mode="r", encoding="utf-8") as f:
                lines = f.readlines()

            for idx, line in enumerate(lines):
                # 调整字体和行高
                line = ui_value_modify(line, FONT_SIZE_REGEX, 0.8)
                line = ui_value_modify(line, LINE_HEIGHT_REGEX, 0.8)

                # 使用中文Locale
                line = line.replace("Locale.ENGLISH", "Locale.CHINESE")

                if file.name == "Game.java":
                    # 修改默认字体大小
                    line = line.replace(
                        "public static final int FONT_SIZE_NORMAL = 18;",
                        "public static final int FONT_SIZE_NORMAL = 15;",
                    )
                    # 调整日期格式
                    line = line.replace(
                        "return date.substring(0, date.length()-5);",
                        "return date.substring(5, date.length());",
                    )
                elif file.name == "Properties.java":
                    # 修改默认字体
                    line = line.replace(
                        "public int fontSize = 18;", "public int fontSize = 15;"
                    )
                elif file.name == "UtilText.java":
                    # 高版本jdk不再自带nashorn
                    if "import jdk.nashorn" in line:
                        line = "//" + line
                    if "import org.openjdk.nashorn" in line:
                        line = line[2:]
                    line = line.replace(
                        ".getGenderName().getFeminine()",
                        ".getGenderName().getFeminineId()",
                    )
                    line = line.replace(
                        ".getGenderName().getMasculine()",
                        ".getGenderName().getMasculineId()",
                    )
                    line = line.replace(
                        ".getGenderName().getNeutral()",
                        ".getGenderName().getNeutralId()",
                    )
                    # 调整频率
                    line = line.replace(
                        "addMuffle(modifiedSentence, 5);",
                        "addMuffle(modifiedSentence, 8);",
                    )
                    line = line.replace(
                        "addSexSounds(modifiedSentence, 6);",
                        "addSexSounds(modifiedSentence, 10);",
                    )
                    line = line.replace(
                        "addBimbo(modifiedSentence, 6);",
                        "addBimbo(modifiedSentence, 10);",
                    )
                    line = line.replace(
                        "addBimbo(modifiedSentence, 6);",
                        "addBro(modifiedSentence, 10);",
                    )
                    line = line.replace(
                        "replaceWithMuffle(modifiedSentence, 2);",
                        "replaceWithMuffle(modifiedSentence, 5);",
                    )

                elif file.name == "AbstractAttribute.java":
                    # Attribute的name同时被用于逻辑和显示，故使用类似的nameAbbreviation暂时替代
                    line = line.replace("return name;", "return nameAbbreviation;")
                    line = line.replace(
                        'return "<"+tag+" style=\'color:"+this.getColour().toWebHexString()+";\'>"+name+"</"+tag+">";',
                        'return "<"+tag+" style=\'color:"+this.getColour().toWebHexString()+";\'>"+nameAbbreviation+"</"+tag+">";',
                    )
                elif file.name == "MainController.java":
                    line = line.replace(
                        "webviewTooltip.setMaxHeight(height);",
                        "webviewTooltip.setMaxHeight(height);\n"
                        + "\t\twebviewTooltip.setPrefHeight(height);",
                    )
                    line = line.replace(
                        "tooltip.setMaxHeight(height);",
                        "tooltip.setMaxHeight(height);\n"
                        + "\t\ttooltip.setPrefHeight(height);",
                    )
                    line = line.replace(
                        'Main.mainController.getWebEngine().getDocument().getElementById("hiddenFieldName").getTextContent().length() < 2',
                        'Main.mainController.getWebEngine().getDocument().getElementById("hiddenFieldName").getTextContent().length() < 1',
                    )
                elif file.name == "CityHallDemographics.java":
                    line = line.replace(
                        'Main.mainController.getWebEngine().getDocument().getElementById("hiddenFieldName").getTextContent().length() < 2',
                        'Main.mainController.getWebEngine().getDocument().getElementById("hiddenFieldName").getTextContent().length() < 1',
                    )
                elif file.name == "CharacterCreation.java":
                    line = line.replace(
                        'Main.mainController.getWebEngine().getDocument().getElementById("hiddenFieldName").getTextContent().length() < 2',
                        'Main.mainController.getWebEngine().getDocument().getElementById("hiddenFieldName").getTextContent().length() < 1',
                    )
                elif file.name == "Main.java":
                    # 内置字体导入
                    line = line.replace(
                        "protected void loadFonts() {",
                        "protected void loadFonts() {\n"
                        + '\t\tif (Font.loadFont(toUri("res/fonts/Source Han/SourceHanSansCN-Regular.otf"), 12) != null) {\n'
                        + '\t\t\tFont.loadFont(toUri("res/fonts/Source Han/SourceHanSansCN-Bold.otf"), 12);\n'
                        + "\t\t} else {\n"
                        + '\t\t\tSystem.err.println("Source Han Sans font could not be loaded.");\n'
                        + "\t\t}\n",
                    )
                elif file.name == "Util.java":
                    # 替换intToString为输出阿拉伯数字
                    line = line.replace(
                        "\tpublic static String intToString(int integer) {",
                        '\tstatic String[] digits = {"零","一","二","三","四","五","六","七","八","九"};\n'
                        + '\tstatic String[] lower_base = {"","十","百","千"};\n'
                        + '\tstatic String[] upper_base = {"","万","亿"};\n'
                        + "\n"
                        + "\tstatic String intBlockToString(int integer, boolean isLower, char charTwo)\n"
                        + "\t{\n"
                        + "\t\tif (integer == 2 && !isLower) return String.valueOf(charTwo);\n"
                        + "\t\tStringBuilder sb = new StringBuilder();\n"
                        + "\t\tString intStr = Integer.toString(integer);\n"
                        + "\t\tint n = intStr.length();\n"
                        + "\t\tfor(int i = 0; i < n; i++)\n"
                        + "\t\t{\n"
                        + "\t\t\tint num = intStr.charAt(i) - '0';\n"
                        + "\t\t\tif (num == 0 && sb.length() > 0 && sb.charAt(sb.length()-1) == '零') continue;\n"
                        + "\t\t\tString digit = digits[num];\n"
                        + "\t\t\tif (num == 2 && n - 1 - i != 0 && n - 1 - i != 1) sb.append('两');\n"
                        + "\t\t\telse sb.append(digit);\n"
                        + "\t\t\tif (num != 0) sb.append(lower_base[n - 1 - i]);\n"
                        + "\t\t\tif (!isLower && sb.length() > 1 && sb.charAt(0) == '一' && sb.charAt(1) == '十') sb.deleteCharAt(0);\n"
                        + "\t\t}\n"
                        + '\t\tif (sb.length() == 0) return "";\n'
                        + "\t\tif (sb.charAt(sb.length()-1) == '零') sb.deleteCharAt(sb.length()-1);\n"
                        + "\t\treturn sb.toString();\n"
                        + "\t}\n"
                        + "\n"
                        + "\tpublic static String intToString(int integer) {\n"
                        + "\t\treturn intToString(integer, true);\n"
                        + "\t}\n"
                        + "\n"
                        + "\tpublic static String intToString(int integer, boolean withLiang) {\n"
                        + '\t\tif (integer == 0) return "零";\n'
                        + "\t\tStringBuilder sb = new StringBuilder();\n"
                        + '\t\tString minus = "";\n'
                        + "\t\tif (integer < 0) \n"
                        + "\t\t{\n"
                        + '\t\t\tminus = "负";\n'
                        + "\t\t\tinteger = -integer;\n"
                        + "\t\t}\n"
                        + "\t\tint upper_cap = 0;\n"
                        + "\t\twhile(integer > 0)\n"
                        + "\t\t{\n"
                        + "\t\t\tint upper = integer%10000;\n"
                        + "\t\t\tif (sb.length() == 1 || (sb.length() > 1 && sb.charAt(1) != '千')) sb.insert(0, '零');\n"
                        + "\t\t\tsb.insert(0, intBlockToString(upper, integer/10000 > 0, withLiang ? '两' : '二')+upper_base[upper_cap]);\n"
                        + "\t\t\tinteger = integer/10000;\n"
                        + "\t\t\tupper_cap++;\n"
                        + "\t\t}\n"
                        + "\n"
                        + "\t\tsb.insert(0, minus);\n"
                        + "\n"
                        + "\t\treturn sb.toString();\n"
                        + "\t}\n"
                        + "\tpublic static String intToStringOld(int integer){",
                    )
                    line = line.replace(
                        "public static String intToPosition(int integer) {",
                        "public static String intToPosition(int integer) {\n"
                        + '\t\treturn "第" + intToString(integer, false);\n'
                        + "\t}\n"
                        + "\tpublic static String intToPositionOld(int integer) {",
                    )
                    # 添加正字标记使用的intToZheng
                    line = line.replace(
                        "public static String intToTally(int integer, int max) {",
                        "public static String intToZheng(int integer, int max) {\n"
                        + '\t\tString[] zhengPhase = {"丨","丄","上","止"};\n'
                        + "\t\tStringBuilder numeralSB = new StringBuilder();\n"
                        + "\t\tint limit = Math.min(integer, max);\n"
                        + '\t\tfor(int i=0; i<limit/5; i++) numeralSB.append("正");\n'
                        + "\t\tif(limit%5 != 0) numeralSB.append(zhengPhase[limit%5-1]);\n"
                        + '\t\tif(limit<integer) numeralSB.append("…… (共计："+integer+")");\n'
                        + "\t\treturn numeralSB.toString();\n"
                        + "\t}\n"
                        + "\tpublic static String intToTally(int integer, int max) {",
                    )
                    line = line.replace(
                        'private static Pattern endOfSentence = Pattern.compile("[,.!?]");',
                        'private static Pattern endOfSentence = Pattern.compile("[,.!?，。！？、]");',
                    )
                    # line = line.replace(
                    #     "if(sentence.charAt(i)==' '",
                    #     "if(true")
                    # line = line.replace(
                    #     "&& Character.isLetter(sentence.charAt(i+1))",
                    #     "&& !isEndOfSentence(sentence.charAt(i+1))"
                    # )
                elif file.name == "Units.java":
                    # 调整日期格式
                    line = line.replace(
                        'DateTimeFormatter.ofPattern(Main.getProperties().hasValue(PropertyValue.internationalDate) ? "dd.MM.yy" : "MM/dd/yy")',
                        'DateTimeFormatter.ofPattern(Main.getProperties().hasValue(PropertyValue.internationalDate) ? "yy.MM.dd" : "yy.MM.dd")',
                    )
                    line = line.replace(
                        "DateTimeFormatter.ofPattern(\"d'%o %m' yyyy\")",
                        'DateTimeFormatter.ofPattern("yyyy年MM月dd日")',
                    )
                    # 调整时间格式
                    line = line.replace(
                        'DateTimeFormatter.ofPattern(Main.getProperties().hasValue(PropertyValue.twentyFourHourTime) ? "HH:mm" : "hh:mm a")',
                        'DateTimeFormatter.ofPattern(Main.getProperties().hasValue(PropertyValue.twentyFourHourTime) ? "HH:mm" : "hh:mm a").withLocale(Locale.ENGLISH)',
                    )
                elif file.name == "AbstractFluidType.java":
                    # 调整精液前缀判断方法
                    line = line.replace(
                        'if(name.endsWith("-")) {',
                        "if(!baseFluidType.getNames().contains(name)) {",
                    )
                elif (
                    file.name == "AbstractPenisType.java"
                    or file.name == "AbstractVaginaType.java"
                ):
                    line = line.replace(
                        'if(name.endsWith("-")) {',
                        "if(!returnNames.containsKey(name)) {",
                    )
                elif file.name == "TattooCountType.java":
                    # 添加正字标记
                    line = line.replace(
                        "public enum TattooCountType {",
                        "public enum TattooCountType {\n"
                        + '\tZHENG("正字") {\n'
                        + "\t\tpublic String convertInt(int input) {\n"
                        + "\t\t\treturn Util.intToZheng(input, 50);\n"
                        + "\t\t}\n"
                        + "\t},\n",
                    )
                elif file.name == "GameCharacter.java":
                    # remove useless 'the'
                    line = line.replace(":determiner)", ':"")')
                elif file.name == "Wes.java":
                    line = line.replace(
                        "return this.getNameIgnoresPlayerKnowledge();", 'return "Wes";'
                    )
                elif file.name == "Brax.java":
                    line = line.replace(
                        "return this.getNameIgnoresPlayerKnowledge();",
                        "if (Main.game.getDialogueFlags().hasFlag(DialogueFlagValue.bimbofiedBrax))\n"
                        + '\t\t\treturn "Brandi";\n'
                        + "\t\telse if (Main.game.getDialogueFlags().hasFlag(DialogueFlagValue.feminisedBrax))\n"
                        + '\t\t\treturn "Bree";\n'
                        + "\t\telse\n"
                        + '\t\t\treturn "Brax";\n',
                    )
                elif file.name == "Sex.java":
                    line = line.replace(
                        "positionActionsPlayer.sort((a1, a2) ->",
                        "positionActionsPlayer.sort((a1, a2) -> true?((a1.getActionType() == a2.getActionType())? (a1.isPositionSwap() == a2.isPositionSwap() ? a1.getActionTitle().compareTo(a2.getActionTitle()) : (a1.isPositionSwap() ? -1 : 1)): (a1.getActionType() == SexActionType.POSITIONING_MENU ? -1 : 1)):",
                    )
                lines[idx] = line

            with open(file, "w", encoding="utf-8") as f:
                f.writelines(lines)

    def modify_xml(self) -> None:
        for file in self.root.glob("**/*.xml"):
            if file.name == "eisek_mob_hideout.xml":
                with open(file, mode="r", encoding="utf-8") as f:
                    line = f.read()
                with open(
                    Path(ROOT_DIR) / SVG_DIR / "eisek_mob_hideout.svg",
                    "r",
                    encoding="utf-8",
                ) as f:
                    svg = f.read()
                new_line = re.sub(r"(<svg.*</svg>)", svg, line, flags=re.DOTALL)
                with open(file, mode="w", encoding="utf-8") as f:
                    f.write(new_line)

    def apply_res(self) -> None:
        original_files = [file for file in self.root.glob("**/*.xml")]
        dict_fils = [
            self.dict_dir.joinpath(file.relative_to(self.root)).with_suffix(".json")
            for file in original_files
        ]

        for original_file, dict_file in zip(original_files, dict_fils):
            if not dict_file.exists():  # 不存在对应字典文件
                continue

            self.apply_xml(original_file, dict_file)

    def apply_xml(self, original_file: Path, dict_file: Path) -> None:
        with open(dict_file, "r", encoding="utf-8") as f:
            entry_list = json.load(f)

        entry_list = [XmlEntry.from_json(original_file, entry) for entry in entry_list]

        parser = etree.XMLParser(strip_cdata=False)

        tree: etree._Element = etree.parse(str(original_file), parser)

        entry_dict: Dict[str, List[XmlEntry]] = {}
        for entry in entry_list:
            if entry_dict.get(entry.node_tag) is None:
                entry_dict[entry.node_tag] = [entry]
            else:
                entry_dict[entry.node_tag].append(entry)

        for tag, entry_cluster in entry_dict.items():
            # special process for htmlContent
            if tag == "htmlContent":
                entry_dict: Dict[str, List[XmlEntry]] = {}
                for entry in entry_cluster:
                    if entry_dict.get(entry.attribute):
                        entry_dict[entry.attribute].append(entry)
                    else:
                        entry_dict[entry.attribute] = [entry]

                for entry_attribute, entries in entry_dict.items():
                    nodes = tree.xpath(f"//htmlContent[@tag='{entry_attribute}']")
                    if len(nodes) > 1:
                        for idx, node in enumerate(nodes):
                            entry = entries[idx]
                            if entry.stage == 0 or entry.translation == entry.original:  # 无需修改
                                continue
                            node.text = node.text.replace(
                                entry.original,
                                entry.translation.replace("\\n", "\n"),
                            )
                            node.text = etree.CDATA(node.text)
                    else:
                        node = nodes[0]
                        for entry in entries:
                            if entry.stage == 0 or entry.translation == entry.original:  # 无需修改
                                continue
                            node.text = node.text.replace(
                                entry.original,
                                entry.translation.replace("\\n", "\n"),
                            )
                            node.text = etree.CDATA(node.text)
            else:
                nodes: List[etree._Element] = list(tree.iter(tag))
                nodes = list(filter(valid_element, nodes))
                for entry in entry_cluster:
                    if entry.stage == 0 or entry.translation == entry.original:  # 无需修改
                        continue
                    node = nodes[entry.node_idx]
                    if entry.attribute is not None:
                        node.set(entry.attribute, entry.translation)
                    else:
                        node.text = entry.translation.replace("\\n", "\n")
                        node.text = etree.CDATA(node.text)

        tree.write(
            original_file.as_posix(),
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=True,
            standalone=False,
        )

    def apply_src(self) -> None:
        original_files = [file for file in self.root.glob("**/*.java")]
        dict_fils = [
            self.dict_dir.joinpath(file.relative_to(self.root)).with_suffix(".json")
            for file in original_files
        ]

        for original_file, dict_file in zip(original_files, dict_fils):
            if not dict_file.exists():  # 不存在对应字典文件
                continue

            self.apply_java(original_file, dict_file)

    def apply_java(self, original_file: Path, dict_file: Path) -> None:
        with open(dict_file, "r", encoding="utf-8") as f:
            entry_list = json.load(f)
        with open(original_file, "r", encoding="utf-8") as f:
            text = f.readlines()

        entry_list = [CodeEntry.from_json(original_file, entry) for entry in entry_list]

        for entry in entry_list:
            line_text = text[entry.line]
            applied_text = self.apply_java_line(
                line_text, entry.original, entry.translation, dict_file, entry.line
            )
            text[entry.line] = applied_text

        with open(original_file, "w", encoding="utf-8") as f:
            f.writelines(text)

    def apply_java_line(
        self, text: str, original: str, translation: str, file: Path, line: int
    ) -> str:
        if len(translation) <= 0:
            return text

        # 常见错误检测
        quote_count = translation.count('"') - translation.count('\\"')
        if quote_count % 2 == 1 and "//" not in translation and "/*" not in translation:
            logger.warning(
                "\t****%s[%s]:翻译文本有奇数个双引号！|https://paratranz.cn/projects/%s/strings?text=%s",
                file.as_posix(),
                line,
                PARATRANZ_PROJECT_ID[self.target],
                quote(original),
            )
            print(text)
        if "\\n" in translation and "\\n" not in original:
            logger.warning(
                "\t****%s[%s]:翻译文本有额外换行符！|https://paratranz.cn/projects/%s/strings?text=%s",
                file.as_posix(),
                line,
                PARATRANZ_PROJECT_ID[self.target],
                quote(original),
            )
            translation = translation.replace("\\n", "")

        if (
            original.endswith(",")
            and not translation.endswith(",")
            and not translation.strip().endswith(",")
        ):
            logger.warning(
                "\t****%s[%s]:翻译文本末尾无逗号！|https://paratranz.cn/projects/%s/strings?text=%s",
                file.as_posix(),
                line,
                PARATRANZ_PROJECT_ID[self.target],
                quote(original),
            )
            translation += ","
        elif (
            original.endswith(";")
            and not translation.endswith(";")
            and not translation.strip().endswith(";")
        ):
            logger.warning(
                "\t****%s[%s]:翻译文本末尾无分号！|https://paratranz.cn/projects/%s/strings?text=%s",
                file.as_posix(),
                line,
                PARATRANZ_PROJECT_ID[self.target],
                quote(original),
            )
            translation += ";"

        index = text.find(original)
        if index == -1:
            logger.warning("\t****原文本无匹配！")
            return text
        else:
            text = text[:index] + translation + text[index + len(original) :]
            return text


if __name__ == "__main__":
    applier = Applier("./liliths-throne-public-dev", "./new_dict")
    applier.apply_special()
