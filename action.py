from calibre.gui2 import question_dialog, warning_dialog, info_dialog
from calibre.gui2.actions import InterfaceAction
from calibre.utils.config import JSONConfig
from PyQt5.QtWidgets import QMessageBox
import logging

try:
    from qt.core import QToolButton, QMenu
except ImportError:
    from PyQt5.Qt import QToolButton, QMenu

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
        #* If no books are selected, show a warning
        if not selected_books:
            warning_dialog(self.gui, _('No Books Selected'), _('Please select books to apply the tag.'), show=True)
            return

        #* Get the current database
        db = self.gui.current_db.new_api

        #* Get the list of custom columns to sync from the preferences
        column_list = self.prefs['column_list']

        if len(column_list) == 0:
            #* If no custom columns are set, show a warning
            warning_dialog(self.gui, _('No Custom Columns'), _('Please setup the custom columns to sync in the settings'), show=True)
            return

        for column_name in column_list:
            try:
                #* Get the list of all characters from the database
                all_column_tags = self.get_all_elements_from_custom_column(column_name)
            except ValueError as e:
                #* Handle the case where the custom column doesn't exist
                warning_dialog(self.gui, _('Custom Column Error'), str(e), show=True)
                return

            for book_id in selected_books:
                book = db.get_metadata(book_id)
                current_tags = book.tags
                current_sub_tags = book.get(column_name, [])

                for tag in current_tags:
                    found_sub_tag = str_iter_compare(tag, all_column_tags)
                    if found_sub_tag is not None:
                        current_tags.remove(tag)
                        if not found_sub_tag in current_sub_tags:
                            current_sub_tags.append(found_sub_tag)

                book.tags = sorted(current_tags)
                book.set(column_name, current_sub_tags)

                #* Update the tags in the database
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
