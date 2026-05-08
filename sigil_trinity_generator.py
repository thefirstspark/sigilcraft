#!/usr/bin/env python3
"""
Sigil Trinity Generator
======================
Generates deterministic sigils from name + intention using seeded RNG.
Outputs SVG, PNG, and PDF formats.

Forges three sigils per customer:
  - Intention (what you want to manifest)
  - Protection (what you want to defend against)
  - Manifestation (what you embody)

All sigils are deterministically generated from the input, so the same
name + intention always produces the same sigil.
"""

import hashlib
import math
from typing import Tuple, List, Dict
from pathlib import Path


# ============================================================
# CORE ALGORITHMS
# ============================================================

def hash_string(s: str) -> int:
    """
    Deterministic hash of a string.
    Returns a 32-bit integer seed.
    """
    h = hashlib.md5(s.lower().strip().encode()).digest()
    return int.from_bytes(h[:4], byteorder='big')


class SeededRandom:
    """
    Mulberry32 seeded RNG (ported from JS).
    Produces reproducible random sequences from a seed.
    """
    def __init__(self, seed: int):
        self.seed = seed

    def next(self) -> float:
        """Return next random float in [0, 1)."""
        self.seed = (self.seed + 0x6D2B79F5) & 0xFFFFFFFF
        t = ((self.seed ^ (self.seed >> 15)) * 1) & 0xFFFFFFFF
        t = (t ^ (t + (self.seed << 7))) & 0xFFFFFFFF
        t = (t ^ (t >> 14))
        return ((t & 0xFFFFFFFF) >> 0) / 4294967296.0


def generate_sigil_svg(
    name: str,
    intention: str,
    width: int = 600,
    height: int = 600,
) -> str:
    """
    Generate a sigil as SVG string.

    Args:
        name: Person's name
        intention: Intention/manifestation text
        width, height: Canvas dimensions (px)

    Returns:
        SVG string (ready to embed or save)
    """
    # Seed from name + intention
    seed_input = f"{name}::{intention}".lower().strip()
    seed = hash_string(seed_input)
    rand = SeededRandom(seed)

    W, H = width, height
    cx, cy = W / 2, H / 2

    # Color palettes (deterministic by seed)
    palettes = [
        {'main': '#26E4D8', 'accent': '#F3B23A'},  # cyan+gold
        {'main': '#6B4DF2', 'accent': '#26E4D8'},  # violet+cyan
        {'main': '#FF6A3D', 'accent': '#F3B23A'},  # ember+gold
        {'main': '#26E4D8', 'accent': '#6B4DF2'},  # cyan+violet
    ]
    pal = palettes[int(rand.next() * len(palettes))]

    # Start SVG
    svg_lines = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
        f'<defs>',
        f'  <style>',
        f'    .sigil-main {{ stroke: {pal["main"]}; fill: none; }}',
        f'    .sigil-accent {{ stroke: {pal["accent"]}; fill: none; }}',
        f'    .sigil-bg {{ fill: #0B0B0C; }}',
        f'  </style>',
        f'</defs>',
        # Background
        f'<rect width="{W}" height="{H}" class="sigil-bg"/>'
    ]

    # --- Subtle background binary (ambient) ---
    for i in range(80):
        x = rand.next() * W
        y = rand.next() * H
        bit = '1' if rand.next() > 0.5 else '0'
        svg_lines.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="12" font-family="monospace" '
            f'fill="{pal["main"]}44">{bit}</text>'
        )

    # --- Outer ring ---
    svg_lines.append(
        f'<circle cx="{cx}" cy="{cy}" r="260" class="sigil-main" stroke-width="1" opacity="0.27"/>'
    )

    # --- Sacred geometry: rotating polygon ---
    sides = 3 + int(rand.next() * 6)  # 3-8 sides
    poly_r = 180 + rand.next() * 40
    poly_rot = rand.next() * math.pi * 2

    poly_points = []
    for i in range(sides + 1):
        angle = poly_rot + (i / sides) * math.pi * 2
        x = cx + math.cos(angle) * poly_r
        y = cy + math.sin(angle) * poly_r
        poly_points.append(f"{x:.1f},{y:.1f}")

    svg_lines.append(
        f'<polyline points="{" ".join(poly_points)}" class="sigil-accent" stroke-width="1.5" opacity="0.33"/>'
    )

    # --- Wave layers (interference pattern) ---
    for layer in range(3):
        amp = 40 + rand.next() * 30
        freq = 0.01 + rand.next() * 0.04
        phase = rand.next() * math.pi * 2
        y_offset = cy + (layer - 1) * 60

        path_d = []
        for x in range(0, W + 10, 10):
            y = y_offset + math.sin(x * freq + phase) * amp
            path_d.append(f"{'M' if x == 0 else 'L'} {x} {y:.1f}")

        svg_lines.append(
            f'<path d="{" ".join(path_d)}" class="sigil-main" stroke-width="1" opacity="0.2"/>'
        )

    # --- Spiral (golden ratio-ish) ---
    spiral_points = []
    t_max = rand.next() * 8 + 4  # 4-12 rotations
    for t in [i * 0.02 for i in range(int(t_max * 50))]:
        r = 20 + t * 25
        angle = t * math.pi * 2
        x = cx + math.cos(angle) * r
        y = cy + math.sin(angle) * r
        spiral_points.append(f"{x:.1f},{y:.1f}")

    svg_lines.append(
        f'<polyline points="{" ".join(spiral_points)}" class="sigil-accent" stroke-width="1.5" opacity="0.4"/>'
    )

    # --- Central mandala (concentric circles + radial lines) ---
    for ring in range(1, 6):
        radius = 30 * ring
        svg_lines.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" class="sigil-main" stroke-width="0.8" opacity="{0.5 - ring * 0.08}"/>'
        )

    # Radial lines from center
    num_rays = 8 + int(rand.next() * 8)
    for i in range(num_rays):
        angle = (i / num_rays) * math.pi * 2
        x2 = cx + math.cos(angle) * 150
        y2 = cy + math.sin(angle) * 150
        svg_lines.append(
            f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'class="sigil-accent" stroke-width="0.8" opacity="0.25"/>'
        )

    # --- Center dot (glyph core) ---
    svg_lines.append(
        f'<circle cx="{cx}" cy="{cy}" r="8" fill="{pal["main"]}" opacity="0.8"/>'
    )

    svg_lines.append('</svg>')

    return '\n'.join(svg_lines)


