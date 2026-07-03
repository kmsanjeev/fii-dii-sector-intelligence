/**
 * tokens.ts — Platform design system
 *
 * THE single source of truth for colors, font sizes, and shared style objects.
 * Every page and component must import from here.
 *
 * Text hierarchy: h1 > text > textSub > muted > dim
 * RULE: never use `dim` for text the user must read.
 * RULE: font sizes — caption (10px) is the absolute minimum.
 */

import type React from 'react'

// ── Color Palette ───────────────────────────────────────────────────────────────

export const T = {
  // Backgrounds
  bg:       '#07091A',   // page root
  panel:    '#0D1525',   // card / section bg
  cell:     '#111B2E',   // inner bg, table rows
  hover:    '#162035',   // hover state

  // Borders
  border:   '#1E2D44',
  borderHi: '#2D4A6B',

  // Text — hierarchy (dim = decorative only, never readable content)
  h1:       '#F8FAFC',   // primary metric values, headlines
  text:     '#E2E8F0',   // body text, tile values
  textSub:  '#B0C4D8',   // labels, supporting info
  muted:    '#7B90A8',   // metadata, chip text, secondary labels
  dim:      '#4E6074',   // decorative: dividers, timestamps, placeholders only

  // Semantic
  green:    '#22D35E',   // bull, positive, strong
  red:      '#F44B4B',   // bear, negative, alert
  amber:    '#F5A524',   // neutral, warning, caution
  blue:     '#4080FF',   // FII, institutional, primary
  teal:     '#0EC4A0',   // DII, secondary bull
  purple:   '#A855F7',   // ML, AI, promoter

  // Participant
  fii:      '#3BAEF0',
  dii:      '#9B7BEA',
  pro:      '#F5833A',
  client:   '#C668E8',
} as const

// ── Font Sizes (px) ─────────────────────────────────────────────────────────────

export const FS = {
  caption: 10,   // minimum — chart axis, timestamps, decorative
  label:   11,   // field labels, chip text, ALL-CAPS tags
  body:    12,   // standard body text, table cells
  md:      13,   // emphasized text, button labels
  lg:      15,   // sub-headings, secondary metric labels
  xl:      18,   // tile values (compact tiles)
  '2xl':   22,   // tile values (standard tiles)
  '3xl':   28,   // hero/dashboard headline values
} as const

// ── Font Weights ─────────────────────────────────────────────────────────────────

export const FW = {
  regular: 400,
  medium:  600,
  bold:    700,
  heavy:   800,
  black:   900,
} as const

// ── Shared Style Objects ─────────────────────────────────────────────────────────

/** Top bar label for a card or section */
export const CARD_HDR: React.CSSProperties = {
  padding: '9px 14px',
  fontSize: FS.label,
  fontWeight: FW.heavy,
  letterSpacing: 1.8,
  textTransform: 'uppercase',
  color: T.textSub,
  borderBottom: `1px solid ${T.border}`,
  background: T.panel,
}

/** Small ALL-CAPS inline field label */
export const FIELD_LBL: React.CSSProperties = {
  fontSize: FS.label,
  fontWeight: FW.bold,
  letterSpacing: 1.5,
  textTransform: 'uppercase',
  color: T.muted,
}

/** Data-tile colored header strip */
export const TILE_HDR: React.CSSProperties = {
  padding: '5px 10px',
  fontSize: FS.caption,
  fontWeight: FW.heavy,
  letterSpacing: 1.2,
  textTransform: 'uppercase',
  color: 'rgba(255,255,255,0.90)',
}

/** Data-tile numeric / primary value */
export const TILE_VAL: React.CSSProperties = {
  fontSize: FS['2xl'],
  fontWeight: FW.black,
  fontFamily: 'monospace',
  lineHeight: 1.1,
}

/** Data-tile sub-label beneath the value */
export const TILE_SUB: React.CSSProperties = {
  fontSize: FS.label,
  color: T.muted,
  marginTop: 5,
  lineHeight: 1.3,
}
