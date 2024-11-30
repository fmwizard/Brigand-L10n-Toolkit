import os, json, re
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import argparse, shutil
class LocalizationProcessor:
    def __init__(self, encoding='gb2312', trans_dir='utf8'):
        self.encoding = encoding
        self.trans_dir = trans_dir
        self.asset_dir = 'Assets'
        self.story_dir = 'Stories'
        self.translations, self.lower_translations = self.load_translations()
        self.combined_regex = self.create_regex_pattern()

    
    def sorted_translations(self):
        """Sort translations by length in descending order"""
        return sorted(self.translations.items(), key=lambda x: len(x[0]), reverse=True)
    
    def chunk_translation(self, translation, chunk_size=24):
        """Chunk translation into lines of a certain length to avoid the issue of automatic line breaking"""
        if '/r' in translation:
            t = translation.split('/r')
            return '/r'.join([self.chunk_translation(i, chunk_size) for i in t])
        return '/r'.join([translation[i:i + chunk_size] for i in range(0, len(translation), chunk_size)])

    def create_regex_pattern(self):
        """Create a combined regular expression pattern"""
        prefix = (
            r"(?<![A-Za-z\\])"           # Ensure original is not preceded by a letter
            r"(?<!(?i:skin)=)"                 # Ensure original is not preceded by "skin="
            r"(?<!(?i:icon)=)"                 # Ensure original is not preceded by "icon="
            r"(?<!(?i:scene)=)"                # Ensure original is not preceded by "scene="
            r"(?<!(?i:playsound)=)"            # Ensure original is not preceded by "playsound="
            r"(?<!(?i:give)=)"
            r"(?<!(?i:make)=)"
            r"(?<!(?i:mapsky)=)"
            #r"(?<!(?i:map)=)"
            r"(?<!_)"                     # Ensure original is not preceded by "_"
            r"(?<!(?i:steam)=)"
            r"(?<!(?i:script)=)"             # Ensure original is not preceded by "callscript="
        )

        suffix = (
            r"(?![A-Za-z=\\])"           # Ensure original is not followed by a letter
            r"(?!\.bmp)"                  # Ensure original is not followed by ".bmp"
            r"(?!\d)"                   # Ensure original is not followed by a digit
        )
        patterns = "|".join(re.escape(original) for original, _ in self.sorted_translations())
        combined_regex = prefix + r"(" + patterns + r")" + suffix
        return re.compile(combined_regex, flags=re.IGNORECASE)
    
    def load_translations(self):
        """Load translations from JSON file"""
        translations = {}
        lower_translations = {}
        for subdir, _, files in os.walk(self.trans_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(subdir, file)
                    data = None
                    try:
                        with open(file_path, 'r', encoding=self.encoding) as f:
                            data = json.load(f)
                    except UnicodeDecodeError as e:
                        # Directly read the file and write it back to fix encoding errors
                        print(f"Not matched with the target {self.encoding} for {file_path}, attempting to fix...")

                        backup_path = file_path + ".bak"
                        shutil.copy(file_path, backup_path)
                        print(f"Fixing might change the original JSON file, so backup created for it: {backup_path}")
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = f.read()
                            
                            with open(file_path, 'w', encoding=self.encoding, errors='ignore') as f:
                                f.write(data)
                        
                            with open(file_path, 'r', encoding=self.encoding) as f:
                                data = json.load(f)
                        except UnicodeDecodeError as e:
                            print(f"Encoding error loading {file_path}, please check if the file encoding is correct.")
                            raise e

                    if data is None:
                        raise ValueError(f"Due to error loading {file_path}, the process cannot continue.")
                    for entry in data:
                        original, translation = entry['original'], entry['translation']
                        if (original.lower() in ['none', 'response']) or len(translation) == 0:
                            continue

                        # The length of chunked translations (24 characters) is suitable for Chinese, you may need to adjust it for other languages
                        if self.encoding == 'gb2312':
                            if "objects" in file_path or "windows" in file_path:
                                translation = self.chunk_translation(translation)
                            elif "globals" in file_path:
                                if "current line: TIP=" not in entry["context"]:
                                    translation = self.chunk_translation(translation)
                        translations[original] = translation
                        lower_translations[original.lower()] = translation
        return translations, lower_translations
    
    def replace_translation(self, match):
        """Replace the translation"""
        original = match.group(1).lower()
        translation = self.lower_translations.get(original, "not found")
        if translation == "not found":
            print(f"Translation not found: {original}")
        return translation
    
    def process_file(self, file_info, sorted_translations):
        """Process the translation of a single file"""
        src_path, base_path = file_info
        try:
            if src_path.endswith('.bsl'):
                with open(src_path, 'r', encoding=self.encoding) as f:
                    content = f.read()
                content = self.combined_regex.sub(self.replace_translation, content)
                output_path = os.path.join("Output", base_path)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                with open(output_path, "w", encoding=self.encoding) as file:
                    file.write(content)
            else:
                with open(src_path, 'rb') as f:
                    file_data = f.read()
                for original, translation in sorted_translations:
                    original_bytes = original.encode('windows-1252')
                    translation_bytes = translation.encode(self.encoding)
                    #file_data = file_data.replace(original.encode('windows-1252'), translation.encode(self.encoding))
                    start = 0
                    while True:
                        index = file_data.find(original_bytes, start)
                        if index == -1:
                            break
                        before_valid = (index == 0 or (not chr(file_data[index - 1]).isalnum() and file_data[index - 1] != ord('=')))
                        after_valid = ((index + len(original_bytes) == len(file_data)) 
                                       or (not chr(file_data[index + len(original_bytes)]).isalnum() and file_data[index + len(original_bytes)] != ord('=')))
                        if before_valid and after_valid:
                            file_data = file_data[:index] + translation_bytes + file_data[index + len(original_bytes):]
                            start = index + len(translation_bytes)
                        else:
                            start = index + len(original_bytes)
                output_path = os.path.join("Output", base_path[:-4] + ".gam")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as file:
                    file.write(file_data)
            return True, src_path
        except Exception as e:
            return False, f"Error processing {src_path}: {e}"
    
    def process_files(self):
        """Process all files in the asset and story directories parallelly"""
        files_to_process = []
        for subdir, _, files in os.walk(self.asset_dir):
            for file in files:
                if file.endswith('.bsl'):
                    file_path = os.path.join(subdir, file)
                    files_to_process.append((file_path, file_path))

        for subdir, _, files in os.walk(self.story_dir):
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(subdir, file)
                    files_to_process.append((file_path, file_path))
        print(f"Importing translations into {len(files_to_process)} files...Please wait until the process is complete...")

        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            results = list(executor.map(partial(self.process_file, sorted_translations=self.sorted_translations()), files_to_process))
        
        successful = 0
        failed = 0
        for success, message in results:
            if success:
                successful += 1
            else:
                failed += 1
                print(message)
        print(f"Processed {successful} files successfully, {failed} files failed.")

def main():
    parser = argparse.ArgumentParser(description="Localization Script for Brigand")
    parser.add_argument("--encoding", default="gb2312", help="Encoding of the target language")
    parser.add_argument("--dir", default="utf8", help="Directory containing translation files")
    args = parser.parse_args()
    processor = LocalizationProcessor(encoding=args.encoding, trans_dir=args.dir)
    processor.process_files()

if __name__ == "__main__":
    main()