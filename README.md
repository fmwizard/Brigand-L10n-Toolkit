# Brigand Localization Toolkit

This repository contains tools to streamline the localization process for the game Brigand. It includes scripts to extract original text, organize it for translation, and re-import translations into the game files with minimal effort and maximum accuracy.

## Prerequisites

- [Python 3.x](https://www.python.org/) and basic knowledge of running Python scripts via the command line.

## Setup

Before starting:
1. Create a new folder as your working directory, and copy extract.py and import.py into this directory. (Or if you're familiar with git, directly clone this repo to your local)
2. Copy the Assets and Stories folders from the game's root directory (...\steamapps\common\Brigand) into your working directory.
   - The Assets folder will be used as the source for extraction
   - In Assets, remove any language versions you don't need to translate (e.g., folders ending with "(RU)" for Russian, "(ES)" for Spanish, etc.), but don't touch with other original versions
3. From the remaining folders in Assets, copy all story-related txt files (e.g., "BRIGAND - OAXACA\BRIGAND - OAXACA.txt") to the Stories folder in your working directory
4. This is an extra step due to a minor issue in the game’s source files. To ensure the localization program runs correctly, a manual adjustment is required. In the file "Assets\BRIGAND - PANAMA\Objects\text\textUse.bsl" (you can ignore this step if you don't have BRIGAND - PANAMA), on line 119, there is an invalid character between "altwin=The Ancient Mariner," and "Water, water, every where,/r". Replace this invalid character with a standard English quotation mark ("), then save the file in UTF-8 format. (This step would be removed if this issue is fixed later)
```
working_directory/
├── extract.py
├── import.py
├── Assets/      (copied from game root)
└── Stories/     (copied from game root)
```

## Usage

### Step 1: Text Extraction

1. Run the extraction script:
   ```bash
   python extract.py
   ```
2. A new `Extracted` folder will be created containing JSON files with the original text. I also put a small excerpt of an extracted JSON in this repo. You can use it as a sample to see how it works.

### Step 2: Translation

Fill in the "translation" field for each JSON entry. We recommend using the [ParaTranz](https://paratranz.cn/projects) platform for more convenient translation, but it's optional:
   - Create a new project on ParaTranz
   - Upload the extracted JSON files
   - Use the platform's visual UI for translation
   - The platform helps prevent formatting errors during editing

### Step 3: Importing Translations

1. Create a new folder in your working directory
2. Place all translated JSON files in this folder
3. Run the import script with the following parameters:
   ```bash
   python import.py --encoding [target_encoding] --dir [translation_folder]
   ```
   Example:
   ```bash
   python import.py --encoding gb2312 --dir chinese_translation
   ```

### Step 4: Testing Translations

After importing, you'll find an `Output` folder containing the translated `Assets` and `Stories` folders. You have two options for testing your translations:

#### Option 1: Direct Overwrite (Quick)
1. **IMPORTANT**: Back up your game's original `Assets`, `Stories`, and `Saves` folders in the game root directory
2. Copy and overwrite the contents of the `Output` folder to your game root directory
3. Run the launcher and select your language charset
4. If you want to restore overwritten files later, use the backups (**REMEMBER TO BACK UP!!!**)

#### Option 2: Create New Story (Stable)
Follow the developer's translation guide to create a new Story using the contents of the `Output` folder.

## Notes

- Always backup your game files before overwriting
- Make sure to use the correct encoding for your target language (e.g., gb2312 for Chinese)
- As the localization project is still ongoing, there may be potential bugs that have not yet been addressed. This repository will be updated periodically to fix issues or introduce new features. In addition, the current version of extract.py does not extract all in-game text considering the progress of our translation team. You are welcome to modify the script to meet your specific needs.

## Support

If you encounter any issues or need assistance, please:
1. Check the [Issues](../../issues) section
2. Create a new issue with detailed information about your problem