import json


def page_url_path(page_type, slug):
    """Return the full URL path for a page given its type and bare slug.
    e.g. page_type='subject', slug='maths-tutor' -> 'services/subjects/maths-tutor'
    """
    prefix_map = {
        "subject":          "services/subjects",
        "level":            "services/levels",
        "specialist":       "services/specialist-admissions",
        "blog":             "blog",
        "location":         "locations",
        "admissions-test":    "admissions-tests",
        "medical-school":     "medical-schools",
        "oxbridge-interview": "oxbridge-interviews",
        "eleven-plus":        "11-plus",
    }
    prefix = prefix_map.get(page_type, "")
    return f"{prefix}/{slug}" if prefix else slug


def breadcrumb_schema(page_type, slug, display_name, section=""):
    """Build BreadcrumbList JSON-LD. page_type: home|location|subject|level|specialist|blog"""
    base_url = "https://www.leadingtuition.co.uk"
    home = {"@type": "ListItem", "position": 1, "name": "Home", "item": base_url}
    full_path = page_url_path(page_type, slug)
    full_url = f"{base_url}/{full_path}"
    if page_type == "home":
        items = [home]
    elif page_type == "location":
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": "Locations", "item": f"{base_url}/locations"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": full_url}]
    elif page_type == "subject":
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": "Subjects", "item": f"{base_url}/services/subjects"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": full_url}]
    elif page_type == "level":
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": "Levels", "item": f"{base_url}/services/levels"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": full_url}]
    elif page_type == "specialist":
        sec = section or "Specialist & Admissions"
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": sec, "item": f"{base_url}/services/specialist-admissions"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": full_url}]
    elif page_type == "blog":
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{base_url}/blog"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": full_url}]
    elif page_type == "admissions-test":
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": "Admissions Tests", "item": f"{base_url}/admissions-tests/"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": full_url}]
    elif page_type == "medical-school":
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": "Medical School Guides", "item": f"{base_url}/medical-schools/"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": full_url}]
    elif page_type == "oxbridge-interview":
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": "Oxbridge Interview Preparation", "item": f"{base_url}/oxbridge-interviews/"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": full_url}]
    elif page_type == "eleven-plus":
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": "11+ Grammar School Preparation", "item": f"{base_url}/11-plus/"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": full_url}]
    else:
        items = [home]
    schema = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}
    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'


def base_html(title, meta_desc="", slug="", og_type="website"):
    """Returns the SEO head block: meta description, canonical, Open Graph, and Twitter Card tags."""
    base_url = "https://www.leadingtuition.co.uk"
    canonical_url = f"{base_url}/{slug}" if slug else base_url
    og_image = f"{base_url}/images/og-default.jpg"
    full_title = f"{title} | Leading Tuition"
    meta_desc_tag = f'<meta name="description" content="{meta_desc}" />' if meta_desc else ""
    return f"""{meta_desc_tag}
<link rel="canonical" href="{canonical_url}" />
<meta property="og:type" content="{og_type}" />
<meta property="og:site_name" content="Leading Tuition" />
<meta property="og:title" content="{full_title}" />
<meta property="og:description" content="{meta_desc}" />
<meta property="og:image" content="{og_image}" />
<meta property="og:url" content="{canonical_url}" />
<meta property="og:locale" content="en_GB" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{full_title}" />
<meta name="twitter:description" content="{meta_desc}" />
<meta name="twitter:image" content="{og_image}" />"""


def service_page_template(title, content, meta_desc="", slug="", og_type="website", page_type="level", section="", schema_extra=""):
    """Template for service/level pages — adds meta description and service-appropriate hero subtext."""
    full_slug = page_url_path(page_type, slug)
    head_extras = base_html(title, meta_desc, full_slug, og_type)
    breadcrumb = breadcrumb_schema(page_type, slug, title, section)
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} | Leading Tuition</title>
{head_extras}
<link rel="stylesheet" href="/style.css" />
<link rel="icon" type="image/png" href="/images/favicon.png" />

<style>

/* HERO HEIGHT REDUCTION */
.hero {{
  height:220px;
  min-height:220px;
}}

.hero-content {{
  padding:0 60px;
}}

.hero-content h1 {{
  font-size:2.2rem;
}}

.hero-content p {{
  font-size:1rem;
  margin-bottom:16px;
}}

.hero-cta {{
  display:inline-block;
}}

