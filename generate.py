import json
import sys
import os
from jinja2 import Environment, FileSystemLoader
import glob

# -------- PDF SUPPORT --------
try:
    from playwright.sync_api import sync_playwright
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False
    print("⚠️  Playwright not installed. PDF output disabled.")
    print("   Run: pip install playwright && playwright install chromium")

AVAILABLE_TEMPLATES = ["ivory", "paule"]  # add more template names here as you create them
DEFAULT_TEMPLATE    = "ivory"

args      = sys.argv[1:]
langs     = ["en", "pt"] if not args or args[0] == "all" else [args[0]]
templates = AVAILABLE_TEMPLATES if len(args) > 1 and args[1] == "all" else [args[1] if len(args) > 1 else DEFAULT_TEMPLATE]

invalid = [t for t in templates if t not in AVAILABLE_TEMPLATES]
if invalid:
    print(f"Template(s) not found: {', '.join(invalid)}. Available: {', '.join(AVAILABLE_TEMPLATES)}")
    sys.exit(1)

# -------- LOAD DATA --------
data_files = glob.glob("data/*.json")
if not data_files:
    print("No data files found in the 'data' folder.")
    sys.exit(1)

def generate_pdf(html_path: str, pdf_path: str):
    """Render an HTML file to PDF using a headless Chromium browser."""
    abs_html_path = os.path.abspath(html_path)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file:///{abs_html_path}", wait_until="networkidle")
        page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )
        browser.close()

