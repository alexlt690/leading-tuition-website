#!/usr/bin/env python3
"""
Build the 3 resource pages:
  seo-generator/output/resources/11-plus.html
  seo-generator/output/resources/pre-11-plus.html
  seo-generator/output/resources/13-plus.html
"""

import csv
import json
import re
from pathlib import Path
from collections import defaultdict

CSV_PATH = Path("/sessions/brave-blissful-mendel/mnt/uploads/resources_page_mapping_with_local_paths_filtered.csv")
OUT_DIR = Path("/sessions/brave-blissful-mendel/mnt/leading-tuition-website/seo-generator/output/resources")


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def clean_repo_filename(src_path_str, is_answer=False):
    src = Path(src_path_str.replace("\\", "/"))
    fname = src.name.lower()
    # Strip leading numeric index e.g. "0225__"
    fname = re.sub(r"^\d+__", "", fname)
    # Strip known source prefixes so they don't appear in URLs
    for prefix in ["elevenaid_", "11plusguide_", "piacademy_"]:
        if fname.startswith(prefix):
            fname = fname[len(prefix):]
            break
    # Strip piacademy-style numeric index immediately before institution name (e.g. "13alleyns")
    fname = re.sub(r"^\d+(?=[a-z])", "", fname)
    fname = fname.lstrip("-_")
    fname = re.sub(r"[^a-z0-9._-]", "-", fname)
    fname = re.sub(r"-+", "-", fname).strip("-")
    if is_answer and not any(x in fname for x in ["mark-scheme", "answers", "answer"]):
        fname = fname.replace(".pdf", "-mark-scheme.pdf")
    return fname


def humanize(title):
    """Convert slug-style 'bancrofts-maths-2018' to 'Bancrofts Maths 2018'. Keep real titles."""
    if " " in title:
        return title.strip()
    t = title.replace("-", " ").replace("_", " ")
    return " ".join(w.capitalize() for w in t.split())


# ── Load CSV ──────────────────────────────────────────────────────────────────
EXCLUDED_INSTITUTIONS = {"PiAcademy Practice"}

