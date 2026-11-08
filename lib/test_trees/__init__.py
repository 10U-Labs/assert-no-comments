from __future__ import annotations

SOURCE = "src/counting.py"
COMPONENT = "src/App.tsx"
NATIVE = "src/native/counting.cpp"
HEADER = "src/native/counting.h"
EXTENSION = "src/extension/counting.c"
SCRIPT = "src/build.sh"
DESIGN = "src/rtl/counter.sv"
LEGACY = "src/rtl/legacy.v"
PAGE_SCRIPT = "src/www/spa/page.js"
WORKFLOW = ".github/workflows/release.yml"
CONFIG = "etc/config.yml"
VENDORED = "src/www/spa/vendor/leaflet.js"
NOTES = "src/notes.md"

CLEAN_PROJECT = {
    SOURCE: "project/clean_python.py",
    WORKFLOW: "project/clean_workflow.yml",
    VENDORED: "project/vendored_javascript.js",
    NOTES: "project/prose.md",
}

PROJECT = {**CLEAN_PROJECT, SOURCE: "project/commented_python.py"}

EXCLUDE_VENDORED = "src/www/spa/vendor/*"

FULL_RUN = ["src", ".github/workflows", "--exclude", EXCLUDE_VENDORED]