</style>

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-D49V0X7BHL"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-D49V0X7BHL');
</script>

</head>
<body>


<nav class="navbar">
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
              <div class="nav-flyout-menu">
                <a href="/subjects/gcse-maths/">Maths</a>
                <a href="/subjects/gcse-chemistry/">Chemistry</a>
              </div>
            </div>
            <div class="nav-flyout">
              <a href="/a-level/">A-Level Tuition</a>
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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
                <a href="/medical-schools/kings">King's College London</a>
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
                <a href="/medical-schools/queens-belfast">Queen's Belfast</a>
                <a href="/medical-schools/sheffield">Sheffield</a>
                <a href="/medical-schools/southampton">Southampton</a>
                <a href="/medical-schools/st-andrews">St Andrews</a>
                <a href="/medical-schools/st-georges">St George's</a>
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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

    <!-- Blog dropdown (grouped by topic) -->
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
</nav>

<section class="hero" style="background-image:url('/images/hero.png');">
<div class="hero-content">
<h1>{title}</h1>
<p>Expert support from Leading Tuition</p>
<a href="/consultation" class="btn btn-dark hero-cta">Book a Free Consultation</a>
</div>
</section>

<section class="section section--cream" style="padding:70px 60px;">
<div class="container" style="max-width:900px;">
{content}
</div>
</section>

{cta_block()}

{faq_block()}

{cta_block()}

<footer>

<h3>Get In Touch</h3>
<hr />

<div class="footer-contact">
<p>+44 207 167 8440</p>
<p>hello@leadingtuition.co.uk</p>
</div>

<div class="copyright">
COPYRIGHT ©2026, Leading Tuition. ALL RIGHTS RESERVED.
</div>

</footer>

<script>
(function() {{
  var hamburger = document.getElementById('navHamburger');
  var nav       = document.getElementById('navbarNav');
  if (!hamburger || !nav) return;

  hamburger.addEventListener('click', function() {{
    var open = nav.classList.toggle('open');
    hamburger.classList.toggle('active', open);
    hamburger.setAttribute('aria-expanded', open);
  }});

  // Mobile: top-level dropdown toggles
  var toggles = document.querySelectorAll('.nav-dropdown-toggle');
  toggles.forEach(function(toggle) {{
    toggle.addEventListener('click', function(e) {{
      if (window.innerWidth <= 900) {{
        e.preventDefault();
        var li = this.parentElement;
        li.classList.toggle('open');
      }}
    }});
  }});

  // Mobile: fly-out sub-menu toggles (button expands; link navigates normally)
  var flyoutToggles = document.querySelectorAll('.nav-flyout-toggle');
  flyoutToggles.forEach(function(btn) {{
    btn.addEventListener('click', function(e) {{
      e.preventDefault();
      e.stopPropagation();
      var flyout = this.parentElement;
      flyout.classList.toggle('open');
      this.setAttribute('aria-expanded', flyout.classList.contains('open'));
    }});
  }});

  document.addEventListener('click', function(e) {{
    if (!e.target.closest('.navbar')) {{
      nav.classList.remove('open');
      hamburger.classList.remove('active');
      hamburger.setAttribute('aria-expanded', 'false');
    }}
  }});
}})();
</script>

