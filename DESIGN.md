# Design System — Reference

A portable design language extracted from the Memcon landing page (`docs/index.html`)
and the chat UI (`api/ui.html`). Use this doc as the base when building a new app —
swap the copy and the data, keep the system.

The goal of the system: **editorial density without decoration.** Looks dense and
intentional, but every "element" is just typography on a line — no boxes, no
gradients, no shadows, no colored accents. The variety comes from *interactions*
that differ per section, not from visual chrome.

---

## 1. Philosophy

Five rules. Break any of them and the look collapses.

1. **Monochrome only.** Black background, white text, a handful of grays.
   No accent color anywhere — not even on the call-to-action. Confidence in
   typography replaces color.
2. **No bordered cards.** No rounded corners. No drop shadows. No
   bracket-corner decorations. Sections are demarcated by **1px lines** and
   negative space, never by boxes.
3. **Massive display type next to tiny micro-labels.** The contrast is
   between **clamp(2.5rem, 7vw, 6rem)** Inter Tight and **0.66rem** uppercase
   tracking-.16em labels. Mid-sized headings (h3, h4) are rare.
4. **Editorial multi-column grids.** Default to **3 columns** (`1.1fr 1.6fr 1fr`)
   even for things that "want" to be centered. Forces the eye to scan.
5. **Different interaction per section.** Hover-shift on links, accordion on
   step-lists, side-panel reveal on tool walls, OS-tabs on installs, live clock
   in headers. Never reuse the same pattern twice on the same page.

> **"Cluttered but pretty."** Dense information per viewport, but every element
> sits on a clean line. Steal the density from broadsheet newspapers, not
> dashboard apps.

---

## 2. Typography

Three families. Loaded together from Google Fonts.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Inter+Tight:wght@200;300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

### 2.1 Roles

| Family | Role | Weights used | When |
|---|---|---|---|
| **Inter Tight** | Display / headings / brand | 300, 400, 500, 600 | All h1/h2, brand wordmark, big numbers, button labels |
| **Inter** | Body | 400, 500 | All paragraph text, form inputs, default UI |
| **JetBrains Mono** | Code · meta · labels | 400, 500 | Code blocks, MCP signatures, terminal commands, `.mono` label microcopy |

Never use Inter Tight for body text. Never use Inter for the giant hero.
The visual identity comes from the **two-family contrast** (sans body vs
tighter sans display + mono micro-text).

### 2.2 Type Scale (clamp-based, responsive)

```css
/* Display (hero, footer wordmark)     */ font-size: clamp(3.2rem, 10vw, 11rem);  letter-spacing: -.05em;  line-height: .93;
/* Section H2                          */ font-size: clamp(2.2rem, 5.5vw, 4.4rem); letter-spacing: -.035em; line-height: 1.02;
/* Sub-heading H3                      */ font-size: 2rem;                         letter-spacing: -.025em; line-height: 1.05;
/* Stat number                         */ font-size: clamp(2.4rem, 5vw, 3.8rem);   letter-spacing: -.035em; line-height: .95;
/* Brand wordmark (nav)                */ font-size: 2.4rem;                       letter-spacing: -.055em; line-height: .95;
/* Body                                */ font-size: 15px;                         line-height: 1.55;
/* Chat message body                   */ font-size: 1.02rem;                      line-height: 1.7;
/* Code (.mono)                        */ font-size: .85rem;                       line-height: 1.65;
/* Section label (.cap)                */ font-size: .66rem;  letter-spacing: .16em; text-transform: uppercase;
/* Tiny micro-label (.label)           */ font-size: .7rem;   letter-spacing: .01em;
```

### 2.3 Letter Spacing — the most important detail

The whole system reads "tight" because the display sizes use **negative
letter-spacing** while the micro-labels use **wide positive tracking**.

| Element | letter-spacing |
|---|---|
| Hero h1 | `-0.05em` |
| Brand wordmark | `-0.055em` |
| H2 | `-0.035em` |
| H3 | `-0.025em` |
| Body | default (`normal`) |
| Mode hint / kbd | `0.02em` |
| `.cap` labels | `0.16em` |
| `.micro-cap` | `0.14em` |
| Footer bar uppercase | `0.05em` |

