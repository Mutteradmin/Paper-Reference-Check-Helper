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

# The modules contained in this file are used to handle application-level functions,
# responsible for theme switching, UI styles, etc.,
# as well as the core operational logic of application functions

class ThemeManager:
    def __init__(self, app):
        self.app = app

    def toggle_theme(self):
        """Switch the interface theme between dark and light modes."""
        self.app.is_dark_theme = not self.app.is_dark_theme
        self.apply_theme()

    def _get_dark_theme_styles(self):
        """Get stylesheet strings for dark mode"""
        return {
            'window_color': QColor(53, 53, 53),
            'window_text_color': Qt.GlobalColor.white,
            'base_color': QColor(35, 35, 35),
            'button_color': QColor(53, 53, 53),
            'button_text_color': Qt.GlobalColor.white,
            'highlight_color': QColor(42, 130, 218),
            'top_bar_style': "background-color: #353535; border-bottom: 1px solid #444;",
            'info_label_style': """
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
            """,
            'main_style': """
                QMainWindow, QWidget { background-color: #353535; color: #FFFFFF; }
                QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }
                QGroupBox { font-weight: bold; font-size: 14px; color: #FFFFFF; }
                QPushButton { border: 1px solid #444; padding: 8px; border-radius: 4px; background-color: #555; color: #FFFFFF; }
                QPushButton:hover { background-color: #666; }
                QPushButton:pressed { background-color: #4CAF50; }
                QLineEdit, QTextEdit { padding: 5px; border: 1px solid #444; border-radius: 4px; background-color: #2E2E2E; color: #FFFFFF; }
                QScrollArea { border: 1px solid #444; border-radius: 4px; background-color: #2E2E2E; }
                QLabel { color: #FFFFFF; }
            """,
            'search_edit_style': "QLineEdit { color: #FFFFFF; background-color: #2E2E2E; } QLineEdit[placeHolderText] { color: #AAAAAA; }",
            'path_edit_style': "QLineEdit { color: #FFFFFF; background-color: #2E2E2E; }",
            'button_icon': "🌞",
            'entry_hover': '#424242',
            'entry_selected': '#1e3a5f',
        }

    def _get_light_theme_styles(self):
        """Get stylesheet strings for light mode"""
        return {
            'window_color': QColor(240, 240, 240),
            'window_text_color': Qt.GlobalColor.black,
            'base_color': QColor(255, 255, 255),
            'button_color': QColor(240, 240, 240),
            'button_text_color': Qt.GlobalColor.black,
            'highlight_color': QColor(42, 130, 218),
            'top_bar_style': "background-color: #f0f0f0; border-bottom: 1px solid #ccc;",
            'info_label_style': """
                QLabel {
                    background-color: #f0f0f0;
                    color: #000000;
                    border: 1px solid #ccc;
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
            """,
            'main_style': """
                QMainWindow, QWidget { background-color: #f0f0f0; color: #000000; }
                QToolTip { color: #000000; background-color: #ffffff; border: 1px solid black; }
                QGroupBox { font-weight: bold; font-size: 14px; color: #000000; }
                QPushButton { border: 1px solid #ccc; padding: 8px; border-radius: 4px; background-color: #ffffff; color: #000000; }
                QPushButton:hover { background-color: #e0e0e0; }
                QPushButton:pressed { background-color: #4CAF50; }
                QLineEdit, QTextEdit { padding: 5px; border: 1px solid #ccc; border-radius: 4px; background-color: #ffffff; color: #000000; }
                QScrollArea { border: 1px solid #ccc; border-radius: 4px; background-color: #ffffff; }
                QLabel { color: #000000; }
            """,
            'search_edit_style': "QLineEdit { color: #000000; background-color: #ffffff; } QLineEdit[placeHolderText] { color: #888888; }",
            'path_edit_style': "QLineEdit { color: #000000; background-color: #ffffff; }",
            'button_icon': "🌙",
            'entry_hover': '#e0e0e0',
            'entry_selected': '#c9dfff',
        }

    def _apply_palette(self, styles):
        """Apply colors based on current theme settings and Apply the palette style"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, styles['window_color'])
        palette.setColor(QPalette.ColorRole.WindowText, styles['window_text_color'])
        palette.setColor(QPalette.ColorRole.Base, styles['base_color'])
        palette.setColor(QPalette.ColorRole.AlternateBase, styles['window_color'])
        palette.setColor(QPalette.ColorRole.ToolTipBase, styles['window_text_color'] if styles['window_text_color'] == Qt.GlobalColor.white else Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, styles['window_text_color'])
        palette.setColor(QPalette.ColorRole.Text, styles['window_text_color'])
        palette.setColor(QPalette.ColorRole.Button, styles['button_color'])
        palette.setColor(QPalette.ColorRole.ButtonText, styles['button_text_color'])
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, styles['highlight_color'])
        palette.setColor(QPalette.ColorRole.Highlight, styles['highlight_color'])
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black if styles['window_text_color'] == Qt.GlobalColor.white else Qt.GlobalColor.white)
        self.app.setPalette(palette)

    def _update_info_labels(self, info_label_style):
        """Update the style of the information tag"""
        for label in self.app.findChildren(QLabel):
            if (label.styleSheet() and
                    ("background-color: #2d2d2d;" in label.styleSheet() or
                     "background-color: #f0f0f0;" in label.styleSheet())):
                label.setStyleSheet(info_label_style)

    def _update_input_fields(self, search_edit_style, path_edit_style):
        """Update input field styles"""
        self.app.search_edit.setStyleSheet(search_edit_style)
        self.app.bib_path_edit.setStyleSheet(path_edit_style)
        self.app.tex_path_edit.setStyleSheet(path_edit_style)

    def apply_theme(self):
        """Apply the selected theme"""
        if self.app.is_dark_theme:
            styles = self._get_dark_theme_styles()
        else:
            styles = self._get_light_theme_styles()

        self._apply_palette(styles)

        if hasattr(self.app, 'top_bar'):
            self.app.top_bar.setStyleSheet(styles['top_bar_style'])

        self.app.theme_toggle_btn.setText(styles['button_icon'])

        self._update_info_labels(styles['info_label_style'])

        self.app.setStyleSheet(styles['main_style'])

        entry_styles = f"""
        QWidget#entryWidget {{ background-color: transparent; }}
        QWidget#entryWidget:hover {{ background-color: {styles['entry_hover']}; }}
        QWidget#entryWidget[selected="true"] {{ background-color: {styles['entry_selected']}; }}
        QWidget#entryWidget[selected="true"]:hover {{ background-color: {styles['entry_selected']}; }}
        """
        self.app.setStyleSheet(self.app.styleSheet() + entry_styles)

        self._update_input_fields(styles['search_edit_style'], styles['path_edit_style'])

        for widget in QApplication.topLevelWidgets():
            widget.setPalette(self.app.palette())
            widget.setStyleSheet(self.app.styleSheet())


class OperationsManager:
    def __init__(self, app):
        self.app = app

    def _pre_check(self, require_tex=False):
        """Helper to check if files are loaded before running an operation."""
        if not self.app.checker.bib_entries:
            if not self.app.bib_manager.load_bib_data():
                return False

        if require_tex and not self.app.tex_path_edit.text():
            self.app.show_error("Please provide a path to the .tex file first.")
            return False

        return True

    def run_check_duplicates(self):
        if not self._pre_check(): return

        bib_text, ok = QInputDialog.getMultiLineText(
            self.app, 'Input BibTeX Entry', 'Paste the new BibTeX entry/entries to check for duplicates:'
        )

        if ok and bib_text:
            try:
                duplicates = self.app.checker.check_duplicates(bib_text)
                self.app.results_text.clear()
                if duplicates:
                    self.app.results_text.append("🚨 Found potential duplicates:\n" + "=" * 40)
                    for dup in duplicates:
                        self.app.results_text.append(
                            f"  - New entry '{dup['user_key']}' looks like existing '{dup['existing_key']}'")
                else:
                    self.app.results_text.append("✅ No duplicates found for the provided entry.")

                    # Ask if user wants to add the new entry
                    reply = QMessageBox.question(self.app, "Add New Entry",
                                                 "No duplicates found. Would you like to add this entry to your bibliography?",
                                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

                    if reply == QMessageBox.StandardButton.Yes:
                        self.app.bib_manager.add_new_entry(bib_text)

            except Exception as e:
                self.app.show_error(f"Error checking duplicates: {str(e)}")

    def run_check_unreferenced_and_duplicates(self):
        if not self._pre_check(require_tex=True): return

        try:
            results = self.app.checker.analyze_tex_citations(self.app.tex_path_edit.text())
            unreferenced = results['unreferenced']
            duplicate_citations = results['duplicates']

            self.app.results_text.clear()
            self.app.results_text.append("--- Analysis of Unreferenced and Duplicate Citations ---\n")

            if unreferenced:
                self.app.results_text.append(
                    f"📌 Found {len(unreferenced)} unreferenced 'zombie' entries in .bib file:\n" + "=" * 60)
                for key in unreferenced:
                    entry = self.app.checker.bib_entries[key]
                    title = entry.fields.get('title', 'No title')
                    self.app.results_text.append(f"  - [{key}] {title[:80]}{'...' if len(title) > 80 else ''}")
            else:
                self.app.results_text.append("✅ All entries in the .bib file are cited in the .tex file. Great!")

            self.app.results_text.append("\n" + "-" * 40 + "\n")

            if duplicate_citations:
                total_refs = len(duplicate_citations)
                total_citations = sum(duplicate_citations.values())
                self.app.results_text.append(
                    f"🔍 Found {total_refs} keys cited multiple times (total {total_citations} citations):\n" + "=" * 60)
                for key, count in sorted(duplicate_citations.items(), key=lambda item: item[1], reverse=True):
                    self.app.results_text.append(f"  - '{key}' was cited {count} times.")
            else:
                self.app.results_text.append("✅ No duplicate citations found in the .tex file.")

        except Exception as e:
            self.app.show_error(f"Error analyzing .tex file: {str(e)}")

    def run_find_missing(self):
        if not self._pre_check(require_tex=True): return

        try:
            results = self.app.checker.analyze_tex_citations(self.app.tex_path_edit.text())
            missing = results['missing']

            self.app.results_text.clear()
            if missing:
                self.app.results_text.append(
                    f"❗ Found {len(missing)} 'ghost' entries cited in .tex but missing from .bib:\n" + "=" * 60)
                for key in missing:
                    self.app.results_text.append(f"  - \\cite{{{key}}} -> This key is not defined in your .bib file.")
            else:
                self.app.results_text.append("✅ All citations in your .tex file are defined in the .bib file. Perfect!")
        except Exception as e:
            self.app.show_error(f"Error analyzing .tex file: {str(e)}")