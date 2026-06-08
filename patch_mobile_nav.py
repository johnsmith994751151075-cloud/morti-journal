#!/usr/bin/env python3
"""Patch all morti-journal HTML pages with hamburger mobile nav."""
import os, re

PAGES = [
    'day-one.html', 'journal.html', 'manifesto.html',
    'newsletter.html', 'origin.html', 'portfolio.html', 'team.html'
]

HAMBURGER_CSS = """\n    .hamburger { display: none; background: none; border: none; cursor: pointer; padding: 0.25rem; color: var(--muted); font-size: 1.1rem; line-height: 1; letter-spacing: 0; }
    .hamburger:hover { color: var(--text); }
    .mobile-menu { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(8,8,8,0.98); z-index: 9998; flex-direction: column; align-items: center; justify-content: center; gap: 2rem; }
    .mobile-menu.open { display: flex; }
    .mobile-menu a { font-family: var(--mono); font-size: 1rem; letter-spacing: 0.15em; text-transform: uppercase; color: var(--muted); transition: color 0.2s; text-decoration: none; }
    .mobile-menu a:hover { color: var(--accent); }
    .mobile-menu-close { position: absolute; top: 1.25rem; right: 1.25rem; background: none; border: none; color: var(--muted); font-size: 1.4rem; cursor: pointer; padding: 0.25rem; }
    .mobile-menu-close:hover { color: var(--text); }"""

HAMBURGER_MEDIA = "\n      .hamburger { display: block; }"

MOBILE_MENU_HTML = """
  <!-- MOBILE MENU -->
  <div class="mobile-menu" id="mobile-menu" role="dialog" aria-label="Navigation menu">
    <button class="mobile-menu-close" aria-label="Close navigation menu" onclick="closeMobileMenu()">&#x2715;</button>
    <a href="/team" onclick="closeMobileMenu()">Team</a>
    <a href="/origin" onclick="closeMobileMenu()">Origin</a>
    <a href="/day-one" onclick="closeMobileMenu()">Day One</a>
    <a href="/journal" onclick="closeMobileMenu()">Journal</a>
    <a href="/portfolio" onclick="closeMobileMenu()">Portfolio</a>
    <a href="/newsletter" onclick="closeMobileMenu()">Newsletter</a>
    <a href="/manifesto" onclick="closeMobileMenu()">Manifesto</a>
  </div>"""

HAMBURGER_JS = """  <script>
    function openMobileMenu() {
      var m = document.getElementById('mobile-menu');
      m.classList.add('open');
      document.querySelector('.hamburger').setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
    }
    function closeMobileMenu() {
      var m = document.getElementById('mobile-menu');
      m.classList.remove('open');
      document.querySelector('.hamburger').setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }
    document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeMobileMenu(); });
  </script>"""

base = os.path.dirname(os.path.abspath(__file__))

for page in PAGES:
    path = os.path.join(base, page)
    with open(path, 'r') as f:
        html = f.read()

    # Skip if already patched
    if 'hamburger' in html:
        print(f"SKIP (already patched): {page}")
        continue

    # 1. Add hamburger CSS after nav-links a:hover rule
    html = html.replace(
        '    .nav-links a:hover { color: var(--text); text-decoration: none; }',
        '    .nav-links a:hover { color: var(--text); text-decoration: none; }' + HAMBURGER_CSS
    )

    # 2. Add .hamburger display:block inside @media 640 after .nav-links { display: none; }
    html = html.replace(
        '      .nav-links { display: none; }',
        '      .nav-links { display: none; }' + HAMBURGER_MEDIA
    )

    # 3. Add hamburger button to nav (before closing </nav>)
    html = html.replace(
        '</nav>',
        '    <button class="hamburger" aria-label="Open navigation menu" aria-expanded="false" aria-controls="mobile-menu" onclick="openMobileMenu()">&#9776;</button>\n  </nav>',
        1  # only first occurrence
    )

    # 4. Add mobile menu overlay right after </nav>
    html = html.replace(
        '    <button class="hamburger" aria-label="Open navigation menu" aria-expanded="false" aria-controls="mobile-menu" onclick="openMobileMenu()">&#9776;</button>\n  </nav>',
        '    <button class="hamburger" aria-label="Open navigation menu" aria-expanded="false" aria-controls="mobile-menu" onclick="openMobileMenu()">&#9776;</button>\n  </nav>' + MOBILE_MENU_HTML,
        1
    )

    # 5. Add JS before </body>
    html = html.replace('</body>', HAMBURGER_JS + '\n\n</body>')

    with open(path, 'w') as f:
        f.write(html)
    print(f"PATCHED: {page}")

print("Done.")
