# Leading Tuition SEO generator config
SITE_NAME = "Leading Tuition"
BASE_URL = "/"
OUTPUT_DIR = "output"

# ── Location config ────────────────────────────────────────────────────────────
# Each entry: name, slug, region, exam_board, local_notes (2-3 bullet strings)
LOCATIONS = [
    {
        "name": "London",
        "slug": "london",
        "region": "Greater London",
        "exam_board": "AQA, Edexcel, OCR (varies by school)",
        "local_notes": [
            "Extremely competitive independent school entry at 7+, 11+, and 13+ across all London boroughs",
            "Largest concentration of Oxbridge and Russell Group applicants in the UK; many families seek subject interview and admissions test preparation",
            "Grammar schools in outer boroughs (Henrietta Barnett, QE Barnet, Tiffin) draw applicants from across the city",
        ],
    },
    {
        "name": "Manchester",
        "slug": "manchester",
        "region": "North West England",
        "exam_board": "AQA",
        "local_notes": [
            "Manchester Grammar School and Manchester High School for Girls are among the most academically selective day schools in the UK",
            "Strong grammar school competition across the Trafford borough: Altrincham Grammar School for Boys, Altrincham Grammar School for Girls, and Sale Grammar School",
            "University of Manchester and its medical school create high local aspiration for medicine preparation and UCAT coaching",
        ],
    },
    {
        "name": "Birmingham",
        "slug": "birmingham",
        "region": "West Midlands",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "The King Edward VI foundation operates five selective grammar schools in Birmingham — among the most academically competitive state schools in England",
            "Edgbaston High School for Girls and King Edward's School Birmingham are leading independent options attracting families from across the West Midlands",
            "University of Birmingham's medical school drives strong local demand for UCAT preparation and medicine admissions coaching",
        ],
    },
    {
        "name": "Leeds",
        "slug": "leeds",
        "region": "Yorkshire",
        "exam_board": "AQA",
        "local_notes": [
            "No grammar schools in Leeds LEA; secondary schools are comprehensive but competition for the best state and independent options is significant",
            "Strong A-Level demand targeting the University of Leeds, Durham, and other Russell Group universities from families in Roundhay, Headingley, and Chapel Allerton",
            "Leeds Grammar School and Notre Dame Catholic Sixth Form College are popular independent and faith-based choices requiring attainment-focused preparation",
        ],
    },
    {
        "name": "Bristol",
        "slug": "bristol",
        "region": "South West England",
        "exam_board": "OCR",
        "local_notes": [
            "Bristol Grammar School and Clifton College are leading academic independent schools with competitive entry; St Mary Redcliffe is a highly regarded state option",
            "OCR is the dominant exam board across Bristol and the surrounding South West region — board-specific preparation is important",
            "University of Bristol is a top Russell Group institution and major driver of A-Level aspiration, with many families also seeking medicine and Oxbridge preparation",
        ],
    },
    {
        "name": "Sheffield",
        "slug": "sheffield",
        "region": "Yorkshire",
        "exam_board": "AQA",
        "local_notes": [
            "Sheffield High School for Girls (GDST) and King Edward VII School are the city's strongest academic options, attracting tutoring demand for entrance and A-Level support",
            "AQA is dominant across Yorkshire; tutors with detailed knowledge of AQA mark schemes and question styles are particularly valuable",
            "The University of Sheffield's medical school drives growing local interest in UCAT preparation among Year 12 and 13 students",
        ],
    },
    {
        "name": "Liverpool",
        "slug": "liverpool",
        "region": "North West England",
        "exam_board": "AQA",
        "local_notes": [
            "Wirral Grammar School for Boys and Wirral Grammar School for Girls serve the Wirral peninsula; 11+ preparation is a significant demand driver in the area",
            "Liverpool College and Merchant Taylors' School are leading independent schools; The Belvedere Academy is a selective GDST school in the city",
            "University of Liverpool Medical School draws strong local aspiration for medicine preparation, UCAT coaching, and personal statement support",
        ],
    },
    {
        "name": "Oxford",
        "slug": "oxford",
        "region": "South East England",
        "exam_board": "OCR",
        "local_notes": [
            "Oxford families have unusually high awareness of university admissions; aspirations for Oxford University itself or other highly selective institutions are common across all age groups",
            "Oxford High School (GDST), Magdalen College School, and St Edward's School are the leading independent options; OCR dominates across Oxfordshire state schools",
            "Admissions test preparation (MAT, LNAT, TSA, HAT, ELAT) and Oxbridge interview coaching are significant demand areas specific to this city",
        ],
    },
    {
        "name": "Cambridge",
        "slug": "cambridge",
        "region": "East of England",
        "exam_board": "OCR",
        "local_notes": [
            "The Perse School and The Stephen Perse Foundation are academically selective independent schools; Hills Road and Long Road Sixth Form Colleges are highly regarded state options",
            "Cambridge's scholarly culture means many families have very high academic expectations; aspirations for Cambridge University and other Russell Group institutions are widespread",
            "OCR dominates across Cambridgeshire; admissions test preparation and Oxbridge interview coaching are particularly prominent demand areas",
        ],
    },
    {
        "name": "Brighton",
        "slug": "brighton",
        "region": "South East England",
        "exam_board": "OCR and Edexcel",
        "local_notes": [
            "Brighton College and Brighton and Hove High School (GDST) are leading academic independents; BHASVIC and Varndean Sixth Form College are the city's most popular state sixth forms",
            "Brighton and Hove has no grammar schools; independent school entrance preparation is the primary driver of 11+ and junior-age tutoring demand",
            "Strong A-Level demand targeting London and Russell Group universities; OCR and Edexcel are the dominant exam boards across Brighton schools",
        ],
    },
    {
        "name": "Nottingham",
        "slug": "nottingham",
        "region": "East Midlands",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Nottingham High School is a leading day independent school; West Bridgford School is one of the most sought-after comprehensives in Nottinghamshire",
            "Nottingham has no grammar schools; demand is driven by GCSE and A-Level support, particularly in the West Bridgford and Beeston suburbs",
            "Nottingham's medical school is one of the UK's most competitive; strong local demand for UCAT preparation and medicine admissions coaching among A-Level students",
        ],
    },
    {
        "name": "Leicester",
        "slug": "leicester",
        "region": "East Midlands",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Leicester Grammar School and Loughborough Grammar School are the region's leading academic independents, attracting aspirational families from across the county",
            "University of Leicester Medical School is one of the UK's leading institutions; UCAT preparation and medicine admissions support are significant demand areas",
            "The affluent Oadby and Stoneygate suburbs generate strong GCSE and A-Level tutoring demand; families in these areas frequently target Russell Group entry",
        ],
    },
    {
        "name": "Reading",
        "slug": "reading",
        "region": "South East England",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Reading School (boys) and Kendrick School (girls) are two of the most academically selective grammar schools in England, with hundreds of applicants competing for a small number of places",
            "The Abbey School Reading and The Oratory School are leading Catholic and independent options; The Grammar School at Leeds has a campus at Reading (The Oratory)",
            "Strong commuter-belt families target London and Russell Group universities; 11+ preparation for Reading and Kendrick is a particularly competitive demand area",
        ],
    },
    {
        "name": "Guildford",
        "slug": "guildford",
        "region": "South East England",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Royal Grammar School Guildford is one of the most academically selective grammar schools in England; Guildford High School and Tormead are leading independent girls' schools",
            "Surrey is one of England's most affluent counties; families in Godalming, Woking, and Farnham frequently seek GCSE and A-Level support targeting London and Oxbridge",
            "Strong demand for 11+ preparation given the competitiveness of RGS Guildford; independent school entrance preparation is also significant for Guildford High and Tormead",
        ],
    },
    {
        "name": "Coventry",
        "slug": "coventry",
        "region": "West Midlands",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Proximity to the University of Warwick — consistently ranked in the UK's top 10 — creates a highly aspirational academic culture and strong demand for A-Level support",
            "King Henry VIII School and Bablake School are the city's leading independent schools; Finham Park School is a popular and oversubscribed state option",
            "Warwick Medical School (one of the UK's leading graduate-entry medical schools) drives interest in medicine preparation from families across Coventry and Leamington Spa",
        ],
    },
    {
        "name": "Watford",
        "slug": "watford",
        "region": "East of England",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Watford Grammar School for Boys and Watford Grammar School for Girls are both highly oversubscribed selective state schools; 11+ preparation is a major demand driver across Hertfordshire",
            "St Michael's Catholic Grammar School and St Columba's College are additional selective options attracting families from across the county",
            "Watford's location between London and Hertfordshire attracts commuter families with high academic expectations; demand for A-Level support targeting Russell Group universities is strong",
        ],
    },
    {
        "name": "Kingston upon Thames",
        "slug": "kingston-upon-thames",
        "region": "South West London",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Tiffin School and Tiffin Girls' School are among the most academically competitive grammar schools in England; each year hundreds of children from across South West London and Surrey compete for a small number of places",
            "Kingston Grammar School and Surbiton High School are leading independent alternatives; Holy Cross School is a selective Catholic independent for girls",
            "The Royal Borough of Kingston upon Thames has high median household incomes and strong academic aspirations; families frequently target Oxbridge and Russell Group universities",
        ],
    },
    {
        "name": "Croydon",
        "slug": "croydon",
        "region": "South London",
        "exam_board": "AQA and Edexcel",
        "local_notes": [
            "Whitgift School and Trinity School Croydon are two of South London's most academically selective independent schools, with competitive entry and strong Oxbridge track records",
            "Old Palace of John Whitgift School is a selective independent for girls; the neighbouring Sutton borough's grammar schools (Nonsuch, Wallington) draw applicants from South Croydon and Purley",
            "Strong demand for 11+ preparation driven by selective school competition in both Croydon's independent sector and the adjacent Sutton grammar schools",
        ],
    },
    {
        "name": "Bromley",
        "slug": "bromley",
        "region": "South East London",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Newstead Wood School (girls) and St Olave's Grammar School (boys) are two of Greater London's most oversubscribed selective state schools; competition for places is exceptionally intense",
            "Ravens Wood School is a third selective option in the borough; Hayes School has a highly regarded sixth form; Langley Park School for Boys is a large comprehensive",
            "Families in Chislehurst, Petts Wood, and Orpington generate significant 11+ preparation demand; many students in the borough also target Russell Group universities at A-Level",
        ],
    },
    {
        "name": "Barnet",
        "slug": "barnet",
        "region": "North London",
        "exam_board": "AQA",
        "local_notes": [
            "Queen Elizabeth's School Barnet is consistently ranked among the top 5 state schools in England by academic results; competition for its 210 annual places is fierce",
            "Henrietta Barnett School is one of England's most selective grammar schools for girls; Mill Hill School and Haberdashers' Boys' School are the leading independent options",
            "The London Borough of Barnet extends into Hertfordshire commuter territory; families in Totteridge, East Barnet, Cockfosters, and Finchley have very high academic aspirations",
        ],
    },
    {
        "name": "Ealing",
        "slug": "ealing",
        "region": "West London",
        "exam_board": "AQA and Edexcel",
        "local_notes": [
            "St Benedict's School is a leading Benedictine independent school; Notting Hill and Ealing High School (GDST) is a selective girls' independent with strong academic results",
            "Ealing has no grammar schools; the borough's independent sector and well-regarded comprehensives (Drayton Manor, Greenford High) generate GCSE and A-Level tutoring demand",
            "West London families frequently target London universities; growing demand for medicine preparation and UCAT coaching among students in the Northfields and Ealing Broadway areas",
        ],
    },
    {
        "name": "Harrow",
        "slug": "harrow",
        "region": "North West London",
        "exam_board": "AQA and Edexcel",
        "local_notes": [
            "Harrow School is one of England's most prestigious boarding schools; John Lyon School is its academic day school counterpart and draws high-aspiration families from across NW London",
            "St Dominic's Sixth Form College is a popular Catholic sixth form; Harrow has no grammar schools, making independent school preparation the main driver of selective entry demand",
            "Families in Stanmore, Pinner, and Hatch End have high academic expectations; demand for A-Level support targeting Russell Group universities is consistent and growing",
        ],
    },
    {
        "name": "Wimbledon",
        "slug": "wimbledon",
        "region": "South West London",
        "exam_board": "AQA and Edexcel",
        "local_notes": [
            "King's College School Wimbledon is one of the most academically selective independent schools in the UK, with a strong Oxbridge track record; Wimbledon High School (GDST) is the leading independent girls' option",
            "Rutlish School and Ricards Lodge High School are well-regarded state comprehensives; the London Borough of Merton has no grammar schools",
            "Families in SW19 and surrounding areas (Raynes Park, Merton Park) frequently target Oxbridge and Russell Group universities, driving demand for A-Level support and admissions test preparation",
        ],
    },
    {
        "name": "Twickenham",
        "slug": "twickenham",
        "region": "South West London",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Hampton School and Lady Eleanor Holles School are two of South West London's most academically selective independent schools; both have outstanding A-Level and Oxbridge results",
            "Proximity to Tiffin School and Tiffin Girls' School in Kingston creates significant 11+ preparation demand across Richmond upon Thames; Radnor House is a growing independent option",
            "The Royal Borough of Richmond upon Thames is one of London's most affluent; families in Twickenham, St Margarets, and Teddington routinely target Russell Group and Oxbridge universities",
        ],
    },
    {
        "name": "York",
        "slug": "york",
        "region": "Yorkshire",
        "exam_board": "AQA",
        "local_notes": [
            "Bootham School and St Peter's School York are ancient independent schools with strong academic track records; The Mount School is a Quaker girls' independent with a distinctive ethos",
            "York has no grammar schools; the independent sector and selective comprehensives (Archbishop Holgate's, Fulford School) are the main drivers of aspirational tutoring demand",
            "The University of York is a founding member of the Russell Group and a strong driver of academic aspiration in the city; growing demand for medicine preparation among A-Level students",
        ],
    },
    {
        "name": "Exeter",
        "slug": "exeter",
        "region": "South West England",
        "exam_board": "OCR",
        "local_notes": [
            "Exeter School is the city's leading independent day school; The Maynard School is a selective independent for girls; both are academically strong with competitive entry",
            "Exeter College is one of the South West's largest sixth form colleges; the University of Exeter (Russell Group) is a major driver of A-Level aspiration across Devon",
            "Devon uses OCR as its dominant exam board; no grammar schools in the county, making independent school preparation and A-Level tuition the primary demand drivers",
        ],
    },
    {
        "name": "Norwich",
        "slug": "norwich",
        "region": "East of England",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Norwich School (in the Cathedral Close) is one of the East of England's most academically selective independents; Notre Dame High School is a leading Catholic girls' school",
            "Norfolk has no grammar schools; Norwich School and Langley School (near Loddon) are the main independent options attracting aspirational families from across the county",
            "The University of East Anglia (UEA) is a significant local presence driving academic aspiration; growing demand for A-Level support targeting Russell Group universities from Eaton and Thorpe families",
        ],
    },
    {
        "name": "Bath",
        "slug": "bath",
        "region": "South West England",
        "exam_board": "OCR",
        "local_notes": [
            "King Edward's School Bath is one of the South West's most academically selective independent schools; Prior Park College and Kingswood School are leading Catholic and traditional independent alternatives",
            "Bath and North East Somerset has no grammar schools; the independent sector drives most selective entry demand; Beechen Cliff School and Hayesfield Girls' School are the most sought-after comprehensives",
            "The University of Bath (top for engineering, science, and pharmacy) creates strong A-Level aspirations; proximity to Bristol University adds further Russell Group aspiration for Bath families",
        ],
    },
    {
        "name": "Cheltenham",
        "slug": "cheltenham",
        "region": "South West England",
        "exam_board": "OCR",
        "local_notes": [
            "Pate's Grammar School is one of England's most academically selective state schools, regularly appearing in the top 5 nationally; competition for places is intense across Gloucestershire",
            "Cheltenham Ladies' College and Cheltenham College are among the UK's most prestigious boarding and day independent schools; Dean Close School is a third highly regarded option",
            "The combination of a highly selective grammar school and one of the UK's strongest private school clusters makes Cheltenham one of the most educationally competitive towns in England",
        ],
    },
    {
        "name": "Milton Keynes",
        "slug": "milton-keynes",
        "region": "South East England",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Buckinghamshire is a fully selective county where the 11+ determines secondary school placement; families in Milton Keynes compete for places at Aylesbury Grammar School and Sir Henry Floyd Grammar School",
            "Walton High School and Denbigh School are the most sought-after non-selective secondaries in MK; the 11+ process across Buckinghamshire is one of the most competitive in England",
            "Milton Keynes is a rapidly growing city with a young demographic; demand for GCSE, A-Level, and 11+ preparation is expanding as the population's academic aspirations increase",
        ],
    },
    {
        "name": "Luton",
        "slug": "luton",
        "region": "East of England",
        "exam_board": "AQA and Edexcel",
        "local_notes": [
            "Luton has no grammar schools; the neighbouring village of Harpenden (within Luton's catchment for tuition) is one of Hertfordshire's most educationally aspirational communities",
            "Families in Harpenden, Dunstable, and Caddington routinely target Russell Group universities; growing demand for A-Level support, medicine preparation, and UCAT coaching",
            "Luton VI Form College and Stopsley High School are the city's main post-16 options; strong demand from families seeking support to access top universities from the Luton and mid-Bedfordshire area",
        ],
    },
    {
        "name": "Derby",
        "slug": "derby",
        "region": "East Midlands",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Derby Grammar School is a selective independent with strong academic results; Ockbrook School (Moravian ethos) offers an alternative independent option; no state grammar schools in the city",
            "The suburbs of Mickleover, Allestree, Littleover, and Chellaston generate consistent GCSE and A-Level tutoring demand from families targeting Nottingham and Leicester universities",
            "Growing interest in medicine preparation among Derby families, with Nottingham and Leicester medical schools being common targets; demand for UCAT coaching is increasing year on year",
        ],
    },
    {
        "name": "Portsmouth",
        "slug": "portsmouth",
        "region": "South East England",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Portsmouth Grammar School is the city's leading academic independent school with strong A-Level results; St John's College Portsmouth is a well-regarded Catholic independent option",
            "Portsmouth is an LEA without state grammar schools; however, Hampshire's selective school tradition means families in Fareham, Havant, and Waterlooville sometimes seek grammar school preparation",
            "The University of Southampton (Russell Group) is a major aspirational driver for Portsmouth families; growing demand for medicine preparation and UCAT coaching among sixth-form students in the Southsea and Cosham areas",
        ],
    },
    {
        "name": "Northampton",
        "slug": "northampton",
        "region": "East Midlands",
        "exam_board": "AQA and OCR",
        "local_notes": [
            "Northampton School for Boys and Northampton High School for Girls (GDST) are the town's strongest academic options; Sponne School in nearby Towcester is a high-performing comprehensive",
            "Northamptonshire has no grammar schools; tutoring demand is driven by GCSE and A-Level support from families in Abington, Kingsthorpe, and Weston Favell targeting Russell Group entry",
            "Growing interest in medicine preparation targeting Nottingham and Leicester medical schools; the University of Northampton's growth has raised local academic aspirations over the past decade",
        ],
    },
]
