# MED13 Foundation Design Guidelines

## Design Philosophy: Family-First Modernity

The MED13 Foundation's design centers on **families, connection, and shared hope** rather than clinical institutions. The visual language should feel **warm, uplifting, and trustworthy** - communicating that this is a place built by and for families navigating MED13 syndrome together.

**Design Tone Keywords:**
💞 *Warm • Inclusive • Trustworthy • Hopeful • Connected • Human-Centered*

## Color System - "Warm Science + Family Hope"

The palette evokes optimism, empathy, and clarity - balancing medical trust with human warmth.

**Primary Palette:**
- **Soft Teal** `#68B0AB` (HSL: 176 31% 55%) - Calming, trustworthy, representing health and growth
- **Coral-Peach** `#FFB6A0` (HSL: 12 100% 81%) - Warmth, compassion, family focus
- **Sunlight Yellow** `#FFD166` (HSL: 43 100% 70%) - Hope, optimism, possibility

**Supporting Colors:**
- **Background** `#FAFAFA` (HSL: 0 0% 98%) - Clean, breathable canvas with subtle warmth
- **Text** `#2E2E2E` (HSL: 0 0% 18%) - Readable, modern contrast
- **Muted** Soft neutral grays for secondary information

**Color Usage:**
- Avoid harsh medical blues or greys
- Use gentle gradients like teal → coral to suggest collaboration between science and love
- Primary buttons and CTAs use the warm teal
- Secondary highlights use coral-peach for emotional warmth
- Accent yellow for hope and optimism touches

### Color Tokens & Implementation

Map every palette color to a token so engineers can reference a single source of truth (`src/web/app/globals.css` + `src/web/tailwind.config.ts`).

| Token | Hex / HSL | CSS Variable | Tailwind Token | Usage & Contrast |
| --- | --- | --- | --- | --- |
| Soft Teal | `#68B0AB` / `176 31% 55%` | `--primary`, `--sidebar-primary`, `--ring` | `theme.extend.colors.brand.primary` | Primary CTAs, focus rings (≥ 4.5:1 on `--card`) |
| Coral-Peach | `#FFB6A0` / `12 100% 81%` | `--secondary`, `--sidebar-accent` | `theme.extend.colors.brand.secondary` | Secondary highlights + card accents with `text-foreground` |
| Sunlight Yellow | `#FFD166` / `43 100% 70%` | `--accent` | `theme.extend.colors.brand.accent` | Status pills and optimism touches (always pair with `--foreground`) |
| Background | `#FAFAFA` / `0 0% 98%` | `--background`, `--card` | `theme.colors.background` | Main surfaces; pair with `--border` for separation |
| Text | `#2E2E2E` / `0 0% 18%` | `--foreground`, `--card-foreground` | `theme.colors.foreground` | Body copy, headings, icons |

Implementation checklist:
- Gradients: `bg-gradient-to-r from-brand-primary/90 to-brand-secondary/90` so the values stay tokenized.
- Text/background pairings are pre-approved (e.g., `bg-brand-secondary` + `text-foreground` = 5.2:1 contrast). Log any exceptions for accessibility review.
- When expanding the palette, add the token to this table, `globals.css`, and `tailwind.config.ts` in the same PR.

## Typography - "Readable, Modern, Gentle"

Communicate clarity and care at first glance with humanistic, approachable type.

**Font Families:**
- **Headings**: Nunito Sans - Rounded, humanistic, family-friendly, easy to read for all ages
- **Body**: Inter - Professional yet friendly, excellent legibility
- **Highlights/Quotes**: Playfair Display - Elegant, adds emotional warmth

Declare the stacks once in `globals.css` so Tailwind `font-heading` / `font-sans` utilities resolve predictably:

```css
:root {
  --font-heading: "Nunito Sans", "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
  --font-body: "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
  --font-display: "Playfair Display", "Times New Roman", serif;
}
```

**Type Scale:**
- Hero Headline: Nunito Sans 48-60px, font-weight 700-800
- Section Heading: Nunito Sans 32-40px, font-weight 600-700
- Subsection: Nunito Sans 20-24px, font-weight 600
- Body Large: Inter 18-20px, font-weight 400, line-height 1.7
- Body Standard: Inter 16px, font-weight 400, line-height 1.7
- Captions: Inter 14px, font-weight 400

**Line Height:** 1.6-1.8 for comfort and accessibility

### Responsive Type Implementation
- Favor `rem` units or Tailwind text utilities instead of fixed px to respect user zoom preferences.
- Hero/section headings use `clamp()` for fluid sizing:
  ```css
  .hero-heading {
    font-family: var(--font-heading);
    font-weight: 700;
    font-size: clamp(2.5rem, 3vw, 3.75rem);
    line-height: 1.15;
  }
  ```
