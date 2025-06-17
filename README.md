# Tag Sync Calibre Plugin

![Calibre](https://img.shields.io/badge/Calibre-8.0.0-green)
![GPL](https://img.shields.io/badge/License-GPL-blue.svg)


Tag Sync is a Calibre plugin that helps you synchronize and manage tags (and custom columns) across your ebook library. It provides advanced tag management, aliasing, and automation features to keep your metadata clean and consistent.

## Features

- **Sync tags** for selected or all books with a single click.
- **Custom column support:** Include any text-based custom columns in tag syncing.
- **Tag aliasing:** Define alternate names for tags.
- **Automatic tag splitting:** Split tags based on patterns (e.g., `alias (add_part)`).
- **Add-tags rule:** Automatically add related tags based on rules.
- **Priority system:** Control which columns take precedence when tags overlap.
- **GUI configuration:** Easily manage settings and tag rules from the Calibre interface.

## Installation

**Option 1: Using the bundled plugin zip**
1. Download the latest bundled plugin zip from the releases.
2. In Calibre, go to `Preferences` > `Plugins` > `Load plugin from file`.
3. Select the `.zip` file containing this plugin.
4. Restart Calibre if required.

**Option 2: Manual installation from source**
1. Download or clone this repository.
2. Run the command `calibre-customize -b .` in the project directory.
3. Restart Calibre if required.

## Usage

- Access the plugin from the Calibre toolbar (`Tag Sync`).
- Use the menu to:
  - Sync tags for selected books.
  - Sync tags for all books.
  - Open the settings dialog to configure columns and tag rules.

Tag Sync will never modify your metadata automatically without your action. However, please note that any metadata changes you make using this plugin are permanent and cannot be undone.

## Configuration

- **Column Choice:** Select which columns to include in tag syncing and set their priority.
- **Tag Details:** Edit tag aliases, add-tags, and splitting behavior.

## File Structure

tag_sync/  
├── [`images/`](images/): Plugin icons.  
├── [`__init__.py`](__init__.py): Plugin entry point for Calibre.  
├── [`action.py`](action.py): Main plugin logic and Calibre integration.  
├── [`config.py`](config.py): GUI configuration and settings management.  
├── [`helper.py`](helper.py): Utility functions and dialog helpers.  
└── [`tag_util.py`](tag_util.py): Tag and rule logic.  

## Credits

- Icons from [flaticon.com](https://www.flaticon.com/), see [`images/sources.txt`](images/sources.txt).

## License

Author: Robert T. Drawe  
This plugin is licensed under the GNU General Public License v3.0 (GPL-3.0).
