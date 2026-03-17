import json

# Exported nav block for use by generate_static_pages()
_NAV_BLOCK = '<nav class="navbar">\n  <a href="/" class="navbar-brand">\n    <img src="images/logo.png" alt="Leading Tuition logo" />\n    Leading Tuition\n  </a>\n\n  <button class="nav-hamburger" id="navHamburger" aria-label="Open menu" aria-expanded="false">\n    <span></span><span></span><span></span>\n  </button>\n\n  <ul class="navbar-nav" id="navbarNav">\n    <li><a href="/">Home</a></li>\n    <li><a href="/about.html">About Us</a></li>\n\n    <!-- Services mega-dropdown -->\n    <li class="nav-dropdown">\n      <a href="/services.html" class="nav-dropdown-toggle">Services <span class="nav-caret">&#9660;</span></a>\n      <div class="nav-mega-menu">\n        <div class="nav-mega-header">\n          <a href="/services.html">&#8592; Our Services</a>\n        </div>\n\n        <div class="nav-mega-cols">\n\n          <div class="nav-mega-col">\n            <div class="nav-mega-col-title">Subjects</div>\n            <a href="/subjects/maths-tutor.html">Maths</a>\n            <a href="/subjects/biology-tutor.html">Biology</a>\n            <a href="/subjects/chemistry-tutor.html">Chemistry</a>\n            <a href="/subjects/physics-tutor.html">Physics</a>\n            <a href="/subjects/english-language-tutor.html">English Language</a>\n            <a href="/subjects/english-literature-tutor.html">English Literature</a>\n            <a href="/subjects/history-tutor.html">History</a>\n            <a href="/subjects/geography-tutor.html">Geography</a>\n            <a href="/subjects/economics-tutor.html">Economics</a>\n            <a href="/subjects/politics-tutor.html">Politics</a>\n            <a href="/subjects/psychology-tutor.html">Psychology</a>\n            <a href="/subjects/computer-science-tutor.html">Computer Science</a>\n            <a href="/subjects/business-studies-tutor.html">Business Studies</a>\n            <a href="/subjects/further-maths-tutor.html">Further Maths</a>\n            <a href="/subjects/statistics-tutor.html">Statistics</a>\n          </div>\n\n          <div class="nav-mega-col">\n            <div class="nav-mega-col-title">Levels</div>\n            <a href="/a-level-tuition.html">A-Level Tuition</a>\n            <a href="/gcse-tuition.html">GCSE Tuition</a>\n            <a href="/primary-tuition.html">Primary Tuition</a>\n            <a href="/sats-tuition.html">SATs Tuition</a>\n            <a href="/11plus-tuition.html">11+ Tuition</a>\n            <a href="/13plus-tuition.html">13+ Tuition</a>\n            <a href="/university-tuition.html">University Tuition</a>\n          </div>\n\n          <div class="nav-mega-col">\n            <div class="nav-mega-col-title">Specialist &amp; Admissions</div>\n            <a href="/oxbridge-admissions-preparation.html">Oxbridge Admissions</a>\n            <a href="/oxbridge-subject-preparation.html">Oxbridge Subject Prep</a>\n            <a href="/ucat-tutor.html">UCAT Tutor</a>\n            <a href="/mmi-interview-coaching.html">MMI Interview Coaching</a>\n            <a href="/medicine-prep-hub.html">Medicine Prep Hub</a>\n            <a href="/university-personal-statement.html">University Personal Statement</a>\n          </div>\n\n        </div>\n      </div>\n    </li>\n\n    <!-- Blog dropdown -->\n    <li class="nav-dropdown">\n      <a href="#" class="nav-dropdown-toggle">Blog <span class="nav-caret">&#9660;</span></a>\n      <div class="nav-dropdown-menu">\n        <a href="/how-long-does-gcse-revision-take.html">How Long Does GCSE Revision Take?</a>\n        <a href="/how-to-find-a-good-private-tutor.html">How to Find a Good Private Tutor</a>\n        <a href="/how-to-prepare-for-a-medical-school-mmi-interview.html">How to Prepare for MMI Interviews</a>\n        <a href="/online-tutoring-vs-in-person-tutoring-for-gcse.html">Online vs In-Person Tutoring for GCSE</a>\n        <a href="/triple-vs-double-science-gcse.html">Triple vs Double Science GCSE</a>\n        <a href="/what-grade-do-you-need-for-oxbridge-chemistry.html">What Grade for Oxbridge Chemistry?</a>\n        <a href="/what-is-the-11-plus-exam.html">What is the 11 Plus Exam?</a>\n        <a href="/a-level-subject-choices-for-medicine-applications.html">A-Level Subjects for Medicine</a>\n        <a href="/ucat-score-requirements-for-uk-medical-schools-2025.html">UCAT Score Requirements 2025</a>\n        <a href="/ucas-personal-statement-guide.html">UCAS Personal Statement Guide</a>\n      </div>\n    </li>\n\n    <!-- Locations dropdown -->\n    <li class="nav-dropdown">\n      <a href="#" class="nav-dropdown-toggle">Locations <span class="nav-caret">&#9660;</span></a>\n      <div class="nav-dropdown-menu nav-dropdown-menu--cols">\n        <a href="/london.html">London</a>\n        <a href="/birmingham.html">Birmingham</a>\n        <a href="/manchester.html">Manchester</a>\n        <a href="/leeds.html">Leeds</a>\n        <a href="/bristol.html">Bristol</a>\n        <a href="/sheffield.html">Sheffield</a>\n        <a href="/leicester.html">Leicester</a>\n        <a href="/liverpool.html">Liverpool</a>\n        <a href="/nottingham.html">Nottingham</a>\n        <a href="/cambridge.html">Cambridge</a>\n        <a href="/oxford.html">Oxford</a>\n        <a href="/brighton.html">Brighton</a>\n        <a href="/guildford.html">Guildford</a>\n        <a href="/reading.html">Reading</a>\n      </div>\n    </li>\n\n    <li><a href="/tutors.html">Our Tutors</a></li>\n    <li><a href="/faqs.html">FAQs</a></li>\n    <li><a href="/contact.html">Contact Us</a></li>\n  </ul>\n</nav>'


