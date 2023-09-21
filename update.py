from pathlib import Path
from typing import List, Dict
import json


def update_dict(old_dict_path: Path, new_dict_path: Path):
	# 获取所有json文件
	new_dict_files: List[Path] = list(new_dict_path.glob('**/*.json'))

	file_pairs = [
		(new_dict_file, old_dict_path / new_dict_file.relative_to(new_dict_path))
		for new_dict_file in new_dict_files
		if (old_dict_path / new_dict_file.relative_to(new_dict_path)).exists()
	] # 无视旧文件中不存在的文件

	for new_dict_file, old_dict_file in file_pairs:
		update_dict_file(new_dict_file, old_dict_file)
		

def update_dict_file(old_dict_file: Path, new_dict_file: Path):
	with open(new_dict_file, 'r') as new_dict:
		new_dict_data : List[Dict] = json.load(new_dict)
	with open(old_dict_file, 'r') as old_dict:
		old_dict_data : List[Dict] = json.load(old_dict)

	new_dict_map: Dict[str, List[int]] = {}
	old_dict_map: Dict[str, List[int]] = {}

	for idx, data in enumerate(new_dict_data):
		if not new_dict_map.get(data["original"]):
			new_dict_map[data["original"]] = [idx]
		else:
			new_dict_map[data["original"]].append(idx)
	
	for idx, data in enumerate(old_dict_data):
		if data["translation"] != "": # 旧字典无汉化
			continue
		if not old_dict_map.get(data["original"]):
			old_dict_map[data["original"]] = [idx]
		else:
			old_dict_map[data["original"]].append(idx)

	for key, value in old_dict_map.items():
		with new_dict_map.get(key) as new_idx_list:
			if new_idx_list is not None:
				for idx, old_idx in enumerate(value[:min(len(value), len(new_idx_list))]):
					new_dict_data[new_idx_list[idx]]["translation"] = old_dict_data[old_idx]["translation"]

	with open(new_dict_file, 'w') as new_dict:
		json.dump(new_dict_data, new_dict, indent=4, ensure_ascii=False)