> When in doubt, **tighten** big text and **widen** small text.

### 2.4 Two utility classes that appear everywhere

```css
.tight { font-family: 'Inter Tight', sans-serif; letter-spacing: -.025em; }
.mono  { font-family: 'JetBrains Mono', ui-monospace, monospace; }
.cap   { font-family: 'Inter Tight', sans-serif; font-weight: 500;
         font-size: .66rem; color: var(--faint);
         text-transform: uppercase; letter-spacing: .16em; }
```

---

## 3. Color Palette

The system is fundamentally **monochrome**. Every value is a shade of gray.
There is exactly one "color" used (a green pulse on the live indicator) and
one error red — both reserved for system status, never UI accent.

### 3.1 Dark theme (canonical)

```css
:root[data-theme="dark"] {
  --bg:      #0a0a0a;   /* page background — almost-black, never pure #000 */
  --bg-2:    #101010;   /* one step up; for inset terminal cards, hover row */
  --bg-3:    #151515;   /* two steps up; rarely used, e.g. active tool tile */
  --line:    #1a1a1a;   /* hairline divider — barely visible on bg */
  --line-2:  #262626;   /* visible divider — section borders, inputs */
  --line-3:  #3a3a3a;   /* prominent divider — kbd outline, active border */
  --text:    #f4f4f4;   /* primary text */
  --text-2:  #cfcfcf;   /* secondary text — used in body paragraphs */
  --dim:     #8a8a8a;   /* tertiary text — captions, microcopy */
  --faint:   #5a5a5a;   /* quaternary — uppercase labels, prompts */
  --ghost:   #2c2c2c;   /* placeholder-ish — terminal dots, line gutter */
  --live:    #3dd07a;   /* the ONLY hue. Pulse dot on "live" indicators */
  --error:   #e07070;   /* the ONLY warm tone. Error states only */
}
```

### 3.2 Light theme (mirror)

```css
:root[data-theme="light"] {
  --bg:      #fafafa;
  --bg-2:    #f3f3f3;
  --bg-3:    #ececec;
  --line:    #e7e7e7;
  --line-2:  #d6d6d6;
  --line-3:  #b8b8b8;
  --text:    #0a0a0a;
  --text-2:  #2a2a2a;
  --dim:     #5a5a5a;
  --faint:   #8a8a8a;
  --ghost:   #c4c4c4;
  --live:    #2aa75e;
  --error:   #b03030;
}
```

### 3.3 The shade ladder — why nine grays

The variables form a **ladder of contrast**:

```
bg ━━━━ bg-2 ━━━━ bg-3 ━━━━ line ━━━━ line-2 ━━━━ line-3 ━━━━ ghost ━━━━ faint ━━━━ dim ━━━━ text-2 ━━━━ text
backgrounds                            dividers                          text colors
```

Use them in order. If something needs to be "a bit lighter than the page,"
that's `bg-2`. If it needs to be "a barely-visible line," that's `line`.
Don't invent new values — every hex code outside this ladder feels wrong.

### 3.4 Selection + scrollbar — match the system

```css
::selection { background: var(--text); color: var(--bg); }
::-webkit-scrollbar      { width:8px; height:8px; }
::-webkit-scrollbar-track{ background:transparent; }
::-webkit-scrollbar-thumb{ background: var(--line-3); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--dim); }
```

---

## 4. Layout & Spacing

### 4.1 Container

```css
.wrap { max-width: 1480px; margin: 0 auto; padding: 0 2.5rem; }
@media (max-width: 900px) { .wrap { padding: 0 1.5rem; } }
```

For the chat UI's narrower content column: `max-width: 820px`.

### 4.2 The signature 3-column grid

Almost every "row" in the landing page uses this grid. It gives the editorial
broadsheet feel:

```css
grid-template-columns: 1.1fr 1.6fr 1fr;
gap: 2.5rem;
```

The asymmetry (1.1 / 1.6 / 1) is intentional. Equal columns feel like a
dashboard. This feels like a magazine.

