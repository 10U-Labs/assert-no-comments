# assert-no-comments

Assert that nothing in a tree carries a comment or a docstring.

## Why

Prose beside code is never checked. The compiler does not read it, the
tests do not run it, and no linter asks whether it is still true, so it
stops being true and nothing says when. The reader who believes it then
works from a program that no longer exists, which is worse than having
read nothing at all.

A rename is where the cost shows up first. Change one identifier and
every sentence naming it is now wrong, in files the change never
touched, and the diff gives no way to find them.

So this tool takes the other position: a name, a signature and the shape
of a function are the whole of what a reader gets. When that is not
enough to say what a thing holds or does, the thing is named or shaped
wrong rather than under-explained. The reasoning still gets written
down, in the commit message and the issue, each of which is dated and
attached to a change instead of sitting beside a line claiming to
describe it forever.

## Installation

```bash
pip install assert-no-comments
```

## Usage

```bash
# Every tree this repository publishes
assert-no-comments .github/workflows etc lib scripts src test

# The same, leaving out code somebody else wrote
assert-no-comments .github/workflows etc lib scripts src test \
  --exclude 'src/www/spa/vendor/*'
```

### Options

| Option | Effect |
| --- | --- |
| `--exclude PATTERNS` | Comma-separated globs to leave out. |
| `--annotate` | Print each finding as a GitHub Actions `::error` annotation. |
| `--quiet` | Print nothing; report through the exit code. |
| `--count` | Print only how many findings there were. |
| `--verbose` | Print the files read, the findings and a summary. |
| `--fail-fast` | Stop at the first finding. |
| `--warn-only` | Always exit 0. |

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Nothing carries a comment |
| 1 | Something carries a comment |
| 2 | A tree was missing, unreadable, or would not parse |

## What counts as a comment

| Read as | Suffixes | Reported |
| --- | --- | --- |
| Python | `.py` | `#`, and any module, class or function docstring |
| YAML | `.yml`, `.yaml` | `#` |
| OpenTofu | `.tf`, `.tfvars`, `.hcl` | `#`, `//`, and `/* */` blocks |
| JavaScript | `.js`, `.jsx`, `.mjs`, `.cjs` | `//`, and `/* */` blocks |

A file whose suffix names none of those is left alone, so a `.md` file
is never read: prose is the content of a markdown file rather than a
gloss on a line of code. `.terraform.lock.hcl` is left alone too,
because OpenTofu writes its header and nobody can delete it.

A docstring counts as a comment. It is the same prose in the same place,
and the fact that a language keeps it in `__doc__` does not make it any
more likely to still be true.

Each reader knows the difference between a marker and a character that
merely looks like one. A `#` inside a Python string, a YAML quoted
scalar or a block scalar is content. A `//` inside a JavaScript string,
template literal or regular expression is content, and a `/` after a
name is division rather than the start of a pattern.

Python is read with `tokenize` and `ast`, and YAML with the `yaml`
scanner, so a file that will not parse is an error rather than a file
with nothing in it. The marker languages are read character by character
and never fail: an unclosed string swallows the rest of the file, and an
unclosed block comment is still reported where it opened.

## What is walked

A directory argument is read recursively. Hidden directories are read,
because `.github/workflows` is one of the trees most worth checking.
`.git`, `__pycache__` and `node_modules` are skipped, and everything
else you want left out goes in `--exclude`.

The usual thing to exclude is code somebody else wrote:

```bash
assert-no-comments src --exclude 'src/www/spa/vendor/*'
```

Nobody here can answer for a vendored library, and a finding against one
is answerable by nobody, so it is not worth reporting.

## GitHub Actions

```yaml
- name: Assert nothing this repository publishes carries a comment
  uses: 10U-Labs/assert-no-comments@latest
  with:
    exclude: src/www/spa/vendor/*
    trees: .github/workflows etc lib scripts src test
```

`annotate` defaults to true there, so each finding lands on the line it
names in the diff.

## License

Apache-2.0
