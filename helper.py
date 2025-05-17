from . import tag_util
from calibre.db.cache import Cache as DB
from calibre.gui2 import info_dialog, question_dialog, warning_dialog, error_dialog
from calibre.gui2.ui import Main as GUI
from calibre.utils.config import JSONConfig
from dataclasses import asdict
from typing import Optional
import json

def get_db(gui: GUI) -> DB:
    return gui.current_db.new_api


def get_custom_column(gui: GUI) -> dict:
    return gui.library_view.model().custom_columns


def get_selected_columns(gui: GUI) -> list:
    column_names: list = list(get_custom_column(gui).keys())

    column_names.append('tags')

    prefs = JSONConfig('plugins/tag_sync')
    return [name for name in column_names if name in prefs['column_list']]


def get_all_field_values(db: DB, field_name: str) -> list[(int, str)]:
    id_map = db.fields[field_name].table.id_map
    fields = [(id, id_map[id]) for id in db.fields[field_name]]
    return fields


def test(gui: GUI):
    tag_rules = tag_util.TagRules.build_tag_rules(gui)

    test_value = asdict(tag_rules)

    Dialog.get().info('json output', f'{type(test_value)}', f'{json.dumps(test_value, indent=4)}')


class Dialog:
    _instance = None

    def __init__(self, gui: GUI):
        self.gui = gui

    def info(self, title:str, msg: str, detail_msg: Optional[str]=None):
        if detail_msg:
            info_dialog(self.gui, title, msg, detail_msg, show=True, only_copy_details=True)
        else:
            info_dialog(self.gui, title, msg, show=True)

    def question(self, title:str, msg: str, detail_msg: Optional[str]=None):
        if detail_msg:
            question_dialog(self.gui, title, msg, detail_msg, show=True, only_copy_details=True)
        else:
            question_dialog(self.gui, title, msg, show=True)

    def warning(self, title:str, msg: str, detail_msg: Optional[str]=None):
        if detail_msg:
            warning_dialog(self.gui, title, msg, detail_msg, show=True, only_copy_details=True)
        else:
            warning_dialog(self.gui, title, msg, show=True)

    def error(self, title:str, msg: str, detail_msg: Optional[str]=None):
        if detail_msg:
            error_dialog(self.gui, title, msg, detail_msg, show=True, only_copy_details=True)
        else:
            error_dialog(self.gui, title, msg, show=True)

    @classmethod
    def get(cls):
        if not cls._instance:
            raise RuntimeError('Gloabl Dialog does not exists')

        return cls._instance

    @classmethod
    def create(cls, gui: GUI):
        if not cls._instance:
            cls._instance = Dialog(gui)