### 4.3 Section vertical rhythm

```css
section        { padding: 6.5rem 0; border-top: 1px solid var(--line); }
.quote section { padding: 9rem 0;   border-top: 1px solid var(--line); }
.sec-head      { margin-bottom: 4rem; }
```

Between major sections: **6.5rem** (~100px). Big breathing room — the dense
content inside earns it.

### 4.4 Section-header pattern

A section never starts with a centered heading. It starts with a 2-column
grid: a thin left column (number + cap label) and a wide right column with
the actual h2.

```html
<div class="sec-head">
  <div class="l">
    <div class="num">01</div>
    <div class="cap">The Loop</div>
  </div>
  <h2 class="tight">
    Before it answers, Claude pulls the few notes that match.<br>
    <span class="dim">After a fix, it writes one back.</span> Plain markdown on disk.
  </h2>
</div>
```

```css
.sec-head { display: grid; grid-template-columns: 1.1fr 2.6fr; gap: 2.5rem; }
.sec-head .l { padding-top: .55rem; display: flex; flex-direction: column; gap: .55rem; }
.sec-head h2 { font-family: 'Inter Tight'; font-size: clamp(2.2rem, 5.5vw, 4.4rem);
               font-weight: 500; letter-spacing: -.035em; line-height: 1.02;
               max-width: 18ch; }
.sec-head h2 .dim  { color: var(--dim);    font-weight: 300; }
.sec-head h2 .lite { color: var(--text-2); font-weight: 300; }
```

Mix three weights/colors inside one heading: bold-default (white 500),
`.lite` (light gray 300), `.dim` (mid gray 300). It creates internal rhythm
inside a single headline.

---

## 5. Components

Reusable patterns you'll find in both files.

### 5.1 Brand wordmark + glyph

```html
<a href="#" class="brand"><span class="glyph"></span>Memcon</a>
```

```css
.brand { font-family: 'Inter Tight'; font-weight: 500; font-size: 2.4rem;
         letter-spacing: -.055em; line-height: .95;
         display: inline-flex; align-items: baseline; gap: .45rem;
         color: var(--text); text-decoration: none; }
.brand .glyph { display: inline-block; width: 1.2rem; height: 1.2rem;
                border: 1.5px solid var(--text); border-radius: 50%;
                position: relative; transform: translateY(.18em); }
.brand .glyph::after { content: ""; position: absolute; inset: 25%;
                       background: var(--text); border-radius: 50%; }
```

The glyph is a circle within a circle — abstract, mono. Built with two
divs, no SVG file needed. For a different brand, change `border-radius`
to make it a square or rotate it.

### 5.2 Live indicator with pulse

```html
<span class="live"><span class="pulse"></span>Local · <span id="localTime">00:00:00</span></span>
```

```css
.pulse { width: 7px; height: 7px; border-radius: 50%; background: var(--live);
         box-shadow: 0 0 8px rgba(61, 208, 122, .5); display: inline-block;
         animation: pulseAnim 2s ease-in-out infinite; }
.pulse.off { background: var(--faint); box-shadow: none; animation: none; }
@keyframes pulseAnim { 0%,100% { opacity: 1 } 50% { opacity: .4 } }
```

Pair it with a JS clock (see §6.1). Subtle but it makes the page feel
*alive* in a way no static element can.

### 5.3 Pill button (outlined)

The only "button-shaped" element. Used for primary CTAs and tab pills.

```css
.nav-cta { border: 1px solid var(--text-2); color: var(--text);
           padding: .55rem 1.5rem; border-radius: 999px;
           font-size: .95rem; text-decoration: none;
           transition: background .15s, color .15s; }
.nav-cta:hover { background: var(--text); color: var(--bg); }
```

For a square button: same colors, `border-radius: 0`. Use a square
button inside dock/input contexts, pill button for headers.

### 5.4 "Startbox" — bottom-line link

Replaces card-style entry points everywhere.

```html
<a href="#install"><div class="startbox">
  <span>One-line install</span>
  <span class="arrow">→</span>
</div></a>
```

