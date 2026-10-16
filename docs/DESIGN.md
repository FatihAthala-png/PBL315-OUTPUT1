---
name: Collector-Grade TCG & Figure Vault
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#45464d'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#855300'
  on-secondary: '#ffffff'
  secondary-container: '#fea619'
  on-secondary-container: '#684000'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#410004'
  on-tertiary-container: '#ef4444'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#ffddb8'
  secondary-fixed-dim: '#ffb95f'
  on-secondary-fixed: '#2a1700'
  on-secondary-fixed-variant: '#653e00'
  tertiary-fixed: '#ffdad7'
  tertiary-fixed-dim: '#ffb3ad'
  on-tertiary-fixed: '#410004'
  on-tertiary-fixed-variant: '#930013'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '800'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0em
  price-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '800'
    lineHeight: 28px
    letterSpacing: -0.02em
  price-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '700'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.04em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.06em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system defines an authoritative, high-energy collector platform. It merges the precision of fine-art archival vaults with the electric dynamism of competitive Pokémon card play and authentic Japanese scale figures. The audience spans competitive TCG players, sealed-product investors, and discerning figure collectors who demand proof of authenticity, pristine grading standards, and instant transactional efficiency.

The aesthetic fuses **Modern Glassmorphic Precision** with **Tactile Collector Cues**:
- Surfaces remain crystalline and high-contrast, pairing crisp off-white canvas spaces (`#F8FAFC`) with deep navy archival structural headers (`#0F172A`).
- Energetic accents evoke classic mechanics: Electric Amber channels rare card foils and primary calls-to-action; Poké-Ball Crimson conveys urgency, rarity badges, and live drops; Electric Cyan mirrors pristine holographic card sheen.
- Micro-interactions are snappy, crisp, and mechanical, instilling confidence in high-value cart transactions and card condition transparency.

## Colors

The palette establishes an ultra-clean, legible e-commerce storefront anchored by deep archival navy and high-voltage accents:

- **Primary (`#0F172A`)**: Rich Midnight Navy used for headers, primary typography, high-impact buttons, and critical framing borders.
- **Secondary (`#F59E0B`)**: Electric Amber for primary interaction buttons, price highlights, and card foil highlights. Supported by `#FBBF24` for hover states and `#B45309` for accessible high-contrast text on bright backgrounds.
- **Tertiary (`#EF4444`)**: Poké-Ball Crimson reserved for discount badges, "Pre-Order" warnings, out-of-stock indicators, and active live-stock pips.
- **Accent Cyan (`#06B6D4`)**: Card grading indicators (PSA/BGS ratings), secret rare ribbons, and TCG foil shimmer borders.
- **Neutral Canvas**: Surface foundation sits on Crisp Slate (`#F8FAFC`) with pure white (`#FFFFFF`) card surfaces and razor-sharp border strokes (`#E2E8F0`). Text scales from Slate-900 (`#0F172A`) down to Slate-500 (`#64748B`) for technical specifications.

## Typography

The typography couples the geometric energy of **Plus Jakarta Sans** for headlines, product nomenclature, and numeric pricing with the utilitarian legibility of **Inter** for descriptions, specifications, and data tables.

All monetary values (Rupiah / Rp) and collector grades (PSA 10, Ungraded, 1/151) utilize tabular figures (`font-variant-numeric: tabular-nums`) within Plus Jakarta Sans to prevent layout jitter during live auction updates or price filtering. Product card titles retain a strict 2-line clamp with a 1.25 line-height ratio to preserve vertical rhythm across uneven product naming lengths.

## Layout & Spacing

The layout operates on a desktop-first 1440px viewport using a 12-column fluid grid system bounded by a max-width container of 1360px:

- **Sidebar & Catalog Architecture**: A 3-column sticky left rail (`280px` fixed or 3 grid columns) houses multi-tiered filters (TCG rarity, set expansion, condition grading, figure scale, manufacturer), while the remaining 9 columns house the product catalog in a 3-column or 4-column card matrix.
- **Rhythm**: Spacing enforces an 8pt spatial cadence. Inner card paddings rely strictly on `space-md` (16px), while layout gutters maintain a firm 24px (`space-lg`) to balance information density with clean white space.
- **Header & Navigation**: Fixed 72px dark navy utility bar hosting integrated search, category dropdown mega-menus, user collection vaults, and live cart slide-over indicators.

## Elevation & Depth

Visual hierarchy combines clean architectural layering with subtle holographic and glassmorphic depth:

