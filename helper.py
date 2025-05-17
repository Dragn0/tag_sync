from . import config
from calibre.db.cache import Cache as DB
from calibre.gui2 import info_dialog, question_dialog, warning_dialog, error_dialog
from calibre.gui2.ui import Main as GUI
from typing import Optional

def get_db(gui: GUI) -> DB:
    return gui.current_db.new_api


def get_custom_column(gui: GUI) -> dict:
    return gui.library_view.model().custom_columns


def get_selected_columns(gui: GUI) -> list:
    column_names: list = list(get_custom_column(gui).keys())

    column_names.append('tags')

    return [name for name in column_names if name in config.prefs.get('columns', dict())]


def get_all_field_values(db: DB, field_name: str) -> list[(int, str)]:
    id_map = db.fields[field_name].table.id_map
    fields = [(id, id_map[id]) for id in db.fields[field_name]]
    return fields


class Dialog:
    _instance = None

    def __init__(self, gui: GUI):
        self.gui = gui

    def info(self, title:str, msg: str, detail_msg: Optional[str]=None):
        if detail_msg:
            return info_dialog(self.gui, title, msg, detail_msg, show=True, only_copy_details=True)
        else:
            return info_dialog(self.gui, title, msg, show=True)

    def question(self, title:str, msg: str, detail_msg: Optional[str]=None):
        if detail_msg:
            return question_dialog(self.gui, title, msg, detail_msg)
        else:
            return question_dialog(self.gui, title, msg)

    def warning(self, title:str, msg: str, detail_msg: Optional[str]=None):
        if detail_msg:
            return warning_dialog(self.gui, title, msg, detail_msg, show=True, only_copy_details=True)
        else:
            return warning_dialog(self.gui, title, msg, show=True)

    def error(self, title:str, msg: str, detail_msg: Optional[str]=None):
        if detail_msg:
            return error_dialog(self.gui, title, msg, detail_msg, show=True, only_copy_details=True)
        else:
            return error_dialog(self.gui, title, msg, show=True)

    @classmethod
    def get(cls):
        if not cls._instance:
            raise RuntimeError('Gloabl Dialog does not exists')

        return cls._instance

    @classmethod
    def create(cls, gui: GUI):
        if not cls._instance:
            cls._instance = Dialog(gui)
