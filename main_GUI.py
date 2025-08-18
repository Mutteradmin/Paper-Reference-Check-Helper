import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFileDialog, QTextEdit, QTextBrowser,
    QGroupBox, QInputDialog, QMessageBox
)
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor
from PyQt6.QtCore import Qt

# Import the refactored logic
from ref_checker_logic import ReferenceChecker
import os
import time

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
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Paper Reference Check Helper")
        self.setGeometry(100, 100, 900, 750)
        self.setWindowIcon(QIcon('icon.png'))  # Optional: add an icon file

        central_widget = QLabel()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 添加信息显示区域
        info_label = QLabel()
        info_label.setMaximumHeight(100)
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
                   <b>Version:</b> 0.0.1 | 
                   <b>License:</b> MIT</p>
                   <b>Note:</b> This is an effective assistant for checking the references in your papers, 
                   which can provide great help when you are writing your papers, especially the literature review. 
                   Please ensure your .bib file is properly formatted for accurate checking. 
                   Verify that all entries have valid syntax before running analysis. |
                   <b>GitHub:</b> <a href="https://github.com" style="color: #4CAF50; text-decoration: none;">Project Repository</a></p>
               """)
        info_label.linkActivated.connect(self.open_github_link)
        main_layout.addWidget(info_label)

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
        main_layout.addWidget(paths_group)

        operations_group = QGroupBox("Operations")
        operations_layout = QHBoxLayout()
        operations_layout.setSpacing(10)

        self.btn1 = QPushButton("1. Check for Duplicates\nin New Entry")
        self.btn1.clicked.connect(self.run_check_duplicates)

        self.btn2 = QPushButton("2. Find Unreferenced & \nDuplicate Citations")
        self.btn2.clicked.connect(self.run_check_unreferenced_and_duplicates)

        self.btn3 = QPushButton("3. Find Missing Entries\n(Cited in .tex, not in .bib)")
        self.btn3.clicked.connect(self.run_find_missing)

        operations_layout.addWidget(self.btn1)
        operations_layout.addWidget(self.btn2)
        operations_layout.addWidget(self.btn3)
        operations_group.setLayout(operations_layout)
        main_layout.addWidget(operations_group)

        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier New", 10))
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

        self.statusBar().showMessage("Ready. Please select your .bib and .tex files.")

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
            start_time = time.time()
            count = self.checker.load_bib_file(bib_path)
            end_time = time.time()
            bib_time = end_time - start_time
            self.results_text.setText(f"✅ Successfully loaded {count} entries from {bib_path}, costing {bib_time:.3f} s.\n")
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
            except Exception as e:
                self.show_error(f"Error checking duplicates: {str(e)}")

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
                    title = self.checker.bib_entries[key]['title']
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
    # ... (Stylesheet code remains the same)
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
    """)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_stylesheet(app)
    main_win = PaperRefCheckApp()
    main_win.show()
    sys.exit(app.exec())