def breadcrumb_schema(page_type, slug, display_name, section=""):
    """Build BreadcrumbList JSON-LD. page_type: home|location|subject|level|specialist|blog"""
    base_url = "https://www.leadingtuition.co.uk"
    home = {"@type": "ListItem", "position": 1, "name": "Home", "item": base_url}
    if page_type == "home":
        items = [home]
    elif page_type == "location":
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": "Locations", "item": f"{base_url}/locations"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": f"{base_url}/{slug}"}]
    elif page_type == "subject":
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": "Subjects", "item": f"{base_url}/subjects"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": f"{base_url}/{slug}"}]
    elif page_type == "level":
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": display_name, "item": f"{base_url}/{slug}"}]
    elif page_type == "specialist":
        sec = section or "Services"
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": sec, "item": f"{base_url}/services"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": f"{base_url}/{slug}"}]
    elif page_type == "blog":
        items = [home,
                 {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{base_url}/blog"},
                 {"@type": "ListItem", "position": 3, "name": display_name, "item": f"{base_url}/{slug}"}]
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
    head_extras = base_html(title, meta_desc, slug, og_type)
    breadcrumb = breadcrumb_schema(page_type, slug, title, section)
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} | Leading Tuition</title>
{head_extras}
<link rel="stylesheet" href="style.css" />
<link rel="icon" type="image/png" href="images/favicon.png" />

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
    <img src="images/logo.png" alt="Leading Tuition logo" />
    Leading Tuition
  </a>

  <button class="nav-hamburger" id="navHamburger" aria-label="Open menu" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>

  <ul class="navbar-nav" id="navbarNav">
    <li><a href="/">Home</a></li>
    <li><a href="/about.html">About Us</a></li>

    <!-- Services mega-dropdown -->
    <li class="nav-dropdown">
      <a href="/services.html" class="nav-dropdown-toggle">Services <span class="nav-caret">&#9660;</span></a>
      <div class="nav-mega-menu">
        <div class="nav-mega-header">
          <a href="/services.html">&#8592; Our Services</a>
        </div>

        <div class="nav-mega-cols">

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Subjects</div>
            <a href="/subjects/maths-tutor.html">Maths</a>
            <a href="/subjects/biology-tutor.html">Biology</a>
            <a href="/subjects/chemistry-tutor.html">Chemistry</a>
            <a href="/subjects/physics-tutor.html">Physics</a>
            <a href="/subjects/english-language-tutor.html">English Language</a>
            <a href="/subjects/english-literature-tutor.html">English Literature</a>
            <a href="/subjects/history-tutor.html">History</a>
            <a href="/subjects/geography-tutor.html">Geography</a>
            <a href="/subjects/economics-tutor.html">Economics</a>
            <a href="/subjects/politics-tutor.html">Politics</a>
            <a href="/subjects/psychology-tutor.html">Psychology</a>
            <a href="/subjects/computer-science-tutor.html">Computer Science</a>
            <a href="/subjects/business-studies-tutor.html">Business Studies</a>
            <a href="/subjects/further-maths-tutor.html">Further Maths</a>
            <a href="/subjects/statistics-tutor.html">Statistics</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Levels</div>
            <a href="/a-level-tuition.html">A-Level Tuition</a>
            <a href="/gcse-tuition.html">GCSE Tuition</a>
            <a href="/primary-tuition.html">Primary Tuition</a>
            <a href="/sats-tuition.html">SATs Tuition</a>
            <a href="/11plus-tuition.html">11+ Tuition</a>
            <a href="/13plus-tuition.html">13+ Tuition</a>
            <a href="/university-tuition.html">University Tuition</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Specialist &amp; Admissions</div>
            <a href="/oxbridge-admissions-preparation.html">Oxbridge Admissions</a>
            <a href="/oxbridge-subject-preparation.html">Oxbridge Subject Prep</a>
            <a href="/ucat-tutor.html">UCAT Tutor</a>
            <a href="/mmi-interview-coaching.html">MMI Interview Coaching</a>
            <a href="/medicine-prep-hub.html">Medicine Prep Hub</a>
            <a href="/university-personal-statement.html">University Personal Statement</a>
          </div>

        </div>
      </div>
    </li>

    <!-- Blog dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Blog <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu">
        <a href="/how-long-does-gcse-revision-take.html">How Long Does GCSE Revision Take?</a>
        <a href="/how-to-find-a-good-private-tutor.html">How to Find a Good Private Tutor</a>
        <a href="/how-to-prepare-for-a-medical-school-mmi-interview.html">How to Prepare for MMI Interviews</a>
        <a href="/online-tutoring-vs-in-person-tutoring-for-gcse.html">Online vs In-Person Tutoring for GCSE</a>
        <a href="/triple-vs-double-science-gcse.html">Triple vs Double Science GCSE</a>
        <a href="/what-grade-do-you-need-for-oxbridge-chemistry.html">What Grade for Oxbridge Chemistry?</a>
        <a href="/what-is-the-11-plus-exam.html">What is the 11 Plus Exam?</a>
        <a href="/a-level-subject-choices-for-medicine-applications.html">A-Level Subjects for Medicine</a>
        <a href="/ucat-score-requirements-for-uk-medical-schools-2025.html">UCAT Score Requirements 2025</a>
        <a href="/ucas-personal-statement-guide.html">UCAS Personal Statement Guide</a>
      </div>
    </li>

    <!-- Locations dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Locations <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu nav-dropdown-menu--cols">
        <a href="/london.html">London</a>
        <a href="/birmingham.html">Birmingham</a>
        <a href="/manchester.html">Manchester</a>
        <a href="/leeds.html">Leeds</a>
        <a href="/bristol.html">Bristol</a>
        <a href="/sheffield.html">Sheffield</a>
        <a href="/leicester.html">Leicester</a>
        <a href="/liverpool.html">Liverpool</a>
        <a href="/nottingham.html">Nottingham</a>
        <a href="/cambridge.html">Cambridge</a>
        <a href="/oxford.html">Oxford</a>
        <a href="/brighton.html">Brighton</a>
        <a href="/guildford.html">Guildford</a>
        <a href="/reading.html">Reading</a>
      </div>
    </li>

    <li><a href="/tutors.html">Our Tutors</a></li>
    <li><a href="/faqs.html">FAQs</a></li>
    <li><a href="/contact.html">Contact Us</a></li>
  </ul>
