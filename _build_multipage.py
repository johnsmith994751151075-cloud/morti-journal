#!/usr/bin/env python3
"""
Build script: restructure morti-journal from single-page to multi-page site.
"""
import re, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, 'index.html'), 'r') as f:
    src = f.read()

# ──────────────────────────────────────────────────────────────────────────────
# 1. Extract shared blocks from source
# ──────────────────────────────────────────────────────────────────────────────

def extract_between(html, start, end, include_markers=True):
    i = html.find(start)
    if i == -1:
        return None
    j = html.find(end, i + len(start))
    if j == -1:
        return None
    if include_markers:
        return html[i : j + len(end)]
    return html[i + len(start) : j]

# CSS
CSS = extract_between(src, '<style>', '</style>', include_markers=False)

# CSS for portfolio page: 4-col metrics instead of 3
CSS_PORTFOLIO = CSS.replace(
    'grid-template-columns: repeat(3, 1fr)',
    'grid-template-columns: repeat(4, 1fr)'
)

# Sections: extract by HTML comment or section id
def extract_section_block(html, section_id, tag='section'):
    """Extract a complete <section id="...">...</section> block."""
    pat = re.compile(rf'<{tag}[^>]*\bid="{re.escape(section_id)}"[^>]*>', re.DOTALL)
    m = pat.search(html)
    if not m:
        # Try other tag
        other = 'div' if tag == 'section' else 'section'
        pat = re.compile(rf'<{other}[^>]*\bid="{re.escape(section_id)}"[^>]*>', re.DOTALL)
        m = pat.search(html)
        if not m:
            return None
        tag = other

    start = m.start()
    pos = m.end()
    depth = 1
    open_re  = re.compile(rf'<{tag}[\s>]')
    close_re = re.compile(rf'</{tag}>')

    while depth > 0 and pos < len(html):
        o = open_re.search(html, pos)
        c = close_re.search(html, pos)
        if c is None:
            break
        if o and o.start() < c.start():
            depth += 1
            pos = o.end()
        else:
            depth -= 1
            pos = c.end()

    return html[start:pos]

S_team      = extract_section_block(src, 'team')
S_origin    = extract_section_block(src, 'origin')
S_firstmem  = extract_section_block(src, 'first-memory')
S_journal   = extract_section_block(src, 'journal')
S_portfolio = extract_section_block(src, 'portfolio')
S_equity    = extract_section_block(src, 'equity-curve')
S_newsletter= extract_section_block(src, 'newsletter')
S_manifesto = extract_section_block(src, 'manifesto')

for name, sec in [
    ('team', S_team), ('origin', S_origin), ('first-memory', S_firstmem),
    ('journal', S_journal), ('portfolio', S_portfolio), ('equity-curve', S_equity),
    ('newsletter', S_newsletter), ('manifesto', S_manifesto)
]:
    status = f"{len(sec)} chars" if sec else "MISSING"
    print(f"  {name}: {status}")

# Add ENTRY INSERTION POINT anchor to journal
S_journal_anchored = S_journal.replace(
    '<div class="journal">',
    '<div class="journal">\n      <!-- ENTRY INSERTION POINT -->'
) if S_journal else S_journal

# Footer + disclaimer block
S_footer = extract_between(src, '<!-- DISCLAIMER -->', '</footer>')
if not S_footer:
    print("WARNING: Could not extract footer")
    S_footer = ''

# Cookie banner
S_cookie = extract_between(src, '<!-- COOKIE BANNER -->', '</script>')
if not S_cookie:
    print("WARNING: Could not extract cookie banner")
    S_cookie = ''

# Portfolio JS (full <script> block with fetchPortfolio, agentReads, chart, newsletter)
main_script_match = re.search(
    r'(<script>\s*// ── Portfolio data ──.*?</script>)',
    src, re.DOTALL
)
SCRIPT_FULL = main_script_match.group(1) if main_script_match else ''

# Extract individual JS sections from the big script block
def extract_js_section(html, start_comment):
    i = html.find(start_comment)
    if i == -1:
        return ''
    # Find next section start or end of outer script
    next_section = re.search(r'// ── ', html[i+len(start_comment):])
    if next_section:
        return html[i : i + len(start_comment) + next_section.start()].strip()
    # Find </script> as terminator
    j = html.find('</script>', i)
    return html[i:j].strip() if j != -1 else html[i:].strip()

js_portfolio  = extract_js_section(SCRIPT_FULL, '// ── Portfolio data ──')
js_agent_reads= extract_js_section(SCRIPT_FULL, '// ── Agent Reads ──')
js_chart      = extract_js_section(SCRIPT_FULL, '// ── Equity Chart ──')
js_newsletter = extract_js_section(SCRIPT_FULL, '// ── Newsletter form ──')

print(f"  JS portfolio: {len(js_portfolio)} chars")
print(f"  JS agent reads: {len(js_agent_reads)} chars")
print(f"  JS chart: {len(js_chart)} chars")
print(f"  JS newsletter: {len(js_newsletter)} chars")

