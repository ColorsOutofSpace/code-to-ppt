# code-to-ppt: Self-Optimizing Workflow for PPTX Generation via Python Code

## 1. Overview

This skill guides you through programmatic `.pptx` generation using `python-pptx`.

Core innovation: **a self-optimization loop — "Python code → PPTX → PNG export → LLM vision review → code fix → regenerate."** Unlike tools that generate static images or fill templates, this workflow produces native, editable `.pptx` files and iterates through visual review → fix cycles to ensure quality.

Suitable for any presentation purpose — defense, report, pitch, lecture, etc. Color schemes are designed autonomously based on each specific use case.

## 2. When to Use

Load this skill when:

- The user asks to generate a `.pptx` file
- The user asks to create slides / a presentation / a deck
- The user asks to modify existing PPT generation code
- The user mentions `python-pptx`

## 3. Self-Optimization Workflow

Follow these 6 phases in strict order. **Phase 1 is mandatory — do not skip it.**

```
Phase 1: Requirements ──→ Phase 2: Color Scheme ──→ Phase 3: Slide Plan
                                                           │
                                                           ▼
Phase 6: Final Delivery ←── Phase 5: Fix & Verify ←── Phase 4: Visual Review
                                                           │
                                           (PPTX → PNG → MCP Vision)
```

---

### Phase 1: Requirements Confirmation (MANDATORY)

**Before writing any code**, confirm the following checklist with the user. Do not proceed to Phase 2 until all items are confirmed.

```
□ Purpose: ________________ (defense / report / pitch / lecture / other)
□ Audience & tone: ________________ (formal / professional / creative / other)
□ Content source: ________________ (paper path / document / data / verbal description)
□ Estimated slide count: ___
□ Image assets path: ________________, count: ___
□ Key data points to highlight: ________________
□ Speaker notes needed: yes / no
□ Output path: ________________
□ Institution/brand info: ________________ (school / company / logo path)
```

Use `AskUserQuestion` to present these grouped into at most 4 questions with 2-4 options plus "Other" each.

---

### Phase 2: Color Scheme Design

**Core principle: never hardcode colors. Design the color scheme based on the purpose and audience from Phase 1.**

Decision dimensions:
- **Purpose** → Hue direction: academic defense → restrained (navy/burgundy); business pitch → sharp (dark gray + bright accent); creative → vibrant (high-saturation accent)
- **Audience** → Contrast: formal occasions → high contrast (dark bg + white text); internal meetings → softer (light bg + dark text)
- **Brand** → Primary source: if logo or brand colors exist, prioritize them

Design a **4-tier palette** with 2-4 colors per tier:

| Tier | Count | Usage |
|------|-------|-------|
| Primary | 1-2 | Cover background, section dividers, page titles |
| Secondary | 2-3 | Card top accent lines, chart colors |
| Neutral | 3-4 | Body text `#1A1A1A`, gray `#6B7B8D`, light bg `#EDF2F8`, white `#FFFFFF` |
| Semantic | 3-4 | Positive/gain = green, warning/limitation = red/orange, contrast/context = gold |

Card accent line semantic mapping:
- General content → Secondary color
- Core innovation / contribution / gain → Semantic-positive (green) or brightened Primary
- Comparison / prior work / context → Semantic-contrast (gold/orange)
- Limitations / issues / cost → Semantic-warning (red)

> See the "Color Methodology" section below for detailed methodology and scenario examples.

---

### Phase 3: Slide Structure Planning

1. Group content into logical sections, determine each slide's topic
2. Slide type distribution: Cover → Outline → Content (N slides) → Summary → Thank You
3. Label each slide: text-only / image / mixed
4. Each slide: no more than 8 lines of body text (excluding footer and section labels)
5. Insert section divider slides between major sections if needed

**Show the outline to the user for approval before proceeding to Phase 4.**

---

### Phase 4: Code Writing

#### 4.1 Set Up Infrastructure

1. Define `RGBColor` constants matching the Phase 2 palette
2. In the generated python-pptx script, **implement helper functions yourself** as needed (`tx`, `cd`, `plot_card`, `img_fit`, `band`, `hero`, `ft`, `st`, `sT`, etc.)
3. Set image path `FIG` and output path `OUT`
4. Update the institution name in `ft()` with the value from Phase 1

#### 4.2 Precise Layout Calculation Per Slide (MANDATORY before coding)

**Before writing any code for a slide, complete the following 4-step calculation. No guesswork.**

**Step A: Vertical Space Budget**

Slide effective area:
- Header (`st` + `sT`): y=0 to y≈0.95, fixed ~0.95"
- Footer (`ft` line): y=5.25 to y=5.625, fixed ~0.375"
- **Usable content height: 5.25 − 0.95 = 4.3"** (y≈1.0 to y≈5.2)

List all elements for this slide with their y-coordinates and heights. Sum must be ≤ 4.3". Distribute leftover space across gaps — never leave it pooled at the bottom.