</nav>

<section class="hero" style="background-image:url('images/hero.png');">
<div class="hero-content">
<h1>{title}</h1>
<p>Expert support from Leading Tuition</p>
<a href="consultation.html" class="btn btn-dark hero-cta">Book a Free Consultation</a>
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
COPYRIGHT ©2023, Leading Tuition. ALL RIGHTS RESERVED.
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
    head_extras = base_html(title, meta_desc, slug, og_type)
    breadcrumb = breadcrumb_schema(page_type, slug, title, section)
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} | Leading Tuition</title>
{head_extras}
<link rel="stylesheet" href="style.css" />
<link rel="icon" type="image/png" href="images/favicon.png" />

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
    <img src="images/logo.png" alt="Leading Tuition logo" />
    Leading Tuition
  </a>

  <button class="nav-hamburger" id="navHamburger" aria-label="Open menu" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>

  <ul class="navbar-nav" id="navbarNav">
    <li><a href="/">Home</a></li>
    <li><a href="/about.html">About Us</a></li>

    <!-- Services mega-dropdown -->
    <li class="nav-dropdown">
      <a href="/services.html" class="nav-dropdown-toggle">Services <span class="nav-caret">&#9660;</span></a>
      <div class="nav-mega-menu">
        <div class="nav-mega-header">
          <a href="/services.html">&#8592; Our Services</a>
        </div>

        <div class="nav-mega-cols">

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Subjects</div>
            <a href="/subjects/maths-tutor.html">Maths</a>
            <a href="/subjects/biology-tutor.html">Biology</a>
            <a href="/subjects/chemistry-tutor.html">Chemistry</a>
            <a href="/subjects/physics-tutor.html">Physics</a>
            <a href="/subjects/english-language-tutor.html">English Language</a>
            <a href="/subjects/english-literature-tutor.html">English Literature</a>
            <a href="/subjects/history-tutor.html">History</a>
            <a href="/subjects/geography-tutor.html">Geography</a>
            <a href="/subjects/economics-tutor.html">Economics</a>
            <a href="/subjects/politics-tutor.html">Politics</a>
            <a href="/subjects/psychology-tutor.html">Psychology</a>
            <a href="/subjects/computer-science-tutor.html">Computer Science</a>
            <a href="/subjects/business-studies-tutor.html">Business Studies</a>
            <a href="/subjects/further-maths-tutor.html">Further Maths</a>
            <a href="/subjects/statistics-tutor.html">Statistics</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Levels</div>
            <a href="/a-level-tuition.html">A-Level Tuition</a>
            <a href="/gcse-tuition.html">GCSE Tuition</a>
            <a href="/primary-tuition.html">Primary Tuition</a>
            <a href="/sats-tuition.html">SATs Tuition</a>
            <a href="/11plus-tuition.html">11+ Tuition</a>
            <a href="/13plus-tuition.html">13+ Tuition</a>
            <a href="/university-tuition.html">University Tuition</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Specialist &amp; Admissions</div>
            <a href="/oxbridge-admissions-preparation.html">Oxbridge Admissions</a>
            <a href="/oxbridge-subject-preparation.html">Oxbridge Subject Prep</a>
            <a href="/ucat-tutor.html">UCAT Tutor</a>
            <a href="/mmi-interview-coaching.html">MMI Interview Coaching</a>
            <a href="/medicine-prep-hub.html">Medicine Prep Hub</a>
            <a href="/university-personal-statement.html">University Personal Statement</a>
          </div>

        </div>
      </div>
    </li>

    <!-- Blog dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Blog <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu">
        <a href="/how-long-does-gcse-revision-take.html">How Long Does GCSE Revision Take?</a>
        <a href="/how-to-find-a-good-private-tutor.html">How to Find a Good Private Tutor</a>
        <a href="/how-to-prepare-for-a-medical-school-mmi-interview.html">How to Prepare for MMI Interviews</a>
        <a href="/online-tutoring-vs-in-person-tutoring-for-gcse.html">Online vs In-Person Tutoring for GCSE</a>
        <a href="/triple-vs-double-science-gcse.html">Triple vs Double Science GCSE</a>
        <a href="/what-grade-do-you-need-for-oxbridge-chemistry.html">What Grade for Oxbridge Chemistry?</a>
        <a href="/what-is-the-11-plus-exam.html">What is the 11 Plus Exam?</a>
        <a href="/a-level-subject-choices-for-medicine-applications.html">A-Level Subjects for Medicine</a>
        <a href="/ucat-score-requirements-for-uk-medical-schools-2025.html">UCAT Score Requirements 2025</a>
        <a href="/ucas-personal-statement-guide.html">UCAS Personal Statement Guide</a>
      </div>
    </li>

    <!-- Locations dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Locations <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu nav-dropdown-menu--cols">
        <a href="/london.html">London</a>
        <a href="/birmingham.html">Birmingham</a>
        <a href="/manchester.html">Manchester</a>
        <a href="/leeds.html">Leeds</a>
        <a href="/bristol.html">Bristol</a>
        <a href="/sheffield.html">Sheffield</a>
        <a href="/leicester.html">Leicester</a>
        <a href="/liverpool.html">Liverpool</a>
        <a href="/nottingham.html">Nottingham</a>
        <a href="/cambridge.html">Cambridge</a>
        <a href="/oxford.html">Oxford</a>
        <a href="/brighton.html">Brighton</a>
        <a href="/guildford.html">Guildford</a>
        <a href="/reading.html">Reading</a>
      </div>
    </li>

    <li><a href="/tutors.html">Our Tutors</a></li>
    <li><a href="/faqs.html">FAQs</a></li>
    <li><a href="/contact.html">Contact Us</a></li>
  </ul>