{breadcrumb}
{schema_extra}
</body>
</html>
"""


def blog_page_template(title, content, meta_desc="", slug="", og_type="article", page_type="blog", section="", schema_extra=""):
    """Template for blog post pages — adds meta description and article-appropriate hero subtext."""
    full_slug = page_url_path(page_type, slug)
    head_extras = base_html(title, meta_desc, full_slug, og_type)
    breadcrumb = breadcrumb_schema(page_type, slug, title, section)
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} | Leading Tuition</title>
{head_extras}
<link rel="stylesheet" href="/style.css" />
<link rel="icon" type="image/png" href="/images/favicon.png" />

<style>

/* HERO HEIGHT REDUCTION */
.hero {{
  height:220px;
  min-height:220px;
}}

.hero-content {{
  padding:0 60px;
}}

.hero-content h1 {{
  font-size:2.2rem;
}}

.hero-content p {{
  font-size:1rem;
  margin-bottom:16px;
}}

.hero-cta {{
  display:inline-block;
}}

</style>

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-D49V0X7BHL"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-D49V0X7BHL');
</script>

</head>
<body>


<nav class="navbar">
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
              <div class="nav-flyout-menu">
                <a href="/subjects/gcse-maths/">Maths</a>
                <a href="/subjects/gcse-chemistry/">Chemistry</a>
              </div>
            </div>
            <div class="nav-flyout">
              <a href="/a-level/">A-Level Tuition</a>
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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
                <a href="/medical-schools/kings">King's College London</a>
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
                <a href="/medical-schools/queens-belfast">Queen's Belfast</a>
                <a href="/medical-schools/sheffield">Sheffield</a>
                <a href="/medical-schools/southampton">Southampton</a>
                <a href="/medical-schools/st-andrews">St Andrews</a>
                <a href="/medical-schools/st-georges">St George's</a>
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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

    <!-- Blog dropdown (grouped by topic) -->
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
</nav>

<section class="hero" style="background-image:url('/images/hero.png');">
<div class="hero-content">
<h1>{title}</h1>
<p>Practical guidance from the Leading Tuition team</p>
<a href="/consultation" class="btn btn-dark hero-cta">Book a Free Consultation</a>
</div>
</section>

<section class="section section--cream" style="padding:70px 60px;">
<div class="container" style="max-width:900px;">
<div class="post-meta">By <strong>Leading Tuition Team</strong> &nbsp;|&nbsp; <time>Published March 2026</time></div>
{content}
</div>
</section>

{cta_block()}

<footer>

<h3>Get In Touch</h3>
<hr />

<div class="footer-contact">
<p>+44 207 167 8440</p>
<p>hello@leadingtuition.co.uk</p>
</div>

<div class="copyright">
COPYRIGHT ©2026, Leading Tuition. ALL RIGHTS RESERVED.
</div>

</footer>

<script>
(function() {{
  var hamburger = document.getElementById('navHamburger');
  var nav       = document.getElementById('navbarNav');
  if (!hamburger || !nav) return;

  hamburger.addEventListener('click', function() {{
    var open = nav.classList.toggle('open');
    hamburger.classList.toggle('active', open);
    hamburger.setAttribute('aria-expanded', open);
  }});

  // Mobile: top-level dropdown toggles
  var toggles = document.querySelectorAll('.nav-dropdown-toggle');
  toggles.forEach(function(toggle) {{
    toggle.addEventListener('click', function(e) {{
      if (window.innerWidth <= 900) {{
        e.preventDefault();
        var li = this.parentElement;
        li.classList.toggle('open');
      }}
    }});
  }});

  // Mobile: fly-out sub-menu toggles (button expands; link navigates normally)
  var flyoutToggles = document.querySelectorAll('.nav-flyout-toggle');
  flyoutToggles.forEach(function(btn) {{
    btn.addEventListener('click', function(e) {{
      e.preventDefault();
      e.stopPropagation();
      var flyout = this.parentElement;
      flyout.classList.toggle('open');
      this.setAttribute('aria-expanded', flyout.classList.contains('open'));
    }});
  }});

  document.addEventListener('click', function(e) {{
    if (!e.target.closest('.navbar')) {{
      nav.classList.remove('open');
      hamburger.classList.remove('active');
      hamburger.setAttribute('aria-expanded', 'false');
    }}
  }});
}})();
</script>

{breadcrumb}
{schema_extra}
</body>
</html>
"""


def cta_block():
    return """
<section class="section section--light" style="padding:35px 60px;">
  <div class="container">
    <div style="max-width:560px;margin:0 auto;text-align:center;">
      <h2 style="margin-bottom:10px;">Ready to get started?</h2>
      <p style="margin-bottom:16px;">
        Book a free consultation and we’ll help you find the right support for your child.
      </p>
      <a href="/consultation" class="btn btn-dark">Book a Free Consultation</a>
    </div>
  </div>
</section>
"""


def faq_block():
    return """
<section class="section section--cream" style="padding:60px 60px;">
  <div class="container" style="max-width:820px;">
    <h2>Frequently Asked Questions</h2>

    <p><strong>How does the consultation work?</strong></p>
    <p>We’ll learn more about your child, the subject or admissions support they need, and the outcomes you’re aiming for before recommending the next step.</p>

    <p><strong>Is the consultation free?</strong></p>
    <p>Yes. It is a free consultation with no obligation, designed to help you understand the best route forward.</p>

    <p><strong>Can you help with specialist support like UCAT or Oxbridge admissions?</strong></p>
    <p>Yes. We support Primary, 11+, 13+, GCSE, A-Level, SATs, UCAT, MMI interview coaching, Oxbridge admissions, university admissions, and personal statement support.</p>
  </div>
</section>
"""


