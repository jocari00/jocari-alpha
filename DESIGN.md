# Jocari Alpha — design

Reference: a private-banking dashboard screenshot chosen by the owner. Values marked *(est.)* are
estimated from the screenshot, not measured. Chart series colours are validated with the
dataviz script and must not be swapped for the UI accent.

## Colour
| Role | Value | Note |
|---|---|---|
| Page | `#F5F2EB` | warm off-white *(est.)* |
| Surface (raised rows, inputs) | `#FBFAF6` | *(est.)* |
| Ink | `#16181D` | near-black text *(est.)* |
| Secondary text | `#5F6168` | *(est.)* |
| Muted / meta | `#8E8F94` | *(est.)* |
| Hairline | `#E3DED3` | 1px dividers *(est.)* |
| Accent (UI) | `#1F2E57` | navy: active tab, selected button *(est.)* |
| Attention | `#B7791F` | amber, always with an icon *(est.)* |
| Series: portfolio / benchmark | `#2A5FA8` / `#B08A3E` | validated; dark mode `#5B8FD6` / `#AD8636` |
| Gain / loss | `#1C7440` / `#B3362B` | with a sign, never colour alone |

## Type
- **Sans:** Libre Franklin. Hero figure 300, 56–64px *(est.)*, tracking −0.02em; headings 300;
  names 500, 15–16px; body 400, 15–16px / 1.6.
- **Mono:** DM Mono 400 for dates, ISINs, account-style codes, statuses and labels; 12–13px.
- **Labels:** mono, UPPERCASE, 11px, tracking +0.12em, muted colour *(est.)*.
- Figures: tabular, right-aligned in lists; typographic minus (−).

## Layout
- Max width 1200px *(est.)*; side gutter 16px (phone) / 40px (desktop).
- Order: thin meta strip → header with tabs → one hero figure → full-width chart → 2–3 equal
  columns of lists.
- Lists, not cards: rows separated by 1px hairlines; name left, figure right, detail in mono
  muted below. Row height ≈ 52px *(est.)*.
- Chart: annotated (leader line + label for meaningful events), recessive grid, period selector
  as a segmented control.

## Spacing and shape
- 8px base. Inside rows 12–16px; between blocks 48px; between page sections 64–80px *(est.)*.
- Radius: 4px for buttons, inputs and segmented controls *(est.)*; 0 for sections and lists.
- No shadows. Separation comes from hairlines and white space.