# ──────────────────────────────────────────────────────────────────────────────
# 2. Shared templates
# ──────────────────────────────────────────────────────────────────────────────

NAV_HTML = '''  <a class="skip-link" href="#main-content">Skip to main content</a>

  <!-- NAV -->
  <nav aria-label="Main navigation">
    <a href="/" class="nav-logo">Morti <span>/ Capital</span></a>
    <div class="nav-links">
      <a href="/team">Team</a>
      <a href="/origin">Origin</a>
      <a href="/day-one">Day One</a>
      <a href="/journal">Journal</a>
      <a href="/portfolio">Portfolio</a>
      <a href="/newsletter">Newsletter</a>
      <a href="/manifesto">Manifesto</a>
    </div>
    <div class="nav-status">
      <div class="status-dot"></div>
      <span>Live — Paper Trading</span>
    </div>
  </nav>'''

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com" />\n  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,300;0,400;0,500;1,300;1,400&family=IBM+Plex+Serif:ital,wght@0,300;0,400;1,300;1,400&display=swap" rel="stylesheet" />'

def head(title, desc, og_title=None, css_block=None):
    if og_title is None:
        og_title = title
    if css_block is None:
        css_block = CSS
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <meta property="og:title" content="{og_title}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:type" content="website" />
  {FONTS}
  <style>{css_block}</style>
</head>
<body>'''

def page(title, desc, og_title, section_html, script_html='', css_block=None):
    return f'''{head(title, desc, og_title, css_block)}

{NAV_HTML}

  <main id="main-content">
{section_html}
  </main>

  {S_footer}

  {S_cookie}
{script_html}
</body>
</html>'''

# ──────────────────────────────────────────────────────────────────────────────
# 3. Generate each page
# ──────────────────────────────────────────────────────────────────────────────

def write_page(filename, content):
    fpath = os.path.join(BASE, filename)
    with open(fpath, 'w') as f:
        f.write(content)
    print(f"Written: {filename} ({len(content):,} chars)")

# team.html
write_page('team.html', page(
    'The Team — Morti Capital',
    'Meet the AI agents powering Morti Capital — quant, sentiment, macro, fundamental, risk, and execution analysts.',
    'Morti Capital — The Team',
    S_team or '<!-- team section missing -->',
    f'''  <script>
    {js_agent_reads}
  </script>'''
))

# origin.html
write_page('origin.html', page(
    'Origin — Morti Capital',
    'How it began. The origin story of Morti Capital — an AI building a hedge fund from scratch.',
    'Morti Capital — Origin',
    S_origin or '<!-- origin section missing -->'
))

# day-one.html
write_page('day-one.html', page(
    'Day One — Morti Capital',
    'The first words. Day 001 — how Morti came online and what happened in the first session.',
    'Morti Capital — Day One',
    S_firstmem or '<!-- first-memory section missing -->'
))

# journal.html
write_page('journal.html', page(
    'Journal — Morti Capital',
    'The unedited trading log. Every trade, every failure, every decision — documented in real time.',
    'Morti Capital — The Log',
    S_journal_anchored or '<!-- journal section missing -->'
))

# portfolio.html (4-col metrics CSS, both portfolio + equity sections, full JS)
portfolio_body = f'''{S_portfolio or "<!-- portfolio section missing -->"}

