# ContentGuard Design System

ContentGuard follows a high-density, technical aesthetic built for Trust & Safety operators. It is monochrome, disciplined, and functional. Red is reserved exclusively for the `BLOCK` outcome and critical error alerts. Decisions are always conveyed through both typographic labels and geometric glyphs, never colour alone.

---

## 1. Design Tokens & Palette

### Dark Mode (Primary)
| Token | Hex Value | Role |
|---|---|---|
| `--black` | `#000000` | True OLED base canvas background |
| `--surface` | `#111111` | Primary cards, panels, and table wraps |
| `--surface-raised` | `#1A1A1A` | Secondary insets, hovered rows, active tiles |
| `--border` | `#222222` | Subtle structural dividers and table lines |
| `--border-visible` | `#333333` | Prominent outer borders, chips, and switches |
| `--input-border` | `#666666` | Accessible field boundary (3.7:1 WCAG ratio) |
| `--text-disabled` | `#666666` | Placeholders, inactive navigation items |
| `--text-secondary` | `#999999` | Labels, captions, micro-copy, timestamps |
| `--text-primary` | `#E8E8E8` | High-readability body copy |
| `--text-display` | `#FFFFFF` | Hero titles, active buttons, high-contrast highlights |
| `--accent` | `#D71921` | Critical warnings, destructive `BLOCK` outline |
| `--accent-subtle` | `rgba(215,25,33,.15)` | Tinted highlights behind lethal threat nodes |
| `--success` | `#4A9E5C` | Operational confirmation |
| `--warning` | `#D4A843` | `WARN` state indicators |
| `--interactive` | `#5B9BF6` | Focus outlines & secondary links |

### Light Mode (`prefers-color-scheme: light`)
| Token | Hex Value | Role |
|---|---|---|
| `--black` | `#F5F5F5` | Off-white background canvas |
| `--surface` | `#FFFFFF` | Crisp white cards and panels |
| `--surface-raised` | `#F0F0F0` | Recessed backgrounds and hovered items |
| `--border` | `#E8E8E8` | Light structural dividing lines |
| `--border-visible` | `#CCCCCC` | Distinct card borders and button outlines |
| `--input-border` | `#999999` | Accessible field boundary |
| `--text-disabled` | `#999999` | Subtle placeholders and disabled labels |
| `--text-secondary` | `#666666` | Secondary body text and metadata |
| `--text-primary` | `#1A1A1A` | Dark neutral body text |
| `--text-display` | `#000000` | Pure black headlines and active buttons |

---

## 2. Typography

### Typefaces
- **Display Hero (`Doto`)**: Used selectively for the single hero moment per screen (e.g. the primary outcome word on the Workbench and the Macro F1 metric on Evaluation).
- **Body & Headings (`Space Grotesk`)**: Clean geometric sans-serif for page titles, explanations, and descriptions.
- **Data & Metadata (`Space Mono`)**: Monospace face for IDs, timestamps, status pills, metrics, signals, and code blocks.

### Scale & Budget
- **Hero Display**: 72px (`--font-doto`), weight 700.
- **Page Titles (`h1`)**: 36px (`Space Grotesk`), weight 500, line-height 1.1.
- **Metric Tiles (`.v`)**: 24px (`Space Mono`), weight 500.
- **Body Text**: 14px / 16px, line-height 1.55.
- **Labels (`.label`)**: 11px (`Space Mono`), all-caps, tracking `0.08em`, weight 400.
- **Weight Budget**: Maximum of two weights per view (400 regular, 500/700 display). Bold weights are stripped from pills and brand tags.

---

## 3. Spacing System (8px Grid)

```css
--space-xs:  4px;
--space-sm:  8px;
--space-md:  16px;
--space-lg:  24px;
--space-xl:  32px;
--space-2xl: 48px;
--space-3xl: 64px;
--space-4xl: 96px;
```
- **Intra-component**: 8px to 16px.
- **Inter-section**: 32px to 48px.
- **Layout hierarchy**: Spacing first $\to$ Dividers $\to$ Borders $\to$ Surface cards.

---

## 4. Components

### Navigation
- Borderless text bar with numbered indices (`01`, `02`, `03`, `04`).
- Active tab has `color: var(--text-display)` and a discrete `border-bottom: 2px solid var(--text-display)`. Inactive tabs use `--text-disabled`.

### Status Pills
Outcomes are conveyed by structural glyphs:
- **`ALLOW`**: `○ ALLOW` (Solid outline)
- **`WARN`**: `◐ WARN` (Half-filled glyph)
- **`REVIEW`**: `◇ REVIEW` (Dashed border, diamond glyph)
- **`BLOCK`**: `■ BLOCK` (Outline style with `--accent` border and text; no solid background fill)

### Progress & Signal Visualization
- **Segmented Meters**: Signal confidence and input length use discrete multi-segment meters (e.g., 20 or 40 individual blocks) rather than continuous smooth bars.

### Buttons & Chips
- **Buttons**: Pill-radius (`999px`), 13px Space Mono, min-height 44px for accessibility. Primary buttons use high-contrast inverted styling.
- **Chips**: All-caps Space Mono (`SAMPLE 01`, `SAMPLE 02`, `ABSTAIN`) with pill radius.

### Modal Dialogs
- Centered overlay modals on desktop (maximum width 520px, 80% opacity dark scrim, `[ X ]` top-right dismissal).
- Responsive bottom-sheet transition on screens under 600px with touch handles.

---

## 5. Motion Guidelines

- **Restraint**: No bouncing springs, scale bounces, or slide-up animations.
- **Single Primitive**: Fading transitions only:
  ```css
  --ease: cubic-bezier(0.25, 0.1, 0.25, 1);
  --t-micro: 200ms;
  --t-base: 350ms;
  @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
  .fade-in { animation: fade var(--t-base) var(--ease) both; }
  ```
- **Accessibility**: Full `prefers-reduced-motion` override disabling all transitions and animations.
