import json


def page_url_path(page_type, slug):
    """Return the full URL path for a page given its type and bare slug.
    e.g. page_type='subject', slug='maths-tutor' -> 'services/subjects/maths-tutor'
    """
    prefix_map = {
        "subject":    "services/subjects",
        "level":      "services/levels",
        "specialist": "services/specialist-admissions",
        "blog":       "blog",
        "location":   "locations",
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

    <!-- Services mega-dropdown -->
    <li class="nav-dropdown">
      <a href="/services" class="nav-dropdown-toggle">Services <span class="nav-caret">&#9660;</span></a>
      <div class="nav-mega-menu">
        <div class="nav-mega-header">
          <a href="/services">&#8592; Our Services</a>
        </div>

        <div class="nav-mega-cols">

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

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Levels</div>
            <a href="/a-level/">A-Level Tuition</a>
            <a href="/gcse/">GCSE Tuition</a>
            <a href="/services/levels/primary-tuition">Primary Tuition</a>
            <a href="/services/levels/sats-tuition">SATs Tuition</a>
            <a href="/services/levels/11plus-tuition">11+ Tuition</a>
            <a href="/services/levels/13plus-tuition">13+ Tuition</a>
            <a href="/services/levels/university-tuition">University Tuition</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Specialist &amp; Admissions</div>
            <a href="/services/specialist-admissions/medicine-prep-hub">Medicine Prep Hub</a>
            <a href="/services/specialist-admissions/medical-school-interviews/">Medical School Interviews</a>
            <a href="/services/specialist-admissions/ucat-tutor">UCAT Tutor</a>
            <a href="/services/specialist-admissions/mmi-interview-coaching">MMI Interview Coaching</a>
            <a href="/services/specialist-admissions/oxbridge-admissions-preparation">Oxbridge Admissions</a>
            <a href="/services/specialist-admissions/oxbridge-subject-preparation">Oxbridge Subject Prep</a>
            <a href="/services/specialist-admissions/university-personal-statement">University Personal Statement</a>
          </div>

        </div>
      </div>
    </li>

    <!-- Blog dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Blog <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu">
        <a href="/blog/how-long-does-gcse-revision-take">How Long Does GCSE Revision Take?</a>
        <a href="/blog/how-to-find-a-good-private-tutor">How to Find a Good Private Tutor</a>
        <a href="/blog/how-to-prepare-for-a-medical-school-mmi-interview">How to Prepare for MMI Interviews</a>
        <a href="/blog/online-tutoring-vs-in-person-tutoring-for-gcse">Online vs In-Person Tutoring for GCSE</a>
        <a href="/blog/triple-vs-double-science-gcse">Triple vs Double Science GCSE</a>
        <a href="/blog/what-grade-do-you-need-for-oxbridge-chemistry">What Grade for Oxbridge Chemistry?</a>
        <a href="/blog/what-is-the-11-plus-exam">What is the 11 Plus Exam?</a>
        <a href="/blog/a-level-subject-choices-for-medicine-applications">A-Level Subjects for Medicine</a>
        <a href="/blog/ucat-score-requirements-for-uk-medical-schools-2025">UCAT Score Requirements 2025</a>
        <a href="/blog/ucas-personal-statement-guide">UCAS Personal Statement Guide</a>
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

    <!-- Services mega-dropdown -->
    <li class="nav-dropdown">
      <a href="/services" class="nav-dropdown-toggle">Services <span class="nav-caret">&#9660;</span></a>
      <div class="nav-mega-menu">
        <div class="nav-mega-header">
          <a href="/services">&#8592; Our Services</a>
        </div>

        <div class="nav-mega-cols">

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

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Levels</div>
            <a href="/a-level/">A-Level Tuition</a>
            <a href="/gcse/">GCSE Tuition</a>
            <a href="/services/levels/primary-tuition">Primary Tuition</a>
            <a href="/services/levels/sats-tuition">SATs Tuition</a>
            <a href="/services/levels/11plus-tuition">11+ Tuition</a>
            <a href="/services/levels/13plus-tuition">13+ Tuition</a>
            <a href="/services/levels/university-tuition">University Tuition</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Specialist &amp; Admissions</div>
            <a href="/services/specialist-admissions/medicine-prep-hub">Medicine Prep Hub</a>
            <a href="/services/specialist-admissions/medical-school-interviews/">Medical School Interviews</a>
            <a href="/services/specialist-admissions/ucat-tutor">UCAT Tutor</a>
            <a href="/services/specialist-admissions/mmi-interview-coaching">MMI Interview Coaching</a>
            <a href="/services/specialist-admissions/oxbridge-admissions-preparation">Oxbridge Admissions</a>
            <a href="/services/specialist-admissions/oxbridge-subject-preparation">Oxbridge Subject Prep</a>
            <a href="/services/specialist-admissions/university-personal-statement">University Personal Statement</a>
          </div>

        </div>
      </div>
    </li>

    <!-- Blog dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Blog <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu">
        <a href="/blog/how-long-does-gcse-revision-take">How Long Does GCSE Revision Take?</a>
        <a href="/blog/how-to-find-a-good-private-tutor">How to Find a Good Private Tutor</a>
        <a href="/blog/how-to-prepare-for-a-medical-school-mmi-interview">How to Prepare for MMI Interviews</a>
        <a href="/blog/online-tutoring-vs-in-person-tutoring-for-gcse">Online vs In-Person Tutoring for GCSE</a>
        <a href="/blog/triple-vs-double-science-gcse">Triple vs Double Science GCSE</a>
        <a href="/blog/what-grade-do-you-need-for-oxbridge-chemistry">What Grade for Oxbridge Chemistry?</a>
        <a href="/blog/what-is-the-11-plus-exam">What is the 11 Plus Exam?</a>
        <a href="/blog/a-level-subject-choices-for-medicine-applications">A-Level Subjects for Medicine</a>
        <a href="/blog/ucat-score-requirements-for-uk-medical-schools-2025">UCAT Score Requirements 2025</a>
        <a href="/blog/ucas-personal-statement-guide">UCAS Personal Statement Guide</a>
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

    <!-- Services mega-dropdown -->
    <li class="nav-dropdown">
      <a href="/services" class="nav-dropdown-toggle">Services <span class="nav-caret">&#9660;</span></a>
      <div class="nav-mega-menu">
        <div class="nav-mega-header">
          <a href="/services">&#8592; Our Services</a>
        </div>

        <div class="nav-mega-cols">

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

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Levels</div>
            <a href="/a-level/">A-Level Tuition</a>
            <a href="/gcse/">GCSE Tuition</a>
            <a href="/services/levels/primary-tuition">Primary Tuition</a>
            <a href="/services/levels/sats-tuition">SATs Tuition</a>
            <a href="/services/levels/11plus-tuition">11+ Tuition</a>
            <a href="/services/levels/13plus-tuition">13+ Tuition</a>
            <a href="/services/levels/university-tuition">University Tuition</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Specialist &amp; Admissions</div>
            <a href="/services/specialist-admissions/medicine-prep-hub">Medicine Prep Hub</a>
            <a href="/services/specialist-admissions/medical-school-interviews/">Medical School Interviews</a>
            <a href="/services/specialist-admissions/ucat-tutor">UCAT Tutor</a>
            <a href="/services/specialist-admissions/mmi-interview-coaching">MMI Interview Coaching</a>
            <a href="/services/specialist-admissions/oxbridge-admissions-preparation">Oxbridge Admissions</a>
            <a href="/services/specialist-admissions/oxbridge-subject-preparation">Oxbridge Subject Prep</a>
            <a href="/services/specialist-admissions/university-personal-statement">University Personal Statement</a>
          </div>

        </div>
      </div>
    </li>

    <!-- Blog dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Blog <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu">
        <a href="/blog/how-long-does-gcse-revision-take">How Long Does GCSE Revision Take?</a>
        <a href="/blog/how-to-find-a-good-private-tutor">How to Find a Good Private Tutor</a>
        <a href="/blog/how-to-prepare-for-a-medical-school-mmi-interview">How to Prepare for MMI Interviews</a>
        <a href="/blog/online-tutoring-vs-in-person-tutoring-for-gcse">Online vs In-Person Tutoring for GCSE</a>
        <a href="/blog/triple-vs-double-science-gcse">Triple vs Double Science GCSE</a>
        <a href="/blog/what-grade-do-you-need-for-oxbridge-chemistry">What Grade for Oxbridge Chemistry?</a>
        <a href="/blog/what-is-the-11-plus-exam">What is the 11 Plus Exam?</a>
        <a href="/blog/a-level-subject-choices-for-medicine-applications">A-Level Subjects for Medicine</a>
        <a href="/blog/ucat-score-requirements-for-uk-medical-schools-2025">UCAT Score Requirements 2025</a>
        <a href="/blog/ucas-personal-statement-guide">UCAS Personal Statement Guide</a>
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

    <!-- Services mega-dropdown -->
    <li class="nav-dropdown">
      <a href="/services" class="nav-dropdown-toggle">Services <span class="nav-caret">&#9660;</span></a>
      <div class="nav-mega-menu">
        <div class="nav-mega-header">
          <a href="/services">&#8592; Our Services</a>
        </div>

        <div class="nav-mega-cols">

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

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Levels</div>
            <a href="/a-level/">A-Level Tuition</a>
            <a href="/gcse/">GCSE Tuition</a>
            <a href="/services/levels/primary-tuition">Primary Tuition</a>
            <a href="/services/levels/sats-tuition">SATs Tuition</a>
            <a href="/services/levels/11plus-tuition">11+ Tuition</a>
            <a href="/services/levels/13plus-tuition">13+ Tuition</a>
            <a href="/services/levels/university-tuition">University Tuition</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Specialist &amp; Admissions</div>
            <a href="/services/specialist-admissions/medicine-prep-hub">Medicine Prep Hub</a>
            <a href="/services/specialist-admissions/medical-school-interviews/">Medical School Interviews</a>
            <a href="/services/specialist-admissions/ucat-tutor">UCAT Tutor</a>
            <a href="/services/specialist-admissions/mmi-interview-coaching">MMI Interview Coaching</a>
            <a href="/services/specialist-admissions/oxbridge-admissions-preparation">Oxbridge Admissions</a>
            <a href="/services/specialist-admissions/oxbridge-subject-preparation">Oxbridge Subject Prep</a>
            <a href="/services/specialist-admissions/university-personal-statement">University Personal Statement</a>
          </div>

        </div>
      </div>
    </li>

    <!-- Blog dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Blog <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu">
        <a href="/blog/how-long-does-gcse-revision-take">How Long Does GCSE Revision Take?</a>
        <a href="/blog/how-to-find-a-good-private-tutor">How to Find a Good Private Tutor</a>
        <a href="/blog/how-to-prepare-for-a-medical-school-mmi-interview">How to Prepare for MMI Interviews</a>
        <a href="/blog/online-tutoring-vs-in-person-tutoring-for-gcse">Online vs In-Person Tutoring for GCSE</a>
        <a href="/blog/triple-vs-double-science-gcse">Triple vs Double Science GCSE</a>
        <a href="/blog/what-grade-do-you-need-for-oxbridge-chemistry">What Grade for Oxbridge Chemistry?</a>
        <a href="/blog/what-is-the-11-plus-exam">What is the 11 Plus Exam?</a>
        <a href="/blog/a-level-subject-choices-for-medicine-applications">A-Level Subjects for Medicine</a>
        <a href="/blog/ucat-score-requirements-for-uk-medical-schools-2025">UCAT Score Requirements 2025</a>
        <a href="/blog/ucas-personal-statement-guide">UCAS Personal Statement Guide</a>
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