```css
.startbox { display: flex; align-items: center; gap: .7rem;
            border-bottom: 1px solid var(--text); padding: .45rem 0; }
.startbox span { font-family: 'Inter Tight'; color: var(--text); font-size: 1.05rem; }
.startbox .arrow { margin-left: auto; color: var(--text);
                   font-size: 1.1rem; transition: transform .2s; }
a:hover .startbox .arrow { transform: translateX(4px); }
```

### 5.5 Row-list (no bordered cards)

The replacement for every "feature card." Instead of bracketed boxes, use
a list of horizontal rows separated by `1px var(--line-2)`.

```css
.list      { display: flex; flex-direction: column; border-top: 1px solid var(--line-2); }
.list .row { border-bottom: 1px solid var(--line-2);
             padding: 1rem 0; cursor: pointer;
             transition: padding-left .15s, background .15s;
             display: grid; grid-template-columns: 80px 1fr auto;
             gap: 1rem; align-items: center; }
.list .row:hover { padding-left: .5rem; background: var(--bg-2); }
.list .row .tag  { font-family: 'JetBrains Mono'; font-size: .68rem;
                   color: var(--faint); text-transform: uppercase; letter-spacing: .05em; }
.list .row .text { font-family: 'Inter Tight'; font-size: 1.05rem; color: var(--text); }
.list .row .arrow{ color: var(--faint); transition: color .15s, transform .15s; }
.list .row:hover .arrow { color: var(--text); transform: translateX(4px); }
```

This is the same template used for starters, chunks, and recent notes.

### 5.6 Underline tabs (OS picker, write-type picker)

```css
.tabs { display: flex; border-bottom: 1px solid var(--line-2); }
.tabs button { background: none; border: none; color: var(--dim);
               font-family: 'Inter Tight'; font-size: .95rem;
               padding: .85rem 1.4rem .85rem 0; margin-right: 1.5rem;
               cursor: pointer; position: relative; transition: color .15s; }
.tabs button:hover { color: var(--text-2); }
.tabs button.on   { color: var(--text); }
.tabs button.on::after { content: ""; position: absolute; left: 0;
                         right: 1.4rem; bottom: -1px;
                         height: 1px; background: var(--text); }
```

### 5.7 Terminal / faux-IDE card

When you need to show code or a command, never use a "card" with rounded
corners. Use a hard-edged inset block with a header bar.

```html
<div class="ide">
  <div class="ide-bar">
    <div class="dots"><span></span><span></span><span></span></div>
    <div class="tab">filename.ext</div>
    <div>TS</div>
  </div>
  <div class="ide-body">
    <div class="gut">1<br>2<br>3</div>
    <div class="src">...</div>
  </div>
</div>
```

```css
.ide      { background:#0d0d0d; border:1px solid var(--line-2); overflow:hidden;
            font-family:'JetBrains Mono'; font-size:.78rem; line-height:1.7; }
.ide-bar  { display:flex; justify-content:space-between; align-items:center;
            padding:.55rem .9rem; background:#080808;
            border-bottom:1px solid var(--line-2);
            color:var(--faint); font-size:.7rem; }
.ide-bar .dots span { width:9px; height:9px; border-radius:50%; background:var(--ghost); }
.ide-body { display:grid; grid-template-columns:32px 1fr; }
.ide-body .gut { background:#080808; color:var(--ghost); text-align:right;
                 padding:.9rem .55rem; border-right:1px solid var(--line);
                 user-select:none; }
.ide-body .src { padding:.9rem 1.1rem; overflow-x:auto; }
.ide-body .src .kw  { color: var(--text); }     /* keyword */
.ide-body .src .str { color: var(--text-2); }   /* string */
.ide-body .src .com { color: var(--faint);   font-style: italic; }  /* comment */
.ide-body .src .hl  { background: rgba(255,255,255,.07); display:inline-block;
                      width:100%; padding-left:.4em; margin-left:-.4em; }
```

Note the three "syntax highlight" tones are just shades of gray — never
the typical purple/blue/red of a code editor.

### 5.8 Massive footer wordmark

