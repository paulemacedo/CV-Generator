# =============================================================================
# Module   : generate.py
# Project  : CV Generator
# Author   : Paule Macedo
# Contact  : Paulemacedo@proton.me
# Created  : 2024-03-03
# Usage    : Generate HTML/PDF CVs from local JSON files
# Notice   : Handle personal data with consent and in compliance with the law
# =============================================================================

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

AVAILABLE_TEMPLATES = ["ivory", "paule"]
DEFAULT_TEMPLATE = "paule"
AVAILABLE_LANGUAGES = ["en", "pt"]
DEFAULT_LABELS = {
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
DEFAULT_CONTACT = {
    "linkedin": "",
    "phone": "",
    "website": "",
    "email": "",
    "github": "",
}

WORKSPACE_ROOT = Path(__file__).resolve().parent
DATA_DIR = WORKSPACE_ROOT / "data"
TEMPLATES_DIR = WORKSPACE_ROOT / "templates"
OUTPUT_DIR = WORKSPACE_ROOT / "output"


try:
    from playwright.sync_api import sync_playwright

    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False
    print("⚠️  Playwright not installed. PDF output disabled.")
    print("   Run: pip install playwright && playwright install chromium")


def generate_pdf(html_path: Path, pdf_path: Path) -> None:
    """Render an HTML file to PDF using a headless Chromium browser."""
    abs_html_path = html_path.resolve()
    with sync_playwright() as browser_context:
        browser = browser_context.chromium.launch()
        page = browser.new_page()
        page.goto(f"file:///{abs_html_path.as_posix()}", wait_until="networkidle")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()


def load_json_file(file_path: Path) -> dict[str, Any]:
    with file_path.open(encoding="utf-8") as file_handle:
        return json.load(file_handle)


def normalize_language_value(value: Any, language: str) -> str:
    if isinstance(value, dict):
        return str(value.get(language, ""))
    if value is None:
        return ""
    return str(value)


def normalize_text_list(value: Any, language: str) -> list[str]:
    if isinstance(value, dict):
        value = value.get(language, [])

    if isinstance(value, str):
        return [value] if value else []

    if not isinstance(value, list):
        return []

    return [str(item) for item in value if str(item).strip()]


def parse_cli_arguments(arguments: list[str]) -> tuple[list[str], list[str]]:
    languages = AVAILABLE_LANGUAGES if not arguments or arguments[0] == "all" else [arguments[0]]

    if len(arguments) > 1:
        selected_templates = AVAILABLE_TEMPLATES if arguments[1] == "all" else [arguments[1]]
    else:
        selected_templates = [DEFAULT_TEMPLATE]

    invalid_templates = [template_name for template_name in selected_templates if template_name not in AVAILABLE_TEMPLATES]
    if invalid_templates:
        print(
            f"Template(s) not found: {', '.join(invalid_templates)}. "
            f"Available: {', '.join(AVAILABLE_TEMPLATES)}"
        )
        sys.exit(1)

    invalid_languages = [language for language in languages if language not in AVAILABLE_LANGUAGES]
    if invalid_languages:
        print(
            f"Language(s) not found: {', '.join(invalid_languages)}. "
            f"Available: {', '.join(AVAILABLE_LANGUAGES)}"
        )
        sys.exit(1)

    return languages, selected_templates


def prepare_contact(profile: dict[str, Any]) -> dict[str, str]:
    contact = dict(DEFAULT_CONTACT)
    contact.update(profile.get("contact", {}))
    return {key: str(value) for key, value in contact.items()}


def prepare_experience(profile: dict[str, Any], language: str) -> list[dict[str, Any]]:
    experience_items: list[dict[str, Any]] = []
    for experience in profile.get("experience", []):
        if not isinstance(experience, dict):
            continue

        experience_items.append(
            {
                "role": normalize_language_value(experience.get("role", ""), language),
                "company": str(experience.get("company", "")),
                "location": str(experience.get("location", "")),
                "date": normalize_language_value(experience.get("date", ""), language),
                "bullets": normalize_text_list(experience.get("bullets", []), language),
            }
        )

    return experience_items


def prepare_education(profile: dict[str, Any], language: str) -> list[dict[str, Any]]:
    raw_education = profile.get("education", [])
    if isinstance(raw_education, dict):
        raw_education = raw_education.get(language, [])

    education_items: list[dict[str, Any]] = []
    for education in raw_education:
        if not isinstance(education, dict):
            continue

        education_items.append(
            {
                "degree": normalize_language_value(education.get("degree", ""), language),
                "institution": str(education.get("institution", "")),
                "location": str(education.get("location", "")),
                "date": normalize_language_value(education.get("date", education.get("expected", "")), language),
                "details": normalize_text_list(education.get("details", []), language),
            }
        )

    return education_items


def split_description_into_bullets(description: str) -> list[str]:
    description = description.strip()
    if not description:
        return []

    segments = [segment.strip() for segment in description.split(". ") if segment.strip()]
    return [segment if segment.endswith(".") else f"{segment}." for segment in segments]


def prepare_publications(profile: dict[str, Any], language: str) -> list[dict[str, Any]]:
    raw_publications = profile.get("publications", [])
    if isinstance(raw_publications, dict):
        raw_publications = raw_publications.get(language, [])

    publication_items: list[dict[str, Any]] = []
    for publication in raw_publications:
        if not isinstance(publication, dict):
            continue

        title = normalize_language_value(publication.get("title", ""), language)
        details = normalize_text_list(publication.get("details", []), language)

        if not details:
            description = normalize_language_value(publication.get("description", ""), language)
            details = split_description_into_bullets(description)

        venue = normalize_language_value(publication.get("venue", ""), language).strip()
        doi = str(publication.get("doi", "")).strip()
        if doi:
            details.append(f"DOI: {doi}.")

        publication_items.append(
            {
                "title": title,
                "venue": venue,
                "date": str(publication.get("date", "")),
                "details": details,
            }
        )

    return publication_items


def prepare_skills(profile: dict[str, Any], language: str) -> list[dict[str, Any]]:
    skill_items: list[dict[str, Any]] = []
    for skill in profile.get("skills", []):
        if not isinstance(skill, dict):
            continue

        normalized_skill = dict(skill)
        if "items" not in normalized_skill:
            normalized_skill["items"] = normalized_skill.get(f"items_{language}", [])
        skill_items.append(normalized_skill)

    return skill_items


def prepare_projects(profile: dict[str, Any], language: str) -> list[str]:
    raw_projects = profile.get("projects", [])
    if isinstance(raw_projects, dict):
        raw_projects = raw_projects.get(language, [])
    elif not isinstance(raw_projects, list):
        raw_projects = []

    project_items: list[str] = []
    for project in raw_projects:
        if isinstance(project, str):
            project_items.append(project)
            continue

        if isinstance(project, dict):
            name = str(project.get("name", "")).strip()
            subtitle = str(project.get("subtitle", "")).strip()
            description = str(project.get("description", "")).strip()
            parts = [part for part in [name, subtitle, description] if part]
            if parts:
                project_items.append(" | ".join(parts))
            continue

        project_items.append(str(project))

    return project_items


def render_profile(
    template: Any,
    profile: dict[str, Any],
    language: str,
    labels: dict[str, str],
) -> str:
    contact = prepare_contact(profile)
    return template.render(
        lang=language,
        nome=profile.get("nome", ""),
        location=normalize_language_value(profile.get("location", {}), language),
        headline=normalize_language_value(profile.get("headline", {}), language),
        contact=contact,
        contact_line=" | ".join(
            [
                contact["linkedin"],
                contact["phone"],
                contact["website"],
                contact["email"],
                contact["github"],
            ]
        ),
        skills=sorted(prepare_skills(profile, language), key=lambda item: item.get("priority", 0)),
        experience=prepare_experience(profile, language),
        projects=prepare_projects(profile, language),
        education=prepare_education(profile, language),
        certifications=normalize_text_list(profile.get("certifications", []), language),
        publications=prepare_publications(profile, language),
        labels=labels,
    )


def generate_cv_files(profile_path: Path, languages: list[str], template_names: list[str]) -> None:
    profile = load_json_file(profile_path)
    labels_by_language = profile.get("labels", DEFAULT_LABELS)
    environment = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    profile_name = profile_path.stem.lstrip("-_") or profile_path.stem

    for template_name in template_names:
        template = environment.get_template(f"{template_name}.html")

        for language in languages:
            html = render_profile(template, profile, language, labels_by_language[language])

            output_directory = OUTPUT_DIR / profile_name / language / template_name
            output_directory.mkdir(parents=True, exist_ok=True)

            html_path = output_directory / "cv.html"
            html_path.write_text(html, encoding="utf-8")
            print(f"CV gerado:  {html_path.relative_to(WORKSPACE_ROOT)}")

            if PDF_ENABLED:
                pdf_path = output_directory / "cv.pdf"
                try:
                    generate_pdf(html_path, pdf_path)
                    print(f"PDF gerado: {pdf_path.relative_to(WORKSPACE_ROOT)}")
                except Exception as exception:
                    print(f"⚠️  Erro ao gerar PDF ({pdf_path.relative_to(WORKSPACE_ROOT)}): {exception}")


def main() -> None:
    languages, template_names = parse_cli_arguments(sys.argv[1:])
    data_files = sorted(DATA_DIR.glob("*.json"))

    if not data_files:
        print("No data files found in the 'data' folder.")
        sys.exit(1)

    for profile_path in data_files:
        generate_cv_files(profile_path, languages, template_names)


if __name__ == "__main__":
    main()