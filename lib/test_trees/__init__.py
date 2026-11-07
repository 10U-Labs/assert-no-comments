from __future__ import annotations

SOURCE = "src/counting.py"
COMPONENT = "src/App.tsx"
NATIVE = "src/native/counting.cpp"
HEADER = "src/native/counting.h"
EXTENSION = "src/extension/counting.c"
SCRIPT = "src/build.sh"
DESIGN = "src/rtl/counter.sv"
LEGACY = "src/rtl/legacy.v"
WORKFLOW = ".github/workflows/release.yml"
CONFIG = "etc/config.yml"
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
