from __future__ import annotations

# =============================================================================
# Module   : generate.py
# Project  : CV Generator
# Author   : Paule Macedo
# Contact  : Paulemacedo@proton.me
# Created  : 2024-03-03
# Usage    : Generate HTML/PDF CVs from local JSON files
# Notice   : Handle personal data with consent and in compliance with the law
# =============================================================================

import json
import sys
import unicodedata
import re
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
HTML_OUTPUT_DIR = OUTPUT_DIR / "html"

LANGUAGE_CODE_MAP = {
    "pt": "PT-BR",
    "en": "EN-US",
}


def parse_cli_arguments(arguments: list[str]) -> tuple[list[str], list[str], bool]:
    explicit_language_request = bool(arguments) and arguments[0] != "all"
    requested_languages = AVAILABLE_LANGUAGES if not arguments or arguments[0] == "all" else [arguments[0]]

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

    invalid_languages = [language for language in requested_languages if language not in AVAILABLE_LANGUAGES]
    if invalid_languages:
        print(
            f"Language(s) not found: {', '.join(invalid_languages)}. "
            f"Available: {', '.join(AVAILABLE_LANGUAGES)}"
        )
        sys.exit(1)

    return requested_languages, selected_templates, explicit_language_request


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


def slugify_filename_part(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", ascii_value).strip("-")
    return re.sub(r"-+", "-", cleaned)


def format_area_name(raw_stem: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", " ", raw_stem).strip()
    if not normalized:
        return "Area"

    tokens = normalized.split()
    formatted_tokens = [token if token.isupper() else token.capitalize() for token in tokens]
    return "-".join(formatted_tokens)


def build_output_basename(profile: dict[str, Any], profile_path: Path, language: str) -> str:
    localized_name = localize_text(profile.get("name", profile.get("nome", "")), language)
    name_part = slugify_filename_part(localized_name) or "Sem-Nome"
    area_part = slugify_filename_part(format_area_name(profile_path.stem)) or "Area"
    language_part = LANGUAGE_CODE_MAP.get(language, language.upper())
    return f"CV-{name_part}-{area_part}-{language_part}"


def normalize_text_list(value: Any, language: str) -> list[str]:
    if isinstance(value, dict):
        value = value.get(language, [])

    if isinstance(value, str):
        return [value] if value else []

    if not isinstance(value, list):
        return []

    normalized_items: list[str] = []
    for item in value:
        if isinstance(item, dict):
            normalized_item = normalize_language_value(item, language)
        else:
            normalized_item = str(item)

        if normalized_item.strip():
            normalized_items.append(normalized_item)

    return normalized_items


def localize_text(value: Any, language: str) -> str:
    if isinstance(value, dict):
        if language in value:
            return localize_text(value[language], language)

        for nested_value in value.values():
            localized_value = localize_text(nested_value, language)
            if localized_value:
                return localized_value

        return ""

    if isinstance(value, list):
        items = [localize_text(item, language) for item in value]
        return " ".join(item for item in items if item).strip()

    if value is None:
        return ""

    return str(value).strip()


def localize_map(value: Any, language: str) -> dict[str, str]:
    if isinstance(value, dict) and ("pt" in value or "en" in value):
        return {
            "pt": localize_text(value.get("pt", ""), "pt"),
            "en": localize_text(value.get("en", ""), "en"),
        }

    localized_value = localize_text(value, language)
    return {"pt": localized_value, "en": localized_value}


def has_meaningful_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(has_meaningful_content(item) for item in value)
    if isinstance(value, dict):
        return any(has_meaningful_content(item) for item in value.values())
    return True


def detect_profile_languages(profile: dict[str, Any]) -> list[str]:
    detected_languages: set[str] = set()

    meta = profile.get("_meta", {})
    if isinstance(meta, dict):
        raw_meta_languages = meta.get("languages", meta.get("language"))
        if isinstance(raw_meta_languages, str):
            raw_meta_languages = [raw_meta_languages]
        if isinstance(raw_meta_languages, list):
            for language_value in raw_meta_languages:
                normalized_language = str(language_value).strip().lower()
                if normalized_language in AVAILABLE_LANGUAGES:
                    detected_languages.add(normalized_language)

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for language in AVAILABLE_LANGUAGES:
                localized_value = value.get(language)
                if has_meaningful_content(localized_value):
                    detected_languages.add(language)

            for nested_value in value.values():
                walk(nested_value)
            return

        if isinstance(value, list):
            for nested_value in value:
                walk(nested_value)

    walk(profile)
    return [language for language in AVAILABLE_LANGUAGES if language in detected_languages]


def resolve_profile_languages(
    profile: dict[str, Any],
    profile_path: Path,
    requested_languages: list[str],
    explicit_language_request: bool,
) -> list[str]:
    detected_languages = detect_profile_languages(profile)

    if not detected_languages:
        if explicit_language_request:
            detected_languages = list(requested_languages)
        else:
            detected_languages = list(AVAILABLE_LANGUAGES)
        print(
            f"⚠️  {profile_path.name}: no explicit language markers found; "
            f"using {', '.join(detected_languages)}."
        )

    if explicit_language_request:
        ignored_languages = [language for language in requested_languages if language not in detected_languages]
        for ignored_language in ignored_languages:
            print(
                f"⚠️  {profile_path.name}: requested language '{ignored_language}' "
                "was ignored (not detected in this profile)."
            )
        return [language for language in requested_languages if language in detected_languages]

    return detected_languages


def get_labels_for_language(labels_by_language: Any, language: str) -> dict[str, str]:
    if isinstance(labels_by_language, dict):
        localized_labels = labels_by_language.get(language)
        if isinstance(localized_labels, dict):
            return {str(key): str(value) for key, value in localized_labels.items()}

    return dict(DEFAULT_LABELS[language])


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
                "role": localize_map(experience.get("role", ""), language),
                "company": str(experience.get("company", "")),
                "location": str(experience.get("location", "")),
                "date": localize_map(experience.get("date", ""), language),
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
                "degree": localize_map(education.get("degree", ""), language),
                "institution": str(education.get("institution", "")),
                "location": str(education.get("location", "")),
                "date": localize_map(education.get("date", education.get("expected", "")), language),
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
        description_text = normalize_language_value(publication.get("description", ""), language)

        if not details:
            details = split_description_into_bullets(description_text)

        venue = normalize_language_value(publication.get("venue", ""), language).strip()
        doi = str(publication.get("doi", "")).strip()
        doi_url = str(publication.get("doi_url", "")).strip()
        if not doi_url and doi:
            doi_url = f"https://doi.org/{doi}"

        # If details were generated from description, keep only one representation.
        has_explicit_details = bool(normalize_text_list(publication.get("details", []), language))
        localized_description = localize_map(publication.get("description", ""), language)
        if not has_explicit_details and details:
            localized_description = {"pt": "", "en": ""}

        publication_items.append(
            {
                "title": localize_map(publication.get("title", ""), language),
                "venue": venue,
                "date": localize_map(publication.get("date", ""), language),
                "description": localized_description,
                "details": details,
                "doi": doi,
                "doi_url": doi_url,
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
        if isinstance(normalized_skill.get("label"), dict):
            normalized_skill["label"] = localize_map(normalized_skill["label"], language)
        skill_items.append(normalized_skill)

    return skill_items


def prepare_projects(profile: dict[str, Any], language: str) -> list[dict[str, Any]]:
    raw_projects = profile.get("projects", [])
    if isinstance(raw_projects, dict):
        raw_projects = raw_projects.get(language, [])
    elif not isinstance(raw_projects, list):
        raw_projects = []

    project_items: list[dict[str, Any]] = []
    for project in raw_projects:
        if isinstance(project, str):
            project_items.append({"name": localize_map(project, language)})
            continue

        if isinstance(project, dict):
            # subtitle pode ser dict de dicts (área -> {pt, en})
            subtitle = project.get("subtitle", "")
            if isinstance(subtitle, dict):
                # Se for dict de áreas, tenta pegar a área "ti" ou a primeira disponível
                area_key = None
                if "ti" in subtitle:
                    area_key = "ti"
                elif len(subtitle) > 0:
                    area_key = next(iter(subtitle))
                if area_key and isinstance(subtitle[area_key], dict):
                    subtitle_value = localize_map(subtitle[area_key], language)
                elif area_key:
                    subtitle_value = localize_map(subtitle[area_key], language)
                else:
                    subtitle_value = {"pt": "", "en": ""}
            else:
                subtitle_value = localize_map(subtitle, language)

            project_items.append(
                {
                    "name": localize_map(project.get("name", ""), language),
                    "subtitle": subtitle_value,
                    "description": localize_map(project.get("description", ""), language),
                    "github": str(project.get("github", "")).strip(),
                    "areas": [str(area) for area in project.get("areas", []) if str(area).strip()],
                }
            )
            continue

        project_items.append({"name": localize_map(project, language)})

    return project_items


def prepare_certifications(profile: dict[str, Any], language: str) -> list[Any]:
    raw_certifications = profile.get("certifications", [])

    if isinstance(raw_certifications, dict):
        selected_items = raw_certifications.get(language, [])
        if isinstance(selected_items, list):
            return [str(item) for item in selected_items if str(item).strip()]
        if isinstance(selected_items, str) and selected_items.strip():
            return [selected_items]
        return []

    certifications: list[Any] = []
    for certification in raw_certifications:
        if not isinstance(certification, dict):
            certification_text = str(certification).strip()
            if certification_text:
                certifications.append(certification_text)
            continue

        certifications.append(
            {
                "name": localize_map(certification.get("name", ""), language),
                "issuer": str(certification.get("issuer", "")),
                "date": localize_map(certification.get("date", ""), language),
                "details": normalize_text_list(certification.get("details", []), language),
                "hours": certification.get("hours"),
                "score": certification.get("score"),
                "url": str(certification.get("url", "")).strip(),
            }
        )

    return certifications


def render_profile(
    template: Any,
    profile: dict[str, Any],
    language: str,
    labels: dict[str, str],
) -> str:
    contact = prepare_contact(profile)
    display_name = localize_text(profile.get("name", profile.get("nome", "")), language)
    return template.render(
        lang=language,
        name=profile.get("name", profile.get("nome", {})),
        nome=display_name,
        location=profile.get("location", {}),
        location_text=localize_text(profile.get("location", {}), language),
        headline=profile.get("headline", {}),
        headline_text=localize_text(profile.get("headline", {}), language),
        summary=profile.get("summary", {}),
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
        certifications=prepare_certifications(profile, language),
        publications=prepare_publications(profile, language),
        labels=labels,
        _meta=profile.get("_meta", {}),
    )


def generate_cv_files(
    profile_path: Path,
    requested_languages: list[str],
    template_names: list[str],
    explicit_language_request: bool,
) -> None:
    profile = load_json_file(profile_path)
    labels_by_language = profile.get("labels", DEFAULT_LABELS)
    environment = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    filename = profile_path.stem.lower()
    prefix = filename.split("-")[0]
    profile_languages = resolve_profile_languages(
        profile,
        profile_path,
        requested_languages,
        explicit_language_request,
    )

    if not profile_languages:
        print(f"⚠️  {profile_path.name}: no languages to generate after filtering.")
        return

    templates_to_use = ["Master"] if prefix == "master" else template_names
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for template_name in templates_to_use:
        template = environment.get_template(f"{template_name}.html")

        for language in profile_languages:
            labels = get_labels_for_language(labels_by_language, language)
            html = render_profile(template, profile, language, labels)
            output_basename = build_output_basename(profile, profile_path, language)
            if len(templates_to_use) > 1:
                output_basename = f"{output_basename}-{template_name.title()}"

            html_path = HTML_OUTPUT_DIR / f"{output_basename}.html"
            html_path.write_text(html, encoding="utf-8")
            print(f"CV gerado:  {html_path.relative_to(WORKSPACE_ROOT)}")

            if PDF_ENABLED:
                pdf_path = OUTPUT_DIR / f"{output_basename}.pdf"
                try:
                    generate_pdf(html_path, pdf_path)
                    print(f"PDF gerado: {pdf_path.relative_to(WORKSPACE_ROOT)}")
                except Exception as exception:
                    print(f"⚠️  Erro ao gerar PDF ({pdf_path.relative_to(WORKSPACE_ROOT)}): {exception}")


def main() -> None:
    requested_languages, template_names, explicit_language_request = parse_cli_arguments(sys.argv[1:])
    data_files = sorted(DATA_DIR.glob("*.json"))

    if not data_files:
        print("No data files found in the 'data' folder.")
        sys.exit(1)

    for profile_path in data_files:
        generate_cv_files(profile_path, requested_languages, template_names, explicit_language_request)


if __name__ == "__main__":
    main()