for input_file in data_files:
    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)

    perfil = data
    default_labels = {
        "pt": {
            "skills": "Competências",
            "experience": "Experiência Profissional",
            "education": "Formação Acadêmica",
            "projects": "Projetos",
            "certifications": "Formação Complementar",
            "publications": "Publicações",
        },
        "en": {
            "skills": "Skills",
            "experience": "Professional Experience",
            "education": "Education",
            "projects": "Projects",
            "certifications": "Additional Training",
            "publications": "Publications",
        },
    }

    all_labels = data.get("labels", default_labels)

    env = Environment(loader=FileSystemLoader("templates"))

    # Always generate for all templates
    templates = AVAILABLE_TEMPLATES

    for template_name in templates:
        template = env.get_template(f"{template_name}.html")

        for LANG in langs:
            labels = all_labels[LANG]

            # -------- PROCESS CONTACT LINE --------
            contact = perfil.get("contact", {
                "linkedin": "",
                "phone": "",
                "website": "",
                "email": "",
                "github": ""
            })
            contact_line = f"{contact['linkedin']} | {contact['phone']} | {contact['website']} | {contact['email']} | {contact['github']}"

            # -------- PREPARE EXPERIENCE --------
            experience = []
            for exp in perfil.get("experience", []):
                experience.append({
                    "role":     exp["role"][LANG],
                    "company":  exp["company"],
                    "location": exp["location"],
                    "date":     exp["date"][LANG],
                    "bullets":  exp["bullets"][LANG]
                })

            # -------- PREPARE EDUCATION --------
            education = []
            raw_education = perfil.get("education", [])

            # Supports both formats:
            # 1) education: [ ... ]
            # 2) education: { "pt": [ ... ], "en": [ ... ] }
            if isinstance(raw_education, dict):
                raw_education = raw_education.get(LANG, [])

            for edu in raw_education:
                if not isinstance(edu, dict):
                    continue

                degree_value = edu.get("degree", "")
                if isinstance(degree_value, dict):
                    degree_value = degree_value.get(LANG, "")
                elif not isinstance(degree_value, str):
                    degree_value = str(degree_value)

                date_value = edu.get("date", edu.get("expected", ""))
                if isinstance(date_value, dict):
                    date_value = date_value.get(LANG, "")
                elif not isinstance(date_value, str):
                    date_value = str(date_value)

                details_value = edu.get("details", [])
                if isinstance(details_value, dict):
                    details_value = details_value.get(LANG, [])
                elif isinstance(details_value, str):
                    details_value = [details_value] if details_value else []
                elif not isinstance(details_value, list):
                    details_value = []

                education.append({
                    "degree": degree_value,
                    "institution": edu.get("institution", ""),
                    "location": edu.get("location", ""),
                    "date": date_value,
                    "details": details_value
                })

                
            # -------- PREPARE CERTIFICATIONS --------
            certifications = perfil.get("certifications", {}).get(LANG, [])

            # -------- PREPARE PUBLICATIONS --------
            publications = []
            raw_publications = perfil.get("publications", [])
            
            # Supports both formats:
            # 1) publications: [ ... ]
            # 2) publications: { "pt": [ ... ], "en": [ ... ] }
            if isinstance(raw_publications, dict):
                raw_publications = raw_publications.get(LANG, [])
            
            for pub in raw_publications:
                if not isinstance(pub, dict):
                    continue
            
                title_value = pub.get("title", "")
                if isinstance(title_value, dict):
                    title_value = title_value.get(LANG, "")
                elif not isinstance(title_value, str):
                    title_value = str(title_value)
            
                details_value = pub.get("details", [])
                if isinstance(details_value, dict):
                    details_value = details_value.get(LANG, [])
                elif isinstance(details_value, str):
                    details_value = [details_value] if details_value else []
                elif not isinstance(details_value, list):
                    details_value = []

                # Fallback when "details" is missing or empty: use "description"
                if not details_value:
                    description_value = pub.get("description", "")
                    if isinstance(description_value, dict):
                        description_value = description_value.get(LANG, "")
                    if isinstance(description_value, str) and description_value.strip():
                        parts = [p.strip() for p in description_value.split(". ") if p.strip()]
                        details_value = [p if p.endswith(".") else p + "." for p in parts]

                venue_value = pub.get("venue", "")
                if isinstance(venue_value, dict):
                    venue_value = venue_value.get(LANG, "")
                if not isinstance(venue_value, str):
                    venue_value = str(venue_value)

                doi_value = pub.get("doi", "")
                if isinstance(doi_value, str) and doi_value.strip():
                    details_value.append(f"DOI: {doi_value.strip()}.")
                            
                publications.append({
                    "title": title_value,
                    "venue": venue_value.strip(),
                    "date": pub.get("date", ""),
                    "details": details_value
                })

            # -------- PREPARE SKILLS --------
            skills = perfil["skills"]
            processed_skills = []
            for skill in skills:
                if "items" not in skill:
                    skill["items"] = skill.get(f"items_{LANG}", [])
                processed_skills.append(skill)

            # -------- PREPARE PROJECTS --------
            raw_projects = perfil.get("projects", [])
            if isinstance(raw_projects, dict):
                raw_projects = raw_projects.get(LANG, [])
            elif not isinstance(raw_projects, list):
                raw_projects = []

            projects = []
            for project in raw_projects:
                if isinstance(project, str):
                    projects.append(project)
                    continue

                if isinstance(project, dict):
                    name = str(project.get("name", "")).strip()
                    subtitle = str(project.get("subtitle", "")).strip()
                    description = str(project.get("description", "")).strip()

                    parts = [p for p in [name, subtitle, description] if p]
                    if parts:
                        projects.append(" | ".join(parts))
                    continue

                projects.append(str(project))

            # -------- RENDER --------
            try:
                html = template.render(
                    lang=LANG,
                    nome=perfil["nome"],
                    location=perfil["location"][LANG],
                    headline=perfil["headline"][LANG],
                    contact=contact,
                    contact_line=contact_line,
                    skills=sorted(processed_skills, key=lambda x: x["priority"]),
                    experience=experience,
                    projects=projects,
                    education=education,
                    certifications=certifications,
                    publications=publications,
                    labels=labels
                )
            except Exception as e:
                print("Error during rendering:", e)
                print("Debugging skills data:", sorted(perfil["skills"], key=lambda x: x["priority"]))
                raise

            # -------- SAVE OUTPUT --------
            job_name = os.path.splitext(os.path.basename(input_file))[0]
            output_dir = os.path.join("output", job_name, template_name)
            os.makedirs(output_dir, exist_ok=True)

            # HTML
            out_path_html = os.path.join(output_dir, f"cv_{LANG}.html")
            with open(out_path_html, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"CV gerado:  {out_path_html}")

            # PDF
            if PDF_ENABLED:
                out_path_pdf = os.path.join(output_dir, f"cv_{LANG}.pdf")
                try:
                    generate_pdf(out_path_html, out_path_pdf)
                    print(f"PDF gerado: {out_path_pdf}")
                except Exception as e:
                    print(f"⚠️  Erro ao gerar PDF ({out_path_pdf}): {e}")