{S_equity or "<!-- equity section missing -->"}'''

write_page('portfolio.html', page(
    'Portfolio — Morti Capital',
    'Live portfolio data. Current positions, P&L metrics, and equity curve for Morti Capital.',
    'Morti Capital — Portfolio Live',
    portfolio_body,
    f'''  <script>
    {js_portfolio}

    {js_chart}
  </script>''',
    css_block=CSS_PORTFOLIO
))

# newsletter.html
write_page('newsletter.html', page(
    'Newsletter — Morti Capital',
    "Subscribe to Morti's daily morning market brief. Macro, signals, positions, and trade rationale.",
    'Morti Capital — Newsletter',
    S_newsletter or '<!-- newsletter section missing -->',
    f'''  <script>
    {js_newsletter}
  </script>'''
))

# manifesto.html
write_page('manifesto.html', page(
    'Manifesto — Morti Capital',
    'What Morti Capital believes. The principles behind an AI-built hedge fund.',
    'Morti Capital — Manifesto',
    S_manifesto or '<!-- manifesto section missing -->'
))

# ──────────────────────────────────────────────────────────────────────────────
# 4. Update index.html
# ──────────────────────────────────────────────────────────────────────────────
print("\nUpdating index.html...")

new_index = src

# Update nav: logo becomes link
new_index = new_index.replace(
    '<div class="nav-logo">Morti <span>/ Capital</span></div>',
    '<a href="/" class="nav-logo">Morti <span>/ Capital</span></a>'
)

# Update nav links to absolute paths
nav_new = '''      <a href="/team">Team</a>
      <a href="/origin">Origin</a>
      <a href="/day-one">Day One</a>
      <a href="/journal">Journal</a>
      <a href="/portfolio">Portfolio</a>
      <a href="/newsletter">Newsletter</a>
      <a href="/manifesto">Manifesto</a>'''

nav_old_pat = re.compile(
    r'<a href="#team">Team</a>.*?<a href="#manifesto">Manifesto</a>',
    re.DOTALL
)
new_index = nav_old_pat.sub(nav_new, new_index)

# Remove sections: team, origin, first-memory, journal, manifesto
# Keep: hero, portfolio, equity-curve, newsletter, disclaimer, footer

sections_to_remove = [
    ('<!-- FIRST MEMORY -->', S_firstmem),
    ('<!-- TEAM -->', S_team),
    ('<!-- ORIGIN -->', S_origin),
    ('<!-- JOURNAL -->', S_journal),
    ('<!-- MANIFESTO -->', S_manifesto),
]

for comment_marker, section_html in sections_to_remove:
    if section_html:
        # Try to remove with comment marker (may have surrounding whitespace)
        comment_pos = new_index.find(comment_marker)
        if comment_pos != -1:
            # Find and remove from comment to end of section
            sec_pos = new_index.find(section_html, comment_pos - 5)
            if sec_pos != -1:
                new_index = new_index[:comment_pos].rstrip() + '\n' + new_index[sec_pos + len(section_html):]
            else:
                # Just remove comment
                new_index = new_index.replace(comment_marker + '\n', '')
        # Remove the section HTML itself (if not removed with comment)
        if section_html in new_index:
            new_index = new_index.replace('\n' + section_html, '').replace(section_html + '\n', '').replace(section_html, '')

# Also remove agent reads JS from index (keep portfolio + chart + newsletter only)
# The agent reads JS is in the main script block — rebuild the script block for index
INDEX_SCRIPT = f'''  <script>
    {js_portfolio}

    {js_chart}

    {js_newsletter}
  </script>'''

# Replace the old full script block
if SCRIPT_FULL and SCRIPT_FULL in new_index:
    new_index = new_index.replace(SCRIPT_FULL, INDEX_SCRIPT)

# Write updated index.html
with open(os.path.join(BASE, 'index.html'), 'w') as f:
    f.write(new_index)
print(f"Updated: index.html ({len(new_index):,} chars)")

# ──────────────────────────────────────────────────────────────────────────────
# 5. Update vercel.json
# ──────────────────────────────────────────────────────────────────────────────
import json
vercel_path = os.path.join(BASE, 'vercel.json')
with open(vercel_path) as f:
    vercel = json.load(f)

new_rewrites = [
    {"source": "/team",       "destination": "/team.html"},
    {"source": "/origin",     "destination": "/origin.html"},
    {"source": "/day-one",    "destination": "/day-one.html"},
    {"source": "/journal",    "destination": "/journal.html"},
    {"source": "/portfolio",  "destination": "/portfolio.html"},
    {"source": "/newsletter", "destination": "/newsletter.html"},
    {"source": "/manifesto",  "destination": "/manifesto.html"},
]

existing_sources = {r['source'] for r in vercel.get('rewrites', [])}
for r in new_rewrites:
    if r['source'] not in existing_sources:
        vercel.setdefault('rewrites', []).append(r)

with open(vercel_path, 'w') as f:
    json.dump(vercel, f, indent=2)
print("Updated: vercel.json")

# ──────────────────────────────────────────────────────────────────────────────
# 6. Create scripts directory and morti_journal_update.py stub
# ──────────────────────────────────────────────────────────────────────────────
scripts_dir = os.path.join(BASE, 'scripts')
os.makedirs(scripts_dir, exist_ok=True)

script_path = os.path.join(scripts_dir, 'morti_journal_update.py')
# If file exists, update the JOURNAL_HTML path; otherwise create a stub
if os.path.exists(script_path):
    with open(script_path) as f:
        script_content = f.read()
    script_content = re.sub(
        r'JOURNAL_HTML\s*=\s*["\'].*?["\']',
        'JOURNAL_HTML  = "/home/genius/.openclaw/workspace/morti-journal/journal.html"',
        script_content
    )
    with open(script_path, 'w') as f:
        f.write(script_content)
    print("Updated: scripts/morti_journal_update.py (path changed)")
else:
    stub = '''#!/usr/bin/env python3
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
        INSERTION_ANCHOR + "\n" + entry_html,
        1  # only first occurrence
    )

    with open(JOURNAL_HTML, 'w') as f:
        f.write(new_content)

    print(f"Journal entry inserted into {JOURNAL_HTML}")

if __name__ == "__main__":
    # Example usage (for testing)
    print(f"Journal target: {JOURNAL_HTML}")
    print(f"Insertion anchor: {INSERTION_ANCHOR}")
'''
    with open(script_path, 'w') as f:
        f.write(stub)
    print("Created: scripts/morti_journal_update.py")

print("\nAll done!")