```html
<div class="wordmark">
  <span class="w">MEMCON</span>
  <div class="cut"></div>
</div>
```

```css
.wordmark        { position: relative; line-height: .78; margin: 1rem 0 2rem; }
.wordmark .w     { font-family: 'Inter Tight'; font-weight: 500;
                   font-size: clamp(6rem, 22vw, 22rem);
                   letter-spacing: -.06em; color: var(--text);
                   display: block; line-height: .78; }
.wordmark .cut   { position: absolute; right: 6%; top: 12%;
                   width: 22%; aspect-ratio: 1/1.25;
                   background: #0e0e0e; border: 1px solid var(--line-2);
                   overflow: hidden; }
```

Put the brand name at giant size in the footer with a small image card
*cutting into* the right edge of it. This is the single biggest move on
the landing page — borrowed directly from Sirnik.

### 5.9 Kbd

```css
.kbd { display: inline-flex; align-items: center; justify-content: center;
       font-family: 'JetBrains Mono'; font-size: .7rem;
       color: var(--text); width: 48px; height: 48px;
       border: 1px solid var(--line-3); text-align: center; }
```

Square. No rounded corners. Use for keyboard shortcuts in feature lists.

### 5.10 Reveal-on-scroll

```css
.reveal { opacity: 0; transform: translateY(14px);
          transition: opacity .7s ease, transform .7s ease; }
.reveal.in { opacity: 1; transform: none; }
```

```js
const io = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('in'); });
}, { threshold: .1, rootMargin: '0px 0px -40px 0px' });
document.querySelectorAll('.reveal').forEach(el => io.observe(el));
```

Apply `class="reveal"` to anything you want to fade-up on scroll. The
animation is **subtle** — 14px translate, 0.7s ease. No bouncing, no
springs, no staggers. Just a calm fade-up.

---

## 6. Interactions — the variety rule

> **Different interaction per section.** Never reuse the same micro-interaction
> on the same page. The system gets its sense of life from the diversity.

The landing page uses **seven** distinct interaction patterns. The chat UI
adds a few more. Use this as a menu — pick a different one per section.

### 6.1 Live clock (header / philosophy row)

```js
function tickClock(){
  const d = new Date();
  const pad = n => n < 10 ? '0'+n : ''+n;
  const el = document.getElementById('localTime');
  if (el) el.textContent = pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
}
tickClock(); setInterval(tickClock, 1000);
```

### 6.2 Cursor crosshair (hero)

Thin viewport-spanning lines that follow the cursor with a pixel-coord
label. Only inside the hero — turns off elsewhere.

### 6.3 Accordion row-list (step lists)

Click row → grid expands inline. Used in "The Loop." Caret rotates 45°
on open.

```css
.step .body  { max-height: 0; overflow: hidden;
               transition: max-height .35s cubic-bezier(.2,.8,.2,1); }
.step.open .body { max-height: 300px; }
.step .caret { transition: transform .2s; }
.step.open .caret { transform: rotate(45deg); }
```

### 6.4 Hover-to-update side panel (tool wall)

Grid of clickable items + sticky side panel. Hover any item → side panel
updates with that item's details. Used for MCP tools.

### 6.5 Tab switcher (OS picker)

See §5.6. Underline-only tabs that swap a `.on`-toggled panel.

### 6.6 Auto-detect by UA

For OS-specific install steps: detect on load, default to the user's OS.

```js
function detectOS(){
  const p = (navigator.userAgent + ' ' + (navigator.platform || '')).toLowerCase();
  if (p.includes('win')) return 'win';
  if (p.includes('mac') || p.includes('iphone') || p.includes('ipad')) return 'mac';
  return 'linux';
}
```

### 6.7 Marquee with hover-pause

Full-bleed scrolling band of tool names (or whatever).

```css
.marq          { overflow: hidden; padding: 1.15rem 0; }
.marq .lane    { display: flex; gap: 3.5rem; white-space: nowrap;
                 animation: slide 50s linear infinite; width: max-content; }
.marq:hover .lane { animation-play-state: paused; }
@keyframes slide { from { transform: translateX(0) } to { transform: translateX(-50%) } }
```

