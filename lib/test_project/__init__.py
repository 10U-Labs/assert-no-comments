from __future__ import annotations

SOURCE = "src/counting.py"
COMPONENT = "src/App.tsx"
WORKFLOW = ".github/workflows/release.yml"
VENDORED = "src/www/spa/vendor/leaflet.js"
NOTES = "src/notes.md"

CLEAN_PROJECT = {
    SOURCE: "project/clean_python",
    WORKFLOW: "project/clean_workflow",
    VENDORED: "project/vendored_javascript",
    NOTES: "project/prose",
}

PROJECT = {**CLEAN_PROJECT, SOURCE: "project/commented_python"}

EXCLUDE_VENDORED = "src/www/spa/vendor/*"

FULL_RUN = ["src", ".github/workflows", "--exclude", EXCLUDE_VENDORED]
