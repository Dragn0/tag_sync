from . import helper, tag_util
from calibre.gui2.ui import Main as GUI
from calibre.utils.config import JSONConfig
from PyQt5.QtWidgets import QApplication
import bisect
import re

try:
    from qt.core import (Qt, QWidget, QGridLayout, QLabel, QPushButton, QUrl,
                          QGroupBox, QComboBox, QVBoxLayout, QCheckBox,
                          QLineEdit, QTabWidget, QAbstractItemView,
                          QTableWidget, QHBoxLayout, QSize, QToolButton, QListWidget, QStackedWidget, QSpinBox, QFrame, QScrollArea)
except ImportError:
    from PyQt5.Qt import (Qt, QWidget, QGridLayout, QLabel, QPushButton, QUrl,
                          QGroupBox, QComboBox, QVBoxLayout, QCheckBox,
                          QLineEdit, QTabWidget,QAbstractItemView,
                          QTableWidget, QHBoxLayout, QSize, QToolButton, QListWidget, QStackedWidget, QSpinBox, QFrame, QScrollArea)

#* This is where all preferences for this plugin will be stored
#* Remember that this name (i.e. plugins/interface_demo) is also
#* in a global namespace, so make it as unique as possible.
#* You should always prefix your config file name with plugins/,
#* so as to ensure you don't accidentally clobber a calibre config file
prefs = JSONConfig('plugins/tag_sync')

#* Set defaults
prefs.defaults['columns'] = {'tags': {'include': True, 'prio': 0, 'split_tag_auto': True}}


class ConfigWidget(QWidget):
    def __init__(self, plugin_action):
        QWidget.__init__(self)

        self.plugin_action = plugin_action
        self.tags = tag_util.Tag.build_tags(self.plugin_action.gui)

        #* Create the main layout elements
        self.main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tag_details = SearchableTagEditor(self.tags, self)
        self.column_widget = ColumnSelect(self)


        #* Populate list and stack
        self.populate_tags(self.tags)

        #* Populate column choices
        self.column_widget.populate(self.plugin_action.gui)

        #* Link the layouts elements
        self.tabs.addTab(self.column_widget, "Column choice")
        self.tabs.addTab(self.tag_details, "Tag Details")

        self.main_layout.addWidget(self.tabs)

        self.setLayout(self.main_layout)

    def populate_tags(self, tags):
        for tag in tags:
            index = bisect.bisect_left(self.tag_details.label_list, tag.name)

            self.tag_details.label_list.insert(index, tag.name)
            self.tag_details.list_widget.insertItem(index, tag.display_name)
            self.tag_details.stack_widget.insertWidget(index, QWidget())

    def save_settings(self):
        #* Sace the settings for selected columns
        self.column_widget.save()

        #* Save the settings for the tag details
        self.tag_details.save()

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
        self.main_layout.addWidget(self.stack_widget, 2)

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


class SearchableTagEditor(SearchableElementEditor):
    def __init__(self, tags: list[tag_util.Tag], parent=None):
        super().__init__(parent)

        self.tags = tags
        self.loaded_tags: list = list()
        self.loaded_ids: set[int] = set()

        self.list_widget.currentRowChanged.connect(self.lazy_load_tag)

    def add_label(self, label):
        #* Add a new item to the list and stack
        index = bisect.bisect_left(self.label_list, label.lower())

        self.list_widget.insertItem(index, label)
        self.stack_widget.insertWidget(index, QWidget())
        self.label_list.insert(index, label.lower())

    def lazy_load_tag(self, index: int):
        cur_widget = self.stack_widget.widget(index)

        if not index in self.loaded_ids:
            tag_name: str = self.label_list[index]

            for tag in self.tags:
                if tag.name == tag_name:
                    break

            scroll = QScrollArea(self.stack_widget)
            scroll.setWidgetResizable(True)

            tag_widget = TagEdit(tag, scroll)

            for name_alias in tag.name_aliases:
                tag_widget.name_aliases.add_row(value=name_alias)

            for add_tag in tag.add_tags:
                tag_widget.add_tags.add_row(value=add_tag)

            scroll.setWidget(tag_widget)

            self.stack_widget.removeWidget(self.stack_widget.widget(index))
            self.stack_widget.insertWidget(index, scroll)

            self.loaded_ids.add(index)
            self.loaded_tags.insert(index, tag_widget)

        self.stack_widget.setCurrentIndex(index)

    def save(self):
        #* Cop the tags from the prefs
        pref_tags: dict = prefs['tags'].copy()

        #* Save the settings for the tag details
        for i in range(len(self.loaded_tags)):
            tag_widget: TagEdit = self.loaded_tags[i]

            tag_obj = tag_widget.tag_obj
            tag_descriptor = tag_obj.get_descriptor()

            #* Set names
            pref_tags.setdefault(tag_descriptor, dict())['display_name'] = tag_obj.display_name
            pref_tags.setdefault(tag_descriptor, dict())['name'] = tag_obj.name

            #* Get the name aliases
            tag_name_aliases = list()
            for name_alias in tag_widget.name_aliases.edits:
                if name_alias.text().strip().lower() != '':
                    tag_name_aliases.append(name_alias.text().strip().lower())

            #* Get the add tags
            tag_add_tags = list()
            for add_tag in tag_widget.add_tags.edits:
                if add_tag.text().strip() != '':
                    tag_add_tags.append(add_tag.text().strip())

            #* Get split_tag
            tag_split_tag = tag_widget.split_tag.isChecked()

            #* Save the tag alias, if there are none, remove the tag from the prefs
            if len(tag_name_aliases) > 0:
                pref_tags.setdefault(tag_descriptor, dict())['name_aliases'] = tag_name_aliases
            else:
                pref_tags.setdefault(tag_descriptor, dict()).pop('name_aliases', None)

            #* Save the add tags, if there are none, remove the tag from the prefs
            if len(tag_add_tags) > 0:
                pref_tags.setdefault(tag_descriptor, dict())['add_tags'] = tag_add_tags
            else:
                pref_tags.setdefault(tag_descriptor, dict()).pop('add_tags', None)

            #* Save split_tag_auto
            if tag_split_tag:
                pref_tags.setdefault(tag_descriptor, dict()).pop('split_tag_auto', None)
            else:
                pref_tags.setdefault(tag_descriptor, dict())['split_tag_auto'] = False

            #* Remove entry if all settings are the default
            if len(tag_name_aliases) <= 0 and len(tag_add_tags) <= 0 and tag_split_tag:
                pref_tags.pop(tag_descriptor, None)


        #* Remove entries that aren't tags anymore
        pref_tags_to_remove: list[str] = list()
        for pref_tag_name, pref_tag_data in pref_tags.items():
            if not any(pref_tag_data['name'] == tag.name for tag in self.tags):
                pref_tags_to_remove.append(pref_tag_name)

        for remove_name in pref_tags_to_remove:
            pref_tags.pop(remove_name)


        #* Reassign the tags to the prefs, else the save to disc is not triggered
        prefs['tags'] = pref_tags



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

        #* Set focus on new element
        column_name_edit.setFocus()


