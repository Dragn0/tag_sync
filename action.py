from . import tag_util
from calibre.gui2 import info_dialog, question_dialog, warning_dialog
from calibre.gui2.actions import InterfaceAction
from calibre.utils.config import JSONConfig
from qt.core import QToolButton, QMenu
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def str_iter_compare(value, iter):
    for iter_value in iter:
        if value.lower() == iter_value.lower():
            return iter_value  #* Return the matching value from the list
    return None  #* Return None if no match is found

class TagSyncPlugin(InterfaceAction):
    name = 'Tag Sync'

    #* Declare the main action associated with this plugin
    #* The keyboard shortcut can be None if you don't want to use a keyboard
    #* shortcut. Remember that currently calibre has no central management for
    #* keyboard shortcuts, so try to use an unusual/unused shortcut.
    action_spec = ('Tag Sync', None, 'Run Tag Sync for selected books', None)
    action_type = 'local'

    #* Settings for this plugin
    #* This is where all preferences for this plugin will be stored
    prefs = JSONConfig('plugins/tag_sync')

    def genesis(self):
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)

        icon = get_icons('images/label.png', 'Tag Sync')
        self.qaction.setIcon(icon)

        self.qaction.triggered.connect(self.sync_for_selected_books)
        self.create_menu_action(self.menu, "Tag Sync selected", "Tag Sync selected", icon=None, shortcut=None, description='Run Tag Sync for selected books', triggered=self.sync_for_selected_books, shortcut_name=None, persist_shortcut=False)
        self.create_menu_action(self.menu, "Tag Sync All", "Tag Sync All", icon=None, shortcut=None, description='Run Tag Sync for all books', triggered=self.sync_for_all_books, shortcut_name=None, persist_shortcut=False)
        self.create_menu_action(self.menu, "Tag Sync settings", "Tag Sync settings", icon=None, shortcut=None, description=None, triggered=lambda: self.interface_action_base_plugin.do_user_config(self.gui), shortcut_name=None, persist_shortcut=False)
        self.create_menu_action(self.menu, "Test", "Test", icon=None, shortcut=None, description=None, triggered=lambda: tag_util.test(self.gui), shortcut_name=None, persist_shortcut=False)

    def apply_settings(self):
        #* Reset the prefs variable to the new settings
        #* This is necessary to ensure that the new settings are used
        self.prefs = JSONConfig('plugins/tag_sync')

    def sync_for_selected_books(self):
        #* Get the selected books from the library view
        selected_books = self.gui.library_view.get_selected_ids()

        self.tag_sync(selected_books)

    def sync_for_all_books(self):
        #* Get the current database
        db = self.gui.current_db.new_api

        #* Get all books from the library
        selected_books = db.all_book_ids()

        self.tag_sync(selected_books)

    def tag_sync(self, selected_books: list):
        db = tag_util.get_db(self.gui)

        #* If no books are selected, show a warning
        if not selected_books:
            warning_dialog(self.gui, _('No Books Selected'), _('Please select books to apply the tag.'), show=True)
            return

        tag_rules = tag_util.TagRules.build_tag_rules(self.gui)

        for book_id in selected_books:
            book = db.get_metadata(book_id)
            book = tag_rules.apply_to_book(book)
            db.set_metadata(book_id, book)

        info_dialog(self.gui, _('Tag Sync'), _('Tag Sync completed successfully.'), show=True)

    def get_all_elements_from_custom_column(self, custom_column_name: str) -> set:
        #* Check if the custom column exists and is of type 'text'
        custom_column = self.gui.library_view.model().custom_columns.get(custom_column_name)

        if not custom_column:
            raise ValueError(f'The custom column \'{custom_column_name}\' doesn\'t exist.')

        custom_column_type = custom_column['datatype']

        if custom_column_type != 'text':
            raise ValueError(f'The custom column \'{custom_column_name}\' doesn\'t exist.')


        #* Get the current database
        db = self.gui.current_db.new_api

        #* Get all book IDs
        book_ids = db.all_book_ids() #* This will return a list of all book IDs

        #* Now, retrieve the values for your custom column for all books
        custom_column_values = set()

        for book_id in book_ids:
            #* Fetch metadata for each book (including the custom column)
            metadata = db.get_metadata(book_id)

            #* Extract the value of the custom column
            custom_column_value = metadata.get(custom_column_name)

            if custom_column_value:
                custom_column_values.update(custom_column_value)

        return custom_column_values
