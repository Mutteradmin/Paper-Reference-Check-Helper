from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFileDialog, QTextEdit, QTextBrowser,
    QGroupBox, QInputDialog, QMessageBox, QListWidget, QListWidgetItem,
    QScrollArea, QSplitter, QComboBox, QMenu, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal

# Import the refactored logic
import time
import json  # Added for favorites persistence

# The module contained in this file is used to handle content related to
# literature data management, responsible for the management of bibtex data
# and the management of favorites data

class InsertDialog(QDialog):
    def __init__(self, parent=None, entries=None):
        super().__init__(parent)
        self.setWindowTitle("Insert New Entry")
        self.setModal(True)
        self.entries = entries or []

        layout = QVBoxLayout(self)

        # Search input
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search entries...")
        self.search_edit.textChanged.connect(self.filter_list)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # List widget for positions
        self.position_list = QListWidget()
        self.position_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.position_list)

        # Populate initially
        self.populate_list()

        # Select "At the end" by default
        for i in range(self.position_list.count()):
            if self.position_list.item(i).text() == "At the end":
                self.position_list.setCurrentRow(i)
                break

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def populate_list(self, filter_text=""):
        self.position_list.clear()
        filter_lower = filter_text.lower()

        # Add "At the beginning"
        beginning_text = "At the beginning"
        if not filter_text or filter_lower in beginning_text.lower():
            item = QListWidgetItem(beginning_text)
            item.setData(Qt.ItemDataRole.UserRole, 0)
            self.position_list.addItem(item)

        # Add "After: entry" for each matching entry
        for i, entry in enumerate(self.entries):
            after_text = f"After: {entry}"
            if not filter_text or filter_lower in after_text.lower():
                item = QListWidgetItem(after_text)
                item.setData(Qt.ItemDataRole.UserRole, i + 1)
                self.position_list.addItem(item)

        # Add "At the end"
        end_text = "At the end"
        if not filter_text or filter_lower in end_text.lower():
            item = QListWidgetItem(end_text)
            item.setData(Qt.ItemDataRole.UserRole, len(self.entries) + 1)
            self.position_list.addItem(item)

    def filter_list(self):
        filter_text = self.search_edit.text()
        self.populate_list(filter_text)

    def get_position(self):
        selected_items = self.position_list.selectedItems()
        if selected_items:
            return selected_items[0].data(Qt.ItemDataRole.UserRole)
        return None


