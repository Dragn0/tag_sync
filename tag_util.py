from . import config, helper
from calibre.db.cache import Cache as DB
from calibre.ebooks.metadata.book.base import Metadata
from calibre.gui2.ui import Main as GUI
from dataclasses import dataclass
from typing import Self, Optional
import json
from dataclasses import asdict

@dataclass
class Tag:
    id             : Optional[int]
    collection_name: str
    display_name   : str
    name           : str
    name_aliases   : list[str]
    add_tags       : list[str]

    def __init__(self, display_name: str, collection: str, id: Optional[int]):
        self.id             : Optional[int] = id
        self.collection_name: str           = collection
        self.display_name   : str           = display_name
        self.name           : str           = display_name.lower()
        self.name_aliases   : list[str]     = list()
        self.add_tags       : list[str]     = list()

    def is_part_of_sub_collection(self) -> bool:
        return self.collection_name != 'tags'

    def get_descriptor(self):
        return f'{self.collection_name}:{self.id}'

    @classmethod
    def build_tags(cls, gui: GUI) -> list[Self]:
        db = helper.get_db(gui)

        results: list[Self] = list()

        column_settings = config.prefs.get('columns', dict())
        tag_settigns = config.prefs.get('tags', dict())

        #* Get the list of custom columns
        columns = helper.get_selected_columns(gui)
        for column in columns:
            column_values = helper.get_all_field_values(db, column)
            for value_id, value_name in column_values:
                tag = Tag(value_name, column, value_id)

                tag.prio = column_settings.get(column, dict()).get('prio', 1)

                #* Load data from Settings
                for tag_setting_descriptor, tag_settings_data in tag_settigns.items():
                    if tag.get_descriptor == tag_setting_descriptor or tag.name == tag_settings_data.get('name', ''):
                        for name_alias in tag_settings_data.get('name_aliases', list()):
                            if not name_alias in tag.name_aliases:
                                tag.name_aliases.append(name_alias)

                        for add_tag in tag_settings_data.get('add_tags', list()):
                            if not add_tag in tag.add_tags:
                                tag.add_tags.append(add_tag)

                #* Find duplicates
                duplicate_found = False
                for result in results:
                    if tag.name == result.name:
                        #* Duplicate found
                        if tag.prio > result.prio:
                            results.remove(result)
                            results.append(tag)

                        duplicate_found = True
                        break

                if not duplicate_found:
                    results.append(tag)

        return results

@dataclass
class TagRules:
    tags: dict[str, Tag]

    def __init__(self):
        self.tags: dict[str, Tag] = dict()

    def apply_to_book(self, book: Metadata) -> Metadata:
        columns = config.prefs['columns']

        #* Get the list of all tags on the book
        current_display_tags: list[str] = list()
        for column_name in columns:
            current_display_tags.extend(book.get(column_name, []))

        #* Convert the current display tags to the compareable format
        current_tags: list = [current_display_tag.lower() for current_display_tag in current_display_tags]

        #* Apply the alias restriction
        tags_to_remove = list()
        for current_tag in current_tags:
            for tag in self.tags.values():
                if current_tag in tag.name_aliases:
                    tags_to_remove.append(current_tag)

                    if tag.name not in current_tag:
                        current_tags.append(tag.name)
                    break

        current_tags = [current_tag for current_tag in current_tags if current_tag not in tags_to_remove]

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
            if len(value) <= 0:
                value.append('') #* An empty array dosent overwrite for some rason
                book.set(key, value)
            else:
                book.set(key, value)

        #* Return the book
        return book

    @classmethod
    def build_tag_rules(cls, gui: GUI) -> Self:
        tag_rules = TagRules()
        tags = Tag.build_tags(gui)

        for tag in tags:
            tag_rules.tags[tag.name] = tag

        return tag_rules

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
            new_tag = Tag(add_tag_display_name, tag.collection_name, None)
            tag_rules.tags[new_tag.name] = new_tag

            #* Add new tag to add_list
            if new_tag.name not in add_list:
                add_list.append(new_tag.name)
