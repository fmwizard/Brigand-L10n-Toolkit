import os, re, json
from typing import Set, List
from pathlib import Path
from dataclasses import dataclass

@dataclass
class LocalizationEntry:
    """Data class for localization JSON entry"""
    key: str
    original: str
    translation: str
    context: str
class TextExtractor:
    def __init__(
        self,
        root_dir: str = "Assets",
        output_dir: str = "Extracted"
    ):
        self.root_dir = root_dir
        self.output_dir = output_dir

        # Translation settings
        self.translation_commands = [
            "desc", "window", "altwin", "editwin",
            "leftwin", "silentwin", "inputwin", "choice"
        ]
        self.name_commands = ["name", "if_name", "pickname"]
        
        self.pattern_globals = re.compile(r"^(.*?(NAME|DESC|TIP))=(.*?)(?:,(.*))?$")
        self.pattern_standard = re.compile(r'^\s*(.*?)=(.*)$')
    
    def is_extractable_assignment(self, before_part: str, after_part: str):
        """Check if the assignment is extractable"""
        return before_part.lower() in self.translation_commands or (
            before_part in self.name_commands and after_part not in ["none", "response"]
        )

    def extract_entry(
        self,
        line: str,
        file_path: str,
        line_num: int,
        lines: List[str],
        is_global: bool
    ):
        pattern = self.pattern_globals if is_global else self.pattern_standard
        match = pattern.match(line)

        entry = []
        if not match:
            return []
        
        if is_global:
            before_part = match.group(3)
            after_part = match.group(4)
            key = f"{file_path}--line: {line_num}"     
            original = after_part.strip() if after_part else before_part.strip()
            translation = ""
            context = self.get_context(lines, line_num)
            entry.append(LocalizationEntry(key, original, translation, context))
        else:
            before_part = match.group(1).strip()
            after_part = match.group(2).strip()
            if self.is_extractable_assignment(before_part, after_part):
                sub_parts = after_part.split(",", 1)
                for i, part in enumerate(sub_parts):
                    normalized_part = part.strip()
                    if normalized_part.isnumeric():
                        continue
                    key = f"{file_path}--line: {line_num}--part: {i}"
                    original = normalized_part
                    translation = ""
                    context = self.get_context(lines, line_num)
                    entry.append(LocalizationEntry(key, original, translation, context))
        return entry

    def get_context(self, lines: List[str], i: int):
        i = i - 1
        prev_line = lines[i - 1] if i > 0 else ""
        next_line = lines[i + 1] if i < len(lines) - 1 else ""
        return f"previous line: {prev_line.strip()}\ncurrent line: {lines[i].strip()}\nnext line: {next_line.strip()}"

    def extract_file(
        self, 
        file_path: str,
        global_entries: List,
        object_entries: List,
        window_entries: List
    ):
    
        with open(file_path, 'r') as f:
            lines = f.readlines()

        is_global = "globals.bsl" in file_path

        for i, line in enumerate(lines, 1):
            entry = self.extract_entry(line, file_path, i, lines, is_global)
            if len(entry) > 0:
                if is_global:
                    global_entries.extend(entry)
                else:
                    m = re.search(r"current line:\s*(.*?)=", entry[0].context)
                    if m and any(x in m.group(1) for x in ["name", "desc"]):
                        object_entries.extend(entry)
                    else:
                        window_entries.extend(entry)

    def write_json(self, entries: List[LocalizationEntry], output_file: str):
        with open(output_file, 'w') as f:
            json.dump([entry.__dict__ for entry in entries], f, indent=4)
        
    def deduplicate_entries(self, entries: List[LocalizationEntry]):
        """Deduplicate entries"""
        seen = set()
        deduplicated = []
        for entry in entries:
            if entry.original not in seen:
                deduplicated.append(entry)
                seen.add(entry.original)
        return deduplicated
    
    def extract_files(self):
        """Extract text from all BSL files"""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            extracted_globals = []
            extracted_objects = []
            extracted_windows = []


            for subdir, _, files in os.walk(self.root_dir):
                for file in files:
                    if file.endswith('.bsl'):
                        file_path = os.path.join(subdir, file)
                        self.extract_file(file_path, extracted_globals, extracted_objects, extracted_windows)
            
            extracted_globals = self.deduplicate_entries(extracted_globals)
            extracted_objects = self.deduplicate_entries(extracted_objects)
            extracted_windows = self.deduplicate_entries(extracted_windows)
                    
            self.write_json(extracted_globals, os.path.join(self.output_dir, "globals.json"))
            self.write_json(extracted_objects, os.path.join(self.output_dir, "objects.json"))
            self.write_json(extracted_windows, os.path.join(self.output_dir, "windows.json"))
        except Exception as e:
            print(f"An error occurred: {e}, exiting...")
        
def main():
    extractor = TextExtractor()
    extractor.extract_files()

if __name__ == "__main__":
    main()



