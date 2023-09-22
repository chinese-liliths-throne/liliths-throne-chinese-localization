from dataclasses import dataclass
from typing import Optional, Dict, List
from pathlib import Path


@dataclass
class Entry:
    file: str
    original: str
    translation: str
    stage: int

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
            original=entry_json["original"],
            translation=entry_json["translation"],
            node_tag=entry_json["key"].split('_')[0],
            attribute=entry_json["key"].split('_')[1] if entry_json["key"].split('_')[
                1] != "text" else None,
            stage=entry_json['stage'] if entry_json.get("stage") is not None else 0
        )

    def to_json(self) -> Dict:
        return {
            "key": self.to_id(),
            "original": self.original,
            "translation": self.translation,
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
            original=entry_json["original"],
            translation=entry_json["translation"],
            line=int(entry_json["key"]),
            stage=entry_json['stage'] if entry_json.get("stage") is not None else 0
        )

    def to_json(self) -> Dict:
        return {
            "key": self.to_id(),
            "original": self.original,
            "translation": self.translation,
            "context": ""
        }

    def to_id(self) -> str:
        return str(self.line)


@dataclass
class FilePair:
    original_file: Path
    entry_file: Path