- Default body copy uses `text-base md:text-lg leading-relaxed`, while long-form sections elevate to `leading-loose`.
- Always pair semantic tags (`<strong>`, `<em>`, `<cite>`) with the typographic class so assistive tech announces emphasis accurately.



## Layout & Structure

**Goal:** Balance storytelling with action, create calm rhythm.

**Key Principles:**
- Maximum section width: 1100-1200px for optimal readability
- Generous padding: 80-100px between sections (py-16 to py-24)
- Use asymmetric grid sections where appropriate (alternating photo/text)
- Soft dividers: Faint gradient lines or curved section breaks
- Replace dense lists with icon cards (rounded corners, pastel backgrounds)

**Cards & Components:**
- Clean white cards with subtle elevation
- 6-8px border radius for gentle, approachable feel
- Semi-transparent cards (bg-card/95) with backdrop blur over background images
- Icon + Title + Description pattern
- Hover: Subtle elevation increase using hover-elevate utility

### Spacing, Elevation & Density Tokens

| Token | Tailwind Utility | px Value | Recommended Use |
| --- | --- | --- | --- |
| `space-sm` | `py-6` / `gap-6` | 24px | Card content, compact stacks |
| `space-md` | `py-10` / `gap-10` | 40px | Default intra-section rhythm |
| `space-lg` | `py-16` / `gap-16` | 64px | Standard section separation |
| `space-xl` | `py-24` / `gap-24` | 96px | Hero blocks, major transitions |

Elevation tokens are defined in `globals.css` (`--shadow-xs` … `--shadow-lg`). Reference them consistently:

| Token | CSS Variable | Usage Pattern |
| --- | --- | --- |
| `shadow-brand-xs` | `--shadow-xs` | Chips, subtle dividers |
| `shadow-brand-sm` | `--shadow-sm` | Cards resting on flat surfaces |
| `shadow-brand-md` | `--shadow-md` | Hovered/active cards, modals |
| `shadow-brand-lg` | `--shadow-lg` | Hero overlays, spotlight cards |

If you need a new spacing or elevation level, update this table, `tailwind.config.ts`, and `globals.css` in the same change to avoid drift.

## Motion & Interaction - "Subtle Emotional Reinforcement"

**Goal:** Enhance without distracting.

**Interaction Patterns:**
- Button hover: Gentle lift + slight color warmth (handled by built-in utilities)
- Section reveal: Fade-in + upward motion on scroll (0.3-0.4s ease)
- Smooth scroll behavior for anchor navigation
- Background parallax on hero for subtle depth

**DO:**
✅ Subtle, meaningful animations
✅ Focus on accessibility (keyboard navigation, WCAG AA contrast)

**DON'T:**
🚫 Excessive motion or distracting effects
🚫 Auto-playing carousels or videos

### Interactive State Specifications
- **Focus**: `focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[hsl(var(--ring))]` keeps teal rings accessible on both themes.
- **Hover**: Primary buttons use `hover:bg-brand-primary/90 hover:shadow-brand-md`; secondary buttons use the same pattern with `brand-secondary`.
- **Active/Pressed**: Apply `translate-y-px` plus `shadow-brand-sm` to signal depth without harsh motion.
- **Disabled**: `opacity-50 cursor-not-allowed` and neutralized shadows; still ensure 3:1 contrast against background.
- **Validation**: Errors rely on `border-[hsl(var(--destructive))]` and destructive focus rings; success states reuse the primary ring with `bg-brand-primary/10`.
- **Animation Tokens**: Entry transitions use `duration-300 ease-out`, exits use `duration-150 ease-in`, and transforms stay within 20px to avoid vestibular discomfort.

## Iconography - "Simple, Rounded, Emotionally Resonant"

**Style:** Duotone line icons with rounded corners (Lucide icons)

**Themes:**
- 🧬 Research → DNA strand in teal
- 👨‍👩‍👧 Family → Coral heart + people silhouettes
- 🤝 Collaboration → Interlocking circles
- 💡 Discovery → Sunlight yellow bulb
- 📊 Data → Chart/graph in teal


## Accessibility Requirements

- WCAG AA contrast ratios minimum (4.5:1 for body text)
- Focus indicators for keyboard navigation
- Semantic HTML throughout
- Alt text for all images
- Form labels explicitly associated
- Skip to content link
- Test with screen readers
- Validate color contrast for every new component using the documented token pairings; exceptions require an accessibility review note.

## Critical Design Principles

1. **Family-First**: Design communicates "built by families, for families"
2. **Warmth with Trust**: Balance emotional connection with credibility
3. **Clarity Above All**: Every element serves understanding
4. **Accessible Always**: Families in vulnerable moments need barrier-free access
5. **Hope and Optimism**: Visual language inspires rather than intimidates
6. **Human-Centered**: People before processes, connection before clinical

---

**Result:** Visitors instantly feel *this is a place built by and for families*, not a distant research entity. The design bridges the scientific rigor of medical research with the warmth and humanity of family support.
