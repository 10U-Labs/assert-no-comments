from __future__ import annotations

CLEAN_PYTHON = """\
def counted():
    return 1
"""

COMMENTED_PYTHON = """\
def counted():
    return 1  # why
"""

DOCUMENTED_PYTHON = '''\
def counted():
    """What counted does."""
    return 1
'''

BROKEN_PYTHON = """\
def counted(
"""

VENDORED_JAVASCRIPT = """\
// somebody else wrote this
const leaflet = 1;
"""

CLEAN_TSX = """\
const App = () => <div />;

export default App;
"""

COMMENTED_TSX = """\
const App = () => (
  <div>
    {/* why */}
    <Foo />
  </div> // why
);

/* why */
export default App;
"""

CLEAN_WORKFLOW = """\
---
jobs:
  counting: 1
"""

COMMENTED_WORKFLOW = """\
---
jobs:
  # why
  counting: 1
"""

PROSE = """\
# A heading, which is not a comment.
"""

SOURCE = "src/counting.py"
COMPONENT = "src/App.tsx"
WORKFLOW = ".github/workflows/release.yml"
VENDORED = "src/www/spa/vendor/leaflet.js"
NOTES = "src/notes.md"

CLEAN_PROJECT = {
    SOURCE: CLEAN_PYTHON,
    WORKFLOW: CLEAN_WORKFLOW,
    VENDORED: VENDORED_JAVASCRIPT,
    NOTES: PROSE,
}

PROJECT = {**CLEAN_PROJECT, SOURCE: COMMENTED_PYTHON}

EXCLUDE_VENDORED = "src/www/spa/vendor/*"

FULL_RUN = ["src", ".github/workflows", "--exclude", EXCLUDE_VENDORED]