</nav>

<section class="hero" style="background-image:url('images/hero.png');">
<div class="hero-content">
<h1>{title}</h1>
<p>Practical guidance from the Leading Tuition team</p>
<a href="consultation.html" class="btn btn-dark hero-cta">Book a Free Consultation</a>
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
COPYRIGHT ©2023, Leading Tuition. ALL RIGHTS RESERVED.
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
      <a href="consultation.html" class="btn btn-dark">Book a Free Consultation</a>
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
    head_extras = base_html(title, meta_desc, slug, og_type)
    breadcrumb = breadcrumb_schema("location", slug, city)
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} | Leading Tuition</title>
{head_extras}
<link rel="stylesheet" href="style.css" />
<link rel="icon" type="image/png" href="images/favicon.png" />

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
    <img src="images/logo.png" alt="Leading Tuition logo" />
    Leading Tuition
  </a>

  <button class="nav-hamburger" id="navHamburger" aria-label="Open menu" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>

  <ul class="navbar-nav" id="navbarNav">
    <li><a href="/">Home</a></li>
    <li><a href="/about.html">About Us</a></li>

    <!-- Services mega-dropdown -->
    <li class="nav-dropdown">
      <a href="/services.html" class="nav-dropdown-toggle">Services <span class="nav-caret">&#9660;</span></a>
      <div class="nav-mega-menu">
        <div class="nav-mega-header">
          <a href="/services.html">&#8592; Our Services</a>
        </div>

        <div class="nav-mega-cols">

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Subjects</div>
            <a href="/subjects/maths-tutor.html">Maths</a>
            <a href="/subjects/biology-tutor.html">Biology</a>
            <a href="/subjects/chemistry-tutor.html">Chemistry</a>
            <a href="/subjects/physics-tutor.html">Physics</a>
            <a href="/subjects/english-language-tutor.html">English Language</a>
            <a href="/subjects/english-literature-tutor.html">English Literature</a>
            <a href="/subjects/history-tutor.html">History</a>
            <a href="/subjects/geography-tutor.html">Geography</a>
            <a href="/subjects/economics-tutor.html">Economics</a>
            <a href="/subjects/politics-tutor.html">Politics</a>
            <a href="/subjects/psychology-tutor.html">Psychology</a>
            <a href="/subjects/computer-science-tutor.html">Computer Science</a>
            <a href="/subjects/business-studies-tutor.html">Business Studies</a>
            <a href="/subjects/further-maths-tutor.html">Further Maths</a>
            <a href="/subjects/statistics-tutor.html">Statistics</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Levels</div>
            <a href="/a-level-tuition.html">A-Level Tuition</a>
            <a href="/gcse-tuition.html">GCSE Tuition</a>
            <a href="/primary-tuition.html">Primary Tuition</a>
            <a href="/sats-tuition.html">SATs Tuition</a>
            <a href="/11plus-tuition.html">11+ Tuition</a>
            <a href="/13plus-tuition.html">13+ Tuition</a>
            <a href="/university-tuition.html">University Tuition</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Specialist &amp; Admissions</div>
            <a href="/oxbridge-admissions-preparation.html">Oxbridge Admissions</a>
            <a href="/oxbridge-subject-preparation.html">Oxbridge Subject Prep</a>
            <a href="/ucat-tutor.html">UCAT Tutor</a>
            <a href="/mmi-interview-coaching.html">MMI Interview Coaching</a>
            <a href="/medicine-prep-hub.html">Medicine Prep Hub</a>
            <a href="/university-personal-statement.html">University Personal Statement</a>
          </div>

        </div>
      </div>
    </li>

    <!-- Blog dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Blog <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu">
        <a href="/how-long-does-gcse-revision-take.html">How Long Does GCSE Revision Take?</a>
        <a href="/how-to-find-a-good-private-tutor.html">How to Find a Good Private Tutor</a>
        <a href="/how-to-prepare-for-a-medical-school-mmi-interview.html">How to Prepare for MMI Interviews</a>
        <a href="/online-tutoring-vs-in-person-tutoring-for-gcse.html">Online vs In-Person Tutoring for GCSE</a>
        <a href="/triple-vs-double-science-gcse.html">Triple vs Double Science GCSE</a>
        <a href="/what-grade-do-you-need-for-oxbridge-chemistry.html">What Grade for Oxbridge Chemistry?</a>
        <a href="/what-is-the-11-plus-exam.html">What is the 11 Plus Exam?</a>
        <a href="/a-level-subject-choices-for-medicine-applications.html">A-Level Subjects for Medicine</a>
        <a href="/ucat-score-requirements-for-uk-medical-schools-2025.html">UCAT Score Requirements 2025</a>
        <a href="/ucas-personal-statement-guide.html">UCAS Personal Statement Guide</a>
      </div>
    </li>

    <!-- Locations dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Locations <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu nav-dropdown-menu--cols">
        <a href="/london.html">London</a>
        <a href="/birmingham.html">Birmingham</a>
        <a href="/manchester.html">Manchester</a>
        <a href="/leeds.html">Leeds</a>
        <a href="/bristol.html">Bristol</a>
        <a href="/sheffield.html">Sheffield</a>
        <a href="/leicester.html">Leicester</a>
        <a href="/liverpool.html">Liverpool</a>
        <a href="/nottingham.html">Nottingham</a>
        <a href="/cambridge.html">Cambridge</a>
        <a href="/oxford.html">Oxford</a>
        <a href="/brighton.html">Brighton</a>
        <a href="/guildford.html">Guildford</a>
        <a href="/reading.html">Reading</a>
      </div>
    </li>

    <li><a href="/tutors.html">Our Tutors</a></li>
    <li><a href="/faqs.html">FAQs</a></li>
    <li><a href="/contact.html">Contact Us</a></li>
  </ul>
