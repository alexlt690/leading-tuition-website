"""
update_meta_descriptions.py
============================
Bulk meta-description update for ALL HTML pages across the site.
No API calls, no regeneration — pure brute-force string replacement.

Updates three tags per file:
  <meta name="description" content="...">
  <meta property="og:description" content="...">
  <meta name="twitter:description" content="...">

Target length: 145–158 characters (none of these go over 162).

Run from repo root:
    python seo-generator/update_meta_descriptions.py

After running:
    python seo-generator/generate.py --sitemap
    git add -A && git commit -m "Bulk meta description refresh — all pages"
    push to dev, verify, then merge to main.
"""

import re
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"

# ── New descriptions ─────────────────────────────────────────────────────────
# Keys are paths relative to OUTPUT_DIR. Values are the new description text.
# All descriptions are 133–162 characters; Google shows ~155 chars.

DESCRIPTIONS = {

    # ── BLOG PAGES ────────────────────────────────────────────────────────────
    "blog/11-plus-pass-marks-by-region-how-high-do-you-need-to-score.html":
        "11 Plus pass marks vary hugely by region — Tiffin needs 380+, Kent around 320. Find the scores your child needs for their target grammar school.",

    "blog/a-level-subject-choices-for-medicine-applications.html":
        "Which A-Levels do you need for Medicine? Chemistry is essential at almost all UK schools. How Biology, Maths, and other choices affect your offer.",

    "blog/creative-writing-for-the-11-plus-how-to-score-in-the-top-5.html":
        "Top 5% 11 Plus creative writing needs a strong opening, controlled pacing, and precise vocabulary. Techniques and marked examples from Leading Tuition.",

    "blog/gl-assessment-vs-cem-vs-local-school-exams-the-2026-format-guide.html":
        "GL Assessment, CEM, and local 11+ exams differ significantly. The 2026 format guide explains which your child faces and exactly how to prepare for each.",

    "blog/grammar-school-vs-private-school-which-is-best-for-your-child.html":
        "Grammar school vs private school: cost, selectivity, culture and outcomes compared. Which is the better choice? An honest comparison for UK parents.",

    "blog/how-long-does-gcse-revision-take.html":
        "How long does GCSE revision take? Most students need 200–400 hours across all subjects. How to build a realistic revision schedule by grade target.",

    "blog/how-to-find-a-good-private-tutor.html":
        "How to find a good private tutor: what qualifications to check, questions to ask, and red flags to avoid. A practical guide for UK parents.",

    "blog/how-to-get-2800-in-the-ucat-a-week-by-week-revision-roadmap.html":
        "How to score 2800+ in the UCAT: a 12-week revision roadmap covering all five sections. Strategy, timing, and practice resources from Leading Tuition.",

    "blog/how-to-prepare-for-a-medical-school-mmi-interview.html":
        "How to prepare for a medical school MMI: the key station types, how to structure your answers, and the mistakes most candidates make. Expert guide.",

    "blog/is-private-tuition-worth-it-a-cost-benefit-analysis-of-1-to-1-learning.html":
        "Is private tuition worth it? We analyse the evidence on 1-to-1 learning, typical costs, and when tutoring makes the most difference — and when it doesn't.",

    "blog/is-the-11-plus-too-stressful-how-to-build-resilience-in-your-child.html":
        "Is the 11 Plus too stressful? Signs to watch for, how to manage exam anxiety, and ways to build resilience in your child without hurting performance.",

    "blog/low-ucat-score-top-5-strategic-uk-medical-schools-to-apply-to-in-2026.html":
        "Low UCAT score? The 5 best UK medical schools to apply to in 2026 if your UCAT is below 2600. Strategic selection to maximise your interview chances.",

    "blog/medical-schools-that-dont-care-about-gcses-a-strategic-selection-guide.html":
        "Some UK medical schools weight GCSEs minimally. A strategic guide to which schools give the most and least GCSE weight — and how to choose wisely.",

    "blog/mmi-interviews-2026-50-real-scenarios-and-model-answer-frameworks.html":
        "50 real MMI interview scenarios for 2026 with model answer frameworks. Ethics, role play, communication and data stations. Expert preparation guide.",

    "blog/online-tutoring-vs-in-person-tutoring-for-gcse.html":
        "Online vs in-person GCSE tutoring: which gets better results? Focus, flexibility, cost, and outcomes compared to help you choose the right format.",

    "blog/oxbridge-interview-questions-100-real-examples-for-every-major-subject.html":
        "100 real Oxbridge interview questions by subject. Sample questions for Medicine, Law, PPE, Maths, Sciences, and more — with expert guidance.",

    "blog/oxford-cambridge-and-ucl-medicine-mastering-the-ucat-for-elite-universities.html":
        "UCAT strategy for Oxford, Cambridge, and UCL Medicine. What UCAT score these elite schools expect, and how to prepare beyond the standard benchmark.",

    "blog/oxford-vs-cambridge-which-university-is-easier-for-your-subject.html":
        "Oxford vs Cambridge: which is easier to get into for your subject? Offer rates, A-Level requirements, and interview styles compared by subject area.",

    "blog/the-6-month-11-plus-countdown-a-monthly-study-milestone-plan.html":
        "The 6-month 11 Plus countdown: a month-by-month plan covering what to study, when to start mocks, and how to peak by September exam day.",

    "blog/the-new-ucas-personal-statement-2026-a-guide-to-the-3-question-format.html":
        "UCAS changed to a 3-question personal statement format in 2026. What each question asks and how to write a strong, structured response.",

    "blog/ucas-personal-statement-guide.html":
        "How to write a UCAS personal statement that stands out: structure, opening lines, super-curricular evidence, and what admissions tutors look for.",

    "blog/ucat-cut-offs-for-every-uk-medical-school-5-year-trends-and-2026-predictions.html":
        "UCAT cut-off scores for every UK medical school: 5-year trends and 2026 predictions. Know exactly where to target your application strategy.",

    "blog/ucat-score-requirements-for-uk-medical-schools-2025.html":
        "UCAT score requirements for UK medical schools in 2025. Minimum thresholds, competitive benchmarks, and how scores are used by each school.",

    "blog/what-grade-do-you-need-for-oxbridge-chemistry.html":
        "What A-Level grades do you need for Oxford or Cambridge Chemistry? Realistic benchmarks, GCSE expectations, and how to make a competitive application.",

    "blog/what-is-super-curricular-how-to-build-a-profile-for-oxford-and-cambridge.html":
        "What is super-curricular? How to build a genuine academic profile for Oxford and Cambridge: reading, projects, and activities that actually impress.",

    "blog/what-is-the-11-plus-exam.html":
        "What is the 11 Plus exam? How it works, which subjects are tested, how it varies by region, and how to start preparing your child for grammar school.",

    # ── LOCATION PAGES ────────────────────────────────────────────────────────
    "locations/barnet.html":
        "Private tutors in Barnet for GCSE, A-Level and 11+ prep. Specialist coaching for QE Barnet and Henrietta Barnett. DBS-checked. 4.8/5 Trustpilot.",

    "locations/bath.html":
        "Private tutors in Bath covering GCSE, A-Level, 11+ and university preparation. Oxford and Cambridge-educated tutors. DBS-checked. 4.8/5 Trustpilot.",

    "locations/birmingham.html":
        "Private tutors in Birmingham for GCSE, A-Level, 11+ and medicine prep. Specialist King Edward's and grammar school coaching. DBS-checked. 4.8/5 Trustpilot.",

    "locations/brighton.html":
        "Private tutors in Brighton for GCSE, A-Level, medicine prep and university applications. Oxford and Cambridge-educated tutors. DBS-checked. 4.8/5 Trustpilot.",

    "locations/bristol.html":
        "Private tutors in Bristol for GCSE, A-Level, 11+ prep, and Bristol University medicine applications. Oxford-educated tutors. DBS-checked. 4.8/5 Trustpilot.",

    "locations/bromley.html":
        "Private tutors in Bromley for GCSE, A-Level and 11+ Kent Test preparation. Grammar school coaching alongside medicine and Oxbridge prep. 4.8/5 Trustpilot.",

    "locations/cambridge.html":
        "Private tutors in Cambridge for GCSE, A-Level, and Oxbridge preparation. Specialist coaching from Cambridge-educated tutors. DBS-checked. 4.8/5 Trustpilot.",

    "locations/cheltenham.html":
        "Private tutors in Cheltenham for GCSE, A-Level and 11+ prep including Pate's Grammar coaching. Oxford-educated tutors. DBS-checked. 4.8/5 Trustpilot.",

    "locations/coventry.html":
        "Private tutors in Coventry for GCSE, A-Level and medicine prep. Specialist support for Warwick University applications. DBS-checked. 4.8/5 Trustpilot.",

    "locations/croydon.html":
        "Private tutors in Croydon for GCSE, A-Level and 11+ Sutton grammar preparation. Specialist Sutton SET coaching alongside medicine prep. 4.8/5 Trustpilot.",

    "locations/derby.html":
        "Private tutors in Derby for GCSE, A-Level, 11+ and medicine preparation. Oxford and Cambridge-educated tutors, all DBS-checked. 4.8/5 Trustpilot.",

    "locations/ealing.html":
        "Private tutors in Ealing for GCSE, A-Level and 11+ preparation. Specialist coaching for West London selective schools. DBS-checked. 4.8/5 Trustpilot.",

    "locations/exeter.html":
        "Private tutors in Exeter for GCSE, A-Level and medicine prep. Specialist support for Exeter University admissions. DBS-checked. 4.8/5 Trustpilot.",

    "locations/guildford.html":
        "Private tutors in Guildford for GCSE, A-Level and 11+ preparation. Specialist coaching for Royal Grammar School Guildford. DBS-checked. 4.8/5 Trustpilot.",

    "locations/harrow.html":
        "Private tutors in Harrow for GCSE, A-Level and 11+ preparation. Specialist coaching for North London selective schools. DBS-checked. 4.8/5 Trustpilot.",

    "locations/kingston-upon-thames.html":
        "Private tutors in Kingston upon Thames for GCSE, A-Level, and specialist 11+ coaching for Tiffin School and Tiffin Girls'. DBS-checked. 4.8/5 Trustpilot.",

    "locations/leeds.html":
        "Private tutors in Leeds for GCSE, A-Level and medicine prep. Specialist support for Leeds University medicine and Oxbridge applications. 4.8/5 Trustpilot.",

    "locations/leicester.html":
        "Private tutors in Leicester for GCSE, A-Level and medicine prep. Support for Leicester medical school applications. DBS-checked. 4.8/5 Trustpilot.",

    "locations/liverpool.html":
        "Private tutors in Liverpool for GCSE, A-Level and medicine prep. Specialist coaching for Liverpool medical school applicants. DBS-checked. 4.8/5 Trustpilot.",

    "locations/london.html":
        "Private tutors across London for GCSE, A-Level, 11+, medicine prep and Oxbridge admissions. Oxbridge-educated, DBS-checked. 4.8/5 Trustpilot.",

    "locations/luton.html":
        "Private tutors in Luton for GCSE, A-Level and 11+ prep. Specialist grammar school coaching for Hertfordshire and Bedfordshire. DBS-checked. 4.8/5.",

    "locations/manchester.html":
        "Private tutors in Manchester for GCSE, A-Level and 11+ Trafford consortium prep. Specialist Altrincham and Sale Grammar coaching. DBS-checked. 4.8/5.",

    "locations/milton-keynes.html":
        "Private tutors in Milton Keynes for GCSE, A-Level, 11+ and medicine preparation. Oxford and Cambridge-educated tutors. DBS-checked. 4.8/5 Trustpilot.",

    "locations/northampton.html":
        "Private tutors in Northampton for GCSE, A-Level, 11+ and medicine preparation. Oxford and Cambridge-educated tutors. DBS-checked. 4.8/5 Trustpilot.",

    "locations/norwich.html":
        "Private tutors in Norwich for GCSE, A-Level and university prep. Specialist coaching for UEA admissions and selective schools. DBS-checked. 4.8/5 Trustpilot.",

    "locations/nottingham.html":
        "Private tutors in Nottingham for GCSE, A-Level and medicine prep. Specialist Nottingham medical school application coaching. DBS-checked. 4.8/5 Trustpilot.",

    "locations/oxford.html":
        "Private tutors in Oxford for GCSE, A-Level and Oxbridge preparation. Expert coaching in one of the UK's most academic cities. DBS-checked. 4.8/5 Trustpilot.",

    "locations/portsmouth.html":
        "Private tutors in Portsmouth for GCSE, A-Level, 11+ and medicine preparation. Oxford and Cambridge-educated tutors, DBS-checked. 4.8/5 Trustpilot.",

    "locations/reading.html":
        "Private tutors in Reading for GCSE, A-Level and 11+ prep. Specialist grammar school coaching including Reading School and Kendrick. 4.8/5 Trustpilot.",

    "locations/sheffield.html":
        "Private tutors in Sheffield for GCSE, A-Level and medicine prep. Specialist Sheffield University medical school coaching. DBS-checked. 4.8/5 Trustpilot.",

    "locations/slough.html":
        "Private tutors in Slough for GCSE, A-Level and 11+ prep. Specialist coaching for Slough grammar schools including Upton Court. DBS-checked. 4.8/5.",

    "locations/twickenham.html":
        "Private tutors in Twickenham for GCSE, A-Level and 11+ preparation. Close to Tiffin School and Richmond Park area. DBS-checked. 4.8/5 Trustpilot.",

    "locations/watford.html":
        "Private tutors in Watford for GCSE, A-Level and 11+ preparation. Specialist grammar school coaching across Hertfordshire. DBS-checked. 4.8/5 Trustpilot.",

    "locations/wimbledon.html":
        "Private tutors in Wimbledon for GCSE, A-Level and 11+ preparation. Expert coaching for Raynes Park and South London selective schools. 4.8/5 Trustpilot.",

    "locations/york.html":
        "Private tutors in York for GCSE, A-Level and 11+ prep. Specialist university admissions coaching for University of York. DBS-checked. 4.8/5 Trustpilot.",

    # ── MEDICAL SCHOOL PAGES ─────────────────────────────────────────────────
    "medical-schools/aberdeen/index.html":
        "Aberdeen Medicine: 5-year MBChB entry requirements, A-Level grades, UCAT thresholds, and interview prep. Scottish school with a focus on rural medicine.",

    "medical-schools/anglia-ruskin/index.html":
        "Anglia Ruskin Medicine: graduate-entry MBChB only, no UCAT required. A-Level background, GAMSAT/MCAT routes, interview format, and how to apply.",

    "medical-schools/aston/index.html":
        "Aston Medicine: lower A-Level requirements, no UCAT for most routes. Entry requirements, interview format, and how to build a strong 2026 application.",

    "medical-schools/barts/index.html":
        "Barts Medicine entry requirements: A-Level grades, UCAT thresholds, and MMI preparation for one of London's most prestigious medical schools.",

    "medical-schools/birmingham/index.html":
        "University of Birmingham Medicine: A-Level grades, UCAT thresholds, MMI format, and application strategy. One of the UK's top Russell Group medical schools.",

    "medical-schools/brighton-sussex/index.html":
        "Brighton and Sussex Medical School: graduate-entry GEM, GAMSAT requirements, and interview coaching. How to apply to this progressive medical school.",

    "medical-schools/bristol/index.html":
        "Bristol Medicine entry: A-Level requirements, UCAT thresholds, panel interview prep, and tips for this highly competitive Russell Group school.",

    "medical-schools/cambridge/index.html":
        "Cambridge Medicine entry: A-Level grades, interview coaching, and the pre-clinical/clinical structure. No UCAT required — the most selective course in the UK.",

    "medical-schools/cardiff/index.html":
        "Cardiff University Medicine: A-Level grades, UCAT thresholds, and MMI interview coaching. Entry requirements for Wales' flagship medical school.",

    "medical-schools/dundee/index.html":
        "University of Dundee Medicine: 5-year MBChB entry requirements, A-Level grades, and interview prep. Scottish school with innovative clinical training.",

    "medical-schools/east-anglia/index.html":
        "University of East Anglia Medicine: A-Level grades, UCAT thresholds, panel interview format, and how to apply. Smaller cohort, strong clinical focus.",

    "medical-schools/edinburgh/index.html":
        "University of Edinburgh Medicine: highly competitive entry, A-Level grades, UCAT thresholds, and interview format. One of Scotland's most selective schools.",

    "medical-schools/exeter/index.html":
        "University of Exeter Medicine: A-Level grades, UCAT thresholds, and panel interview prep. A competitive but accessible school with small cohorts.",

    "medical-schools/glasgow/index.html":
        "University of Glasgow Medicine: 5-year MBChB entry requirements, UCAT thresholds, and interview coaching for Scotland's leading research medical school.",

    "medical-schools/hull-york/index.html":
        "Hull York Medical School: problem-based learning, A-Level grades, UCAT thresholds, and interview prep. An innovative approach to medical education.",

    "medical-schools/imperial/index.html":
        "Imperial College London Medicine: A-Level grades, UCAT requirements, and interview coaching. One of London's most competitive and research-intensive schools.",

    "medical-schools/keele/index.html":
        "Keele Medicine entry: 5-year MBChB requirements, A-Level grades, UCAT thresholds, and interview format. Integrated clinical training from year one.",

    "medical-schools/kings/index.html":
        "King's College London Medicine: competitive A-Level grades, UCAT thresholds, and MMI coaching. How to apply to one of London's top medical schools.",

    "medical-schools/lancaster/index.html":
        "Lancaster University Medicine: 5-year MBChB entry requirements, A-Level grades, UCAT thresholds and interview preparation. Newer school, growing reputation.",

    "medical-schools/leeds/index.html":
        "University of Leeds Medicine: competitive A-Level grades, UCAT thresholds, and MMI interview prep. How to build a strong application for Leeds.",

    "medical-schools/leicester/index.html":
        "University of Leicester Medicine: A-Level grades, UCAT thresholds, and MMI coaching. A research-strong school with a diverse and competitive intake.",

    "medical-schools/lincoln/index.html":
        "University of Lincoln Medicine: entry requirements, A-Level grades, UCAT thresholds, and interview tips. Newer school with growing NHS placement reputation.",

    "medical-schools/liverpool/index.html":
        "University of Liverpool Medicine: A-Level grades, UCAT thresholds, MMI interview coaching and application strategy. Based in a major NHS teaching city.",

    "medical-schools/manchester/index.html":
        "University of Manchester Medicine: highly competitive entry grades, UCAT thresholds, and interview coaching. One of the UK's largest medical schools.",

    "medical-schools/newcastle/index.html":
        "Newcastle University Medicine: A-Level grades, UCAT thresholds, MMI interview coaching, and application strategy. Strong clinical placements.",

    "medical-schools/nottingham/index.html":
        "University of Nottingham Medicine: A-Level grades, UCAT thresholds, and MMI interview prep. Both 5-year and graduate-entry routes explained.",

    "medical-schools/oxford/index.html":
        "University of Oxford Medicine: the most competitive course in the UK. A-Level grades, interview coaching, and the pre-clinical/clinical structure explained.",

    "medical-schools/plymouth/index.html":
        "University of Plymouth Medicine: A-Level grades, UCAT thresholds, and interview coaching. Peninsula Medical School with a strong rural medicine focus.",

    "medical-schools/queens-belfast/index.html":
        "Queen's University Belfast Medicine: A-Level grades, UCAT thresholds, and interview coaching for Northern Ireland's leading medical school.",

    "medical-schools/sheffield/index.html":
        "University of Sheffield Medicine: competitive A-Level grades, UCAT thresholds, and MMI interview coaching. Strong academic and clinical reputation.",

    "medical-schools/southampton/index.html":
        "University of Southampton Medicine: A-Level grades, UCAT thresholds, and interview prep. Academic entry focus with a strong research reputation.",

    "medical-schools/st-andrews/index.html":
        "University of St Andrews Medicine: pre-clinical BSc only, A-Level grades, and interview coaching. The 2+2 clinical route to medicine fully explained.",

    "medical-schools/st-georges/index.html":
        "St George's Medicine: A-Level grades, UCAT thresholds, and MMI interview coaching. A diverse London medical school specialising in healthcare practice.",

    "medical-schools/sunderland/index.html":
        "University of Sunderland Medicine: A-Level grades, UCAT thresholds, and interview tips. Newer medical school with lower competition and smaller cohorts.",

    "medical-schools/swansea/index.html":
        "Swansea Medicine: graduate-entry only MBBCh programme. GAMSAT requirements, A-Level background, interview coaching. Wales' graduate medical school.",

    "medical-schools/ucl/index.html":
        "University College London Medicine: highly competitive A-Level grades, UCAT thresholds, and MMI coaching. One of the UK's most prestigious medical schools.",

    "medical-schools/uclan/index.html":
        "University of Central Lancashire Medicine: A-Level grades, UCAT thresholds, and interview tips. A growing medical school in Preston with NHS placements.",

    "medical-schools/warwick/index.html":
        "University of Warwick Medicine: graduate-entry only, UCAT thresholds, MMI interview coaching, and how to apply. One of the UK's top graduate medical schools.",

    # ── OXBRIDGE INTERVIEW PAGES ──────────────────────────────────────────────
    "oxbridge-interviews/biology-interview/index.html":
        "Oxford and Cambridge Biology interview preparation: ESAT coaching, problem-solving technique, and mock interviews. Expert support from Oxbridge-educated tutors.",

    "oxbridge-interviews/chemistry-interview/index.html":
        "Oxford and Cambridge Chemistry interview prep: ESAT coaching, problem-solving technique, and mock interviews. Expert support from Oxbridge-educated tutors.",

    "oxbridge-interviews/classics-interview/index.html":
        "Oxford and Cambridge Classics interview preparation: unseen texts, written work coaching, and mock interviews from Oxbridge-educated Classics tutors.",

    "oxbridge-interviews/computer-science-interview/index.html":
        "Oxford and Cambridge Computer Science interview prep: algorithmic thinking, MAT and TMUA coaching, and mock interviews from Oxbridge-educated tutors.",

    "oxbridge-interviews/economics-interview/index.html":
        "Oxford and Cambridge Economics interview prep: graph analysis, TSA coaching, and mock interviews to build economic reasoning. Oxbridge-educated tutors.",

    "oxbridge-interviews/engineering-interview/index.html":
        "Oxford and Cambridge Engineering interview preparation: applied problem-solving, PAT and ESAT coaching. Expert support from Oxbridge-educated engineers.",

    "oxbridge-interviews/english-interview/index.html":
        "Oxford and Cambridge English interview preparation: close reading, ELAT coaching, and literary argument technique. Expert support from Oxbridge-educated tutors.",

    "oxbridge-interviews/geography-interview/index.html":
        "Oxford and Cambridge Geography interview preparation: essay and map questions, fieldwork discussion, and mock interviews from Oxbridge-educated tutors.",

    "oxbridge-interviews/history-interview/index.html":
        "Oxford and Cambridge History interview prep: HAT coaching, source analysis, and historical argument technique. Expert support from Oxbridge-educated tutors.",

    "oxbridge-interviews/law-interview/index.html":
        "Oxford and Cambridge Law interview preparation: LNAT coaching, legal reasoning, and mock interviews. Expert support from Oxbridge-educated law tutors.",

    "oxbridge-interviews/maths-interview/index.html":
        "Oxford and Cambridge Mathematics interview prep: MAT and STEP coaching, problem-solving technique from Cambridge-educated mathematicians. 4.8/5 Trustpilot.",

    "oxbridge-interviews/medicine-interview/index.html":
        "Oxbridge Medicine interview preparation: MMI and panel coaching, ethical scenarios, and scientific reasoning. Expert support from Oxford and Cambridge medics.",

    "oxbridge-interviews/modern-languages-interview/index.html":
        "Oxford and Cambridge Modern Languages interview prep: language discussion, MLAT coaching, and literature analysis from Oxbridge-educated tutors.",

    "oxbridge-interviews/natural-sciences-interview/index.html":
        "Cambridge Natural Sciences interview preparation: ESAT coaching, problem-solving technique, and mock interviews from Cambridge-educated Natural Sciences tutors.",

    "oxbridge-interviews/philosophy-interview/index.html":
        "Oxford and Cambridge Philosophy interview preparation: argument analysis, PHIL test coaching, and philosophical reasoning with Oxbridge-educated tutors.",

    "oxbridge-interviews/physics-interview/index.html":
        "Oxford and Cambridge Physics interview preparation: PAT and ESAT coaching, applied problem-solving, and mock interviews from Oxbridge-educated physicists.",

    "oxbridge-interviews/ppe-interview/index.html":
        "Oxford PPE interview preparation: TSA coaching, cross-disciplinary reasoning across Politics, Philosophy and Economics. Expert Oxford-educated tutors.",

    "oxbridge-interviews/psychology-interview/index.html":
        "Oxford and Cambridge Psychology interview preparation: research critique, scientific reasoning, and mock interviews from Oxbridge-educated Psychology tutors.",

    # ── ADMISSIONS TEST PAGES ────────────────────────────────────────────────
    "admissions-tests/elat-preparation/index.html":
        "Expert ELAT preparation for Oxford English applicants. Close reading technique, comparative essay writing, and timed practice from Oxford-educated tutors. 4.8/5.",

    "admissions-tests/esat-preparation/index.html":
        "Expert ESAT preparation for Cambridge Engineering and Natural Science applicants. Section-by-section strategy from Cambridge-educated tutors. 4.8/5 Trustpilot.",

    "admissions-tests/hat-preparation/index.html":
        "Expert HAT preparation for Oxford History applicants. Source analysis, time management, and timed practice from Oxford-educated tutors. 4.8/5 Trustpilot.",

    "admissions-tests/lnat-preparation/index.html":
        "Expert LNAT preparation from Oxbridge-educated tutors. Critical reasoning strategies for Section A and essay technique for Section B. 4.8/5 Trustpilot.",

    "admissions-tests/mat-preparation/index.html":
        "Expert MAT preparation for Oxford and Imperial Mathematics. Problem-solving technique, past paper coaching, and mock tests from Oxford-educated tutors. 4.8/5.",

    "admissions-tests/mlat-preparation/index.html":
        "Expert MLAT preparation for Oxford Modern Languages applicants. Language reasoning, vocabulary analysis, and timed practice from Oxford-educated tutors. 4.8/5.",

    "admissions-tests/pat-preparation/index.html":
        "Expert PAT preparation for Oxford Physics applicants. Mechanics, electricity, and optics coaching from Oxford-educated physicists. 4.8/5 Trustpilot.",

    "admissions-tests/phil-preparation/index.html":
        "Expert Oxford PHIL test preparation. Argument analysis, philosophical reasoning, and written response coaching from Oxford-educated Philosophy tutors. 4.8/5.",

    "admissions-tests/step-preparation/index.html":
        "Expert STEP Maths preparation for Cambridge and Warwick applicants. Pure and applied problem-solving coaching from Cambridge-educated mathematicians. 4.8/5.",

    "admissions-tests/tmua-preparation/index.html":
        "Expert TMUA preparation for Cambridge, Bath, and Durham applicants. Mathematical reasoning strategies and timed practice from Cambridge-educated tutors. 4.8/5.",

    "admissions-tests/tsa-preparation/index.html":
        "Expert TSA preparation for Oxford Economics, PPE, and Psychology applicants. Critical thinking and problem solving coaching from Oxford-educated tutors. 4.8/5.",

    # ── 11+ SCHOOL-SPECIFIC PAGES ────────────────────────────────────────────
    "11-plus/altrincham-grammar-schools/index.html":
        "Expert 11+ prep for Altrincham Grammar School and Sale Grammar. Specialist Trafford consortium coaching: GL-style reasoning and maths. 4.8/5 Trustpilot.",

    "11-plus/slough-grammar-schools/index.html":
        "Expert Slough grammar school 11+ preparation. Specialist SET coaching for all 5 Slough schools: Upton Court, Herschel, Langley, Slough Grammar and Khalsa.",

    "11-plus/sale-grammar-school/index.html":
        "Expert Sale Grammar School 11+ preparation. Specialist Trafford consortium coaching with past papers, timed tests, and targeted weak-area support. 4.8/5.",

    "11-plus/st-olaves-grammar-school/index.html":
        "Expert St Olave's Grammar School 11+ preparation. One of the UK's most selective schools — specialist coaching for the TBGS Orpington selective entry.",

    "11-plus/sutton-grammar-schools/index.html":
        "Expert Sutton grammar school 11+ preparation. Specialist Sutton SET coaching for Wilson's, Sutton Grammar, Wallington, Nonsuch and Greenshaw. 4.8/5 Trustpilot.",

    # ── SERVICE SUBJECT PAGES ─────────────────────────────────────────────────
    "services/subjects/biology-tutor.html":
        "Expert Biology tutors for GCSE and A-Level. All specifications covered: AQA, OCR, Edexcel. Required practicals, essay skills, and A-Level scaling. 4.8/5.",

    "services/subjects/business-studies-tutor.html":
        "Expert Business Studies tutors for GCSE and A-Level. Case study technique, financial ratios, and business analysis. AQA, Edexcel, OCR. 4.8/5 Trustpilot.",

    "services/subjects/chemistry-tutor.html":
        "Expert Chemistry tutors for GCSE and A-Level. Organic mechanisms, stoichiometry, required practicals. AQA, Edexcel and OCR. DBS-checked. 4.8/5 Trustpilot.",

    "services/subjects/computer-science-tutor.html":
        "Expert Computer Science tutors for GCSE and A-Level. Programming, algorithms, networks and theory. AQA and OCR specifications. DBS-checked. 4.8/5 Trustpilot.",

    "services/subjects/economics-tutor.html":
        "Expert Economics tutors for GCSE and A-Level. Micro and macroeconomics, evaluation skills, and essay technique. AQA, Edexcel, OCR. 4.8/5 Trustpilot.",

    "services/subjects/english-language-tutor.html":
        "Expert English Language tutors for GCSE and A-Level. Analytical frameworks, language analysis, and creative writing. AQA, Edexcel, OCR. 4.8/5 Trustpilot.",

    "services/subjects/english-literature-tutor.html":
        "Expert English Literature tutors for GCSE and A-Level. Text analysis, essay technique, and unseen poetry. AQA, Edexcel, OCR. DBS-checked. 4.8/5 Trustpilot.",

    "services/subjects/further-maths-tutor.html":
        "Expert Further Maths tutors for GCSE and A-Level. Decision maths, mechanics, statistics, and pure modules. AQA, Edexcel, OCR. DBS-checked. 4.8/5 Trustpilot.",

    "services/subjects/geography-tutor.html":
        "Expert Geography tutors for GCSE and A-Level. Physical and human geography, fieldwork, and evaluation skills. AQA, Edexcel, OCR. 4.8/5 Trustpilot.",

    "services/subjects/history-tutor.html":
        "Expert History tutors for GCSE and A-Level. Source analysis, essay structure, and argument development. AQA, Edexcel, OCR. DBS-checked. 4.8/5 Trustpilot.",

    "services/subjects/maths-tutor.html":
        "Expert Maths tutors for GCSE and A-Level. Pure, Statistics, and Mechanics modules covered. AQA, Edexcel, OCR. Higher and Foundation. 4.8/5 Trustpilot.",

    "services/subjects/physics-tutor.html":
        "Expert Physics tutors for GCSE and A-Level. Mechanics, electricity, waves and nuclear physics. AQA, Edexcel, OCR. DBS-checked. 4.8/5 Trustpilot.",

    "services/subjects/politics-tutor.html":
        "Expert Politics tutors for GCSE and A-Level. UK Government and Politics, political ideologies, and comparative politics. AQA, Edexcel. 4.8/5 Trustpilot.",

    "services/subjects/psychology-tutor.html":
        "Expert Psychology tutors for GCSE and A-Level. Research methods, biological, cognitive, and social psychology. AQA, OCR. DBS-checked. 4.8/5 Trustpilot.",

    "services/subjects/statistics-tutor.html":
        "Expert Statistics tutors for GCSE and A-Level. Probability, hypothesis testing, distributions, and data analysis. AQA, Edexcel, OCR. 4.8/5 Trustpilot.",

}


