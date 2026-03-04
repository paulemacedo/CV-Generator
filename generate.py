import json
import sys
import os
from jinja2 import Environment, FileSystemLoader
import glob

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

for input_file in data_files:
    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)

    perfil = data
    all_labels = data["labels"]

    # Ensure the environment is defined before use
    env = Environment(loader=FileSystemLoader("templates"))

    # Always generate for all templates
    templates = AVAILABLE_TEMPLATES

    for template_name in templates:
        template = env.get_template(f"{template_name}.html")

        for LANG in langs:
            labels = all_labels[LANG]

            # -------- PROCESS CONTACT LINE --------
            contact = perfil["contact"]
            contact_line = f"{contact['linkedin']} | {contact['phone']} | {contact['website']} | {contact['email']} | {contact['github']}"

            # -------- PREPARE EXPERIENCE --------
            experience = []
            for exp in perfil["experience"]:
                experience.append({
                    "role":     exp["role"][LANG],
                    "company":  exp["company"],
                    "location": exp["location"],
                    "date":     exp["date"][LANG],
                    "bullets":  exp["bullets"][LANG]
                })

            # -------- PREPARE EDUCATION --------
            education = []
            if "education" in perfil:
                for edu in perfil["education"]:
                    education.append({
                        "degree": edu["degree"][LANG],
                        "institution": edu["institution"],
                        "location": edu["location"],
                        "date": edu["date"][LANG],
                        "details": edu.get("details", {}).get(LANG, [])
                    })

            # -------- PREPARE CERTIFICATIONS --------
            certifications = perfil.get("certifications", {}).get(LANG, [])

            # -------- PREPARE PUBLICATIONS --------
            publications = []
            if "publications" in perfil:
                for pub in perfil["publications"]:
                    publications.append({
                        "title": pub["title"][LANG],
                        "date": pub["date"],
                        "details": pub.get("details", {}).get(LANG, [])
                    })

            # -------- PREPARE SKILLS --------
            skills = perfil["skills"]
            # Preprocess skills to ensure consistent 'items' key
            processed_skills = []
            for skill in skills:
                if "items" not in skill:
                    skill["items"] = skill.get(f"items_{LANG}", [])
                processed_skills.append(skill)

            # -------- RENDER --------
            try:
                html = template.render(
                    lang=LANG,
                    nome=perfil["nome"],
                    location=perfil["location"][LANG],
                    headline=perfil["headline"][LANG],
                    contact=contact,  # Pass the contact dictionary
                    contact_line=contact_line,
                    skills=sorted(processed_skills, key=lambda x: x["priority"]),
                    experience=experience,
                    projects=perfil["projects"][LANG],
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
            job_name = os.path.splitext(os.path.basename(input_file))[0]  # Extract job name from input file
            output_dir = os.path.join("output", job_name, template_name)
            os.makedirs(output_dir, exist_ok=True)  # Create directories if they don't exist

            out_path_html = os.path.join(output_dir, f"cv_{LANG}.html")
            with open(out_path_html, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"CV gerado: {out_path_html}")