The `-50%` translate requires you to **duplicate** the lane contents in
HTML so it loops seamlessly.

### 6.8 Underline-on-hover (links)

The link interaction. Never a color change.

```css
a.dashed     { color: var(--text-2); border-bottom: 1px dashed var(--line-3);
               text-decoration: none; }
a.dashed:hover { color: var(--text); border-bottom-color: var(--text); }
```

### 6.9 Pad-left on hover (row lists)

The signature hover effect — instead of color or scale, the row pads-left
by `.5rem`. Used on starters, chunks, recent notes.

```css
.row         { transition: padding-left .15s, background .15s; }
.row:hover   { padding-left: .5rem; background: var(--bg-2); }
```

### 6.10 Animated underline reveal (hero)

For the one word in the hero that gets emphasis:

```css
.ul::after { content: ""; position: absolute; left: 0; right: 0; bottom: .08em;
             height: 2px; background: var(--text);
             transform-origin: left;
             animation: underline 1.4s .6s cubic-bezier(.65,0,.35,1) both; }
@keyframes underline { from { transform: scaleX(0) } to { transform: scaleX(1) } }
```

---

## 7. Anti-patterns — what NOT to do

The system fails the moment you introduce any of these. They look
"good" in isolation but break the whole language.

| Don't | Because |
|---|---|
| ❌ Rounded corners > 4px on cards/inputs | Reads as Bootstrap / generic SaaS |
| ❌ Drop shadows of any kind | The system relies on **lines**, not depth |
| ❌ Color accents (blue, red, brand color) | Replaces the typographic confidence with chrome |
| ❌ Gradients on text or backgrounds | Reads as crypto landing page |
| ❌ Icon next to every label | Tracking-.16em uppercase is the icon |
| ❌ Multiple-paragraph blocks of body copy | One sentence per "card." Density comes from columns, not prose |
| ❌ Centered text by default | Editorial layouts are left-aligned. Center only quotes & CTAs |
| ❌ Big paragraph leading (line-height > 1.7) | 1.55 is the target. Tight body text under huge display = the look |
| ❌ Decorative SVG illustrations | Real screenshots / terminal output only |
| ❌ Bracket-corner card decorations (`::before` + `::after` with 8px L-shapes) | Was the previous mistake — feels 2020-template-y |
| ❌ Reusing the same hover effect on 5+ sections | Kills the "different interaction per section" principle |
| ❌ Pure `#000` background | Use `#0a0a0a`. Pure black amplifies banding artifacts. |

---

## 8. Adapting to a different domain

Concrete recipe for spinning this system up on a different app.

### 8.1 Step 1 — copy the foundation

Copy these blocks unchanged into your new app:

- The Google Fonts `<link>` from §2
- All CSS variables from §3.1 (and §3.2 if you need light mode)
- The container `.wrap` from §4.1
- The `.tight`, `.mono`, `.cap` utility classes from §2.4
- The `::selection` and scrollbar styles from §3.4
- The reveal-on-scroll CSS + JS from §5.10

### 8.2 Step 2 — swap the brand

Change three things only:

1. The wordmark text (everywhere it appears: nav, footer giant text)
2. The glyph if you want a different mark (still mono — circle, square,
   rotated square, or a CSS-drawn shape)
3. The one keyword in the hero h1 that gets the `.ul` animated underline

### 8.3 Step 3 — fit your content to the layouts

The system has eight "section archetypes." Map your content to one of:

| Archetype | When to use | From |
|---|---|---|
| **Philosophy row** (3-col grid, prose · clock · status) | Below the nav, sets context | Landing |
| **Hero with corner artwork** (giant headline + terminal card + start links) | The home page | Landing |
| **Marquee band** | Visual rhythm break with keywords | Landing |
| **Numbered section header + accordion row-list** | Stepped processes, FAQs, changelogs | Landing |
| **Editorial stat columns** (4-col big numbers) | Metrics, social proof | Landing |
| **Tool wall + side panel** | Catalog of items you want to compare | Landing |
| **Split: faux-IDE + bullet list** | Showing code while explaining concepts | Landing |
| **Underline-tab switcher** (OS, type, mode) | Multi-variant content | Landing + chat |
| **Side-nav + scrollable column + bottom dock** | Stateful tool / chat app | Chat UI |
| **Side-by-side: prose + interactive widget** | Install/onboarding | Landing |
| **Centered quote + signature** | Manifesto-style closer | Landing |
| **Giant wordmark footer with image cut** | Closing | Landing |