rows = []
with open(CSV_PATH, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["institution"] not in EXCLUDED_INSTITUTIONS:
            rows.append(row)

# Build per-page data
pages_data = defaultdict(list)
for row in rows:
    slug = row["page_slug"]
    institution = row["institution"]
    inst_slug = slugify(institution)
    subject = row["subject"]
    year_raw = row["year"].strip()
    year = str(int(float(year_raw))) if year_raw else ""
    display_title = humanize(row["display_title"])

    q_src = (row["question_absolute_path"] or "").strip()
    a_src = (row["answer_absolute_path"] or "").strip()
    if not q_src:
        continue  # skip rows with no question path
    has_answer = row["answer_file_exists"] == "True" and bool(a_src)

    q_fname = clean_repo_filename(q_src, False)
    a_fname = clean_repo_filename(a_src, True) if has_answer else ""

    repo_q = f"/public/papers/{slug}/{inst_slug}/{q_fname}"
    repo_a = f"/public/papers/{slug}/{inst_slug}/{a_fname}" if has_answer else ""
    # R2 key for answer (no leading slash, no /public/ prefix) — used by paid download system
    r2_key = f"{slug}/{inst_slug}/{a_fname}" if has_answer else ""

    pages_data[slug].append({
        "i": institution,
        "s": subject,
        "y": year,
        "t": display_title,
        "q": repo_q,
        "a": repo_a,
        "ak": r2_key,   # answer R2 key — empty until answers uploaded
    })


# ── Page configs ──────────────────────────────────────────────────────────────
PAGE_CONFIGS = {
    "11-plus": {
        "file": "11-plus.html",
        "title": "11+ Past Papers | Free Practice Papers by School | Leading Tuition",
        "desc": "Download free 11+ past papers from 54 UK independent and grammar schools. Maths, English, VR and more — organised by school and year. All PDFs direct download.",
        "canonical": "https://www.leadingtuition.co.uk/resources/11-plus",
        "h1": "11+ Past Papers",
        "subtitle": "Free practice papers from 54 schools — Maths, English, VR and more. All available as direct PDF downloads.",
        "breadcrumb_name": "11+ Past Papers",
        "schema_name": "11+ Past Papers",
    },
    "pre-11-plus": {
        "file": "pre-11-plus.html",
        "title": "Pre-11+ Papers | 7+, 8+, 9+ & 10+ Practice Papers | Leading Tuition",
        "desc": "Download free pre-11+ past papers for 7+, 8+, 9+ and 10+ entry. Practice Maths and English papers from leading independent schools — all free, direct PDF downloads.",
        "canonical": "https://www.leadingtuition.co.uk/resources/pre-11-plus",
        "h1": "Pre-11+ Past Papers",
        "subtitle": "Free 7+, 8+, 9+ and 10+ entry papers from top independent schools. All available as direct PDF downloads.",
        "breadcrumb_name": "Pre-11+ Past Papers",
        "schema_name": "Pre-11+ Past Papers",
    },
    "13-plus": {
        "file": "13-plus.html",
        "title": "13+ Past Papers | Common Entrance & CE Papers | Leading Tuition",
        "desc": "Download free 13+ Common Entrance past papers covering Maths, English and Biology. Papers from top independent schools, organised by school and year.",
        "canonical": "https://www.leadingtuition.co.uk/resources/13-plus",
        "h1": "13+ Past Papers",
        "subtitle": "Free Common Entrance and 13+ papers covering Maths, English and Biology — organised by school and year.",
        "breadcrumb_name": "13+ Past Papers",
        "schema_name": "13+ Past Papers",
    },
}

NAVBAR = """<nav class="navbar">
  <a href="/" class="navbar-brand">
    <img src="/images/logo.png" alt="Leading Tuition logo" />
    Leading Tuition
  </a>

  <button class="nav-hamburger" id="navHamburger" aria-label="Open menu" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>

  <ul class="navbar-nav" id="navbarNav">
    <li><a href="/">Home</a></li>
    <li><a href="/about">About Us</a></li>

    <!-- Services mega-dropdown (4 columns) -->
    <li class="nav-dropdown">
      <a href="/services" class="nav-dropdown-toggle">Services <span class="nav-caret">&#9660;</span></a>
      <div class="nav-mega-menu">
        <div class="nav-mega-header">
          <a href="/services">&#8592; Our Services</a>
        </div>

        <div class="nav-mega-cols">

          <!-- Column 1: Subjects -->
          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Subjects</div>
            <a href="/services/subjects/maths-tutor">Maths</a>
            <a href="/services/subjects/biology-tutor">Biology</a>
            <a href="/services/subjects/chemistry-tutor">Chemistry</a>
            <a href="/services/subjects/physics-tutor">Physics</a>
            <a href="/services/subjects/english-language-tutor">English Language</a>
            <a href="/services/subjects/english-literature-tutor">English Literature</a>
            <a href="/services/subjects/history-tutor">History</a>
            <a href="/services/subjects/geography-tutor">Geography</a>
            <a href="/services/subjects/economics-tutor">Economics</a>
            <a href="/services/subjects/politics-tutor">Politics</a>
            <a href="/services/subjects/psychology-tutor">Psychology</a>
            <a href="/services/subjects/computer-science-tutor">Computer Science</a>
            <a href="/services/subjects/business-studies-tutor">Business Studies</a>
            <a href="/services/subjects/further-maths-tutor">Further Maths</a>
            <a href="/services/subjects/statistics-tutor">Statistics</a>
          </div>

          <!-- Column 2: Levels -->
          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Levels</div>
            <a href="/services/levels/11plus-tuition">11+ Tuition</a>
            <a href="/11-plus/">11+ School Guides</a>
            <a href="/services/levels/13plus-tuition">13+ Tuition</a>
            <div class="nav-flyout">
              <a href="/gcse/">GCSE Tuition</a>
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">&#9662;</button>
              <div class="nav-flyout-menu">
                <a href="/subjects/gcse-maths/">Maths</a>
                <a href="/subjects/gcse-chemistry/">Chemistry</a>
              </div>
            </div>
            <div class="nav-flyout">
              <a href="/a-level/">A-Level Tuition</a>
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">&#9662;</button>
              <div class="nav-flyout-menu">
                <a href="/subjects/a-level-maths/">Maths</a>
                <a href="/subjects/a-level-biology/">Biology</a>
                <a href="/subjects/a-level-chemistry/">Chemistry</a>
                <a href="/subjects/a-level-english/">English</a>
              </div>
            </div>
            <a href="/services/levels/primary-tuition">Primary Tuition</a>
            <a href="/services/levels/sats-tuition">SATs Tuition</a>
            <a href="/services/levels/university-tuition">University Tuition</a>
          </div>

          <!-- Column 3: Medicine -->
          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Medicine</div>
            <a href="/services/specialist-admissions/medicine-prep-hub">Medicine Prep Hub</a>
            <div class="nav-flyout">
              <a href="/medical-schools/">Medical School Guides</a>
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">&#9662;</button>
              <div class="nav-flyout-menu nav-flyout-menu--cols">
                <a href="/medical-schools/aberdeen">Aberdeen</a>
                <a href="/medical-schools/anglia-ruskin">Anglia Ruskin</a>
                <a href="/medical-schools/aston">Aston</a>
                <a href="/medical-schools/barts">Barts &amp; London</a>
                <a href="/medical-schools/birmingham">Birmingham</a>
                <a href="/medical-schools/brighton-sussex">Brighton &amp; Sussex</a>
                <a href="/medical-schools/bristol">Bristol</a>
                <a href="/medical-schools/cambridge">Cambridge</a>
                <a href="/medical-schools/cardiff">Cardiff</a>
                <a href="/medical-schools/dundee">Dundee</a>
                <a href="/medical-schools/east-anglia">East Anglia</a>
                <a href="/medical-schools/edinburgh">Edinburgh</a>
                <a href="/medical-schools/exeter">Exeter</a>
                <a href="/medical-schools/glasgow">Glasgow</a>
                <a href="/medical-schools/hull-york">Hull York</a>
                <a href="/medical-schools/imperial">Imperial</a>
                <a href="/medical-schools/keele">Keele</a>
                <a href="/medical-schools/kings">King&#39;s College London</a>
                <a href="/medical-schools/lancaster">Lancaster</a>
                <a href="/medical-schools/leeds">Leeds</a>
                <a href="/medical-schools/leicester">Leicester</a>
                <a href="/medical-schools/lincoln">Lincoln</a>
                <a href="/medical-schools/liverpool">Liverpool</a>
                <a href="/medical-schools/manchester">Manchester</a>
                <a href="/medical-schools/newcastle">Newcastle</a>
                <a href="/medical-schools/nottingham">Nottingham</a>
                <a href="/medical-schools/oxford">Oxford</a>
                <a href="/medical-schools/plymouth">Plymouth</a>
                <a href="/medical-schools/queens-belfast">Queen&#39;s Belfast</a>
                <a href="/medical-schools/sheffield">Sheffield</a>
                <a href="/medical-schools/southampton">Southampton</a>
                <a href="/medical-schools/st-andrews">St Andrews</a>
                <a href="/medical-schools/st-georges">St George&#39;s</a>
                <a href="/medical-schools/sunderland">Sunderland</a>
                <a href="/medical-schools/swansea">Swansea</a>
                <a href="/medical-schools/ucl">UCL</a>
                <a href="/medical-schools/uclan">UCLAN</a>
                <a href="/medical-schools/warwick">Warwick</a>
              </div>
            </div>
            <a href="/services/specialist-admissions/medical-school-interviews/">Medical School Interviews</a>
            <a href="/services/specialist-admissions/ucat-tutor">UCAT Tutor</a>
            <a href="/services/specialist-admissions/mmi-interview-coaching">MMI Interview Coaching</a>
          </div>

          <!-- Column 4: Oxbridge -->
          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Oxbridge</div>
            <div class="nav-flyout">
              <a href="/oxbridge-interviews/">Oxbridge Interview Preparation</a>
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">&#9662;</button>
              <div class="nav-flyout-menu nav-flyout-menu--two-cols">
                <a href="/oxbridge-interviews/biology-interview">Biology</a>
                <a href="/oxbridge-interviews/chemistry-interview">Chemistry</a>
                <a href="/oxbridge-interviews/classics-interview">Classics</a>
                <a href="/oxbridge-interviews/computer-science-interview">Computer Science</a>
                <a href="/oxbridge-interviews/economics-interview">Economics</a>
                <a href="/oxbridge-interviews/engineering-interview">Engineering</a>
                <a href="/oxbridge-interviews/english-interview">English</a>
                <a href="/oxbridge-interviews/geography-interview">Geography</a>
                <a href="/oxbridge-interviews/history-interview">History</a>
                <a href="/oxbridge-interviews/law-interview">Law</a>
                <a href="/oxbridge-interviews/maths-interview">Mathematics</a>
                <a href="/oxbridge-interviews/medicine-interview">Medicine</a>
                <a href="/oxbridge-interviews/modern-languages-interview">Modern Languages</a>
                <a href="/oxbridge-interviews/natural-sciences-interview">Natural Sciences</a>
                <a href="/oxbridge-interviews/philosophy-interview">Philosophy</a>
                <a href="/oxbridge-interviews/physics-interview">Physics</a>
                <a href="/oxbridge-interviews/ppe-interview">PPE</a>
                <a href="/oxbridge-interviews/psychology-interview">Psychology</a>
              </div>
            </div>
            <a href="/services/specialist-admissions/oxbridge-admissions-preparation">Oxbridge Admissions Preparation</a>
            <a href="/services/specialist-admissions/oxbridge-subject-preparation">Oxbridge Subject Preparation</a>
            <a href="/services/specialist-admissions/university-personal-statement">University Personal Statement Help</a>
            <div class="nav-flyout">
              <a href="/admissions-tests/">Oxbridge Admissions Tests</a>
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">&#9662;</button>
              <div class="nav-flyout-menu nav-flyout-menu--two-cols">
                <a href="/admissions-tests/lnat-preparation/">LNAT (Law)</a>
                <a href="/admissions-tests/mat-preparation/">MAT (Maths)</a>
                <a href="/admissions-tests/tsa-preparation/">TSA</a>
                <a href="/admissions-tests/pat-preparation/">PAT (Physics)</a>
                <a href="/admissions-tests/step-preparation/">STEP (Maths)</a>
                <a href="/admissions-tests/tmua-preparation/">TMUA</a>
                <a href="/admissions-tests/esat-preparation/">ESAT (Engineering)</a>
                <a href="/admissions-tests/hat-preparation/">HAT (History)</a>
                <a href="/admissions-tests/elat-preparation/">ELAT (English)</a>
                <a href="/admissions-tests/mlat-preparation/">MLAT (Languages)</a>
                <a href="/admissions-tests/phil-preparation/">Philosophy Test</a>
                <a href="/admissions-tests/bmat-history/">BMAT History</a>
              </div>
            </div>
          </div>

        </div>
      </div>
    </li>

    <!-- Resources dropdown -->
    <li class="nav-dropdown">
      <a href="/resources/" class="nav-dropdown-toggle">Resources <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu">
        <a href="/resources/pre-11-plus">Pre 11+ Resources</a>
        <a href="/resources/11-plus">11+ Resources</a>
        <a href="/resources/13-plus">13+ Resources</a>
        <a href="/resources/oxbridge-interview-questions">Oxbridge Interview Questions</a>
        <a href="/resources/gcse-resources-for-parents">GCSE Resources for Parents</a>
        <a href="/resources/" style="font-weight:600;color:#e63946;">View all resources &rarr;</a>
      </div>
    </li>

    <!-- Blog dropdown -->
    <li class="nav-dropdown">
      <a href="/blog/" class="nav-dropdown-toggle">Blog <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu">
        <span class="nav-dropdown-category">11+ &amp; Grammar School</span>
        <a href="/blog/what-is-the-11-plus-exam">What is the 11 Plus Exam?</a>
        <a href="/blog/the-6-month-11-plus-countdown-a-monthly-study-milestone-plan">11 Plus 6-Month Countdown</a>
        <a href="/blog/2026-grammar-school-league-tables-top-schools-ranked-by-gcse-results">Grammar School League Tables 2026</a>
        <span class="nav-dropdown-category">Medical &amp; Oxbridge</span>
        <a href="/blog/ucat-score-requirements-for-uk-medical-schools-2025">UCAT Score Requirements 2025</a>
        <a href="/blog/how-to-prepare-for-a-medical-school-mmi-interview">How to Prepare for MMI Interviews</a>
        <a href="/blog/oxbridge-interview-questions-100-real-examples-for-every-major-subject">Oxbridge Interview Questions</a>
        <span class="nav-dropdown-category">GCSE &amp; Tuition</span>
        <a href="/blog/how-long-does-gcse-revision-take">How Long Does GCSE Revision Take?</a>
        <a href="/blog/how-to-find-a-good-private-tutor">How to Find a Good Private Tutor</a>
        <a href="/blog/is-private-tuition-worth-it-a-cost-benefit-analysis-of-1-to-1-learning">Is Private Tuition Worth It?</a>
        <a href="/blog/" style="font-weight:600;color:#e63946;">View all 30 posts &rarr;</a>
      </div>
    </li>

    <!-- Locations dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Locations <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu nav-dropdown-menu--cols">
        <a href="/locations/london">London</a>
        <a href="/locations/birmingham">Birmingham</a>
        <a href="/locations/manchester">Manchester</a>
        <a href="/locations/leeds">Leeds</a>
        <a href="/locations/bristol">Bristol</a>
        <a href="/locations/sheffield">Sheffield</a>
        <a href="/locations/leicester">Leicester</a>
        <a href="/locations/liverpool">Liverpool</a>
        <a href="/locations/nottingham">Nottingham</a>
        <a href="/locations/cambridge">Cambridge</a>
        <a href="/locations/oxford">Oxford</a>
        <a href="/locations/brighton">Brighton</a>
        <a href="/locations/guildford">Guildford</a>
        <a href="/locations/reading">Reading</a>
        <a href="/locations/barnet">Barnet</a>
        <a href="/locations/bath">Bath</a>
        <a href="/locations/bromley">Bromley</a>
        <a href="/locations/cheltenham">Cheltenham</a>
        <a href="/locations/coventry">Coventry</a>
        <a href="/locations/croydon">Croydon</a>
        <a href="/locations/derby">Derby</a>
        <a href="/locations/ealing">Ealing</a>
        <a href="/locations/exeter">Exeter</a>
        <a href="/locations/harrow">Harrow</a>
        <a href="/locations/kingston-upon-thames">Kingston upon Thames</a>
        <a href="/locations/luton">Luton</a>
        <a href="/locations/milton-keynes">Milton Keynes</a>
        <a href="/locations/northampton">Northampton</a>
        <a href="/locations/norwich">Norwich</a>
        <a href="/locations/portsmouth">Portsmouth</a>
        <a href="/locations/slough">Slough</a>
        <a href="/locations/twickenham">Twickenham</a>
        <a href="/locations/watford">Watford</a>
        <a href="/locations/wimbledon">Wimbledon</a>
        <a href="/locations/york">York</a>
      </div>
    </li>

    <li><a href="/tutors">Our Tutors</a></li>
    <li><a href="/faqs">FAQs</a></li>
    <li><a href="/contact">Contact Us</a></li>
  </ul>
</nav>"""

FOOTER = """<footer>
  <h3>Get In Touch</h3>
  <hr />
  <div class="footer-contact">
    <p>
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.62 10.79a15.05 15.05 0 006.59 6.59l2.2-2.2a1 1 0 011.01-.24c1.12.37 2.33.57 3.58.57a1 1 0 011 1V20a1 1 0 01-1 1C10.56 21 3 13.44 3 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.57 3.58a1 1 0 01-.25 1.01l-2.2 2.2z"/></svg>
      +44 207 167 8440
    </p>
    <p>
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
      hello@leadingtuition.co.uk
    </p>
  </div>

  <div class="footer-social">
    <a href="https://facebook.com" target="_blank" rel="noopener noreferrer" aria-label="Facebook">
      <svg viewBox="0 0 24 24"><path d="M18 2h-3a5 5 0 00-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 011-1h3z"/></svg>
    </a>
    <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" aria-label="Instagram">
      <svg viewBox="0 0 24 24"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1112.63 8 4 4 0 0116 11.37z" fill="none" stroke="white" stroke-width="2"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5" stroke="white" stroke-width="2"/></svg>
    </a>
    <a href="https://wa.me/447360278449" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp">
      <svg viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
    </a>
    <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
      <svg viewBox="0 0 24 24"><path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6zM2 9h4v12H2z"/><circle cx="4" cy="4" r="2"/></svg>
    </a>
  </div>

  <div class="copyright">COPYRIGHT &copy;2026, Leading Tuition. ALL RIGHTS RESERVED.</div>
</footer>"""

NAV_JS = """<script>
(function() {
  var hamburger = document.getElementById('navHamburger');
  var nav       = document.getElementById('navbarNav');
  if (!hamburger || !nav) return;

  hamburger.addEventListener('click', function() {
    var open = nav.classList.toggle('open');
    hamburger.classList.toggle('active', open);
    hamburger.setAttribute('aria-expanded', open);
  });

  var toggles = document.querySelectorAll('.nav-dropdown-toggle');
  toggles.forEach(function(toggle) {
    toggle.addEventListener('click', function(e) {
      if (window.innerWidth <= 900) {
        e.preventDefault();
        var li = this.parentElement;
        li.classList.toggle('open');
      }
    });
  });

  var flyoutToggles = document.querySelectorAll('.nav-flyout-toggle');
  flyoutToggles.forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      var flyout = this.parentElement;
      flyout.classList.toggle('open');
      this.setAttribute('aria-expanded', flyout.classList.contains('open'));
    });
  });

  document.addEventListener('click', function(e) {
    if (!e.target.closest('.navbar')) {
      nav.classList.remove('open');
      hamburger.classList.remove('active');
      hamburger.setAttribute('aria-expanded', 'false');
    }
  });
})();
</script>"""

PAPERS_CSS = """<style>
/* ── Papers page styles ─────────────────────────────────── */
.papers-hero-pills {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-top: 1rem;
}
.papers-hero-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 20px;
  padding: 0.3rem 0.85rem;
  font-size: 0.82rem;
  color: rgba(255,255,255,0.9);
}
.papers-main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 2rem 1.5rem 3rem;
}
/* Subject tabs */
.papers-tabs {
  display: flex;
  gap: 0;
  flex-wrap: wrap;
  border-bottom: 2px solid #dee2e6;
  margin-bottom: 1.25rem;
}
.ptab {
  padding: 0.6rem 1.1rem;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 0.875rem;
  color: #666;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.15s;
  font-family: inherit;
}
.ptab:hover { color: #1d3557; }
.ptab.active { color: #1d3557; border-bottom-color: #e63946; font-weight: 600; }
/* Filters */
.papers-filters {
  display: flex;
  gap: 0.625rem;
  flex-wrap: wrap;
  align-items: center;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
}
.papers-filters select,
.papers-filters input[type="search"] {
  padding: 0.375rem 0.625rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.85rem;
  background: #fff;
  font-family: inherit;
  color: #333;
}
.papers-filters select { min-width: 165px; }
.papers-filters input[type="search"] { flex: 1; min-width: 140px; }
.pf-toggle {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.85rem;
  color: #444;
  cursor: pointer;
  white-space: nowrap;
}
#pfReset {
  padding: 0.375rem 0.875rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background: #fff;
  font-size: 0.85rem;
  cursor: pointer;
  color: #555;
  font-family: inherit;
}
#pfReset:hover { background: #e9ecef; }
/* Summary */
.papers-summary {
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 1rem;
}
/* Accordion */
.papers-accordion { display: flex; flex-direction: column; gap: 0.4rem; }
.pa-item {
  border: 1px solid #e0e4e8;
  border-radius: 6px;
  overflow: hidden;
}
.pa-header {
  width: 100%;
  display: flex;
  align-items: center;
  padding: 0.8rem 1.25rem;
  background: #fff;
  border: none;
  cursor: pointer;
  text-align: left;
  gap: 0.75rem;
  transition: background 0.15s;
  font-family: inherit;
}
.pa-header:hover { background: #f8f9fa; }
.pa-header.open { background: #f0f6ff; border-bottom: 1px solid #e0e4e8; }
.pa-inst-name { font-weight: 600; color: #1d3557; font-size: 0.925rem; flex: 1; }
.pa-count { font-size: 0.78rem; color: #999; white-space: nowrap; }
.pa-chevron { font-size: 1rem; color: #aaa; transition: transform 0.2s; line-height: 1; flex-shrink: 0; }
.pa-header.open .pa-chevron { transform: rotate(90deg); }
.pa-body { background: #fff; }
.pa-year-group { border-top: 1px solid #f0f0f0; padding: 0.75rem 1.25rem 0.875rem; }
.pa-year-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #aaa;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.5rem;
}
/* Table */
.pa-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.pa-table th {
  text-align: left;
  color: #aaa;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0 0.625rem 0.4rem;
  border-bottom: 1px solid #eee;
}
.pa-table td { padding: 0.45rem 0.625rem; border-bottom: 1px solid #f5f5f5; vertical-align: middle; }
.pa-table tr:last-child td { border-bottom: none; }
.pa-title { color: #333; max-width: 380px; line-height: 1.35; }
/* Buttons */
.pa-btn {
  display: inline-block;
  padding: 0.28rem 0.7rem;
  border-radius: 4px;
  font-size: 0.78rem;
  font-weight: 600;
  text-decoration: none;
  background: #1d3557;
  color: #fff;
  white-space: nowrap;
  transition: background 0.15s;
}
.pa-btn:hover { background: #16294a; }
.pa-btn-ans { background: #457b9d; }
.pa-btn-ans:hover { background: #3a6a8a; }
.pa-no-ans { font-size: 0.78rem; color: #ccc; }
/* Subject badges */
.pa-subj-badge {
  display: inline-block;
  padding: 0.12rem 0.45rem;
  border-radius: 3px;
  font-size: 0.72rem;
  font-weight: 600;
  white-space: nowrap;
}
.pa-subj-maths      { background: #e8f0fe; color: #1a56db; }
.pa-subj-english    { background: #fef3c7; color: #92400e; }
.pa-subj-vr         { background: #d1fae5; color: #065f46; }
.pa-subj-nvr        { background: #ede9fe; color: #5b21b6; }
.pa-subj-mixedother { background: #f3f4f6; color: #374151; }
.pa-subj-biology    { background: #d1fae5; color: #065f46; }
/* Mobile cards */
.pa-cards { display: none; }
.papers-empty {
  text-align: center;
  padding: 3rem 1.5rem;
  color: #aaa;
  font-size: 0.95rem;
}
/* CTA strip */
.papers-cta {
  margin-top: 3rem;
  background: #f1faee;
  border-left: 4px solid #457b9d;
  border-radius: 6px;
  padding: 1.75rem 2rem;
}
.papers-cta h2 { margin-top: 0; font-size: 1.1rem; }
.papers-cta p { color: #555; line-height: 1.7; margin-bottom: 1rem; }
.papers-cta a.cta-btn {
  display: inline-block;
  padding: 0.7rem 1.5rem;
  background: #e63946;
  color: #fff;
  border-radius: 4px;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
}
/* Responsive */
@media (max-width: 720px) {
  .pa-table { display: none; }
  .pa-cards { display: block; }
  .pa-card {
    border: 1px solid #eee;
    border-radius: 6px;
    padding: 0.75rem;
    margin-bottom: 0.4rem;
    background: #fafafa;
  }
  .pa-card-title { font-size: 0.85rem; color: #333; font-weight: 500; margin-bottom: 0.35rem; line-height: 1.35; }
  .pa-card-meta { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
  .pa-card-year { font-size: 0.75rem; color: #999; }
  .pa-card-actions { display: flex; gap: 0.4rem; flex-wrap: wrap; }
  .papers-filters { gap: 0.4rem; }
  .papers-filters select { min-width: 130px; }
  .papers-tabs { gap: 0; }
  .ptab { padding: 0.5rem 0.75rem; font-size: 0.82rem; }
  .papers-main { padding: 1.25rem 1rem 2.5rem; }
}
/* ── Cart button ─────────────────────────────────────────────────────── */
.pa-add-btn {
  display: inline-block;
  padding: 0.28rem 0.7rem;
  border-radius: 4px;
  font-size: 0.78rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  background: #f0f6ff;
  color: #1d3557;
  border: 1px solid #c7daf5;
  white-space: nowrap;
  transition: background 0.15s, color 0.15s;
  font-family: inherit;
}
.pa-add-btn:hover { background: #dceeff; }
.pa-add-btn.cart-added { background: #1d3557; color: #fff; border-color: #1d3557; }
/* ── Sticky cart bar ─────────────────────────────────────────────────── */
#cartBar {
  display: none;
  position: fixed;
  bottom: 0; left: 0; right: 0;
  background: #1d3557;
  color: #fff;
  padding: 0.75rem 1.5rem;
  z-index: 9999;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  box-shadow: 0 -2px 12px rgba(0,0,0,0.2);
  font-family: inherit;
}
#cartBar.visible { display: flex; }
.cart-left { display: flex; flex-direction: column; gap: 0.1rem; }
.cart-count { font-weight: 700; font-size: 0.95rem; }
.cart-msg { font-size: 0.78rem; color: #a8c9e4; }
.cart-right { display: flex; align-items: center; gap: 1rem; flex-shrink: 0; }
.cart-price { font-size: 1.1rem; font-weight: 700; }
.cart-buy-btn {
  padding: 0.55rem 1.4rem;
  background: #e63946;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}
.cart-buy-btn:hover { background: #c1121f; }
@media (max-width: 720px) {
  #cartBar { flex-direction: column; align-items: flex-start; padding: 0.75rem 1rem; }
  .cart-right { width: 100%; justify-content: space-between; }
}
</style>"""


def build_page(slug, cfg, data):
    items = data.get(slug, [])
    total = len(items)
    institutions = sorted(set(p["i"] for p in items))
    num_insts = len(institutions)
    subjects = sorted(set(p["s"] for p in items))

    # Subject counts for tabs
    subj_counts = {}
    for p in items:
        subj_counts[p["s"]] = subj_counts.get(p["s"], 0) + 1

    # Build tabs
    tabs_html = f'<button class="ptab active" data-subject="">All ({total})</button>\n'
    subject_order = ["Maths", "English", "VR", "NVR", "Biology", "Mixed/Other"]
    for s in subject_order:
        if s in subj_counts:
            tabs_html += f'    <button class="ptab" data-subject="{s}">{s} ({subj_counts[s]})</button>\n'
    for s in subjects:
        if s not in subject_order and s in subj_counts:
            tabs_html += f'    <button class="ptab" data-subject="{s}">{s} ({subj_counts[s]})</button>\n'

    # Institution options for filter
    inst_options = "\n".join(
        f'<option value="{i}">{i}</option>' for i in institutions
    )

    # All years
    all_years = sorted(set(p["y"] for p in items if p["y"]), reverse=True)
    year_options = "\n".join(f'<option value="{y}">{y}</option>' for y in all_years)

    # Compact JSON for data
    data_json = json.dumps(items, separators=(",", ":"), ensure_ascii=False)

    canonical = cfg["canonical"]
    breadcrumb_name = cfg["breadcrumb_name"]
    schema_name = cfg["schema_name"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="google-site-verification" content="google81c812594c7ae29d" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Leading Tuition" />
  <meta property="og:image" content="https://www.leadingtuition.co.uk/images/og-default.jpg" />
  <meta property="og:locale" content="en_GB" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:image" content="https://www.leadingtuition.co.uk/images/og-default.jpg" />
  <link rel="stylesheet" href="/style.css" />
  <link rel="icon" type="image/png" href="/images/favicon.png" />
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-D49V0X7BHL"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-D49V0X7BHL');
  </script>
  <title>{cfg["title"]}</title>
  <meta name="description" content="{cfg["desc"]}" />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:title" content="{cfg["title"]}" />
  <meta property="og:description" content="{cfg["desc"]}" />
  <meta property="og:url" content="{canonical}" />
  <meta name="twitter:title" content="{cfg["title"]}" />
  <meta name="twitter:description" content="{cfg["desc"]}" />
  {PAPERS_CSS}
</head>
<body>

{NAVBAR}

<!-- HERO -->
<section class="hero" style="background: linear-gradient(135deg, #1d3557 0%, #457b9d 100%); min-height: 240px;">
  <div class="hero-content">
    <h1>{cfg["h1"]}</h1>
    <p style="font-size:1.05rem; margin-top:0.5rem; color:#f1faee;">{cfg["subtitle"]}</p>
    <div class="papers-hero-pills">
      <span class="papers-hero-pill">&#10003; {total} papers</span>
      <span class="papers-hero-pill">&#10003; {num_insts} institutions</span>
      <span class="papers-hero-pill">&#10003; All free &amp; direct download</span>
    </div>
  </div>
</section>

<!-- BREADCRUMB -->
<nav aria-label="Breadcrumb" style="padding:0.65rem 1.5rem; background:#f8f9fa; font-size:0.85rem;">
  <ol style="list-style:none; margin:0; padding:0; display:flex; gap:0.4rem; flex-wrap:wrap;">
    <li><a href="/" style="color:#457b9d;">Home</a></li>
    <li style="color:#bbb;">&rsaquo;</li>
    <li><a href="/resources/" style="color:#457b9d;">Resources</a></li>
    <li style="color:#bbb;">&rsaquo;</li>
    <li style="color:#555;">{breadcrumb_name}</li>
  </ol>
</nav>

<!-- PAPERS UI -->
<main class="papers-main">

  <!-- Subject tabs -->
  <div class="papers-tabs" id="papersTabs">
    {tabs_html}
  </div>

  <!-- Filter bar -->
  <div class="papers-filters" id="papersFilters">
    <select id="pfInstitution" aria-label="Filter by institution">
      <option value="">All institutions</option>
      {inst_options}
    </select>
    <select id="pfYear" aria-label="Filter by year">
      <option value="">All years</option>
      {year_options}
    </select>
    <input type="search" id="pfSearch" placeholder="Search papers&hellip;" aria-label="Search papers" />
    <button id="pfReset" type="button">Reset</button>
  </div>

  <!-- Summary line -->
  <div id="papersSummary" class="papers-summary"></div>

  <!-- Results accordion -->
  <div id="papersAccordion" class="papers-accordion"></div>

  <!-- No results -->
  <div id="papersEmpty" class="papers-empty" style="display:none;">
    No papers match your filters. <button onclick="resetAll()" style="background:none;border:none;color:#457b9d;cursor:pointer;font-size:inherit;text-decoration:underline;">Reset filters</button>
  </div>

  <!-- CTA -->
  <div class="papers-cta">
    <h2>Need Expert Tuition Alongside These Papers?</h2>
    <p>Our specialist tutors work through past papers with your child, identifying gaps and building exam technique. Book a free consultation to find out how we can help.</p>
    <a href="/consultation" class="cta-btn">Book a Free Consultation</a>
  </div>

</main>

<!-- RELATED CALLOUT -->
<section style="max-width:1100px; margin:0 auto 0; padding:0 1.5rem 2.5rem;">
  <div style="background:#f1faee; border-left:4px solid #457b9d; padding:1.5rem 2rem; border-radius:6px;">
    <h2 style="margin-top:0; font-size:1rem; color:#1d3557;">Related: Tuition &amp; Preparation Services</h2>
    <ul style="margin:0; padding-left:1.25rem; columns:2; column-gap:2rem; font-size:0.875rem; color:#444; line-height:2.1;">
      <li><a href="/services/levels/11plus-tuition" style="color:#1d3557;">11+ Tuition</a></li>
      <li><a href="/services/levels/13plus-tuition" style="color:#1d3557;">13+ Tuition</a></li>
      <li><a href="/11-plus/" style="color:#1d3557;">11+ School Guides</a></li>
      <li><a href="/gcse/" style="color:#1d3557;">GCSE Tuition</a></li>
      <li><a href="/a-level/" style="color:#1d3557;">A-Level Tuition</a></li>
      <li><a href="/consultation" style="color:#1d3557;">Book a Free Consultation</a></li>
    </ul>
  </div>
</section>

<!-- CART BAR -->
<div id="cartBar" role="region" aria-label="Answer cart">
  <div class="cart-left">
    <span class="cart-count" id="cartCount">0 answers in cart</span>
    <span class="cart-msg" id="cartMsg"></span>
  </div>
  <div class="cart-right">
    <span class="cart-price" id="cartPrice">£0.00</span>
    <button class="cart-buy-btn" id="cartBuy">Buy answers &rarr;</button>
  </div>
</div>

{FOOTER}

{NAV_JS}

<script>
var PAPERS_DATA = {data_json};

var activeSubject   = '';
var activeInst      = '';
var activeYear      = '';
var activeSearch    = '';

function esc(s) {{
  return String(s)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}}

function subjClass(s) {{
  return s.toLowerCase().replace(/[^a-z0-9]/g,'-');
}}

function getFiltered() {{
  return PAPERS_DATA.filter(function(p) {{
    if (activeSubject && p.s !== activeSubject) return false;
    if (activeInst    && p.i !== activeInst)    return false;
    if (activeYear    && p.y !== activeYear)    return false;
    if (activeSearch) {{
      var q = activeSearch.toLowerCase();
      if (p.t.toLowerCase().indexOf(q) === -1 &&
          p.i.toLowerCase().indexOf(q) === -1 &&
          p.y.indexOf(q)               === -1 &&
          p.s.toLowerCase().indexOf(q) === -1) return false;
    }}
    return true;
  }});
}}

function render() {{
  var filtered = getFiltered();

  // Group by institution
  var byInst = {{}};
  filtered.forEach(function(p) {{
    if (!byInst[p.i]) byInst[p.i] = [];
    byInst[p.i].push(p);
  }});
  var institutions = Object.keys(byInst).sort();

  // Summary
  var nPapers = filtered.length;
  var nInsts  = institutions.length;
  var sumEl   = document.getElementById('papersSummary');
  if (nPapers === 0) {{
    sumEl.textContent = '';
  }} else {{
    sumEl.textContent = 'Showing ' + nPapers + ' paper' + (nPapers !== 1 ? 's' : '') +
      ' across ' + nInsts + ' institution' + (nInsts !== 1 ? 's' : '');
  }}

  var accordion = document.getElementById('papersAccordion');
  var emptyEl   = document.getElementById('papersEmpty');

  if (institutions.length === 0) {{
    accordion.innerHTML = '';
    emptyEl.style.display = '';
    return;
  }}
  emptyEl.style.display = 'none';

  var html = '';
  institutions.forEach(function(instName) {{
    var papers = byInst[instName];

    // Group by year
    var byYear = {{}};
    papers.forEach(function(p) {{
      var yr = p.y || '__unknown__';
      if (!byYear[yr]) byYear[yr] = [];
      byYear[yr].push(p);
    }});
    var years = Object.keys(byYear).sort(function(a, b) {{
      if (a === '__unknown__') return 1;
      if (b === '__unknown__') return -1;
      return parseInt(b) - parseInt(a);
    }});

    var instId = 'inst-' + instName.replace(/[^a-z0-9]/gi,'-').toLowerCase();

    html += '<div class="pa-item">';
    html += '<button class="pa-header" data-acc-id="' + instId + '" ' +
            'aria-expanded="false" id="btn-' + instId + '">';
    html += '<span class="pa-inst-name">' + esc(instName) + '</span>';
    html += '<span class="pa-count">' + papers.length + ' paper' + (papers.length !== 1 ? 's' : '') + '</span>';
    html += '<span class="pa-chevron">&#8250;</span>';
    html += '</button>';
    html += '<div class="pa-body" id="' + instId + '" hidden>';

    years.forEach(function(yr) {{
      var yearPapers = byYear[yr];
      var yearLabel  = yr === '__unknown__' ? 'Unknown year' : yr;

      html += '<div class="pa-year-group">';
      html += '<div class="pa-year-label">' + esc(yearLabel) + '</div>';

      // Desktop table
      html += '<table class="pa-table"><thead><tr>';
      html += '<th>Paper</th><th>Subject</th><th>Questions</th><th>Answers</th>';
      html += '</tr></thead><tbody>';
      yearPapers.forEach(function(p) {{
        html += '<tr>';
        html += '<td class="pa-title">' + esc(p.t) + '</td>';
        html += '<td><span class="pa-subj-badge pa-subj-' + subjClass(p.s) + '">' + esc(p.s) + '</span></td>';
        html += '<td><a href="' + esc(p.q) + '" target="_blank" rel="noopener noreferrer" class="pa-btn">View Paper</a></td>';
        if (p.ak) {{
          html += '<td><button class="pa-add-btn" data-ak="' + esc(p.ak) + '" data-label="' + esc(p.t) + '">+ Add answers £3</button></td>';
        }} else {{
          html += '<td><span class="pa-no-ans">Coming soon</span></td>';
        }}
        html += '</tr>';
      }});
      html += '</tbody></table>';

      // Mobile cards
      html += '<div class="pa-cards">';
      yearPapers.forEach(function(p) {{
        html += '<div class="pa-card">';
        html += '<div class="pa-card-title">' + esc(p.t) + '</div>';
        html += '<div class="pa-card-meta">';
        html += '<span class="pa-subj-badge pa-subj-' + subjClass(p.s) + '">' + esc(p.s) + '</span>';
        html += '<span class="pa-card-year">' + esc(yearLabel) + '</span>';
        html += '</div>';
        html += '<div class="pa-card-actions">';
        html += '<a href="' + esc(p.q) + '" target="_blank" rel="noopener noreferrer" class="pa-btn">View Paper</a>';
        if (p.ak) {{
          html += ' <button class="pa-add-btn" data-ak="' + esc(p.ak) + '" data-label="' + esc(p.t) + '">+ Add answers £3</button>';
        }} else {{
          html += ' <span class="pa-no-ans">Coming soon</span>';
        }}
        html += '</div></div>';
      }});
      html += '</div>'; // pa-cards

      html += '</div>'; // pa-year-group
    }});

    html += '</div>'; // pa-body
    html += '</div>'; // pa-item
  }});

  accordion.innerHTML = html;

  // Wire accordion button clicks
  accordion.querySelectorAll('.pa-header').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      toggleAcc(this.dataset.accId);
    }});
  }});

  // Wire "Add answers" cart buttons
  accordion.querySelectorAll('.pa-add-btn').forEach(function(btn) {{
    // Restore cart state if already added
    var ak = btn.dataset.ak;
    if (cart.some(function(c) {{ return c.ak === ak; }})) {{
      btn.textContent = '\u2713 Added';
      btn.classList.add('cart-added');
    }}
    btn.addEventListener('click', function() {{
      toggleCartItem(this.dataset.ak, this.dataset.label, this);
    }});
  }});

  // Auto-open first institution when filtered to one
  if (institutions.length === 1) {{
    var id = 'inst-' + institutions[0].replace(/[^a-z0-9]/gi,'-').toLowerCase();
    toggleAcc(id);
  }}
}}

