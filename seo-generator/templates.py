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


def page_template(title, content):
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} | Leading Tuition</title>
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
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-D49V0X7BHL');
</script>

</head>
<body>


<nav class="navbar">
  <a href="index.html" class="navbar-brand">
    <img src="images/logo.png" alt="Leading Tuition logo" />
    Leading Tuition
  </a>

  <button class="nav-hamburger" id="navHamburger" aria-label="Open menu" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>

  <ul class="navbar-nav" id="navbarNav">
    <li><a href="index.html">Home</a></li>
    <li><a href="about.html">About Us</a></li>

    <!-- Services mega-dropdown -->
    <li class="nav-dropdown">
      <a href="services.html" class="nav-dropdown-toggle">Services <span class="nav-caret">&#9660;</span></a>
      <div class="nav-mega-menu">
        <div class="nav-mega-header">
          <a href="services.html">&#8592; Our Services</a>
        </div>

        <div class="nav-mega-cols">

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Subjects</div>
            <a href="maths-tutor.html">Maths</a>
            <a href="biology-tutor.html">Biology</a>
            <a href="chemistry-tutor.html">Chemistry</a>
            <a href="physics-tutor.html">Physics</a>
            <a href="english-language-tutor.html">English Language</a>
            <a href="english-literature-tutor.html">English Literature</a>
            <a href="history-tutor.html">History</a>
            <a href="geography-tutor.html">Geography</a>
            <a href="economics-tutor.html">Economics</a>
            <a href="politics-tutor.html">Politics</a>
            <a href="psychology-tutor.html">Psychology</a>
            <a href="computer-science-tutor.html">Computer Science</a>
            <a href="business-studies-tutor.html">Business Studies</a>
            <a href="further-maths-tutor.html">Further Maths</a>
            <a href="statistics-tutor.html">Statistics</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Levels</div>
            <a href="a-level-tuition.html">A-Level Tuition</a>
            <a href="gcse-tuition.html">GCSE Tuition</a>
            <a href="primary-tuition.html">Primary Tuition</a>
            <a href="sats-tuition.html">SATs Tuition</a>
            <a href="11plus-tuition.html">11+ Tuition</a>
            <a href="13plus-tuition.html">13+ Tuition</a>
            <a href="university-tuition.html">University Tuition</a>
          </div>

          <div class="nav-mega-col">
            <div class="nav-mega-col-title">Specialist & Admissions</div>
            <a href="oxbridge-admissions-preparation.html">Oxbridge Admissions</a>
            <a href="oxbridge-subject-preparation.html">Oxbridge Subject Prep</a>
            <a href="ucat-tutor.html">UCAT Tutor</a>
            <a href="mmi-interview-coaching.html">MMI Interview Coaching</a>
            <a href="medicine-prep-hub.html">Medicine Prep Hub</a>
            <a href="university-personal-statement.html">University Personal Statement</a>
          </div>

        </div>
      </div>
    </li>

    <!-- Blog dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Blog <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu">
        <a href="how-long-does-gcse-revision-take.html">How Long Does GCSE Revision Take?</a>
        <a href="how-to-find-a-good-private-tutor.html">How to Find a Good Private Tutor</a>
        <a href="how-to-prepare-for-a-medical-school-mmi-interview.html">How to Prepare for MMI Interviews</a>
        <a href="online-tutoring-vs-in-person-tutoring-for-gcse.html">Online vs In-Person Tutoring for GCSE</a>
        <a href="triple-vs-double-science-gcse.html">Triple vs Double Science GCSE</a>
        <a href="what-grade-do-you-need-for-oxbridge-chemistry.html">What Grade for Oxbridge Chemistry?</a>
        <a href="what-is-the-11-plus-exam.html">What is the 11 Plus Exam?</a>
        <a href="a-level-subject-choices-for-medicine-applications.html">A-Level Subjects for Medicine</a>
        <a href="ucat-score-requirements-for-uk-medical-schools-2025.html">UCAT Score Requirements 2025</a>
        <a href="ucas-personal-statement-guide.html">UCAS Personal Statement Guide</a>
      </div>
    </li>

    <!-- Locations dropdown -->
    <li class="nav-dropdown">
      <a href="#" class="nav-dropdown-toggle">Locations <span class="nav-caret">&#9660;</span></a>
      <div class="nav-dropdown-menu nav-dropdown-menu--cols">
        <a href="london.html">London</a>
        <a href="birmingham.html">Birmingham</a>
        <a href="manchester.html">Manchester</a>
        <a href="leeds.html">Leeds</a>
        <a href="bristol.html">Bristol</a>
        <a href="edinburgh.html">Edinburgh</a>
        <a href="sheffield.html">Sheffield</a>
        <a href="leicester.html">Leicester</a>
        <a href="liverpool.html">Liverpool</a>
        <a href="nottingham.html">Nottingham</a>
        <a href="cambridge.html">Cambridge</a>
        <a href="oxford.html">Oxford</a>
        <a href="brighton.html">Brighton</a>
        <a href="guildford.html">Guildford</a>
        <a href="reading.html">Reading</a>
      </div>
    </li>

    <li><a href="tutors.html">Our Tutors</a></li>
    <li><a href="faqs.html">FAQs</a></li>
    <li><a href="contact.html">Contact Us</a></li>
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

  document.addEventListener('click', function(e) {
    if (!e.target.closest('.navbar')) {
      nav.classList.remove('open');
      hamburger.classList.remove('active');
      hamburger.setAttribute('aria-expanded', 'false');
    }
  });
})();
</script>

</body>
</html>
"""