class BibManager:
    def __init__(self, app):
        self.app = app

    def load_bib_data(self):
        bib_path = self.app.bib_path_edit.text()
        if not bib_path:
            self.app.show_error("Please provide a path to the .bib file first.")
            return False
        try:
            self.app.statusBar().showMessage("Loading .bib file...")
            QApplication.processEvents()  # Update UI

            # Store the file path
            self.app.bib_file_path = bib_path

            start_time = time.time()
            count = self.app.checker.load_bib_file(bib_path)
            end_time = time.time()
            bib_time = end_time - start_time

            # Update the entries list using the preserved order
            if hasattr(self.app.checker, 'entry_order'):
                self.app.bib_entries_list = self.app.checker.entry_order
            else:
                # Fallback to dictionary keys if order is not preserved
                self.app.bib_entries_list = list(self.app.checker.bib_entries.keys())

            # Update the entries list
            self.update_entries_list()

            self.app.results_text.setText(
                f"✅ Successfully loaded {count} entries from {bib_path}, costing {bib_time:.3f} s.\n")
            self.app.statusBar().showMessage(f"✅ Bib file loaded with {count} entries, costing {bib_time:.3f} s.")
            return True
        except Exception as e:
            self.app.show_error(f"Failed to load .bib file: {str(e)}")
            self.app.results_text.setText(f"❌ Failed to load .bib file: {str(e)}")
            return False

    def update_entries_list(self):
        """Update the left sidebar with all bib entries"""
        # Clear existing entries
        for i in reversed(range(self.app.entries_layout.count())):
            widget = self.app.entries_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.app.entry_widgets.clear()

        # Add each entry to the list, respecting the order in self.app.bib_entries_list
        for key in self.app.bib_entries_list:
            entry = self.app.checker.bib_entries.get(key)
            if not entry:
                continue

            entry_widget = QWidget()
            entry_widget.setObjectName("entryWidget")
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
            view_btn.clicked.connect(lambda checked, k=key: self.app.show_entry_details(k))

            # Star button for favorites
            original_text = self.app.checker.get_original_entry(key)
            is_favorite = original_text in self.app.favorites
            star_btn = QPushButton("⭐" if is_favorite else "☆")
            star_btn.setFixedSize(35, 35)
            star_btn.clicked.connect(lambda checked, k=key: self.app.favorites_manager.toggle_favorite(k))

            # Delete button
            delete_btn = QPushButton("❌")
            delete_btn.setFixedSize(35, 35)
            delete_btn.clicked.connect(lambda checked, k=key: self.delete_entry(k))

            entry_layout.addWidget(label, 1)
            entry_layout.addWidget(view_btn)
            entry_layout.addWidget(star_btn)
            entry_layout.addWidget(delete_btn)

            if key == self.app.current_entry_key:
                entry_widget.setProperty("selected", True)
                entry_widget.style().polish(entry_widget)
            else:
                entry_widget.setProperty("selected", False)
                entry_widget.style().polish(entry_widget)

            self.app.entries_layout.addWidget(entry_widget)
            self.app.entry_widgets.append(entry_widget)

            # Store the key as a property for filtering
            entry_widget.setProperty("entry_key", key)
            entry_widget.setProperty("entry_title", self.app.checker.normalize_title(title).lower())

        # If current entry still exists, refresh details
        if self.app.current_entry_key and self.app.current_entry_key in self.app.bib_entries_list:
            self.app.show_entry_details(self.app.current_entry_key)

    def add_new_entry(self, bib_text):
        """Add a new entry to the bibliography at a selected position"""
        try:
            new_entries, new_original_blocks = self.app.checker.parse_bib_string(bib_text)
            if not new_entries:
                self.app.show_error("Could not parse the provided BibTeX entry.")
                return

            # Show dialog to select insertion position
            dialog = InsertDialog(self.app, self.app.bib_entries_list)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                position = dialog.get_position()
                if position is None:
                    self.app.show_error("No position selected.")
                    return

                # Add new entries to the checker's data structures
                for key, entry in new_entries.items():
                    self.app.checker.bib_entries[key] = entry
                    if not hasattr(self.app.checker, 'original_entries'):
                        self.app.checker.original_entries = {}
                    self.app.checker.original_entries[key] = new_original_blocks[key]

                # Update the ordered list of entries
                new_keys = list(new_entries.keys())
                if position == 0:  # At the beginning
                    self.app.bib_entries_list = new_keys + self.app.bib_entries_list
                elif position > len(self.app.bib_entries_list):  # At the end
                    self.app.bib_entries_list.extend(new_keys)
                else:  # After a specific entry
                    self.app.bib_entries_list = (
                        self.app.bib_entries_list[:position] +
                        new_keys +
                        self.app.bib_entries_list[position:]
                    )

                # Update the UI
                self.update_entries_list()

                self.app.results_text.append(f"\n✅ Added {len(new_keys)} new entry/entries.")
                self.app.statusBar().showMessage(f"Added new entry/entries to bibliography.")

        except Exception as e:
            self.app.show_error(f"Error adding new entry: {str(e)}")

    def delete_entry(self, key):
        """Delete an entry from the bib data"""
        reply = QMessageBox.question(self.app, "Confirm Delete",
                                     f"Are you sure you want to delete entry '{key}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if key in self.app.checker.bib_entries:
                # Remove from our data structures
                del self.app.checker.bib_entries[key]
                if key in self.app.checker.original_entries:
                    del self.app.checker.original_entries[key]

                if key in self.app.bib_entries_list:
                    self.app.bib_entries_list.remove(key)

                # If current details is this key, clear
                if self.app.current_entry_key == key:
                    self.app.current_entry_key = None
                    # Clear form
                    for i in reversed(range(self.app.details_form.count())):
                        self.app.details_form.itemAt(i).widget().deleteLater()
                    self.app.bibtex_display.clear()

                # Update the UI
                self.update_entries_list()
                self.app.statusBar().showMessage(f"Deleted entry: {key}")

                # Also update the results text if it mentions this entry
                current_text = self.app.results_text.toPlainText()
                if key in current_text:
                    self.app.results_text.append(f"\nNote: Entry '{key}' has been deleted.")

    def save_bib_file(self):
        """Save the modified bib file"""
        if not self.app.bib_file_path:
            self.app.show_error("No Bib file loaded.")
            return

        # Create a backup of the original file
        backup_path = self.app.bib_file_path + ".backup"
        try:
            with open(self.app.bib_file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
        except Exception as e:
            self.app.show_error(f"Failed to create backup: {str(e)}")
            return

        # Reconstruct the bib file content from original entries
        # Follow the order in bib_entries_list
        new_content = ""

        # Add all entries in the correct order
        for key in self.app.bib_entries_list:
            if key in self.app.checker.original_entries:
                new_content += self.app.checker.original_entries[key] + "\n\n"

        # Write the new content to the file
        try:
            with open(self.app.bib_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.app.statusBar().showMessage(f"✅ Bib file saved successfully. Backup created at {backup_path}")
            self.app.results_text.append(f"\n✅ Bib file saved successfully. Backup created at {backup_path}")
        except Exception as e:
            self.app.show_error(f"Failed to save Bib file: {str(e)}")

    def export_bib_file(self):
        """Export the modified bib file as a new file"""
        if not self.app.bib_file_path:
            self.app.show_error("No Bib file loaded.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self.app, "Export Bib File", "", "BibTeX Files (*.bib)")
        if not file_path:
            return

        # Reconstruct the bib file content from original entries
        # Follow the order in bib_entries_list
        new_content = ""

        # Add all entries in the correct order
        for key in self.app.bib_entries_list:
            if key in self.app.checker.original_entries:
                new_content += self.app.checker.original_entries[key] + "\n\n"

        # Write the new content to the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.app.statusBar().showMessage(f"✅ Bib file exported successfully to {file_path}")
            self.app.results_text.append(f"\n✅ Bib file exported successfully to {file_path}")
        except Exception as e:
            self.app.show_error(f"Failed to export Bib file: {str(e)}")

    def filter_entries(self):
        """Filter entries based on search text"""
        search_text = self.app.search_edit.text().lower()

        for widget in self.app.entry_widgets:
            key = widget.property("entry_key")
            title = widget.property("entry_title")

            if search_text in key.lower() or search_text in title:
                widget.show()
            else:
                widget.hide()

    def clear_filter(self):
        """Clear the search filter"""
        self.app.search_edit.clear()
        for widget in self.app.entry_widgets:
            widget.show()


class FavoritesManager:
    def __init__(self, app):
        self.app = app

    def load_favorites(self):
        """Load favorites from a persistent JSON file."""
        try:
            with open('favorites.json', 'r', encoding='utf-8') as f:
                self.app.favorites = json.load(f)
        except FileNotFoundError:
            self.app.favorites = []
        except Exception as e:
            self.app.show_error(f"Failed to load favorites: {str(e)}")
            self.app.favorites = []

    def save_favorites(self):
        """Save favorites to a persistent JSON file."""
        try:
            if not self.app.bib_file_path:
                self.app.show_error("Nothing new to save to your favorites.")
            else:
                with open('favorites.json', 'w', encoding='utf-8') as f:
                    json.dump(self.app.favorites, f)
                self.app.statusBar().showMessage(f"✅ Successfully saved favorites.")
        except Exception as e:
            self.app.show_error(f"Failed to save favorites: {str(e)}")

    def toggle_favorite(self, key):
        """Toggle the favorite status of an entry."""
        original = self.app.checker.get_original_entry(key)
        if original in self.app.favorites:
            self.app.favorites.remove(original)
            self.app.statusBar().showMessage(f"Removed {key} from favorites.")
        else:
            self.app.favorites.append(original)
            self.app.statusBar().showMessage(f"Added {key} to favorites.")
        self.app.bib_manager.update_entries_list()  # Refresh to update star icons

    def view_favorites(self):
        """Open a dialog to view and manage favorites."""
        dialog = QDialog(self.app)
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
        for i, fav in enumerate(self.app.favorites):
            try:
                entries, _ = self.app.checker.parse_bib_string(fav)
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
        if 0 <= idx < len(self.app.favorites):
            del self.app.favorites[idx]
            self.save_favorites()
            self.populate_fav_list(list_widget)
            self.app.statusBar().showMessage("Removed entry from favorites.")
            # Also refresh main list if needed
            self.app.bib_manager.update_entries_list()

    def export_favorites(self):
        """Export all favorites to a new .bib file."""
        if not self.app.favorites:
            self.app.show_error("No favorites to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self.app, "Export Favorites", "", "BibTeX Files (*.bib)")
        if not file_path:
            return

        try:
            content = "\n\n".join(self.app.favorites)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.app.statusBar().showMessage(f"✅ Favorites exported to {file_path}")
        except Exception as e:
            self.app.show_error(f"Failed to export favorites: {str(e)}")