</nav>

<section class="hero" style="background-image:url('images/hero.png');">
<div class="hero-content">
<h1>{title}</h1>
<p>Expert tutors supporting families across {city}</p>
<a href="consultation.html" class="btn btn-dark hero-cta">Book a Free Consultation</a>
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
COPYRIGHT ©2023, Leading Tuition. ALL RIGHTS RESERVED.
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
    head_extras = base_html(title, meta_desc, slug, og_type)
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
<link rel="stylesheet" href="style.css" />
<link rel="icon" type="image/png" href="images/favicon.png" />

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
    <img src="images/logo.png" alt="Leading Tuition logo" />
    Leading Tuition
  </a>

  <button class="nav-hamburger" id="navHamburger" aria-label="Open menu" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>

  <ul class="navbar-nav" id="navbarNav">
    <li><a href="/">Home</a></li>
    <li><a href="/about.html">About Us</a></li>

    <!-- Services mega-dropdown -->
    <li class="nav-dropdown">
      <a href="/services.html" class="nav-dropdown-toggle">Services <span class="nav-caret">&#9660;</span></a>
      <div class="nav-mega-menu">
        <div class="nav-mega-header">
          <a href="/services.html">&#8592; Our Services</a>
        </div>

        <div class="nav-mega-cols">

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Subjects</div>
            <a href="/subjects/maths-tutor.html">Maths</a>
            <a href="/subjects/biology-tutor.html">Biology</a>
            <a href="/subjects/chemistry-tutor.html">Chemistry</a>
            <a href="/subjects/physics-tutor.html">Physics</a>
            <a href="/subjects/english-language-tutor.html">English Language</a>
            <a href="/subjects/english-literature-tutor.html">English Literature</a>
            <a href="/subjects/history-tutor.html">History</a>
            <a href="/subjects/geography-tutor.html">Geography</a>
            <a href="/subjects/economics-tutor.html">Economics</a>
            <a href="/subjects/politics-tutor.html">Politics</a>
            <a href="/subjects/psychology-tutor.html">Psychology</a>
            <a href="/subjects/computer-science-tutor.html">Computer Science</a>
            <a href="/subjects/business-studies-tutor.html">Business Studies</a>
            <a href="/subjects/further-maths-tutor.html">Further Maths</a>
            <a href="/subjects/statistics-tutor.html">Statistics</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Levels</div>
            <a href="/a-level-tuition.html">A-Level Tuition</a>
            <a href="/gcse-tuition.html">GCSE Tuition</a>
            <a href="/primary-tuition.html">Primary Tuition</a>
            <a href="/sats-tuition.html">SATs Tuition</a>
            <a href="/11plus-tuition.html">11+ Tuition</a>
            <a href="/13plus-tuition.html">13+ Tuition</a>
            <a href="/university-tuition.html">University Tuition</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Specialist & Admissions</div>
            <a href="/oxbridge-admissions-preparation.html">Oxbridge Admissions</a>
            <a href="/oxbridge-subject-preparation.html">Oxbridge Subject Prep</a>
            <a href="/ucat-tutor.html">UCAT Tutor</a>
            <a href="/mmi-interview-coaching.html">MMI Interview Coaching</a>
            <a href="/medicine-prep-hub.html">Medicine Prep Hub</a>
            <a href="/university-personal-statement.html">University Personal Statement</a>
          </div>

        </div>
      </div>
    </li>

    <!-- Blog dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Blog <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu">
        <a href="/how-long-does-gcse-revision-take.html">How Long Does GCSE Revision Take?</a>
        <a href="/how-to-find-a-good-private-tutor.html">How to Find a Good Private Tutor</a>
        <a href="/how-to-prepare-for-a-medical-school-mmi-interview.html">How to Prepare for MMI Interviews</a>
        <a href="/online-tutoring-vs-in-person-tutoring-for-gcse.html">Online vs In-Person Tutoring for GCSE</a>
        <a href="/triple-vs-double-science-gcse.html">Triple vs Double Science GCSE</a>
        <a href="/what-grade-do-you-need-for-oxbridge-chemistry.html">What Grade for Oxbridge Chemistry?</a>
        <a href="/what-is-the-11-plus-exam.html">What is the 11 Plus Exam?</a>
        <a href="/a-level-subject-choices-for-medicine-applications.html">A-Level Subjects for Medicine</a>
        <a href="/ucat-score-requirements-for-uk-medical-schools-2025.html">UCAT Score Requirements 2025</a>
        <a href="/ucas-personal-statement-guide.html">UCAS Personal Statement Guide</a>
      </div>
    </li>

    <!-- Locations dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Locations <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu nav-dropdown-menu--cols">
        <a href="/london.html">London</a>
        <a href="/birmingham.html">Birmingham</a>
        <a href="/manchester.html">Manchester</a>
        <a href="/leeds.html">Leeds</a>
        <a href="/bristol.html">Bristol</a>
        <a href="/sheffield.html">Sheffield</a>
        <a href="/leicester.html">Leicester</a>
        <a href="/liverpool.html">Liverpool</a>
        <a href="/nottingham.html">Nottingham</a>
        <a href="/cambridge.html">Cambridge</a>
        <a href="/oxford.html">Oxford</a>
        <a href="/brighton.html">Brighton</a>
        <a href="/guildford.html">Guildford</a>
        <a href="/reading.html">Reading</a>
      </div>
    </li>

    <li><a href="/tutors.html">Our Tutors</a></li>
    <li><a href="/faqs.html">FAQs</a></li>
    <li><a href="/contact.html">Contact Us</a></li>
  </ul>
</nav>

<section class="hero" style="background-image:url('images/hero.png');">
<div class="hero-content">
<h1>{title}</h1>
<p>Expert support from Leading Tuition</p>
<a href="consultation.html" class="btn btn-dark hero-cta">Book a Free Consultation</a>
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
COPYRIGHT ©2023, Leading Tuition. ALL RIGHTS RESERVED.
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