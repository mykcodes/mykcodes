"""
Portrait Animation Generator — Optimized
==========================================
Generates a particle animation: Logo → Dispersion → Portrait
Uses luminance-aware sampling, edge detection, and smooth easing.

Optimizations:
- Reduced frame count for smaller GIF
- Color quantization for compression
- Configurable quality/size tradeoff
"""

import json
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "profile.json"
PORTRAIT_SRC = ROOT / "assets" / "source" / "portrait.png"
LOGO_SRC = ROOT / "assets" / "source" / "logo.png"
OUTPUT_PATH = ROOT / "assets" / "generated" / "portrait-animation.gif"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def ease_in_out_cubic(t):
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def load_gray(path, size):
    if not path.exists():
        return None
    return np.array(Image.open(path).convert("L").resize(size, Image.LANCZOS), dtype=np.float64) / 255.0


def edge_detect(gray):
    img = Image.fromarray((gray * 255).astype(np.uint8), mode="L")
    return np.array(img.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1)), dtype=np.float64) / 255.0


def sample_bright(gray, edges, n, rng):
    h, w = gray.shape
    combined = 0.7 * gray + 0.3 * edges
    flat = combined.flatten()
    total = flat.sum()
    if total == 0:
        indices = rng.choice(h * w, size=n, replace=True)
    else:
        indices = rng.choice(h * w, size=n, replace=True, p=flat / total)
    return (indices % w).astype(np.float64), (indices // w).astype(np.float64)


def generate_portrait_animation():
    config = load_config()
    anim = config["animation"]
    
    W = anim["portrait_width"]
    H = anim["portrait_height"]
    N = anim["particle_count"]
    FPS = anim["fps"]
    BG = hex_to_rgb(anim["background_color"])
    SEED = anim["random_seed"]
    NOISE = anim["movement_noise"]
    
    # Tighter frame budget for smaller GIF
    GATHER = 18     # random → logo
    LOGO_HOLD = 20  # hold logo
    DISPERSE = 14   # logo → scatter  
    FORM = 25       # scatter → portrait
    FINAL = 25      # hold portrait
    TOTAL = GATHER + LOGO_HOLD + DISPERSE + FORM + FINAL
    
    rng = np.random.default_rng(SEED)
    margin = 16
    rw, rh = W - 2 * margin, H - 2 * margin
    
    # Colors
    colors = [hex_to_rgb(anim[f"particle_color_{c}"]) for c in ("primary", "secondary", "tertiary")]
    
    # Load images
    logo_g = load_gray(LOGO_SRC, (rw, rh))
    port_g = load_gray(PORTRAIT_SRC, (rw, rh))
    
    # Sample points
    if logo_g is not None:
        lx, ly = sample_bright(logo_g, edge_detect(logo_g), N, rng)
    else:
        s = int(math.sqrt(N)) + 1
        gx, gy = np.meshgrid(np.linspace(10, rw - 10, s), np.linspace(10, rh - 10, s))
        lx, ly = gx.flatten()[:N], gy.flatten()[:N]
    
    if port_g is not None:
        px, py = sample_bright(port_g, edge_detect(port_g), N, rng)
    else:
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
        radii = rng.uniform(20, min(rw, rh) / 2 - 10, N)
        px, py = rw / 2 + radii * np.cos(angles), rh / 2 + radii * np.sin(angles)
    
    # Add margin offset
    lx += margin; ly += margin
    px += margin; py += margin
    
    # Initial random positions
    start_x = rng.uniform(0, W, N)
    start_y = rng.uniform(0, H, N)
    
    # Disperse positions
    disp_x = rng.uniform(0, W, N)
    disp_y = rng.uniform(0, H, N)
    
    # Particle properties
    radii = rng.uniform(anim["particle_radius_min"], anim["particle_radius_max"], N)
    opacities = rng.uniform(anim["particle_opacity_min"], anim["particle_opacity_max"], N)
    color_idx = np.arange(N) % len(colors)
    noise_ox = rng.uniform(0, 100, N)
    noise_oy = rng.uniform(0, 100, N)
    
    frames = []
    durations = []
    
    for fi in range(TOTAL):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img, "RGBA")
        
        # Calculate positions for all particles at once
        if fi < GATHER:
            t = ease_in_out_cubic(fi / max(GATHER - 1, 1))
            cur_x = start_x + (lx - start_x) * t
            cur_y = start_y + (ly - start_y) * t
        elif fi < GATHER + LOGO_HOLD:
            cur_x = lx.copy()
            cur_y = ly.copy()
        elif fi < GATHER + LOGO_HOLD + DISPERSE:
            t = ease_in_out_cubic((fi - GATHER - LOGO_HOLD) / max(DISPERSE - 1, 1))
            cur_x = lx + (disp_x - lx) * t
            cur_y = ly + (disp_y - ly) * t
        elif fi < GATHER + LOGO_HOLD + DISPERSE + FORM:
            t = ease_in_out_cubic((fi - GATHER - LOGO_HOLD - DISPERSE) / max(FORM - 1, 1))
            cur_x = disp_x + (px - disp_x) * t
            cur_y = disp_y + (py - disp_y) * t
        else:
            drift = (fi - GATHER - LOGO_HOLD - DISPERSE - FORM) / max(FINAL, 1)
            cur_x = px + np.sin(drift * 4 + noise_ox) * NOISE
            cur_y = py + np.cos(drift * 4 + noise_oy) * NOISE
        
        # Add micro noise during transitions
        if fi < GATHER + LOGO_HOLD + DISPERSE + FORM:
            cur_x += np.sin(fi * 0.3 + noise_ox) * NOISE * 0.4
            cur_y += np.cos(fi * 0.3 + noise_oy) * NOISE * 0.4
        
        # Fade-in for first few frames
        fade = min(1.0, fi / 4.0)
        
        # Draw all particles
        for i in range(N):
            alpha = int(opacities[i] * fade * 255)
            alpha = max(0, min(255, alpha))
            c = colors[color_idx[i]]
            r = radii[i]
            x, y = cur_x[i], cur_y[i]
            draw.ellipse([x - r, y - r, x + r, y + r], fill=(c[0], c[1], c[2], alpha))
        
        # Quantize for smaller GIF
        img_q = img.quantize(colors=64, method=Image.Quantize.MEDIANCUT)
        frames.append(img_q)
        
        # Timing
        if fi == TOTAL - 1:
            durations.append(2500)  # Hold final frame
        elif fi >= GATHER + LOGO_HOLD + DISPERSE + FORM:
            durations.append(int(1000 / FPS * 1.3))
        elif fi < GATHER + LOGO_HOLD and fi >= GATHER:
            durations.append(int(1000 / FPS * 1.15))
        else:
            durations.append(int(1000 / FPS))
    
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUTPUT_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"[OK] Portrait animation: {OUTPUT_PATH}")
    print(f"     {len(frames)} frames, {size_kb:.0f} KB, {W}x{H}, {N} particles")
    
    return OUTPUT_PATH


if __name__ == "__main__":
    generate_portrait_animation()
