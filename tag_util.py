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
        result: list[Self] = list()
        prefs = JSONConfig('plugins/tag_sync')
        tag_settigns = prefs.get('tags', dict())

        #* Get the list of custom columns
        columns = prefs['column_list']
        for column in columns:
            column_values = db.all_field_names(column)
            for column_value in column_values:
                tag = Tag(column_value, column)

                for name_alias in tag_settigns.get(tag.name, dict()).get('name_aliases', list()):
                    tag.name_aliases.append(name_alias)

                for add_tag in tag_settigns.get(tag.name, dict()).get('add_tags', list()):
                    tag.add_tags.append(add_tag)

                result.append(tag)

        return result

@dataclass
class TagRules:
    tags: dict[str, Tag]

    def __init__(self):
        self.tags: dict[str, Tag] = dict()

    def apply_to_book(self, book: Metadata) -> Metadata:
        prefs = JSONConfig('plugins/tag_sync')

        columns = prefs['column_list']

        #* Get the list of all tags on the book
        current_display_tags: list[str] = list()
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

        #* Apply the add tags rule
        tags_to_add = list()
        for current_tag in current_tags:
            current_tags_obj = self.tags[current_tag]
            add_add_tags_recursive(self, current_tags_obj, tags_to_add)

        for tags_to_add in tags_to_add:
            if not tags_to_add in current_tags:
                current_tags.append(tags_to_add)

        #* Build the tag dict ordered by collection
        ordered_tags = dict()

        #* create the column lists
        for column_name in columns:
            ordered_tags[column_name] = list()

        #* Add the tags to the column lists
        for current_tag in current_tags:
            tag_obj = self.tags.get(current_tag, None)
            if tag_obj:
                ordered_tags[tag_obj.collection_name].append(tag_obj.display_name)
            else:
                raise RuntimeError(f'Tag object with name \'{current_tag}\' not found')

        #* Apply the orderd tags to the book
        for key, value in ordered_tags.items():
            book.set(key, value)

        #* Return the book
        return book

    @classmethod
    def build_tag_rules(cls, db: DB) -> Self:
        tag_rules = TagRules()
        tags = Tag.build_tags(db)

        for tag in tags:
            tag_rules.tags[tag.name] = tag

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

def add_add_tags_recursive(tag_rules: TagRules, tag: Tag, add_list: list[str], max_recursion: int = 30):
    if max_recursion <= 0:
        raise RecursionError()

    #* For all add tags
    for add_tag_display_name in tag.add_tags:
        add_tag_name = add_tag_display_name.lower()
        tag_found = False

        #* For all tag object of the tag_rules
        for find_tag in tag_rules.tags.values():
            #* Test if the current tag is the right one
            if add_tag_name == find_tag.name or add_tag_name in find_tag.name_aliases:

                #* Add found tag to add_list
                if find_tag.name not in add_list:
                    add_list.append(find_tag.name)
                    add_add_tags_recursive(tag_rules, find_tag, add_list, max_recursion - 1) #* Recursion
                    tag_found = True
                    break

        if not tag_found:
            #* Create new tag in the collection of the parent tag
            new_tag = Tag(add_tag_display_name, tag.collection_name)
            tag_rules.tags[new_tag.name] = new_tag

            #* Add new tag to add_list
            if new_tag.name not in add_list:
                add_list.append(new_tag.name)