class TagEdit(QWidget):
    def __init__(self, tag_obj: tag_util.Tag, parent=None):
        super().__init__(parent)

        self.tag_obj: tag_util.Tag = tag_obj

        #* create the layout elements
        self.main_layout = QVBoxLayout()
        self.title_layout = QHBoxLayout()
        self.title = QLabel(f'Settings for tag: \'{tag_obj.display_name}\'\nFrom column: \'{tag_obj.collection_name}\'\nUsed by {tag_obj.in_book_count} {"book" if tag_obj.in_book_count == 1 else "books"}')
        self.copy_button = QToolButton()
        self.split_tag_layout = QHBoxLayout()
        self.split_tag_label = QLabel('Split tag automatically?')
        self.split_tag = QCheckBox()
        self.name_aliases = ListEdit(self, 'Name aliases')
        self.add_tags = ListEdit(self, 'Add tags')

        #* Set split tag default
        self.split_tag.setChecked(tag_obj.split_tag)

        #* Link copy button click event
        self.copy_button.setIcon(get_icons('images/copy.png', 'Tag Sync')) # type: ignore
        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(tag_obj.display_name))

        #* Link the layouts elements
        self.title_layout.addWidget(self.title)
        self.title_layout.addStretch()
        self.title_layout.addWidget(self.copy_button, alignment=Qt.AlignTop | Qt.AlignRight)

        self.split_tag_layout.addWidget(self.split_tag_label)
        self.split_tag_layout.addWidget(self.split_tag)
        self.split_tag_layout.addStretch()

        self.main_layout.addLayout(self.title_layout)

        #* Hide the split_tag checkbox if split is not possible
        if re.match(r'[^\(]*\(([^\)]*?)\).*', tag_obj.name):
            self.main_layout.addLayout(self.split_tag_layout)

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

        header = QHBoxLayout()
        header.addWidget(QLabel('Coulmn name'))
        header.addWidget(QLabel('Include?'))
        header.addWidget(QLabel('Priority'))

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setLineWidth(1)

        #* Link the layouts elements
        self.main_layout.addLayout(header)
        self.main_layout.addWidget(separator)
        self.setLayout(self.main_layout)

    def populate(self, gui: GUI):
        self.selections = dict()

        #* Add custom columns
        columns = dict()
        columns['tags'] = None
        columns.update(helper.get_custom_column(gui))
        for name, data in columns.items():
            if name != 'tags':
                if data.get('datatype', '') != 'text':
                    continue

            #* create the layout elements
            layout = QHBoxLayout()
            lable = QLabel(name)
            check = QCheckBox()
            prio = QSpinBox()

            #check.stateChanged.connect(self.save)

            self.selections[name] = { 'check': check, 'prio': prio}

            #* Link the layouts elements
            layout.addWidget(lable)
            layout.addWidget(check)
            layout.addWidget(prio)

            self.main_layout.addLayout(layout)

        self.main_layout.addStretch()

        prefs_column = prefs.get('columns', dict())
        for name, inputs in self.selections.items():
            pref_data = prefs_column.get(name, dict())

            inputs['check'].setChecked(pref_data.get('include', False))

            inputs['prio'].setValue(pref_data.get('prio', 1))

    def save(self):
        result = dict()
        for name, data in self.selections.items():
            result[name] = {
                'include': data['check'].isChecked(),
                'prio': data['prio'].value(),
            }

        prefs['columns'] = result