function toggleAcc(id) {{
  var body = document.getElementById(id);
  var btn  = document.getElementById('btn-' + id);
  if (!body) return;
  var opening = body.hasAttribute('hidden');
  if (opening) {{ body.removeAttribute('hidden'); }} else {{ body.setAttribute('hidden', ''); }}
  if (btn) {{
    btn.setAttribute('aria-expanded', opening ? 'true' : 'false');
    btn.classList.toggle('open', opening);
  }}
}}

function populateFilters() {{
  var relevant = activeSubject
    ? PAPERS_DATA.filter(function(p) {{ return p.s === activeSubject; }})
    : PAPERS_DATA;

  // Institutions
  var insts = [];
  relevant.forEach(function(p) {{ if (insts.indexOf(p.i) === -1) insts.push(p.i); }});
  insts.sort();
  var instSel = document.getElementById('pfInstitution');
  var savedInst = instSel.value;
  instSel.innerHTML = '<option value="">All institutions</option>';
  insts.forEach(function(inst) {{
    var opt = document.createElement('option');
    opt.value = inst; opt.textContent = inst;
    if (inst === savedInst) opt.selected = true;
    instSel.appendChild(opt);
  }});
  if (insts.indexOf(activeInst) === -1) {{ activeInst = ''; instSel.value = ''; }}

  // Years — scope to selected institution so only that school's years appear
  var yearRelevant = activeInst
    ? relevant.filter(function(p) {{ return p.i === activeInst; }})
    : relevant;
  var yrs = [];
  yearRelevant.forEach(function(p) {{ if (p.y && yrs.indexOf(p.y) === -1) yrs.push(p.y); }});
  yrs.sort(function(a,b) {{ return parseInt(b)-parseInt(a); }});
  var yrSel = document.getElementById('pfYear');
  var savedYr = yrSel.value;
  yrSel.innerHTML = '<option value="">All years</option>';
  yrs.forEach(function(yr) {{
    var opt = document.createElement('option');
    opt.value = yr; opt.textContent = yr;
    if (yr === savedYr) opt.selected = true;
    yrSel.appendChild(opt);
  }});
  if (yrs.indexOf(activeYear) === -1) {{ activeYear = ''; yrSel.value = ''; }}
}}