def location_page_template(city, title, content, meta_desc="", slug="", og_type="website", schema_extra=""):
    """Variant of page_template for location pages — adds meta description and city-specific hero subtext."""
    full_slug = page_url_path("location", slug)
    head_extras = base_html(title, meta_desc, full_slug, og_type)
    breadcrumb = breadcrumb_schema("location", slug, city)
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} | Leading Tuition</title>
{head_extras}
<link rel="stylesheet" href="/style.css" />
<link rel="icon" type="image/png" href="/images/favicon.png" />

<style>

/* HERO HEIGHT REDUCTION */
.hero {{
  height:220px;
  min-height:220px;
}}

.hero-content {{
  padding:0 60px;
}}

.hero-content h1 {{
  font-size:2.4rem;
}}

.hero-content p {{
  font-size:1rem;
  margin-bottom:16px;
}}

.hero-cta {{
  display:inline-block;
}}

</style>

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-D49V0X7BHL"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-D49V0X7BHL');
</script>

</head>
<body>


<nav class="navbar">
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
              <div class="nav-flyout-menu">
                <a href="/subjects/gcse-maths/">Maths</a>
                <a href="/subjects/gcse-chemistry/">Chemistry</a>
              </div>
            </div>
            <div class="nav-flyout">
              <a href="/a-level/">A-Level Tuition</a>
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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
                <a href="/medical-schools/kings">King's College London</a>
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
                <a href="/medical-schools/queens-belfast">Queen's Belfast</a>
                <a href="/medical-schools/sheffield">Sheffield</a>
                <a href="/medical-schools/southampton">Southampton</a>
                <a href="/medical-schools/st-andrews">St Andrews</a>
                <a href="/medical-schools/st-georges">St George's</a>
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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

    <!-- Blog dropdown (grouped by topic) -->
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
</nav>

<section class="hero" style="background-image:url('/images/hero.png');">
<div class="hero-content">
<h1>{title}</h1>
<p>Expert tutors supporting families across {city}</p>
<a href="/consultation" class="btn btn-dark hero-cta">Book a Free Consultation</a>
</div>
</section>

<section class="section section--cream" style="padding:70px 60px;">
<div class="container" style="max-width:900px;">
{content}
</div>
</section>

{cta_block()}

{faq_block()}

{cta_block()}

<footer>

<h3>Get In Touch</h3>
<hr />

<div class="footer-contact">
<p>+44 207 167 8440</p>
<p>hello@leadingtuition.co.uk</p>
</div>

<div class="copyright">
COPYRIGHT ©2026, Leading Tuition. ALL RIGHTS RESERVED.
</div>

</footer>

<script>
(function() {{
  var hamburger = document.getElementById('navHamburger');
  var nav       = document.getElementById('navbarNav');
  if (!hamburger || !nav) return;

  hamburger.addEventListener('click', function() {{
    var open = nav.classList.toggle('open');
    hamburger.classList.toggle('active', open);
    hamburger.setAttribute('aria-expanded', open);
  }});

  // Mobile: top-level dropdown toggles
  var toggles = document.querySelectorAll('.nav-dropdown-toggle');
  toggles.forEach(function(toggle) {{
    toggle.addEventListener('click', function(e) {{
      if (window.innerWidth <= 900) {{
        e.preventDefault();
        var li = this.parentElement;
        li.classList.toggle('open');
      }}
    }});
  }});

  // Mobile: fly-out sub-menu toggles (button expands; link navigates normally)
  var flyoutToggles = document.querySelectorAll('.nav-flyout-toggle');
  flyoutToggles.forEach(function(btn) {{
    btn.addEventListener('click', function(e) {{
      e.preventDefault();
      e.stopPropagation();
      var flyout = this.parentElement;
      flyout.classList.toggle('open');
      this.setAttribute('aria-expanded', flyout.classList.contains('open'));
    }});
  }});

  document.addEventListener('click', function(e) {{
    if (!e.target.closest('.navbar')) {{
      nav.classList.remove('open');
      hamburger.classList.remove('active');
      hamburger.setAttribute('aria-expanded', 'false');
    }}
  }});
}})();
</script>

