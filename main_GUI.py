import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFileDialog, QTextEdit, QTextBrowser,
    QGroupBox, QInputDialog, QMessageBox, QListWidget, QListWidgetItem,
    QScrollArea, QSplitter, QComboBox, QMenu, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox
)
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QAction
from PyQt6.QtCore import Qt, pyqtSignal

# Import the refactored logic
from ref_checker_logic import ReferenceChecker
import os
import time
import re
import json  # Added for favorites persistence
from pybtex.database import Person  # Added for editing persons


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("..")

    return os.path.join(base_path, relative_path)


class InsertDialog(QDialog):
    def __init__(self, parent=None, entries=None):
        super().__init__(parent)
        self.setWindowTitle("Insert New Entry")
        self.setModal(True)
        self.entries = entries or []

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.position_combo = QComboBox()
        self.position_combo.addItem("At the beginning", 0)

        for i, entry in enumerate(self.entries):
            self.position_combo.addItem(f"After: {entry}", i + 1)

        self.position_combo.addItem("At the end", len(self.entries) + 1)

        form_layout.addRow("Insert position:", self.position_combo)
        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_position(self):
        return self.position_combo.currentData()


class PaperRefCheckApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.checker = ReferenceChecker()
        self.bib_entries_list = []  # Store the order of bib entries
        self.bib_file_path = ""  # Store the current bib file path
        self.favorites = []  # List to store favorite entries as original strings
        self.load_favorites()  # Load persisted favorites
        self.current_entry_key = None
        self.field_edits = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Paper Reference Check Helper")
        self.setGeometry(100, 100, 1400, 750)
        self.setWindowIcon(QIcon('icon.png'))  # Optional: add an icon file

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main splitter for left, middle, and right panels
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout = QHBoxLayout(central_widget)
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
        self.search_edit.textChanged.connect(self.filter_entries)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_edit)

        # Add clear filter button
        clear_filter_btn = QPushButton("Clear")
        clear_filter_btn.clicked.connect(self.clear_filter)
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
        view_fav_btn = QPushButton("View Favorites")
        view_fav_btn.clicked.connect(self.view_favorites)
        left_layout.addWidget(view_fav_btn)

        # Save button
        save_btn = QPushButton("Save Changes to Bib File")
        save_btn.clicked.connect(self.save_bib_file)
        left_layout.addWidget(save_btn)

        # Export button
        export_btn = QPushButton("Export as New Bib File")
        export_btn.clicked.connect(self.export_bib_file)
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

        save_details_btn = QPushButton("Save Changes")
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
                   <b>Version:</b> 0.0.5 | 
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
        self.btn1.clicked.connect(self.run_check_duplicates)

        self.btn2 = QPushButton("Find Unreferenced & \nDuplicate Citations")
        self.btn2.clicked.connect(self.run_check_unreferenced_and_duplicates)

        self.btn3 = QPushButton("Find Missing Entries\n(Cited in .tex, not in .bib)")
        self.btn3.clicked.connect(self.run_find_missing)

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

        # Initialize entries list
        self.entry_widgets = []

    def load_favorites(self):
        """Load favorites from a persistent JSON file."""
        try:
            with open('favorites.json', 'r', encoding='utf-8') as f:
                self.favorites = json.load(f)
        except FileNotFoundError:
            self.favorites = []
        except Exception as e:
            self.show_error(f"Failed to load favorites: {str(e)}")
            self.favorites = []

    def save_favorites(self):
        """Save favorites to a persistent JSON file."""
        try:
            if not self.bib_file_path:
                self.show_error("Nothing new to save to your favorites.")
            else:
                with open('favorites.json', 'w', encoding='utf-8') as f:
                    json.dump(self.favorites, f)
                self.statusBar().showMessage(f"✅ Successfully saved favorites.")
        except Exception as e:
            self.show_error(f"Failed to save favorites: {str(e)}")

    def update_entries_list(self):
        """Update the left sidebar with all bib entries"""
        # Clear existing entries
        for i in reversed(range(self.entries_layout.count())):
            widget = self.entries_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.entry_widgets.clear()

        # Add each entry to the list, respecting the order in self.bib_entries_list
        for key in self.bib_entries_list:
            entry = self.checker.bib_entries.get(key)
            if not entry:
                continue

            entry_widget = QWidget()
            entry_layout = QHBoxLayout(entry_widget)
            entry_layout.setContentsMargins(5, 2, 5, 2)

            # Entry label with title and key
            title = entry.fields.get('title', 'No title')
            title_preview = title[:50] + "..." if len(title) > 50 else title
            label = QLabel(f"{key}: {title_preview}")
            label.setWordWrap(True)

            # Create tooltip with full information
            tooltip = f"Key: {key}\nType: {entry.type}"

            # Persons
            for role, persons in entry.persons.items():
                tooltip += f"\n{role.capitalize()}: {' and '.join(str(p) for p in persons)}"

            # Fields
            for field, value in entry.fields.items():
                tooltip += f"\n{field.capitalize()}: {value}"

            label.setToolTip(tooltip)

            # View button (eye)
            view_btn = QPushButton("👁")
            view_btn.setFixedSize(35, 35)
            view_btn.clicked.connect(lambda checked, k=key: self.show_entry_details(k))

            # Star button for favorites
            original_text = self.checker.get_original_entry(key)
            is_favorite = original_text in self.favorites
            star_btn = QPushButton("⭐" if is_favorite else "☆")
            star_btn.setFixedSize(35, 35)
            star_btn.clicked.connect(lambda checked, k=key: self.toggle_favorite(k))

            # Delete button
            delete_btn = QPushButton("❌")
            delete_btn.setFixedSize(35, 35)
            delete_btn.clicked.connect(lambda checked, k=key: self.delete_entry(k))

            entry_layout.addWidget(label, 1)
            entry_layout.addWidget(view_btn)
            entry_layout.addWidget(star_btn)
            entry_layout.addWidget(delete_btn)

            self.entries_layout.addWidget(entry_widget)
            self.entry_widgets.append(entry_widget)

            # Store the key as a property for filtering
            entry_widget.setProperty("entry_key", key)
            entry_widget.setProperty("entry_title", self.checker.normalize_title(title).lower())

        # If current entry still exists, refresh details
        if self.current_entry_key and self.current_entry_key in self.bib_entries_list:
            self.show_entry_details(self.current_entry_key)

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

    def save_entry_changes(self):
        """Save changes to the entry."""
        if not self.current_entry_key:
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
        self.update_entries_list()

        self.statusBar().showMessage(f"Entry '{self.current_entry_key}' updated.", 3000)

    def toggle_favorite(self, key):
        """Toggle the favorite status of an entry."""
        original = self.checker.get_original_entry(key)
        if original in self.favorites:
            self.favorites.remove(original)
            self.statusBar().showMessage(f"Removed {key} from favorites.")
        else:
            self.favorites.append(original)
            self.statusBar().showMessage(f"Added {key} to favorites.")
        # self.save_favorites()
        self.update_entries_list()  # Refresh to update star icons

    def view_favorites(self):
        """Open a dialog to view and manage favorites."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Favorites")
        dialog.setMinimumSize(600, 400)
        layout = QVBoxLayout(dialog)

        list_widget = QListWidget()
        self.populate_fav_list(list_widget)
        layout.addWidget(list_widget)

        save_btn = QPushButton("Save Favorites")
        save_btn.clicked.connect(self.save_favorites)
        layout.addWidget(save_btn)

        export_btn = QPushButton("Export Favorites to .bib")
        export_btn.clicked.connect(self.export_favorites)
        layout.addWidget(export_btn)

        dialog.exec()

    def populate_fav_list(self, list_widget):
        """Populate the favorites list widget with entries and delete buttons."""
        list_widget.clear()
        for i, fav in enumerate(self.favorites):
            try:
                entries, _ = self.checker.parse_bib_string(fav)
                for key, entry in entries.items():
                    item = QListWidgetItem()
                    wid = QWidget()
                    lay = QHBoxLayout(wid)
                    title_preview = entry.fields.get('title', '')[:50] + "..." if len(entry.fields.get('title', '')) > 50 else entry.fields.get('title', '')
                    label = QLabel(f"{key}: {title_preview}")
                    label.setWordWrap(True)
                    del_btn = QPushButton("❌")
                    del_btn.setFixedSize(35, 35)
                    del_btn.clicked.connect(lambda checked, idx=i, lw=list_widget: self.remove_fav_and_refresh(idx, lw))
                    lay.addWidget(label, 1)
                    lay.addWidget(del_btn)
                    item.setSizeHint(wid.sizeHint())
                    list_widget.addItem(item)
                    list_widget.setItemWidget(item, wid)
            except Exception as e:
                # Skip invalid entries
                pass

    def remove_fav_and_refresh(self, idx, list_widget):
        """Remove a favorite and refresh the list."""
        if 0 <= idx < len(self.favorites):
            del self.favorites[idx]
            self.save_favorites()
            self.populate_fav_list(list_widget)
            self.statusBar().showMessage("Removed entry from favorites.")
            # Also refresh main list if needed
            self.update_entries_list()

    def export_favorites(self):
        """Export all favorites to a new .bib file."""
        if not self.favorites:
            self.show_error("No favorites to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Favorites", "", "BibTeX Files (*.bib)")
        if not file_path:
            return

        try:
            content = "\n\n".join(self.favorites)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.statusBar().showMessage(f"✅ Favorites exported to {file_path}")
        except Exception as e:
            self.show_error(f"Failed to export favorites: {str(e)}")

    def filter_entries(self):
        """Filter entries based on search text"""
        search_text = self.search_edit.text().lower()

        for widget in self.entry_widgets:
            key = widget.property("entry_key")
            title = widget.property("entry_title")

            if search_text in key.lower() or search_text in title:
                widget.show()
            else:
                widget.hide()

    def clear_filter(self):
        """Clear the search filter"""
        self.search_edit.clear()
        for widget in self.entry_widgets:
            widget.show()

    def delete_entry(self, key):
        """Delete an entry from the bib data"""
        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete entry '{key}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if key in self.checker.bib_entries:
                # Remove from our data structures
                del self.checker.bib_entries[key]
                if key in self.checker.original_entries:
                    del self.checker.original_entries[key]

                if key in self.bib_entries_list:
                    self.bib_entries_list.remove(key)

                # If current details is this key, clear
                if self.current_entry_key == key:
                    self.current_entry_key = None
                    # Clear form
                    for i in reversed(range(self.details_form.count())):
                        self.details_form.itemAt(i).widget().deleteLater()
                    self.bibtex_display.clear()

                # Update the UI
                self.update_entries_list()
                self.statusBar().showMessage(f"Deleted entry: {key}")

                # Also update the results text if it mentions this entry
                current_text = self.results_text.toPlainText()
                if key in current_text:
                    self.results_text.append(f"\nNote: Entry '{key}' has been deleted.")

    def save_bib_file(self):
        """Save the modified bib file"""
        if not self.bib_file_path:
            self.show_error("No Bib file loaded.")
            return

        # Create a backup of the original file
        backup_path = self.bib_file_path + ".backup"
        try:
            with open(self.bib_file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
        except Exception as e:
            self.show_error(f"Failed to create backup: {str(e)}")
            return

        # Reconstruct the bib file content from original entries
        # Follow the order in bib_entries_list
        new_content = ""

        # Add all entries in the correct order
        for key in self.bib_entries_list:
            if key in self.checker.original_entries:
                new_content += self.checker.original_entries[key] + "\n\n"

        # Write the new content to the file
        try:
            with open(self.bib_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.statusBar().showMessage(f"✅ Bib file saved successfully. Backup created at {backup_path}")
            self.results_text.append(f"\n✅ Bib file saved successfully. Backup created at {backup_path}")
        except Exception as e:
            self.show_error(f"Failed to save Bib file: {str(e)}")

    def export_bib_file(self):
        """Export the modified bib file as a new file"""
        if not self.bib_file_path:
            self.show_error("No Bib file loaded.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Bib File", "", "BibTeX Files (*.bib)")
        if not file_path:
            return

        # Reconstruct the bib file content from original entries
        # Follow the order in bib_entries_list
        new_content = ""

        # Add all entries in the correct order
        for key in self.bib_entries_list:
            if key in self.checker.original_entries:
                new_content += self.checker.original_entries[key] + "\n\n"

        # Write the new content to the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.statusBar().showMessage(f"✅ Bib file exported successfully to {file_path}")
            self.results_text.append(f"\n✅ Bib file exported successfully to {file_path}")
        except Exception as e:
            self.show_error(f"Failed to export Bib file: {str(e)}")

    def _pre_check(self, require_tex=False):
        """Helper to check if files are loaded before running an operation."""
        if not self.checker.bib_entries:
            if not self.load_bib_data():
                return False

        if require_tex and not self.tex_path_edit.text():
            self.show_error("Please provide a path to the .tex file first.")
            return False

        return True

    def browse_bib_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Bib File", "", "BibTeX Files (*.bib)")
        if file_path:
            self.bib_path_edit.setText(file_path)
            self.load_bib_data()

    def browse_tex_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select LaTeX File", "", "LaTeX Files (*.tex)")
        if file_path:
            self.tex_path_edit.setText(file_path)
            self.statusBar().showMessage(f"✅ Tex file selected: {file_path}")

    def load_bib_data(self):
        bib_path = self.bib_path_edit.text()
        if not bib_path:
            self.show_error("Please provide a path to the .bib file first.")
            return False
        try:
            self.statusBar().showMessage("Loading .bib file...")
            QApplication.processEvents()  # Update UI

            # Store the file path
            self.bib_file_path = bib_path

            start_time = time.time()
            count = self.checker.load_bib_file(bib_path)
            end_time = time.time()
            bib_time = end_time - start_time

            # Update the entries list using the preserved order
            if hasattr(self.checker, 'entry_order'):
                self.bib_entries_list = self.checker.entry_order
            else:
                # Fallback to dictionary keys if order is not preserved
                self.bib_entries_list = list(self.checker.bib_entries.keys())

            # Update the entries list
            self.update_entries_list()

            self.results_text.setText(
                f"✅ Successfully loaded {count} entries from {bib_path}, costing {bib_time:.3f} s.\n")
            self.statusBar().showMessage(f"✅ Bib file loaded with {count} entries, costing {bib_time:.3f} s.")
            return True
        except Exception as e:
            self.show_error(f"Failed to load .bib file: {str(e)}")
            self.results_text.setText(f"❌ Failed to load .bib file: {str(e)}")
            return False

    def run_check_duplicates(self):
        if not self._pre_check(): return

        bib_text, ok = QInputDialog.getMultiLineText(
            self, 'Input BibTeX Entry', 'Paste the new BibTeX entry/entries to check for duplicates:'
        )

        if ok and bib_text:
            try:
                duplicates = self.checker.check_duplicates(bib_text)
                self.results_text.clear()
                if duplicates:
                    self.results_text.append("🚨 Found potential duplicates:\n" + "=" * 40)
                    for dup in duplicates:
                        self.results_text.append(
                            f"  - New entry '{dup['user_key']}' looks like existing '{dup['existing_key']}'")
                else:
                    self.results_text.append("✅ No duplicates found for the provided entry.")

                    # Ask if user wants to add the new entry
                    reply = QMessageBox.question(self, "Add New Entry",
                                                 "No duplicates found. Would you like to add this entry to your bibliography?",
                                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

                    if reply == QMessageBox.StandardButton.Yes:
                        self.add_new_entry(bib_text)

            except Exception as e:
                self.show_error(f"Error checking duplicates: {str(e)}")

    def add_new_entry(self, bib_text):
        """Add a new entry to the bibliography at a selected position"""
        try:
            new_entries, new_original_blocks = self.checker.parse_bib_string(bib_text)
            if not new_entries:
                self.show_error("Could not parse the provided BibTeX entry.")
                return

            # Show dialog to select insertion position
            dialog = InsertDialog(self, self.bib_entries_list)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                position = dialog.get_position()

                # Add new entries to the checker's data structures
                for key, entry in new_entries.items():
                    self.checker.bib_entries[key] = entry
                    if not hasattr(self.checker, 'original_entries'):
                        self.checker.original_entries = {}
                    self.checker.original_entries[key] = new_original_blocks[key]

                # Update the ordered list of entries
                new_keys = list(new_entries.keys())
                if position == 0:  # At the beginning
                    self.bib_entries_list = new_keys + self.bib_entries_list
                elif position > len(self.bib_entries_list):  # At the end
                    self.bib_entries_list.extend(new_keys)
                else:  # After a specific entry
                    self.bib_entries_list = (
                            self.bib_entries_list[:position] +
                            new_keys +
                            self.bib_entries_list[position:]
                    )

                # Update the UI
                self.update_entries_list()

                self.results_text.append(f"\n✅ Added {len(new_keys)} new entry/entries.")
                self.statusBar().showMessage(f"Added new entry/entries to bibliography.")

        except Exception as e:
            self.show_error(f"Error adding new entry: {str(e)}")

    def run_check_unreferenced_and_duplicates(self):
        if not self._pre_check(require_tex=True): return

        try:
            results = self.checker.analyze_tex_citations(self.tex_path_edit.text())
            unreferenced = results['unreferenced']
            duplicate_citations = results['duplicates']

            self.results_text.clear()
            self.results_text.append("--- Analysis of Unreferenced and Duplicate Citations ---\n")

            if unreferenced:
                self.results_text.append(
                    f"📌 Found {len(unreferenced)} unreferenced 'zombie' entries in .bib file:\n" + "=" * 60)
                for key in unreferenced:
                    entry = self.checker.bib_entries[key]
                    title = entry.fields.get('title', 'No title')
                    self.results_text.append(f"  - [{key}] {title[:80]}{'...' if len(title) > 80 else ''}")
            else:
                self.results_text.append("✅ All entries in the .bib file are cited in the .tex file. Great!")

            self.results_text.append("\n" + "-" * 40 + "\n")

            if duplicate_citations:
                total_refs = len(duplicate_citations)
                total_citations = sum(duplicate_citations.values())
                self.results_text.append(
                    f"🔍 Found {total_refs} keys cited multiple times (total {total_citations} citations):\n" + "=" * 60)
                for key, count in sorted(duplicate_citations.items(), key=lambda item: item[1], reverse=True):
                    self.results_text.append(f"  - '{key}' was cited {count} times.")
            else:
                self.results_text.append("✅ No duplicate citations found in the .tex file.")

        except Exception as e:
            self.show_error(f"Error analyzing .tex file: {str(e)}")

    def run_find_missing(self):
        if not self._pre_check(require_tex=True): return

        try:
            results = self.checker.analyze_tex_citations(self.tex_path_edit.text())
            missing = results['missing']

            self.results_text.clear()
            if missing:
                self.results_text.append(
                    f"❗ Found {len(missing)} 'ghost' entries cited in .tex but missing from .bib:\n" + "=" * 60)
                for key in missing:
                    self.results_text.append(f"  - \\cite{{{key}}} -> This key is not defined in your .bib file.")
            else:
                self.results_text.append("✅ All citations in your .tex file are defined in the .bib file. Perfect!")
        except Exception as e:
            self.show_error(f"Error analyzing .tex file: {str(e)}")

    def show_error(self, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText("Error")
        msg_box.setInformativeText(message)
        msg_box.setWindowTitle("Error")
        msg_box.exec()
        self.statusBar().showMessage(f"Error: {message}", 5000)

    def open_github_link(self, link):
        """打开GitHub链接"""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(link))


def apply_stylesheet(app):
    """A simple dark theme for a modern look."""
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(dark_palette)
    app.setStyleSheet("""
        QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }
        QGroupBox { font-weight: bold; font-size: 14px; }
        QPushButton { border: 1px solid #444; padding: 8px; border-radius: 4px; background-color: #555; }
        QPushButton:hover { background-color: #666; }
        QPushButton:pressed { background-color: #4CAF50; }
        QLineEdit, QTextEdit { padding: 5px; border: 1px solid #444; border-radius: 4px; background-color: #2E2E2E; }
        QScrollArea { border: 1px solid #444; border-radius: 4px; background-color: #2E2E2E; }
    """)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_stylesheet(app)
    main_win = PaperRefCheckApp()
    main_win.show()
    sys.exit(app.exec())