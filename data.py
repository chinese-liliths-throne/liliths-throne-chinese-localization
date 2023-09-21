from dataclasses import dataclass
from typing import Optional, Dict, List
from pathlib import Path


@dataclass
class Entry:
    file: str
    original_text: str
    translated_text: str

    def to_json(self) -> dict:
        pass

    def to_id(self) -> str:
        pass


@dataclass
class XmlEntry(Entry):
    node_tag: str
    attribute: Optional[str]

    @staticmethod
    def from_json(file: Path, entry_json: Dict[str, str]) -> "XmlEntry":
        return XmlEntry(
            file=file.as_posix(),
            original_text=entry_json["original"],
            translated_text=entry_json["translation"],
            node_tag=entry_json["key"].split('_')[0],
            attribute=entry_json["key"].split('_')[1] if entry_json["key"].split('_')[
                1] != "text" else None
        )

    def to_json(self) -> Dict:
        return {
            "key": self.to_id(),
            "original": self.original_text,
            "translation": self.translated_text,
            "context": ""
        }

    def to_id(self) -> str:
        return "{}_{}".format(self.node_tag, self.attribute if self.attribute is not None else "text")


@dataclass
class CodeEntry(Entry):
    line: int

    @staticmethod
    def from_json(file: Path, entry_json: Dict[str, str]) -> "CodeEntry":
        return CodeEntry(
            file=file.as_posix(),
            original_text=entry_json["original"],
            translated_text=entry_json["translation"],
            line=int(entry_json["key"])
        )

    def to_json(self) -> Dict:
        return {
            "key": self.to_id(),
            "original": self.original_text,
            "translation": self.translated_text,
            "context": ""
        }

    def to_id(self) -> str:
        return str(self.line)


@dataclass
class FilePair:
    original_file: Path
    entry_file: Path