function resetAll() {{
  activeSubject = ''; activeInst = ''; activeYear = ''; activeSearch = '';
  document.querySelectorAll('.ptab').forEach(function(t) {{ t.classList.remove('active'); }});
  document.querySelector('.ptab[data-subject=""]').classList.add('active');
  document.getElementById('pfInstitution').value = '';
  document.getElementById('pfYear').value = '';
  document.getElementById('pfSearch').value = '';
  populateFilters();
  render();
}}

// Tab clicks
document.getElementById('papersTabs').addEventListener('click', function(e) {{
  if (e.target.classList.contains('ptab')) {{
    document.querySelectorAll('.ptab').forEach(function(t) {{ t.classList.remove('active'); }});
    e.target.classList.add('active');
    activeSubject = e.target.dataset.subject;
    populateFilters();
    render();
  }}
}});

document.getElementById('pfInstitution').addEventListener('change', function() {{
  activeInst = this.value; populateFilters(); render();
}});
document.getElementById('pfYear').addEventListener('change', function() {{
  activeYear = this.value; render();
}});
var _st;
document.getElementById('pfSearch').addEventListener('input', function() {{
  var v = this.value; clearTimeout(_st);
  _st = setTimeout(function() {{ activeSearch = v; render(); }}, 180);
}});
document.getElementById('pfReset').addEventListener('click', resetAll);