```
Example — two-card slide vertical budget:
  st+sT           0.00 – 0.95  (fixed)
  cd(card1)       1.05 – 2.75  (h=1.7)
  gap             2.75 – 2.90  (h=0.15)
  cd(card2)       2.90 – 4.60  (h=1.7)
  gap             4.60 – 4.85  (h=0.25)
  ft              5.25 – 5.625 (fixed)
  Content total: 1.7+0.15+1.7+0.25 = 3.8" ≤ 4.3" ✓, 0.5" leftover → distributed to gaps
```

**Step B: Actual Rendered Line Count (most error-prone step)**

`cd()` body text is typeset within width `(w − 0.28)"`. For 9.5pt Microsoft YaHei:
- Chinese char width ≈ 9.5/72 ≈ 0.132"
- English/digit width ≈ 0.066" (roughly half)
- Chars per line ≈ `(w − 0.28) / 0.132`
- Mixed text: count Chinese chars as 1 equivalent char, English/digits as 0.5

**Actual rendered lines** = Σ ceil(eq_chars_in_logical_line / chars_per_line), where logical lines = `text.split('\n')`

> See the "Line Count Estimation" section below for detailed formulas and lookup tables.

**Step C: Required cd() Height**

```
Required h_card = 0.42 + (rendered_lines × fs × ls / 72) + 0.05 (safety margin)
```

`cd()` default `fs=9.5, ls=1.45` → per-line height = `9.5 × 1.45 / 72 = 0.191"`

| Rendered Lines | Minimum h_card | Recommended h_card |
|---------------|---------------|-------------------|
| 2 | 0.87" | 1.0" |
| 3 | 1.06" | 1.2" |
| 4 | 1.25" | 1.4" |
| 5 | 1.44" | 1.6" |
| 6 | 1.63" | 1.8" |
| 7 | 1.83" | 2.0" |
| 8 | 2.02" | 2.2" |

If the required `h_card` doesn't fit the page budget, shorten the text first, then consider widening the card.

**Step D: Distribute Leftover Space**

If `sum(content_elements + gaps) < 4.3"`:
1. **Deficit < 0.3"** → spread evenly across gaps
2. **Deficit 0.3"–0.8"** → proportionally increase card/image heights
3. **Deficit > 0.8"** → consider adding a `band()` or `hero()` module to fill the page

**Step E: Write the Code**

Annotate each slide with the calculation results:

```python
# === S7: Dataset Overview ===
# Vertical: st+sT(0.95) + cd(1.7) + gap(0.15) + plot_card(1.7) + ft(0.375) = 4.875 ✓
# cd body w=4.12": 4 logical lines→5 rendered→need h≥1.43, h_card=1.7 ✓
```

- Use `plot_card()` for image slides, `cd()` for text slides
- For mixed layouts, allocate height according to Step A budget
- End each slide with `ft(sl, page_number)`
- Add `print("S7")` after each slide to locate runtime errors

#### 4.3 Follow Design Principles

- See Section 5 "Design Guidelines"

---

### Phase 5: Visual Review

This is the core differentiator of this skill.

1. **Generate PPTX**: Run the Python script
2. **Export PNGs**:
   - Windows: Use PowerPoint COM automation to export each slide as PNG (1920×1080)
   - Linux/Mac: Use LibreOffice command-line export
3. **Review each slide**: Use an MCP vision tool (such as `mcp__MiniMax__understand_image`) to check:
   - Text overflow — any text exceeding card/box boundaries
   - Image distortion — wrong aspect ratio
   - Element overlap — shapes or text overlapping
   - Font too small — anything below 7pt
   - Color consistency — matches Phase 2 palette
4. **Log issues**: slide number + specific element + description

Per-slide review prompt template:
```
Check this PPT slide for:
1. Text overflow — any text touching or exceeding card/box borders
2. Image distortion — wrong aspect ratio
3. Element overlap — shapes or text overlapping each other
4. Font too small — text below 7pt
5. Color consistency — colors match the defined palette
Report only problems found. Say "no problems" if clean.
```

---

### Phase 6: Fix & Verify + Final Delivery

1. Fix each issue found in Phase 5
2. Re-export only affected slides, review again
3. Loop fix → review until all slides pass
4. Deliver the final `.pptx` file
5. Report to user: total slides, image count, key data points

---

## 4. Infrastructure: Helper Function Reference

> Quick reference below (LLM tool generates full code as needed).

python-pptx uses inches (Inches). 16:9 canvas = 10 × 5.625".

