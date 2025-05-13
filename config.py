from calibre.gui2 import question_dialog, warning_dialog
from calibre.utils.config import JSONConfig

try:
    from qt.core import (Qt, QWidget, QGridLayout, QLabel, QPushButton, QUrl,
                          QGroupBox, QComboBox, QVBoxLayout, QCheckBox,
                          QLineEdit, QTabWidget, QAbstractItemView,
                          QTableWidget, QHBoxLayout, QSize, QToolButton)
except ImportError:
    from PyQt5.Qt import (Qt, QWidget, QGridLayout, QLabel, QPushButton, QUrl,
                          QGroupBox, QComboBox, QVBoxLayout, QCheckBox,
                          QLineEdit, QTabWidget,QAbstractItemView,
                          QTableWidget, QHBoxLayout, QSize, QToolButton)

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
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.column_list = ListEdit()
        self.main_layout.addWidget(self.column_list)

    def save_settings(self):
        self.column_list.save_settings()

    def validate(self):
        #* Get the list of custom columns to sync from the preferences
        column_list = [column_name.text() for column_name in self.column_list.column_edits if column_name.text().strip() != '']

        #* Validate column names
        if not all(column_name in self.plugin_action.gui.library_view.model().custom_columns for column_name in column_list):
            warning_dialog(self, 'Invalid Column name', 'All custom columns must be defined in the setting \'#{column_name}\'', show=True)
            return False

        #* Validate column types
        #* All custom columns must be of type 'text'
        if not all(self.plugin_action.gui.library_view.model().custom_columns.get(column_name, dict()).get('datatype', '') == 'text' for column_name in column_list):
            warning_dialog(self, 'Invalid Column type', 'All custom columns must be of type "text"\nEither normal text or comma-separatedt', show=True)
            return False

        return True

class ListEdit(QWidget):
    def __init__(self, parent=None):
        super(ListEdit, self).__init__(parent)
        self.setWindowTitle("List Edit")
        self.setGeometry(0, 0, 400, 300)

        #* Create a QVBoxLayout for the main layout
        self.layout = QVBoxLayout(self)

        #* Create a QTableWidget
        self.table = QTableWidget(self)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Column Names"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setColumnWidth(0, 400);
        self.layout.addWidget(self.table)

        #* Create a button to add new rows
        self.add_button = QPushButton("Add Row", self)
        self.add_button.clicked.connect(self.add_row)
        self.layout.addWidget(self.add_button)

        self.column_edits = list()

        #* Init data
        data = prefs['column_list']
        for d in data:
            self.add_row(value=d)


    def save_settings(self):
        new_data = list()

        for edit in self.column_edits:
            if edit.text().strip() != '':
                new_data.append(edit.text().strip())

        prefs['column_list'] = new_data

    def add_row(self, *, value:str = ''):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        #* Create QLineEdit widgets for the new row
        column_name_edit = QLineEdit(self)
        column_name_edit.setText(value)

        #* Add the QLineEdit widgets to the table
        self.table.setCellWidget(row_position, 0, column_name_edit)

        #* Add the QLineEdit widgets to the column_edits list
        self.column_edits.append(column_name_edit)
