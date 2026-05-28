---
tags: [bug-fix]
---

# Anchor link blue color leak

**`.logo` was an `<a>` tag inheriting the browser default blue. Style cascade missed it.**

The brand logo at the top-left of the landing page is an `<a>` tag
(it links to `#`). Original CSS only set `color: var(--text)` on `.logo`
without specifying the `:link / :visited / :hover / :active` pseudo-
classes.

Browsers apply default `<a>` colors (blue, then purple after visit)
*via these pseudo-classes*, which beat the bare element selector.
Result: the logo turned blue after the user clicked it once. Looked
broken.

**Fix:** explicit cover of all states:
```css
.logo:link, .logo:visited, .logo:hover, .logo:active {
  color: var(--text);
  text-decoration: none;
}
```

**Lesson:** if you're styling `<a>` and color matters, set every
pseudo-class explicitly.

## Related
- [[UI v3 — Sirnik editorial final]]