- **Level 0 (Canvas)**: `#F8FAFC` flat matte base.
- **Level 1 (Catalog Tiles & Panels)**: `#FFFFFF` surface with a micro-border `1px solid #E2E8F0` paired with an ambient shadow `0 1px 3px rgba(15, 23, 42, 0.04), 0 4px 12px rgba(15, 23, 42, 0.03)`.
- **Level 2 (Active Product Cards & Flyouts)**: On hover, cards float with `translateY(-4px)` accompanied by `0 12px 24px -4px rgba(15, 23, 42, 0.08), 0 4px 8px -2px rgba(15, 23, 42, 0.04)` and an optional electric amber outline (`rgba(245, 158, 11, 0.3)`).
- **Level 3 (Sticky Headers & Overlays)**: Header navigation and modal drawers utilize dark glassmorphism: `#0F172A` at 92% opacity with `backdrop-filter: blur(12px)` and bottom border `1px solid rgba(255, 255, 255, 0.08)`.
- **Collector Badge Shimmer**: Rare Holo and PSA 10 badges incorporate an ultra-subtle linear gradient sheen (`linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 60%)`) simulating foil card reflection.

## Shapes

The design system adopts a balanced **Rounded (`2`)** shape vocabulary:

- **Base Radius**: 8px (`0.5rem`) applied to input fields, buttons, small badges, and dropdown menus.
- **Large Radius**: 16px (`1rem`) applied to product showcase cards, filter containers, and informational banners.
- **Pill Treatment (`rounded-full`)**: Strictly reserved for contextual metadata badges (e.g., "Ready Stock", "1/7 Scale", "Booster Box"), category quick-filter pills, and avatar/cart counters.

## Components

### Buttons
- **Primary CTA ("Tambah ke Keranjang")**: Background `#F59E0B`, text `#0F172A` bold. Hover transition to `#FBBF24` with a subtle elevation shift. Contains integrated cart icon on the left.
- **Secondary Action ("Lihat Detail / Vault")**: Border `1.5px solid #0F172A`, transparent background, text `#0F172A`. On hover: solid `#0F172A` fill with `#FFFFFF` text.
- **Wishlist Quick-Action**: Floating circular button (36x36px) top right of product image; white glass background (`rgba(255, 255, 255, 0.9)`), border `#E2E8F0`, crimson heart stroke `#EF4444` filling on active state.

### Product Card
- **Structure**: Outer card `16px` border radius, `#FFFFFF` fill, `1px solid #E2E8F0`.
- **Top Badge Zone**: Floats over product photo. Left: Category Tag (`#0F172A` background, `#FFFFFF` text). Right: Condition/Stock Tag (e.g., "Holo Rare" in Cyan tint `#ECFEFF` with text `#0891B2`, or "Ready Stock" in emerald `#ECFDF5` / `#059669`).
- **Image Container**: Aspect ratio 1:1 for figures, 3:4 for TCG slabs/singles, set against neutral `#F1F5F9` podium framing with smooth image scaling on card hover.
- **Information Cluster**: Category breadcrumb in `#64748B` (12px), title in `#0F172A` (16px semi-bold), 5-star rating chip with numeric review count `(128)`, and bold Rupiah currency display in `#B45309` (e.g., `Rp 1.450.000`).

### Category Filter Pills & Checkbox Trees
- **Pills**: Horizontal scrolling cluster at catalog head. Inactive: `#FFFFFF` fill, `#E2E8F0` border, text `#475569`. Active: `#0F172A` fill, text `#FFFFFF` with check icon.
- **Checkbox Trees**: Nested tree with custom 18px square checkboxes. Checked state: `#0F172A` fill with crisp white checkmark. Hover: border `#F59E0B`. Includes numeric count badges aligned right (e.g., `(42)`).

### Price Range Slider & Inputs
- Dual thumb slider track in `#E2E8F0` with the active selected span highlighted in Electric Amber (`#F59E0B`).
- Dual Rupiah currency inputs below the track prefixed with static gray "Rp" labels, numeric alignment right, and focus rings tinted in Amber.

### Search Bar & Autocomplete
- Large 48px height input within navigation. Background `rgba(255, 255, 255, 0.08)` on dark header, border `1px solid rgba(255, 255, 255, 0.15)`. Text `#FFFFFF`, placeholder `#94A3B8`.
- Live dropdown panel (`#FFFFFF`, elevated Level 3) with grouped results: "Kartu Populer", "Action Figure Terlaris", and direct card suggestions displaying mini-thumbnail, set symbol, and instant price tag.

### Cart Counter & User Profile
- Dark utility header hosts cart icon with an absolute badge in Poké-Crimson (`#EF4444`), white bold text, pulsing briefly upon item addition.
- User profile module includes circular avatar with gold status border indicating VIP collector tier.