{breadcrumb}
{schema_extra}
</body>
</html>
"""


def page_template(title, content, meta_desc="", slug="", og_type="website", page_type="specialist", section="Services", schema_extra="", base_tag=""):
    full_slug = page_url_path(page_type, slug) if page_type == "specialist" else slug
    head_extras = base_html(title, meta_desc, full_slug, og_type)
    breadcrumb = breadcrumb_schema(page_type, slug, title, section)
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
{base_tag}
<title>{title} | Leading Tuition</title>
{head_extras}
<link rel="stylesheet" href="/style.css" />
<link rel="icon" type="image/png" href="/images/favicon.png" />

<style>

/* HERO HEIGHT REDUCTION */
.hero {{
  height:220px;
  min-height:220px;
}}

.hero-content {{
  padding:0 60px;
}}

.hero-content h1 {{
  font-size:2.4rem;
}}

.hero-content p {{
  font-size:1rem;
  margin-bottom:16px;
}}

.hero-cta {{
  display:inline-block;
}}

</style>

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-D49V0X7BHL"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-D49V0X7BHL');
</script>

</head>
<body>


<nav class="navbar">
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
              <div class="nav-flyout-menu">
                <a href="/subjects/gcse-maths/">Maths</a>
                <a href="/subjects/gcse-chemistry/">Chemistry</a>
              </div>
            </div>
            <div class="nav-flyout">
              <a href="/a-level/">A-Level Tuition</a>
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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
                <a href="/medical-schools/kings">King's College London</a>
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
                <a href="/medical-schools/queens-belfast">Queen's Belfast</a>
                <a href="/medical-schools/sheffield">Sheffield</a>
                <a href="/medical-schools/southampton">Southampton</a>
                <a href="/medical-schools/st-andrews">St Andrews</a>
                <a href="/medical-schools/st-georges">St George's</a>
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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
              <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
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

    <!-- Blog dropdown (grouped by topic) -->
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
</nav>

<section class="hero" style="background-image:url('/images/hero.png');">
<div class="hero-content">
<h1>{title}</h1>
<p>Expert support from Leading Tuition</p>
<a href="/consultation" class="btn btn-dark hero-cta">Book a Free Consultation</a>
</div>
</section>

<section class="section section--cream" style="padding:70px 60px;">
<div class="container" style="max-width:900px;">
{content}
</div>
</section>

{cta_block()}

{faq_block()}

{cta_block()}

<footer>

<h3>Get In Touch</h3>
<hr />

<div class="footer-contact">
<p>+44 207 167 8440</p>
<p>hello@leadingtuition.co.uk</p>
</div>

<div class="copyright">
COPYRIGHT ©2026, Leading Tuition. ALL RIGHTS RESERVED.
</div>

</footer>

<script>
(function() {{
  var hamburger = document.getElementById('navHamburger');
  var nav       = document.getElementById('navbarNav');
  if (!hamburger || !nav) return;

  hamburger.addEventListener('click', function() {{
    var open = nav.classList.toggle('open');
    hamburger.classList.toggle('active', open);
    hamburger.setAttribute('aria-expanded', open);
  }});

  // Mobile: top-level dropdown toggles
  var toggles = document.querySelectorAll('.nav-dropdown-toggle');
  toggles.forEach(function(toggle) {{
    toggle.addEventListener('click', function(e) {{
      if (window.innerWidth <= 900) {{
        e.preventDefault();
        var li = this.parentElement;
        li.classList.toggle('open');
      }}
    }});
  }});

  // Mobile: fly-out sub-menu toggles (button expands; link navigates normally)
  var flyoutToggles = document.querySelectorAll('.nav-flyout-toggle');
  flyoutToggles.forEach(function(btn) {{
    btn.addEventListener('click', function(e) {{
      e.preventDefault();
      e.stopPropagation();
      var flyout = this.parentElement;
      flyout.classList.toggle('open');
      this.setAttribute('aria-expanded', flyout.classList.contains('open'));
    }});
  }});

  document.addEventListener('click', function(e) {{
    if (!e.target.closest('.navbar')) {{
      nav.classList.remove('open');
      hamburger.classList.remove('active');
      hamburger.setAttribute('aria-expanded', 'false');
    }}
  }});
}})();
</script>

{breadcrumb}
{schema_extra}
</body>
</html>
"""