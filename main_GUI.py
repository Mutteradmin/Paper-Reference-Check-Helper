import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFileDialog, QTextEdit, QTextBrowser,
    QGroupBox, QInputDialog, QMessageBox, QListWidget, QListWidgetItem,
    QScrollArea, QSplitter, QComboBox, QMenu, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox
)
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QAction
from PyQt6.QtCore import Qt, pyqtSignal

# Import the refactored logic and all kinds of utils
from pybtex.database import Person  # Added for editing persons
from ref_checker_logic import ReferenceChecker
from app_utils import ThemeManager, OperationsManager
from bib_utils import BibManager, FavoritesManager


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("..")

    return os.path.join(base_path, relative_path)


class PaperRefCheckApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.checker = ReferenceChecker()
        self.bib_entries_list = []  # Store the order of bib entries
        self.bib_file_path = ""  # Store the current bib file path
        self.favorites = []  # List to store favorite entries as original strings
        self.current_entry_key = None
        self.field_edits = {}
        self.is_dark_theme = True  # Track current theme
        self.entry_widgets = []

        # Instantiate managers
        self.favorites_manager = FavoritesManager(self)
        self.bib_manager = BibManager(self)
        self.theme_manager = ThemeManager(self)
        self.operations_manager = OperationsManager(self)

        self.initUI()

        self.favorites_manager.load_favorites()

    def initUI(self):
        self.setWindowTitle("Paper Reference Check Helper")
        self.setGeometry(100, 100, 1400, 750)
        self.setWindowIcon(QIcon('icon.png'))  # Optional: add an icon file

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout for central widget
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar for theme toggle button
        self.top_bar = QWidget()  # 使用self引用
        self.top_bar.setObjectName("top_bar")
        self.top_bar.setStyleSheet("background-color: #353535; border-bottom: 1px solid #444;")
        top_bar_layout = QHBoxLayout(self.top_bar)
        top_bar_layout.setContentsMargins(10, 5, 10, 5)
        self.top_bar.setFixedHeight(43)

        # Add stretch to push the button to the right
        top_bar_layout.addStretch()

        # Theme toggle button
        self.theme_toggle_btn = QPushButton("🌞")
        self.theme_toggle_btn.setFixedSize(35, 35)
        self.theme_toggle_btn.clicked.connect(self.theme_manager.toggle_theme)
        self.theme_toggle_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 15px;
                font-size: 16px;
            }
        """)
        top_bar_layout.addWidget(self.theme_toggle_btn)

        main_layout.addWidget(self.top_bar)

        # Create main splitter for left, middle, and right panels
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        # Left panel for bib entries
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)

        # Search/filter area
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search entries...")
        self.search_edit.setStyleSheet("QLineEdit { color: #FFFFFF; } QLineEdit[placeHolderText] { color: #FFFFFF; }")
        self.search_edit.textChanged.connect(self.bib_manager.filter_entries)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_edit)

        # Add clear filter button
        clear_filter_btn = QPushButton("Clear")
        clear_filter_btn.clicked.connect(self.bib_manager.clear_filter)
        search_layout.addWidget(clear_filter_btn)

        left_layout.addLayout(search_layout)

        # Create scroll area for entries list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.entries_layout = QVBoxLayout(scroll_content)
        self.entries_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(scroll_content)

        left_layout.addWidget(scroll_area)

        # View Favorites button
        view_fav_btn = QPushButton("💖 View Favorites")
        view_fav_btn.clicked.connect(self.favorites_manager.view_favorites)
        left_layout.addWidget(view_fav_btn)

        # Save button
        save_btn = QPushButton("Save Changes to Bib File")
        save_btn.clicked.connect(self.bib_manager.save_bib_file)
        left_layout.addWidget(save_btn)

        # Export button
        export_btn = QPushButton("Export as New Bib File")
        export_btn.clicked.connect(self.bib_manager.export_bib_file)
        left_layout.addWidget(export_btn)

        # Add left widget to splitter
        main_splitter.addWidget(left_widget)

        # middle panel for entry details
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(5, 5, 5, 5)

        self.details_form = QFormLayout()
        details_group = QGroupBox("Entry Details")
        details_group.setLayout(self.details_form)

        details_scroll = QScrollArea()
        details_scroll.setWidget(details_group)
        details_scroll.setWidgetResizable(True)
        middle_layout.addWidget(details_scroll)

        self.bibtex_display = QTextEdit()
        self.bibtex_display.setReadOnly(True)
        middle_layout.addWidget(self.bibtex_display)

        # Add the copy button to bibtex_display and hide it initially
        self.bibtex_copy_button = QPushButton("📋")
        self.bibtex_copy_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 100, 100, 180);
                border: none;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(120, 120, 120, 200);
            }
        """)
        self.bibtex_copy_button.setFixedSize(30, 30)
        self.bibtex_copy_button.clicked.connect(self.copy_bibtex_to_clipboard)
        self.bibtex_copy_button.setParent(self.bibtex_display.viewport())
        self.bibtex_copy_button.hide()

        # Monitor the content changes of bibtex_display
        self.bibtex_display.textChanged.connect(self.toggle_bibtex_copy_button)
        # Monitor the size changes of bibtex_display
        self.bibtex_display.installEventFilter(self)

        save_details_btn = QPushButton("🖊️ Save Changes")
        save_details_btn.clicked.connect(self.save_entry_changes)
        middle_layout.addWidget(save_details_btn)

        # Add right widget to splitter
        main_splitter.addWidget(middle_widget)

        # Right panel (existing operations and results)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(15, 15, 15, 15)

        # Add area to display information
        info_label = QLabel()
        info_label.setMaximumHeight(120)
        info_label.setStyleSheet("""
                   QLabel {
                       background-color: #2d2d2d;
                       color: #ffffff;
                       border: 1px solid #444;
                       border-radius: 4px;
                       padding: 5px;
                       font-size: 12px;
                   }
                   QLabel a {
                       color: #4CAF50;
                       text-decoration: none;
                   }
                   QLabel a:hover {
                       text-decoration: underline;
                   }
               """)
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setText("""
                   <p><b>Author:</b> Kewei Tsinghua University| 
                   <b>Date:</b> 2025 | 
                   <b>Version:</b> 0.0.7 | 
                   <b>License:</b> MIT</p> 
                   <p><b>Note:</b> This is an effective and light-flash assistant for checking the references and rapidly finding out problems 
                   in your papers with just uploading .bib and .tex file of the paper, 
                   which can provide great help when you are writing papers agonizingly, especially the literature review.
                   Please ensure your .bib file is properly formatted for accurate checking. 
                   Verify that all entries have valid syntax before running analysis. |
                   <b>GitHub:</b> <a href="https://github.com/Mutteradmin/Paper_Reference_Check_Helper.git" style="color: #4CAF50; text-decoration: none;">Project Repository</a></p>
               """)
        info_label.linkActivated.connect(self.open_github_link)
        right_layout.addWidget(info_label)

        paths_group = QGroupBox("File Paths")
        paths_layout = QVBoxLayout()

        bib_layout = QHBoxLayout()
        self.bib_path_edit = QLineEdit()
        self.bib_path_edit.setPlaceholderText("Select your main .bib file...")
        self.bib_path_edit.setStyleSheet("QLineEdit { color: #FFFFFF; } QLineEdit[placeHolderText] { color: #FFFFFF; }")
        bib_browse_btn = QPushButton("Browse...")
        bib_browse_btn.clicked.connect(self.browse_bib_file)
        bib_layout.addWidget(QLabel("Bib File:"))
        bib_layout.addWidget(self.bib_path_edit)
        bib_layout.addWidget(bib_browse_btn)
        paths_layout.addLayout(bib_layout)

        tex_layout = QHBoxLayout()
        self.tex_path_edit = QLineEdit()
        self.tex_path_edit.setPlaceholderText("Select your main .tex file...")
        self.tex_path_edit.setStyleSheet("QLineEdit { color: #FFFFFF; } QLineEdit[placeHolderText] { color: #FFFFFF; }")
        tex_browse_btn = QPushButton("Browse...")
        tex_browse_btn.clicked.connect(self.browse_tex_file)
        tex_layout.addWidget(QLabel("Tex File:"))
        tex_layout.addWidget(self.tex_path_edit)
        tex_layout.addWidget(tex_browse_btn)
        paths_layout.addLayout(tex_layout)

        paths_group.setLayout(paths_layout)
        right_layout.addWidget(paths_group)

        operations_group = QGroupBox("Operations")
        operations_layout = QHBoxLayout()
        operations_layout.setSpacing(10)

        self.btn1 = QPushButton("Check for Duplicates\nin New Entry")
        self.btn1.clicked.connect(self.operations_manager.run_check_duplicates)

        self.btn2 = QPushButton("Find Unreferenced & \nDuplicate Citations")
        self.btn2.clicked.connect(self.operations_manager.run_check_unreferenced_and_duplicates)

        self.btn3 = QPushButton("Find Missing Entries\n(Cited in .tex, not in .bib)")
        self.btn3.clicked.connect(self.operations_manager.run_find_missing)

        operations_layout.addWidget(self.btn1)
        operations_layout.addWidget(self.btn2)
        operations_layout.addWidget(self.btn3)
        operations_group.setLayout(operations_layout)
        right_layout.addWidget(operations_group)

        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier New", 10))
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        right_layout.addWidget(results_group)

        # Add middle widget to splitter
        main_splitter.addWidget(right_widget)

        # Set initial splitter sizes
        main_splitter.setSizes([300, 300, 350])

        self.statusBar().showMessage("Ready. Please select your .bib and .tex files.")

        # Apply initial theme
        self.theme_manager.apply_theme()

    def eventFilter(self, obj, event):
        """Event filter, used to handle size changes of bibtex_display"""
        if obj == self.bibtex_display and event.type() in [14, 15]:  # Resize and Move events
            if self.bibtex_display.toPlainText().strip():
                self.position_bibtex_copy_button()
        return super().eventFilter(obj, event)

    def toggle_bibtex_copy_button(self):
        """Whether to display the copy button depends on whether there is content in bibtex_display"""
        if self.bibtex_display.toPlainText().strip():
            self.bibtex_copy_button.show()
            self.position_bibtex_copy_button()
        else:
            self.bibtex_copy_button.hide()

    def position_bibtex_copy_button(self):
        """Position the Copy button to the lower right corner of bibtex_display"""
        text_edit_pos = self.bibtex_display.viewport().geometry()
        button_x = text_edit_pos.width() - self.bibtex_copy_button.width() - 10
        button_y = text_edit_pos.height() - self.bibtex_copy_button.height() - 10
        self.bibtex_copy_button.move(button_x, button_y)

    def copy_bibtex_to_clipboard(self):
        """Copy the content in bibtex_display to the clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.bibtex_display.toPlainText())
        self.statusBar().showMessage("BibTeX has copied to clipboard.")

    def resizeEvent(self, event):
        """Reposition the copy button when the window size changes"""
        super().resizeEvent(event)
        if self.bibtex_display.toPlainText().strip():
            self.position_bibtex_copy_button()

    def show_entry_details(self, key):
        """Display and allow editing of entry details in the right panel."""
        self.current_entry_key = key
        entry = self.checker.bib_entries[key]

        # Clear existing form widgets
        for i in reversed(range(self.details_form.count())):
            item = self.details_form.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        self.field_edits = {}

        # Key (non-editable)
        self.details_form.addRow("Key:", QLabel(key))

        # Entry type
        type_edit = QLineEdit(entry.type)
        self.field_edits[('type', '')] = type_edit
        self.details_form.addRow("Entry Type:", type_edit)

        # Persons (e.g., author, editor)
        for role, persons in entry.persons.items():
            value = ' and '.join(str(p) for p in persons)
            edit = QLineEdit(value)
            self.field_edits[('person', role)] = edit
            self.details_form.addRow(role.capitalize() + ":", edit)

        # Fields (e.g., title, year, doi, publisher)
        for field, value in entry.fields.items():
            edit = QLineEdit(str(value))
            self.field_edits[('field', field)] = edit
            self.details_form.addRow(field.capitalize() + ":", edit)

        # Display BibTeX
        self.bibtex_display.setText(self.checker.get_original_entry(key))

        for widget in self.entry_widgets:
            widget_key = widget.property("entry_key")
            if widget_key == key:
                widget.setProperty("selected", True)
            else:
                widget.setProperty("selected", False)
            widget.style().polish(widget)

    def save_entry_changes(self):
        """Save changes to the entry."""
        if not self.current_entry_key:
            self.show_error("No entry selected.")
            return

        entry = self.checker.bib_entries[self.current_entry_key]

        for (typ, name), edit in self.field_edits.items():
            if typ == 'type':
                entry.type = edit.text()
            elif typ == 'person':
                try:
                    persons = [Person(s.strip()) for s in edit.text().split(' and ') if s.strip()]
                    entry.persons[name] = persons
                except Exception as e:
                    self.show_error(f"Error parsing {name}: {str(e)}")
                    return
            elif typ == 'field':
                entry.fields[name] = edit.text()

        try:
            original = entry.to_string('bibtex')
            self.checker.original_entries[self.current_entry_key] = original
            self.bibtex_display.setText(original)
        except Exception as e:
            self.show_error(f"Error generating BibTeX: {str(e)}")
            return

        # Refresh the entries list to reflect changes
        self.bib_manager.update_entries_list()

        self.statusBar().showMessage(f"Entry '{self.current_entry_key}' updated.", 3000)

    def browse_bib_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Bib File", "", "BibTeX Files (*.bib)")
        if file_path:
            self.bib_path_edit.setText(file_path)
            self.bib_manager.load_bib_data()

    def browse_tex_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select LaTeX File", "", "LaTeX Files (*.tex)")
        if file_path:
            self.tex_path_edit.setText(file_path)
            self.statusBar().showMessage(f"✅ Tex file selected: {file_path}")

    def show_error(self, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText("Error")
        msg_box.setInformativeText(message)
        msg_box.setWindowTitle("Error")
        msg_box.exec()
        self.statusBar().showMessage(f"Error: {message}", 5000)

    def open_github_link(self, link):
        """open the github link"""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(link))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    main_win = PaperRefCheckApp()
    main_win.show()
    sys.exit(app.exec())