Don't try to use all of them. Pick 4–6 that fit your content.

### 8.4 Step 4 — pick interactions per section

Use the menu from §6. **Never reuse the same interaction.** If section 1
has the accordion, section 2 should have the hover-side-panel, section 3
should have the OS tabs, etc. Variety is the whole game.

### 8.5 Step 5 — copy writing

Two rules:

1. **No "card" gets more than 2 sentences.** Cut everything else.
2. **Mix three text colors in one heading.** Default white, `.lite` gray,
   `.dim` gray. Pick which words deserve which weight.

> Example:
> `<h2>Before it answers, Claude pulls the few notes that match. <span class="dim">After a fix, it writes one back.</span> <span class="lite">Plain markdown on disk.</span></h2>`

### 8.6 Files to look at

| File | What it demonstrates |
|---|---|
| `docs/index.html` | The complete landing-page template (1100+ lines, all components) |
| `api/ui.html` | Same system applied to a stateful chat/tool UI |
| (this file) | The reference — read first, then steal from the two above |

---

## 9. Quick-start CSS — paste this to bootstrap

If you want to start a new HTML file with the design system pre-loaded,
paste this between your `<head>` tags as the entire starting point:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Inter+Tight:wght@200;300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#0a0a0a; --bg-2:#101010; --bg-3:#151515;
    --line:#1a1a1a; --line-2:#262626; --line-3:#3a3a3a;
    --text:#f4f4f4; --text-2:#cfcfcf;
    --dim:#8a8a8a; --faint:#5a5a5a; --ghost:#2c2c2c;
    --live:#3dd07a; --error:#e07070;
  }
  *{box-sizing:border-box;margin:0;padding:0;-webkit-font-smoothing:antialiased}
  html{scroll-behavior:smooth}
  body{background:var(--bg);color:var(--text);
       font-family:'Inter',system-ui,sans-serif;
       font-size:15px;line-height:1.55;overflow-x:hidden}
  a{color:inherit}
  ::selection{background:var(--text);color:var(--bg)}
  .tight{font-family:'Inter Tight',sans-serif;letter-spacing:-.025em}
  .mono{font-family:'JetBrains Mono',monospace}
  .dim{color:var(--dim)} .faint{color:var(--faint)}
  .cap{font-family:'Inter Tight',sans-serif;font-weight:500;
       font-size:.66rem;color:var(--faint);
       text-transform:uppercase;letter-spacing:.16em}
  .wrap{max-width:1480px;margin:0 auto;padding:0 2.5rem}
  @media(max-width:900px){.wrap{padding:0 1.5rem}}
  section{padding:6.5rem 0;border-top:1px solid var(--line)}
  .reveal{opacity:0;transform:translateY(14px);transition:opacity .7s ease,transform .7s ease}
  .reveal.in{opacity:1;transform:none}
  ::-webkit-scrollbar{width:8px;height:8px}
  ::-webkit-scrollbar-track{background:transparent}
  ::-webkit-scrollbar-thumb{background:var(--line-3);border-radius:4px}
  ::-webkit-scrollbar-thumb:hover{background:var(--dim)}
</style>
<script>
  document.addEventListener('DOMContentLoaded',()=>{
    const io=new IntersectionObserver(es=>es.forEach(e=>e.isIntersecting&&e.target.classList.add('in')),
      {threshold:.1,rootMargin:'0px 0px -40px 0px'});
    document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
  });
</script>
```

That's the entire base. Everything else is content.

---

## 10. The one-line summary

> **Editorial typography on lines, not in boxes. Different interaction per
> section. One word of color, ever — and it's reserved for "alive."**

If a design choice contradicts that sentence, it's wrong.
