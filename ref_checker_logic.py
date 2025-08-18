from pybtex.database import parse_string
import os
import difflib
import re
from collections import Counter


class ReferenceChecker:
    """
    Encapsulates all the logic for checking references.
    This class holds the state (loaded bib entries) and performs operations.
    """

    def __init__(self):
        self.bib_entries = {}

    def normalize_title(self, title):
        """Standardizes title: lowercase, remove punctuation, spaces, braces."""
        if not title:
            return ""
        title = re.sub(r"[{}$\\]", "", title)
        title = re.sub(r"[^\w\s]", "", title).lower()
        title = re.sub(r"\s+", " ", title).strip()
        return title

    def _parse_and_store(self, block, entries):
        """Helper to parse a single entry block and store it."""
        try:
            bib_data = parse_string(block, 'bibtex')
            for key, entry in bib_data.entries.items():
                fields = {
                    'key': key,
                    'title': self.normalize_title(entry.fields.get('title', '')),
                    'author': entry.fields.get('author', '').lower(),
                    'year': entry.fields.get('year', ''),
                }
                entries[key] = fields
        except Exception as e:
            print(f"⚠️ Could not parse entry block: {e}")

    def load_bib_file(self, file_path):
        """Reads a .bib file and returns a dictionary of entries."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.splitlines()
        entries = {}
        current_block = ""
        bracket_count = 0

        # This parsing logic is simplified to better handle various bib file formats
        for line in lines:
            if line.strip().startswith('@'):
                if current_block and bracket_count == 0:
                    self._parse_and_store(current_block, entries)
                current_block = ""

            if current_block or line.strip().startswith('@'):
                current_block += line + "\n"
                bracket_count += line.count('{') - line.count('}')

        if current_block.strip():
            self._parse_and_store(current_block, entries)

        self.bib_entries = entries
        return len(self.bib_entries)

    def load_user_bib_input(self, user_bib_str):
        """Parses a user-provided BibTeX string."""
        if not user_bib_str.strip():
            return {}
        try:
            bib_data = parse_string(user_bib_str, 'bibtex')
            entries = {}
            for key, entry in bib_data.entries.items():
                entries[key] = {
                    'key': key,
                    'title': self.normalize_title(entry.fields.get('title', '')),
                    'author': entry.fields.get('author', '').lower(),
                    'year': entry.fields.get('year', ''),
                }
            return entries
        except Exception as e:
            raise ValueError(f"Failed to parse user BibTeX input: {e}")

    def are_titles_similar(self, title1, title2, threshold):
        """Judges title similarity."""
        return difflib.SequenceMatcher(None, title1, title2).ratio() >= threshold

    def check_duplicates(self, user_bib_str, title_threshold=0.9):
        """Checks if user-input entries are duplicates of existing ones."""
        if not self.bib_entries:
            raise ValueError("The main .bib file has not been loaded yet.")

        user_entries = self.load_user_bib_input(user_bib_str)
        duplicates = []
        for u_key, u_entry in user_entries.items():
            for e_key, e_entry in self.bib_entries.items():
                if self.are_titles_similar(u_entry['title'], e_entry['title'], threshold=title_threshold):
                    year_match = difflib.SequenceMatcher(None, u_entry['year'], e_entry['year']).ratio()
                    author_match = difflib.SequenceMatcher(None, u_entry['author'], e_entry['author']).ratio()
                    if year_match > 0.3 and author_match > 0.3:
                        duplicates.append({
                            'user_key': u_key,
                            'existing_key': e_key,
                            'title': u_entry['title'],
                            'reason': 'Title match + partial metadata'
                        })
                        break
        return duplicates

    def extract_citations_from_tex(self, tex_file_path):
        """
        Extracts all \cite{...} keys from a .tex file.
        This function now FAITHFULLY replicates the logic from the original script.
        """
        if not os.path.exists(tex_file_path):
            raise FileNotFoundError(f"LaTeX file not found: {tex_file_path}")

        with open(tex_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # FIXED: Reverted to the original, more robust regex.
        pattern = r'\\cite(?:p)?\{([^}]*)\}'
        matches = re.findall(pattern, content)

        all_keys = []
        for m in matches:
            # FIXED: Re-implemented the original's robust key splitting and cleaning.
            keys = [k.strip() for k in m.split(',')]
            keys = [k for k in keys if k]  # Filter out empty strings from trailing commas etc.
            all_keys.extend(keys)

        counter = Counter(all_keys)
        # The dictionary of keys cited MORE THAN ONCE.
        duplicated_keys = {key: count for key, count in counter.items() if count > 1}
        # The set of ALL UNIQUE cited keys.
        cited_keys = set(all_keys)

        return cited_keys, duplicated_keys

    def analyze_tex_citations(self, tex_file_path):
        """
        NEW: A single, efficient function to perform all .tex-based analysis at once.
        This reads the .tex file only one time.
        """
        if not self.bib_entries:
            raise ValueError("The main .bib file has not been loaded yet.")

        # 1. Extract all citation data in one go
        cited_keys, duplicated_citations = self.extract_citations_from_tex(tex_file_path)

        bib_keys = set(self.bib_entries.keys())

        # 2. Find unreferenced ("zombie") entries
        unreferenced = sorted(list(bib_keys - cited_keys))

        # 3. Find missing ("ghost") entries
        missing_in_bib = sorted(list(cited_keys - bib_keys))

        # 4. Return all results in a dictionary
        return {
            'unreferenced': unreferenced,
            'missing': missing_in_bib,
            'duplicates': duplicated_citations
        }