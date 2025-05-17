from calibre.gui2 import question_dialog, warning_dialog
from calibre.utils.config import JSONConfig
import bisect
from calibre.gui2.ui import Main as GUI

from . import tag_util

try:
    from qt.core import (Qt, QWidget, QGridLayout, QLabel, QPushButton, QUrl,
                          QGroupBox, QComboBox, QVBoxLayout, QCheckBox,
                          QLineEdit, QTabWidget, QAbstractItemView,
                          QTableWidget, QHBoxLayout, QSize, QToolButton, QListWidget, QStackedWidget)
except ImportError:
    from PyQt5.Qt import (Qt, QWidget, QGridLayout, QLabel, QPushButton, QUrl,
                          QGroupBox, QComboBox, QVBoxLayout, QCheckBox,
                          QLineEdit, QTabWidget,QAbstractItemView,
                          QTableWidget, QHBoxLayout, QSize, QToolButton, QListWidget, QStackedWidget)

#* This is where all preferences for this plugin will be stored
#* Remember that this name (i.e. plugins/interface_demo) is also
#* in a global namespace, so make it as unique as possible.
#* You should always prefix your config file name with plugins/,
#* so as to ensure you don't accidentally clobber a calibre config file
prefs = JSONConfig('plugins/tag_sync')

#* Set defaults
prefs.defaults['column_list'] = list()


class ConfigWidget(QWidget):
    def __init__(self, plugin_action):
        QWidget.__init__(self)

        self.plugin_action = plugin_action

        #* Create the main layout elements
        self.main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tag_details = SearchableElementEditor(self)
        self.column_widget = ColumnSelect(self)


        #* Populate list and stack
        self.populate_tags()

        #* Populate column choices
        self.column_widget.populate(self.plugin_action.gui)

        #* Link the layouts elements
        self.tabs.addTab(self.column_widget, "Column choice")
        self.tabs.addTab(self.tag_details, "Tag Details")

        self.main_layout.addWidget(self.tabs)

        self.setLayout(self.main_layout)

    def populate_tags(self):
        tags = tag_util.Tag.build_tags(self.plugin_action.gui)
        for tag in tags:
            tag_widget = TagEdit(tag, self)

            for name_alias in tag.name_aliases:
                tag_widget.name_aliases.add_row(value=name_alias)

            for add_tag in tag.add_tags:
                tag_widget.add_tags.add_row(value=add_tag)

            self.tag_details.add_element(tag.display_name, tag_widget)

    def save_settings(self):
        #* Sace the settings for selected columns
        self.column_widget.save()

        #* Save the settings for the tag details

        #* Cop the tags from the prefs
        tags = prefs.get('tags', {}).copy()

        #* Save the settings for the tag details
        for i in range(self.tag_details.list_widget.count()):
            item = self.tag_details.list_widget.item(i)
            detail: TagEdit = self.tag_details.stack_widget.widget(i)

            tag_obj = detail.tag_obj
            tag_descriptor = tag_obj.get_descriptor()
            tag_widget = detail

            #* Set display name
            tags.setdefault(tag_descriptor, dict())['display_name'] = tag_obj.display_name

            #* Get the name aliases
            tag_name_aliases = list()
            for name_alias in tag_widget.name_aliases.edits:
                if name_alias.text().strip() != '':
                    tag_name_aliases.append(name_alias.text().strip())

            #* Get the add tags
            tag_add_tags = list()
            for add_tag in tag_widget.add_tags.edits:
                if add_tag.text().strip() != '':
                    tag_add_tags.append(add_tag.text().strip())

            #* Save the tag alias, if there are none, remove the tag from the prefs
            if len(tag_name_aliases) > 0:
                tags.setdefault(tag_descriptor, dict())['name_aliases'] = tag_name_aliases
            else:
                tags.setdefault(tag_descriptor, dict()).pop('name_aliases', None)

            #* Save the add tags, if there are none, remove the tag from the prefs
            if len(tag_add_tags) > 0:
                tags.setdefault(tag_descriptor, dict())['add_tags'] = tag_add_tags
            else:
                tags.setdefault(tag_descriptor, dict()).pop('add_tags', None)

            #* If there are no name aliases and no add tags, remove the tag from the prefs
            if len(tag_name_aliases) <= 0 and len(tag_add_tags) <= 0:
                tags.pop(tag_descriptor, None)

        #* Reassign the tags to the prefs, else the save to disc is not triggered
        prefs['tags'] = tags


    def validate(self):
        return True

class SearchableElementEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        #* create list of element labels
        self.label_list: list[str] = list()

        #* create the main layout elements
        self.main_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search tags...")

        self.list_widget = QListWidget()
        self.stack_widget = QStackedWidget()

        #* Hook search to filter
        self.search_box.textChanged.connect(self.filter_list)

        #* Hook selection to stack
        self.list_widget.currentRowChanged.connect(self.stack_widget.setCurrentIndex)

        #* Link the layouts elements
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.search_box)
        left_layout.addWidget(self.list_widget)

        self.main_layout.addLayout(left_layout, 1)
        self.main_layout.addWidget(self.stack_widget, 3)

        self.setLayout(self.main_layout)

    def add_element(self, label: str, widget):
        #* Add a new item to the list and stack
        index = bisect.bisect_left(self.label_list, label.lower())

        self.list_widget.insertItem(index, label)
        self.stack_widget.insertWidget(index, widget)
        self.label_list.insert(index, label.lower())

    def filter_list(self, text):
        #* Filter the list based on the search text
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())

        #* If the current item is hidden, select the first visible item
        selected_item = self.list_widget.currentItem()
        if selected_item and selected_item.isHidden():
            for i in range(self.list_widget.count()):
                if not self.list_widget.item(i).isHidden():
                    self.list_widget.setCurrentRow(i)
                    break

        #* Scroll to the selected item
        selected_item = self.list_widget.currentItem()
        if selected_item:
            self.list_widget.scrollToItem(selected_item, QAbstractItemView.PositionAtCenter)


class ListEdit(QWidget):
    def __init__(self, parent=None, title:str = ''):
        super().__init__(parent)

        self.edits = list()

        #* create the main layout elements
        self.main_layout = QVBoxLayout(self)
        self.title = QLabel(title)
        self.list = QVBoxLayout(self)
        self.add_button = QPushButton("Add Row", self)

        #* Connect the add button to the add_row method
        self.add_button.clicked.connect(self.add_row)

        #* Link the layouts elements
        self.main_layout.addWidget(self.title)
        self.main_layout.addLayout(self.list)
        self.main_layout.addWidget(self.add_button)

        self.setLayout(self.main_layout)

    def add_row(self, *, value:str = ''):
        #* create the main layout elements
        main_layout = QHBoxLayout(self)
        column_name_edit = QLineEdit(value, self)
        del_button = QPushButton("Del", self)

        #* design the del button
        del_button.setStyleSheet("background-color: red; color: white;")

        #* Connect the del button
        del_button.clicked.connect(lambda: (main_layout.removeWidget(column_name_edit),
                                            self.edits.remove(column_name_edit),
                                            column_name_edit.deleteLater(),
                                            main_layout.removeWidget(del_button),
                                            del_button.deleteLater(),
                                            self.list.removeItem(main_layout),
                                            main_layout.setParent(None),
                                            main_layout.deleteLater()))

        #* Link the layouts elements
        main_layout.addWidget(column_name_edit, 5)
        main_layout.addWidget(del_button, 1)

        #* Add the QLineEdit widgets to the line
        self.list.addLayout(main_layout)

        #* Add the QLineEdit widgets to the column_edits list
        self.edits.append(column_name_edit)


class TagEdit(QWidget):
    def __init__(self, tag_obj: tag_util.Tag, parent=None):
        super().__init__(parent)

        self.tag_obj: tag_util.Tag = tag_obj

        #* create the layout elements
        self.main_layout = QVBoxLayout()
        self.title = QLabel(f'Settings for tag: \'{tag_obj.display_name}\'\nfrom column: \'{tag_obj.collection_name}\'')
        self.name_aliases = ListEdit(self, 'Name aliases')
        self.add_tags = ListEdit(self, 'Add tags')

        #* Link the layouts elements
        self.main_layout.addWidget(self.title)
        self.main_layout.addWidget(self.name_aliases)
        self.main_layout.addWidget(self.add_tags)
        self.main_layout.addStretch()

        self.setLayout(self.main_layout)

class ColumnSelect(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        #* create the layout elements
        self.main_layout = QVBoxLayout()

        self.main_layout.setSpacing(5)  # Space between widgets

        #* Link the layouts elements
        self.setLayout(self.main_layout)

    def populate(self, gui: GUI):
        self.selections = dict()

        #* Add tags
        #* create the layout elements
        layout = QHBoxLayout()
        lable = QLabel('tags')
        check = QCheckBox()

        #check.stateChanged.connect(self.save)

        self.selections['tags'] = check

        #* Link the layouts elements
        layout.addWidget(lable)
        layout.addWidget(check)

        self.main_layout.addLayout(layout)

        #* Add custom columns
        for name, data in tag_util.get_custom_column(gui).items():
            if data.get('datatype', '') != 'text':
                continue

            #* create the layout elements
            layout = QHBoxLayout()
            lable = QLabel(name)
            check = QCheckBox()

            #check.stateChanged.connect(self.save)

            self.selections[name] = check

            #* Link the layouts elements
            layout.addWidget(lable)
            layout.addWidget(check)

            self.main_layout.addLayout(layout)

        self.main_layout.addStretch()

        for column in prefs['column_list']:
            if column in self.selections:
                self.selections[column].setChecked(True)

    def save(self):
        result = list()
        for name, check in self.selections.items():
            if check.isChecked():
                result.append(name)

        prefs['column_list'] = result
