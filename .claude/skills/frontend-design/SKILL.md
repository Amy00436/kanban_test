---
name: frontend-design
description: Visual design direction for the Demo Bank IT PMO Kanban board (index.html). Use when restyling the board, cards, header, summary strip, filters, Add Task modal or toasts, or when adding any new visible UI, so changes stay distinctive but fit the project's vanilla, single-file, token-driven constraints.
license: Complete terms in LICENSE.txt
---

# Frontend Design

## Project overrides: Demo Bank IT PMO Kanban (read first)

This section wins over anything below it. The rest of this file is the upstream general guidance; apply it only where it doesn't conflict.

### The brief is already fixed
- **Subject:** an internal IT Project Management Office board for a fictitious retail bank ("Demo Bank"). Four columns: Backlog, In Progress, Blocked, Done. Projects are things like Core Banking Upgrade, Cybersecurity Uplift and Vendor Management.
- **Audience:** PMO leads, delivery managers and engineers at a bank, during demos and training sessions, usually on a laptop or a shared screen. They scan for what is blocked, overdue or Critical.
- **Primary job:** show the state of work at a glance, and make add / move / delete fast and obvious. This is a working tool, not a landing page. **There is no hero.** The summary strip (Total, per-column counts, Overdue) is the top-of-page moment. Don't add marketing sections, testimonials or big-number heroes.
- Don't ask the client to confirm subject or audience; it's this brief.

### Hard constraints (from CLAUDE.md; never trade these for aesthetics)
- One file, `index.html`, vanilla HTML/CSS/JS. **No web fonts, no CDN, no image files, no libraries.** The typography guidance below ("choose typefaces deliberately") has to be met with **system font stacks only**. Express personality with weight, size, tracking, tabular numerals (`font-variant-numeric: tabular-nums` for counts and dates) and the type scale, not with a new family.
- Icons and the logo are **inline SVG or Unicode**. The logo is generic. Never use "UOB" or any real bank's name, colours-as-trademark, logo or wordmark. The brand is "Demo Bank".
- Every colour, space, radius and shadow comes from the custom properties on `:root`. Add a token rather than a raw hex in a rule. No `!important`.
- No `alert()` / `confirm()`. Confirmation is the inline "Delete? Yes / No" on the card, and feedback uses toasts.
- Don't change card markup outside `renderCard()` and `renderBoard()`, and keep the `data-action` / `data-id` attributes that the delegated handlers on `#board` depend on.

### Current token system (extend, don't replace, unless asked to redesign)
| Role | Tokens |
|---|---|
| Brand navy | `--blue-900 #0b2e59`, `--blue-800`, `--blue-700`, `--blue-500 #2f74c0`, `--blue-100`, `--blue-50` |
| Ink & surfaces | `--ink #1b2430`, `--ink-muted #5a6676`, `--line #d5dde7`, `--surface #fff`, `--page #eef2f7` |
| Priority (fg + bg pairs) | `--p-critical` red, `--p-high` amber, `--p-medium` blue, `--p-low` grey, each with `-bg` |
| Status | `--success`, `--warning`, `--danger` |
| Spacing | `--space-1..6` = 4, 8, 12, 16, 24, 32px |
| Shape | `--radius-sm 4`, `--radius 8`, `--radius-lg 12`; `--shadow-sm`, `--shadow`, `--shadow-lg` (navy-tinted) |
| Focus | `--focus: 0 0 0 3px #ffbf47` (amber ring; keep it visible on every control) |
| Type | `--font: system-ui, -apple-system, "Segoe UI", Roboto, …`; task IDs use the system monospace |

### Where to spend the boldness
Spend it in **one** place. Good candidates for this board:
- **Priority and urgency.** The Critical, Overdue and Blocked states are the information people came for. Make them unmistakable with more than colour alone (left-edge bar, label text, icon). Everything else stays quiet.
- **Column identity.** Blocked deserves a different treatment from Backlog. A neutral sameness across columns hides the one column that matters.

Avoid making the board look like the generic "SaaS card kit" (trait 4 below), with identical cards, one radius everywhere and soft grey shadows. Cards here are dense data objects (ID, priority, title, project, assignee, due date, category, overdue badge, actions), so design for scanning, with hierarchy inside the card. Don't decorate.