// ── Cart ──────────────────────────────────────────────────────────────────────
var cart = []; // [{{ak, label}}]

function updateCartBar() {{
  var bar = document.getElementById('cartBar');
  var n = cart.length;
  if (n === 0) {{
    bar.classList.remove('visible');
    return;
  }}
  bar.classList.add('visible');

  var price = n * 3.00;
  var msg = '';
  if (n >= 3) {{
    price = price * 0.80;
    msg = '\u2713 20% off applied!';
  }} else if (n === 2) {{
    price = price * 0.90;
    msg = '\u2713 10% off applied \u2014 add 1 more for 20% off';
  }} else {{
    msg = 'Add 1 more for 10% off';
  }}

  document.getElementById('cartCount').textContent = n + ' answer' + (n !== 1 ? 's' : '') + ' in cart';
  document.getElementById('cartMsg').textContent   = msg;
  document.getElementById('cartPrice').textContent = '\u00a3' + price.toFixed(2);
}}

function toggleCartItem(ak, label, btn) {{
  var idx = cart.findIndex(function(c) {{ return c.ak === ak; }});
  if (idx === -1) {{
    cart.push({{ ak: ak, label: label }});
    btn.textContent = '\u2713 Added';
    btn.classList.add('cart-added');
  }} else {{
    cart.splice(idx, 1);
    btn.textContent = '+ Add answers \u00a33';
    btn.classList.remove('cart-added');
  }}
  updateCartBar();
}}

