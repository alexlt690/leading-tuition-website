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

</head>
<body>

<nav class="navbar">
<a href="index.html" class="navbar-brand">
<img src="images/logo.png" alt="Leading Tuition logo" />
Leading Tuition
</a>

<ul class="navbar-nav">
<li><a href="index.html">Home</a></li>
<li><a href="about.html">About Us</a></li>
<li><a href="services.html">Our Services</a></li>
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

</body>
</html>
"""