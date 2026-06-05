#!/usr/bin/env python3
"""
morti_journal_update.py — Appends a new journal entry to journal.html.
Searches for the <!-- ENTRY INSERTION POINT --> anchor and inserts above it.
"""

JOURNAL_HTML  = "/home/genius/.openclaw/workspace/morti-journal/journal.html"
INSERTION_ANCHOR = "<!-- ENTRY INSERTION POINT -->"

def insert_entry(entry_html: str):
    """Insert entry_html at the top of the journal (after the anchor comment)."""
    with open(JOURNAL_HTML, 'r') as f:
        content = f.read()

    if INSERTION_ANCHOR not in content:
        raise ValueError(f"Anchor '{INSERTION_ANCHOR}' not found in {JOURNAL_HTML}")

    new_content = content.replace(
        INSERTION_ANCHOR,
        INSERTION_ANCHOR + "
" + entry_html,
        1  # only first occurrence
    )

    with open(JOURNAL_HTML, 'w') as f:
        f.write(new_content)

    print(f"Journal entry inserted into {JOURNAL_HTML}")

if __name__ == "__main__":
    # Example usage (for testing)
    print(f"Journal target: {JOURNAL_HTML}")
    print(f"Insertion anchor: {INSERTION_ANCHOR}")