| Function | Purpose | Key Parameters |
|----------|---------|----------------|
| `get_img_size(name)` | PIL pre-read image dimensions, cached | `name`: filename relative to FIG |
| `img_fit(sl, name, l, t, max_w, max_h, align)` | Place image preserving aspect ratio | `align`: "center"/"left"/"right" |
| `tx(sl, l, t, w, h, text, **kw)` | Single-paragraph text; must set `eaTypeface` | `fs`, `cl`, `bd`, `ls` |
| `ri(sl, l, t, w, h, runs)` | Multi-paragraph mixed-format text | `runs`: [(text, {kw}), ...] |
| `bu(sl, l, t, w, h, items)` | Bulleted list | Auto blue bullet dots |
| `cd(sl, l, t, w, h, title, body, accent)` | Content card: white bg + top accent line + title + body | `accent`: semantic color |
| `plot_card(sl, l, t, w, h, name, title, accent)` | Image card: white bg + accent line + image | Auto aspect-ratio fit |
| `img_top(sl, name, l, t, w)` | Place image at fixed width, return actual height | No height constraint |
| `band(sl, l, t, w, h, color)` | Solid-color rectangle band | Emphasis / separator |
| `hero(sl, l, t, w, h, number, label, accent)` | Big stat (42pt + label) | Key metrics |
| `cn(sl, x, y, num, color)` | Numbered circle (0.5" diameter) | Timeline / steps |
| `ft(sl, n)` | Standard footer: short line + institution + page number | Footer line at y=5.25" |
| `st(sl, title)` | Section label (8pt + top thin line) | Top of content pages |
| `sT(sl, title, sub)` | Page title (27pt) + optional subtitle | Right after `st()` |
| `section_divider(prs, num, title, subtitle)` | Dark full-screen section divider | Between major sections |
| `ns(prs, bgc)` | New blank slide | Layout index 6 |
| `setbg(sl, c)` | Set solid background color | — |
| `_rect(sl, l, t, w, h, color)` | Filled rectangle (internal) | No border |
| `_line(sl, l, t, w, color, thickness)` | Horizontal line (internal) | Default 0.005" |

---

## 5. Design Guidelines

### 5.1 Anti-AI-Flavor Checklist

Self-check every slide against these:

- [ ] **No left vertical accent bars** — the #1 AI-generated PPT fingerprint. Use thin top horizontal lines (0.03") instead
- [ ] **No box shadows / drop shadows** — all shapes use flat solid fills
- [ ] **Layout variety** — mix at least 3 different layout types (see 5.3)
- [ ] **Hero stats present** — use `hero()` for the 1-3 most important numbers (42pt+)
- [ ] **Bands break rhythm** — use `band()` to insert full-width color strips between card-heavy pages
- [ ] **Footer line is short** — ~1.8 inches, not full-width
- [ ] **Colors are semantic** — different info types use different card accent line colors (see Phase 2)
- [ ] **Data is concrete** — embed specific values in card body text, not just qualitative descriptions
- [ ] **No clipart icons** — use only geometric shapes: rectangles, lines, circles (`cn()`)

### 5.2 Content Density Rules

- Max 8 body text lines per slide (excluding footer and section labels)
- Minimum body font size: 9.5pt in cards, 7pt in footer
- Card body usable height: `h_body = h_card - 0.42` (inches)
- Height per line: `h_line = fs × ls / 72` (inches)
- Max lines: `N_max = floor(h_body / h_line)`

> Detailed capacity table in the "Layout Dimensions" section below.

### 5.3 Page Layout Patterns

Common layout types. Colors and backgrounds are determined by Phase 2 — only structure is described here.

| Pattern | Structure | Use Case |
|---------|-----------|----------|
| **Cover** | Full-screen bg color + main title (30-36pt white) + subtitle + info area | First slide |
| **Outline** | Light bg + large numbers (23pt) + titles (17pt) + short descriptions | Table of contents |
| **Section Divider** | Dark full-screen + large section number (72pt) + section title (30pt white) | Between major sections |
| **Two-Column Compare** | Left and right `cd()` with different accent line colors | Baseline vs improved, prior vs ours |
| **Image-Top Analysis-Below** | Top image (55-60% height) + bottom `cd()` analysis card | Data/chart presentation |
| **Image-Left Text-Right** | Left `plot_card()` (55-60% width) + right `cd()` | Architecture diagram, flowchart |
| **Three-Up Images** | Three small images side by side + bottom `band()` with unified conclusion | Distribution comparison |
| **Timeline** | Left `cn()` numbered circles + right title & description, vertical | Contributions, steps, workflow |
| **Hero Panel** | 1-3 `hero()` big stats + short analysis text | Key results summary |
| **Summary / Thank You** | Dark full-screen, echoing the cover color scheme | Closing slides |

---

## 6. Common Mistakes

| Problem | Root Cause | Prevention |
|---------|-----------|------------|
| Card body text overflow | **Skipped Phase 4.2 Step B/C** — guessed `h_card` | Calculate actual rendered lines for every `cd()` before coding, derive height from formula |
| Large empty space at page bottom | **No vertical space budget (Step A)** — arbitrary heights | List all element y/h and sum before coding; distribute leftover evenly |
| Distorted images | Direct `add_picture()` without aspect-ratio calc | Always use `img_fit()` |
| Footer overlaps content | Card bottom exceeds y=5.25 | Ensure `y + h ≤ 5.25` |
| Chinese renders in wrong typeface | Missing `eaTypeface` setting | Add `rPr.set(qn("a:eaTypeface"), fn)` to every text run |
| Inconsistent colors | Accent line colors chosen arbitrarily | Review Phase 2 palette; use semantic mapping |
| Missing image crash | Wrong path or filename | `img_fit()` has red placeholder fallback; verify `FIG` path |
| Monotonous layout | All slides use the same layout | Mix at least 3 layout types (see 5.3) |

---

## 7. References

- `SKILL.md` — Chinese version of this workflow