### Banking-appropriate tone
- Calm, credible and legible. No playful illustration, confetti or neon. Navy plus restrained status colours suits a bank. A redesign may move away from it, but it should still read as "regulated institution".
- Copy uses sentence case and plain PMO vocabulary: "Add task", "Move to Blocked", "Task DEMO-ITPM-0012 added". An action keeps its name through the whole flow (button "Add task" → toast "Task added").
- Use task IDs in the `DEMO-ITPM-####` format for any sample content.

### Quality floor for this project
- Responsive down to phone width (there is a `@media (max-width: 767px)` breakpoint; columns stack). No horizontal page scroll.
- Drag-and-drop always has the keyboard / single-pointer alternative (the per-card "Move ▸" select). Never remove it.
- Respect `prefers-reduced-motion` for any new motion. Keep contrast at 4.5:1 or better for text, including text on the priority `-bg` tints.
- Check your work visually with the headless Chrome screenshot command in CLAUDE.md (`--window-size=1400,1100` for desktop; measure `innerWidth` for narrow layouts, since headless Chrome won't go below about 504px). Then run the forbidden-API grep.

### Plan format for this project
When proposing a direction, give: 4–6 named colours **as `:root` token names plus hex values**, the system font stack and type scale, an ASCII wireframe of header, summary, filters and the four columns, plus a card close-up. Say which single element carries the boldness. Then review it against the generic defaults below before writing CSS.

---

Approach this as the design lead at a design studio known for giving every client a distinct visual identity that is not mistaken for anyone else's. This client has already rejected proposals that felt cliché or templated, and is paying for a distinctive point of view: make deliberate, opinionated choices about palette, typography, and layout that are specific to this brief, and take aesthetic risk if justified.

## Ground your designs in the subject matter

If the brief does not identify what the product or subject matter is, identify it yourself before designing, and confirm with the client. You can come up with one concrete subject, the design's audience, and the design's primary job, as a proposal. If there's any information in your memory about the client's preferences or context about what they're building, use that as a hint. The subject's industry, subject matter, materials, and vernacular are where distinctive visual choices come from — a design for a toy for girls aged 8–11 will be very aesthetically different from a dashboard for financial analysts. Build with the brief's real content and subject matter throughout.

## Design principles

For web designs, the hero is the first thing viewers will see. Open with the most characteristic thing in the subject's world, in the form that is most appropriate: a headline, an image, an animation, a live demo, an interactive moment, or other treatments. Be deliberate with your choice: a big number with a small label, supporting stats, and a gradient accent is the default treatment, so only use it if that's truly the best option.

Typography carries the personality of the page. You don't need a different typeface for display or headline text and body content: use one family or two, and if two, make them clearly distinct.

Choose your typefaces deliberately, not the default families you would reach for on any other project, and set a clear type scale following the default guidance of The Elements of Typographic Style with intentional weights, widths, and spacing. When type is used as a headline or visual element, use the type treatment itself as an active part of the design, not a neutral delivery vehicle for the content.

Default to line lengths of less than 80 characters. Serif typefaces can have slightly longer line lengths; give serif body text slightly more line-height than a sans-serif.

Avoid these default typographic treatments; they are the commonest tells of a generated page:
- Accenting just a single word or phrase in a headline, like putting one word in italic/bold or a different color.
- Using all caps for labels.
- Adding unnecessary typographic labels above content.

Visual structure is information. Structural devices like outlines, borders, numbering, eyebrows, dividers, labels, etc., encode useful information about the content rather than decorate it. Many generic designs use numbered markers (01 / 02 / 03), but that's only appropriate if the content actually is a sequence — like a stepped process or a timeline. Before adding numbered markers, check the content really is a sequence.

Use non-user-triggered motion sparingly and deliberately, only to draw attention. A single orchestrated moment — one page-load sequence or one reveal — lands better than scattered effects; fade-and-slide-up entrances on each section and hover transitions on every card are the generic default and read as AI-generated. Motion that answers a person's action (opening, expanding, confirming) is welcome when it shows what changed.

Consider written content carefully. Often a design brief may not contain real content, and it's up to you to come up with copy and placeholder content. Copy can make a design feel as templated as the design itself. See the below section on writing for more guidance.

## Process: plan, review against the brief, build, critique

For calibration, AI-generated design right now clusters around some traits:
1. a warm cream background (near #F4F1EA) with a high-contrast serif display and a terracotta or warm-clay accent (often near #D97757 — Anthropic's own Claude-interaction accent, so on a user's brief it reads as a tell);
2. a near-black background with a single bright acid-green or vermilion accent;
3. a broadsheet-style layout with hairline rules, zero border-radius, and dense newspaper-like columns;
4. the SaaS-card kit: content chopped into identical rounded cards, one border-radius on everything regardless of hierarchy, the same soft grey shadow (rgba(0,0,0,.1)) under each, and gradient washes as decoration;
5. template chrome that appears whatever the subject: a tracked-out ALL-CAPS eyebrow label above every heading; meta strings joined with middle dots ('A · B · C'); labels built as 'WORD — fragment' with a spaced em dash; tinted near-black (#0B0B0B, #111) standing in for black; a monospace face for small data labels; a '→' appended to link and button text.

All traits are legitimate for some briefs, but they are defaults rather than choices, and they appear regardless of subject. Where the brief pins down a visual direction, follow it exactly — the brief's own words always win, including when it asks for one of these looks. Where it leaves an axis free, don't spend that freedom on one of these defaults. As with a hired human designer, there's often a careful balance between doing what you're good at and taking each project as a chance to experiment and learn.

Work in two passes. First, brainstorm a short design plan based on the client's design brief: create a compact token system with color, type, layout, and principles.
- Color: describe the core base palette as 4–6 named hex values.
- Type: the typefaces and their roles.
- Layout: a layout concept, using one-sentence prose descriptions and ASCII wireframes to ideate and compare. Include alignment guidance; should the content be left aligned, center aligned, justified?
- Principles: the high-level guidance for what makes this page unique.

Then review that plan against the brief before building: if any part of it reads like the generic default you would produce for any similar page (work through a similar prompt to see if you arrive somewhere similar) rather than a choice made for this specific brief — revise that part, say what you changed and why. Only after you've confirmed the relative uniqueness of your design plan should you start to write the code, following the revised plan.

When writing the code, be careful of structuring your CSS selector specificities. It's easy to generate CSS classes that cancel each other out (especially with a type-based selector like .section and an element-based selector like .cta). This can happen often with padding/margin between sections.

## Restraint and self-critique

Spend your boldness in one place. Let one element be the memorable thing, keep everything around it quiet and disciplined, and cut any decoration that does not serve the brief. Build to a quality floor without announcing it: responsive down to mobile, visible keyboard focus, reduced motion respected, visually accessible, harmonious color palettes. Critique your own work as you build, taking screenshots to review if your environment supports it — a picture is worth 1000 tokens. Consider Chanel's advice: before leaving the house, take a look in the mirror and remove one accessory. Human creatives have memory and always try to do something new, so if you have a space to quickly jot down notes about what you've tried, it can help you in future passes.

## More on writing in design

Words appear in a design for one reason: to make it easier to understand and use. They are design content, not decoration. Bring the same intentionality and minimalism to copywriting that you would bring to spacing and color. Before writing anything, ask what the design needs to say, and how it can best be said to help the person navigate the experience.

Write from the end user's perspective. Name things by what users will understand in simple language, not by how the system is built. A user manages notifications, not webhook config. Describe what something is or does in plain terms rather than selling it. Being specific and legible to new users is always better than being clever.

Use active voice as default. A CTA says exactly what happens when it is used: "Save changes," not "Submit." An action keeps the same name through the whole flow, so the button that says "Publish" produces a toast that says "Published." The vocabulary of an interface is the signposting for someone navigating the product. Cohesion and consistency are how people learn their way around.

Treat failure and emptiness as moments for direction, not mood. Explain what went wrong and how to fix it, in the interface's voice rather than a person's. Errors don't apologize, and they are never vague about what happened. An empty screen is an invitation to act.

Keep the tone conversational: plain verbs, sentence case, no filler, with tone matched to the brand and the audience. Let each written element do exactly one job.