# ── Replacement engine ────────────────────────────────────────────────────────

def escape_for_regex(text):
    """Escape special regex characters in the old content."""
    return re.escape(text)


def update_meta_tags(html: str, new_desc: str) -> tuple[str, bool]:
    """Replace all three meta description tags with new_desc. Returns (new_html, changed)."""
    result = html

    patterns = [
        # <meta name="description" content="...">
        (r'(<meta\s+name="description"\s+content=")[^"]*(")', r'\g<1>' + new_desc + r'\2'),
        # <meta property="og:description" content="...">
        (r'(<meta\s+property="og:description"\s+content=")[^"]*(")', r'\g<1>' + new_desc + r'\2'),
        # <meta name="twitter:description" content="...">
        (r'(<meta\s+name="twitter:description"\s+content=")[^"]*(")', r'\g<1>' + new_desc + r'\2'),
    ]

    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)

    return result, result != html


def main():
    updated = []
    skipped = []
    errors = []

    for rel_path, new_desc in DESCRIPTIONS.items():
        html_path = OUTPUT_DIR / rel_path

        if not html_path.exists():
            errors.append(f"  MISSING: {rel_path}")
            continue

        char_count = len(new_desc)
        if char_count > 162:
            errors.append(f"  TOO LONG ({char_count} chars): {rel_path}")
            continue

        html = html_path.read_text(encoding="utf-8")
        new_html, changed = update_meta_tags(html, new_desc)

        if changed:
            html_path.write_text(new_html, encoding="utf-8")
            updated.append(f"  [{char_count}c] {rel_path}")
        else:
            skipped.append(f"  {rel_path}")

    print(f"✅ Updated ({len(updated)}):")
    print("\n".join(updated) if updated else "  (none)")

    print(f"\n⏭  Already up to date ({len(skipped)}):")
    print("\n".join(skipped) if skipped else "  (none)")

    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        print("\n".join(errors))

    print(f"\nDone. {len(updated)} updated, {len(skipped)} skipped, {len(errors)} errors.")


if __name__ == "__main__":
    main()
