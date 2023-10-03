from pathlib import Path
from lxml import etree
from typing import List, Dict
import json
import re
import shutil

from data import XmlEntry, CodeEntry
from logger import logger
from const import *

FONT_SIZE_REGEX = r"font-size\s*:\s*(\d+)\s*(?:px|pt)"
LINE_HEIGHT_REGEX = r"line-height\s*:\s*(\d+)\s*(?:px|pt)"


def ui_value_modify(line: str, regex: str, multiplier: float) -> str:
    matches = re.search(regex, line)
    if matches is not None:
        for group in matches.groups():
            if group.isdigit():
                value = int(group)
                if value <= 16:
                    value = int(value * min(multiplier+0.1, 1))
                else:
                    value = int(value * multiplier)
                line = line.replace(group, str(value))
            else:
                multiplier = int(multiplier*10)
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
    def __init__(self, root: str, dict_dir: str) -> None:
        self.root = Path(root)
        self.dict_dir = Path(dict_dir)

    def apply(self) -> None:
        self.apply_res()
        self.apply_src()
        self.apply_special()  # 对于其他优化游戏的文件进行调整

    def apply_special(self) -> None:
        self.modify_css()
        self.modify_java()
        self.add_files()

    def add_files(self) -> None:
        # 复制字体文件
        shutil.copytree(Path(ROOT_DIR) / FONT_DIR / FONT_DIR_NAME,
                        self.root / FONT_TARGET_DIR / FONT_DIR_NAME)

    def modify_css(self) -> None:
        for file in self.root.glob("**/*.css"):
            with open(file, mode='r', encoding='utf-8') as f:
                lines = f.readlines()

            for idx, line in enumerate(lines):
                if line.strip().startswith("-fx-font-family") or line.strip().startswith("font-family"):
                    item = line.split(":")
                    fonts = item[1].split(",")
                    fonts.insert(0, "\"Source Han Sans CN\"")
                    item[1] = ",".join(fonts)
                    line = ":".join(item)

                line = ui_value_modify(line, FONT_SIZE_REGEX, 0.8)
                line = ui_value_modify(line, LINE_HEIGHT_REGEX, 0.9)

                lines[idx] = line

            with open(file, 'w', encoding='utf-8') as f:
                f.writelines(lines)

    def modify_java(self) -> None:
        for file in self.root.glob("**/*.java"):
            with open(file, mode='r', encoding='utf-8') as f:
                lines = f.readlines()

            for idx, line in enumerate(lines):
                # 调整字体和行高
                line = ui_value_modify(line, FONT_SIZE_REGEX, 0.8)
                line = ui_value_modify(line, LINE_HEIGHT_REGEX, 0.8)

                # 使用中文Locale
                line = line.replace("Locale.ENGLISH", "Locale.CHINESE")

                if file.name == "Game.java":
                    # 修改默认字体大小
                    line = line.replace("public static final int FONT_SIZE_NORMAL = 18;",
                                        "public static final int FONT_SIZE_NORMAL = 15;")
                    # 调整日期格式
                    line = line.replace("return date.substring(0, date.length()-5);",
                                        "return date.substring(5, date.length());")
                elif file.name == "Properties.java":
                    # 修改默认字体
                    line = line.replace(
                        "public int fontSize = 18;", "public int fontSize = 15;")
                elif file.name == "UtilText.java":
                    # 高版本jdk不再自带nashorn
                    if "import jdk.nashorn" in line:
                        line = "//" + line
                    if "import org.openjdk.nashorn" in line:
                        line = line[2:]
                elif file.name == "AbstractAttribute.java":
                    # Attribute的name同时被用于逻辑和显示，故使用类似的nameAbbreviation暂时替代
                    line = line.replace(
                        "return name;", "return nameAbbreviation;")
                    line = line.replace("return \"<\"+tag+\" style='color:\"+this.getColour().toWebHexString()+\";'>\"+name+\"</\"+tag+\">\";",
                                        "return \"<\"+tag+\" style='color:\"+this.getColour().toWebHexString()+\";'>\"+nameAbbreviation+\"</\"+tag+\">\";")
                elif file.name == "MainController.java":
                    line = line.replace("webviewTooltip.setMaxHeight(height);",
                                        "webviewTooltip.setMaxHeight(height);\n"
                                        + "\t\twebviewTooltip.setPrefHeight(height);")
                    line = line.replace("tooltip.setMaxHeight(height);",
                                        "tooltip.setMaxHeight(height);\n" +
                                        "\t\ttooltip.setPrefHeight(height);")
                elif file.name == "Main.java":
                    # 内置字体导入
                    line = line.replace("protected void loadFonts() {",
                                        "protected void loadFonts() {\n"
                                        + "\t\tif (Font.loadFont(toUri(\"res/fonts/Source Han/SourceHanSansCN-Regular.otf\"), 12) != null) {\n"
                                        + "\t\t\tFont.loadFont(toUri(\"res/fonts/Source Han/SourceHanSansCN-Bold.otf\"), 12);\n"
                                        + "\t\t} else {\n"
                                        + "\t\t\tSystem.err.println(\"Source Han Sans font could not be loaded.\");\n"
                                        + "\t\t}\n"
                                        )
                elif file.name == "Util.java":
                    # 替换intToString为输出阿拉伯数字
                    line = line.replace("public static String intToString(int integer) {",
                                        "public static String intToString(int integer) {\n"
                                        + "\t\tString[] digits = {\"零\",\"一\",\"二\",\"三\",\"四\",\"五\",\"六\",\"七\",\"八\",\"九\"};\n"
                                        + "\t\tString[] caps   = {\"十\",\"百\",\"千\",\"万\",\"十\",\"百\",\"千\",\"亿\",\"十\",\"百\",\"千\"};\n"
                                        + "\t\tStringBuilder sb = new StringBuilder();\n"
                                        + "\t\tString intStr = Integer.toString(integer);\n"
                                        + "\t\tint n = intStr.length();\n"
                                        + "\t\tfor (int i = 0; i < n; i++) {\n"
                                        + "\t\t\tif (intStr.charAt(i) == '-') {\n"
                                        + "\t\t\t\tsb.append(\"负\");\n"
                                        + "\t\t\t\tcontinue;\n"
                                        + "\t\t\t}\n"
                                        + "\t\t\tint num = intStr.charAt(i) - '0';\n"
                                        + "\t\t\tif (num == 0 && sb.charAt(sb.length()-1) == '零') continue;\n"
                                        + "\t\t\tString digit = digits[num];\n"
                                        + "\t\t\tif (num == 2 && n == 1) digit = \"两\";\n"
                                        + "\t\t\tif (i != n - 1 && num != 0) {\n"
                                        + "\t\t\t\tsb.append(digit).append(caps[n - 2 - i]);\n"
                                        + "\t\t\t} else {\n"
                                        + "\t\t\t\tsb.append(digit);\n"
                                        + "\t\t\t}\n"
                                        + "\t\t}\n"
                                        + "\t\tif (sb.charAt(sb.length()-1) == '零') sb.deleteCharAt(sb.length()-1);\n"
                                        + "\t\treturn sb.toString();\n"
                                        + "\t}\n"
                                        + "\tpublic static String intToStringOld(int integer){")
                elif file.name == "Units.java":
                    # 调整日期格式
                    line = line.replace("DateTimeFormatter.ofPattern(Main.getProperties().hasValue(PropertyValue.internationalDate) ? \"dd.MM.yy\" : \"MM/dd/yy\")",
                                        "DateTimeFormatter.ofPattern(Main.getProperties().hasValue(PropertyValue.internationalDate) ? \"yy.MM.dd\" : \"yy.MM.dd\")")
                    line = line.replace("DateTimeFormatter.ofPattern(\"d'%o %m' yyyy\")",
                                        "DateTimeFormatter.ofPattern(\"yyyy年MM月dd日\")")
                    # 调整时间格式
                    line = line.replace("DateTimeFormatter.ofPattern(Main.getProperties().hasValue(PropertyValue.twentyFourHourTime) ? \"HH:mm\" : \"hh:mm a\")",
                                        "DateTimeFormatter.ofPattern(Main.getProperties().hasValue(PropertyValue.twentyFourHourTime) ? \"HH:mm\" : \"hh:mm a\").withLocale(Locale.ENGLISH)")
                elif file.name == "AbstractFluidType.java":
                    # 调整精液前缀判断方法
                    line = line.replace("if(name.endsWith(\"-\")) {",
                                        "if(baseFluidType.getNames().contains(name)) {")
                lines[idx] = line

            with open(file, 'w', encoding='utf-8') as f:
                f.writelines(lines)

    def apply_res(self) -> None:
        original_files = [file for file in self.root.glob("**/*.xml")]
        dict_fils = [self.dict_dir.joinpath(file.relative_to(
            self.root)).with_suffix('.json') for file in original_files]

        for original_file, dict_file in zip(original_files, dict_fils):
            if not dict_file.exists():  # 不存在对应字典文件
                continue

            self.apply_xml(original_file, dict_file)

    def apply_xml(self, original_file: Path, dict_file: Path) -> None:
        with open(dict_file, "r", encoding="utf-8") as f:
            entry_list = json.load(f)

        entry_list = [XmlEntry.from_json(
            original_file, entry) for entry in entry_list]

        parser = etree.XMLParser(strip_cdata=False)

        tree: etree._Element = etree.parse(str(original_file), parser)

        entry_dict: Dict[str, List[XmlEntry]] = {}
        for entry in entry_list:
            if entry_dict.get(entry.node_tag) is None:
                entry_dict[entry.node_tag] = [entry]
            else:
                entry_dict[entry.node_tag].append(entry)

        for tag, entry_cluster in entry_dict.items():
            nodes: List[etree._Element] = list(tree.iter(tag))
            nodes = list(filter(lambda node: valid_element(node), nodes))
            if len(entry_cluster) != len(nodes):
                logger.warning(
                    f"\t****{original_file.relative_to(self.root)}: 节点{tag}数量({len(nodes)})与字典数量({len(entry_cluster)})不匹配")
                continue
            for entry, node in zip(entry_cluster, nodes):
                if len(entry.translation) <= 0 or entry.translation == entry.original:  # 暂无汉化或无需修改
                    continue

                if entry.attribute is not None:
                    node.set(entry.attribute, entry.translation)
                else:
                    node.text = entry.translation.replace("\\n", "\n")
                    node.text = etree.CDATA(node.text)

        tree.write(original_file.as_posix(), encoding="utf-8",
                   xml_declaration=True, pretty_print=True, standalone=False)

    def apply_src(self) -> None:
        original_files = [file for file in self.root.glob("**/*.java")]
        dict_fils = [self.dict_dir.joinpath(file.relative_to(
            self.root)).with_suffix('.json') for file in original_files]

        for original_file, dict_file in zip(original_files, dict_fils):
            if not dict_file.exists():  # 不存在对应字典文件
                continue

            self.apply_java(original_file, dict_file)

    def apply_java(self, original_file: Path, dict_file: Path) -> None:
        with open(dict_file, "r", encoding="utf-8") as f:
            entry_list = json.load(f)
        with open(original_file, "r", encoding="utf-8") as f:
            text = f.readlines()

        entry_list = [CodeEntry.from_json(
            original_file, entry) for entry in entry_list]

        for entry in entry_list:
            line_text = text[entry.line]
            applied_text = self.apply_java_line(
                line_text, entry.original, entry.translation, dict_file, entry.line)
            text[entry.line] = applied_text

        with open(original_file, "w", encoding="utf-8") as f:
            f.writelines(text)

    def apply_java_line(self, text: str, original: str, translation: str, file: Path, line: int) -> str:
        if len(translation) <= 0:
            return text

        # 常见错误检测
        if translation.count("\"") % 2 == 1 and "//" not in translation:
            logger.warning(f"\t****{file.as_posix()}[{line}]:翻译文本有奇数个双引号！")
        if "\\n" in translation:
            logger.warning(f"\t****{file.as_posix()}[{line}]:翻译文本有额外换行符！")
            translation.replace("\\n", "")

        index = text.find(original)
        if index == -1:
            logger.warning("\t****原文本无匹配！")
            return text
        else:
            text = text[:index] + translation + text[index + len(original):]
            return text


if __name__ == "__main__":
    applier = Applier("./liliths-throne-public-dev", "./new_dict")
    applier.apply_special()
