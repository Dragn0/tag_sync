from calibre.db.cache import Cache as DB
from calibre.ebooks.metadata.book.base import Metadata
from calibre.gui2 import info_dialog, question_dialog, warning_dialog
from calibre.gui2.ui import Main as GUI
from calibre.utils.config import JSONConfig
from dataclasses import asdict, dataclass
from typing import Self
import json

@dataclass
class Tag:
    collection_name: str
    display_name      : str
    name              : str
    name_aliases      : list[str]
    add_tags          : list[str]

    def __init__(self, display_name: str, collection: str):
        self.collection_name: str          = collection
        self.display_name      : str       = display_name
        self.name              : str       = display_name.lower()
        self.name_aliases      : list[str] = list()
        self.add_tags          : list[str] = list()

    def is_part_of_sub_collection(self) -> bool:
        return self.collection_name != 'tags'

    @classmethod
    def build_tags(cls, db: DB) -> list[Self]:
        result = list()
        prefs = JSONConfig('plugins/tag_sync')
        tag_settigns = prefs.get('tags', dict())

        #* Get the list of custom columns
        columns = prefs['column_list']
        for column in columns:
            column_values = db.all_field_names(column)
            for column_value in column_values:
                tag = Tag(column_value, column)

                for name_alias in tag_settigns.get(column_value, dict()).get('name_aliases', list()):
                    tag.name_aliases.append(name_alias)

                for add_tag in tag_settigns.get(column_value, dict()).get('add_tags', list()):
                    tag.add_tags.append(add_tag)

                result.append(tag)

        return result

@dataclass
class TagRules:
    tags: dict[str, Tag]

    def __init__(self):
        self.tags: dict[str, Tag] = dict()

    def add_tag(self, tag_display_name: str, collection: str) -> bool:
        tag_name = tag_display_name.lower()

        #* Check if the Tag already exists
        for tag in self.tags.values():
            if tag_name == tag.name:
                #* Check if the tag should overwrite the basic collection
                if collection != 'tags' and not self.tags[tag_name].is_part_of_sub_collection():
                    self.tags[tag_name].collection_name = collection
                    return True

                raise ValueError(f'The tag \'{tag_display_name}\' exists in multiple sub collections: \'{tag.collection_name}\' and \'{collection}\'.')

        #* Check if the Tag is already an alias
        for tag in self.tags.values():
            if tag_name in tag.name_aliases:
                return False

        self.tags[tag_name] = Tag(tag_display_name, collection)
        return True

    def apply_to_book(self, book: Metadata) -> Metadata:
        prefs = JSONConfig('plugins/tag_sync')

        columns = prefs['column_list']

        #* Get the list of all tags on the book
        current_display_tags: list[str] = book.tags

        for column_name in columns:
            current_display_tags.extend(book.get(column_name, []))

        #* Convert the current display tags to the compareable format
        current_tags: list = [current_display_tag.lower() for current_display_tag in current_display_tags]

        #* Apply the alias restriction
        for current_tag in current_tags:
            for tag in self.tags.values():
                if current_tag in tag.name_aliases:
                    current_tags.remove(current_tag)

                    if tag.name not in current_tags:
                        current_tags.append(tag.name)
                    break


        #* Build the tag dict ordered by collection
        ordered_tags = dict()
        ordered_tags['tags'] = list()
        for column_name in columns:
            ordered_tags[column_name] = list()

        for current_tag in current_tags:
            tag_obj = self.tags[current_tag]
            ordered_tags[tag_obj.collection_name].append(tag_obj.display_name)

        #* Apply the orderd tags to the book
        for key, value in ordered_tags.items():
            book.set(key, value)

        #* Return the book
        return book

    @classmethod
    def build_tag_rules(cls, db: DB) -> Self:
        prefs = JSONConfig('plugins/tag_sync')

        tag_rules = TagRules()

        #* Get the list of base tags and add all to the tag rules
        tag_values = db.all_field_names('tags')
        for tag_value in tag_values:
            tag_rules.add_tag(tag_value, 'tags')

        #* Get the list of custom columns and add all values to the tag rules
        columns = prefs['column_list']
        for column in columns:
            column_values = db.all_field_names(column)
            for column_value in column_values:
                tag_rules.add_tag(column_value, column)

        return tag_rules


def test(gui: GUI):
    db = get_db(gui)

    tag_rules = TagRules.build_tag_rules(db)


    test_value = asdict(tag_rules)


    info_dialog(gui, 'json output', f'{type(test_value)}', f'{json.dumps(test_value, indent=4)}', show=True, only_copy_details=True)

def get_custom_column(gui: GUI) -> dict:
    return gui.library_view.model().custom_columns

def get_db(gui: GUI) -> DB:
    return gui.current_db.new_api