document.getElementById('cartBuy').addEventListener('click', function() {{
  if (cart.length === 0) return;
  var btn = this;
  btn.textContent = 'Processing\u2026';
  btn.disabled = true;
  fetch('/api/create-checkout', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ papers: cart }})
  }})
  .then(function(r) {{ return r.json(); }})
  .then(function(data) {{
    if (data.url) {{
      window.location.href = data.url;
    }} else {{
      alert('Something went wrong. Please try again.');
      btn.textContent = 'Buy answers \u2192';
      btn.disabled = false;
    }}
  }})
  .catch(function() {{
    alert('Network error. Please try again.');
    btn.textContent = 'Buy answers \u2192';
    btn.disabled = false;
  }});
}});

// Init
populateFilters();
render();
</script>

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{"@type":"ListItem","position":1,"name":"Home","item":"https://www.leadingtuition.co.uk/"}},
    {{"@type":"ListItem","position":2,"name":"Resources","item":"https://www.leadingtuition.co.uk/resources/"}},
    {{"@type":"ListItem","position":3,"name":"{schema_name}","item":"{canonical}"}}
  ]
}}
</script>
</body>
</html>"""


# ── Generate all 3 pages ──────────────────────────────────────────────────────
for slug, cfg in PAGE_CONFIGS.items():
    html = build_page(slug, cfg, pages_data)
    out_path = OUT_DIR / cfg["file"]
    out_path.write_text(html, encoding="utf-8")
    n = len(pages_data.get(slug, []))
    print(f"Written: {out_path.name}  ({n} papers)")

print("\nAll 3 pages built.")