# ============================================================
# FILE I/O & EXPORT
# ============================================================

def save_sigil_svg(name: str, intention: str, output_path: Path) -> str:
    """Generate and save sigil as SVG file."""
    svg_content = generate_sigil_svg(name, intention)
    output_path.write_text(svg_content)
    return svg_content


def generate_sigil_triple(
    name: str,
    intention_text: str,
    protection_text: str,
    manifestation_text: str,
    output_dir: Path = None,
) -> Dict[str, str]:
    """
    Generate all three sigils for a customer.

    Returns dict with keys: 'intention_svg', 'protection_svg', 'manifestation_svg'
    """
    if output_dir is None:
        output_dir = Path.cwd()

    output_dir.mkdir(parents=True, exist_ok=True)

    result = {}

    # Generate intention sigil
    result['intention_svg'] = generate_sigil_svg(name, intention_text)

    # Generate protection sigil
    result['protection_svg'] = generate_sigil_svg(name, protection_text)

    # Generate manifestation sigil
    result['manifestation_svg'] = generate_sigil_svg(name, manifestation_text)

    return result


# ============================================================
# PERSONALIZATION
# ============================================================

def personalize_template(
    template_html: str,
    customer_name: str,
    customer_first_name: str,
    birth_date: str,  # MMDDYYYY
    birth_location: str,
    intention_text: str,
    protection_text: str,
    manifestation_text: str,
    intention_svg: str,
    protection_svg: str,
    manifestation_svg: str,
) -> str:
    """
    Replace all tokens in the template HTML.

    Tokens:
      {{CUSTOMER_NAME}} → Full name
      {{CUSTOMER_FIRST_NAME}} → First name
      {{FORGE_DATE}} → Today's date (MM.DD.YYYY)
      {{INITIALS}} → Lowercase initials
      {{BIRTH_MMDDYYYY}} → Birth date (8 digits)
      {{BIRTH_LOCATION}} → City, state
      {{INTENTION_QUOTE}} → Intention text
      {{PROTECTION_QUOTE}} → Protection text
      {{MANIFESTATION_QUOTE}} → Manifestation text
      {{INTENTION_SIGIL}} → SVG
      {{PROTECTION_SIGIL}} → SVG
      {{MANIFESTATION_SIGIL}} → SVG
    """
    from datetime import date

    initials = ''.join([c for c in customer_name if c.isupper()]).lower()
    today = date.today()
    forge_date = f"{today.month:02d}.{today.day:02d}.{today.year}"

    html = template_html
    html = html.replace('{{CUSTOMER_NAME}}', customer_name)
    html = html.replace('{{CUSTOMER_FIRST_NAME}}', customer_first_name)
    html = html.replace('{{FORGE_DATE}}', forge_date)
    html = html.replace('{{INITIALS}}', initials)
    html = html.replace('{{BIRTH_MMDDYYYY}}', birth_date)
    html = html.replace('{{BIRTH_LOCATION}}', birth_location or '—')
    html = html.replace('{{INTENTION_QUOTE}}', intention_text)
    html = html.replace('{{PROTECTION_QUOTE}}', protection_text)
    html = html.replace('{{MANIFESTATION_QUOTE}}', manifestation_text)
    html = html.replace('{{INTENTION_SIGIL}}', intention_svg)
    html = html.replace('{{PROTECTION_SIGIL}}', protection_svg)
    html = html.replace('{{MANIFESTATION_SIGIL}}', manifestation_svg)

    return html


if __name__ == '__main__':
    # Test
    print("Generating test sigil...")
    svg = generate_sigil_svg("Sarah Marie Lee", "I radiate clarity and confidence")
    print(svg[:200] + "...")
