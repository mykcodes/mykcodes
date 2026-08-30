"""
Portrait Animation Generator — Optimized for Phase 3
====================================================
Generates a highly-detailed particle animation: Logo → Dispersion → Portrait
Features:
- Image color sampling
- Edge-aware density mapping
- Multi-scale particles for pixel-art feel
- Smooth transitions
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


def get_density_map(img_gray, img_rgb):
    # Edge detection
    edges = np.array(img_gray.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1)), dtype=np.float64) / 255.0
    gray_arr = np.array(img_gray, dtype=np.float64) / 255.0
    
    # Weight edges highly to preserve facial features, but keep luminance for fill
    # Brighter pixels get more particles in luminance
    combined = 0.3 * gray_arr + 0.7 * edges
    return combined


def sample_points_and_colors(img_rgb, img_gray, n, rng):
    w, h = img_rgb.size
    density = get_density_map(img_gray, img_rgb)
    flat = density.flatten()
    total = flat.sum()
    
    if total == 0:
        indices = rng.choice(h * w, size=n, replace=True)
    else:
        indices = rng.choice(h * w, size=n, replace=True, p=flat / total)
        
    x = (indices % w).astype(np.float64)
    y = (indices // w).astype(np.float64)
    
    # Extract colors
    rgb_arr = np.array(img_rgb)
    colors = rgb_arr[y.astype(int), x.astype(int), :]
    
    return x, y, colors


def map_points(px, py, lx, ly):
    # Sort both sets of points spatially to minimize intersecting paths during transition
    px_sorted_idx = np.argsort(px + py * 0.1)
    lx_sorted_idx = np.argsort(lx + ly * 0.1)
    
    lx_mapped = np.zeros_like(lx)
    ly_mapped = np.zeros_like(ly)
    lx_mapped[px_sorted_idx] = lx[lx_sorted_idx]
    ly_mapped[px_sorted_idx] = ly[lx_sorted_idx]
    
    return lx_mapped, ly_mapped


def generate_portrait_animation():
    config = load_config()
    anim = config["animation"]
    
    W = anim["portrait_width"]
    H = anim["portrait_height"]
    N = anim.get("particle_count", 8000)
    FPS = anim["fps"]
    BG = hex_to_rgb(anim["background_color"])
    SEED = anim["random_seed"]
    NOISE = anim["movement_noise"]
    
    APPEAR = anim.get("logo_appearance_frames", 15)
    LOGO_HOLD = anim.get("logo_hold_frames", 30)
    DISPERSE = anim.get("dispersion_frames", 25)
    FORM = anim.get("portrait_formation_frames", 40)
    FINAL = anim.get("final_hold_frames", 50)
    TOTAL = APPEAR + LOGO_HOLD + DISPERSE + FORM + FINAL
    
    rng = np.random.default_rng(SEED)
    margin = 16
    rw, rh = W - 2 * margin, H - 2 * margin
    
    # Load and resize images
    logo_img = Image.open(LOGO_SRC).convert("RGB").resize((rw, rh), Image.LANCZOS)
    logo_gray = logo_img.convert("L")
    
    port_img = Image.open(PORTRAIT_SRC).convert("RGB").resize((rw, rh), Image.LANCZOS)
    port_gray = port_img.convert("L")
    
    # Sample Portrait
    px, py, p_colors = sample_points_and_colors(port_img, port_gray, N, rng)
    
    # Sample Logo
    lx, ly, l_colors_raw = sample_points_and_colors(logo_img, logo_gray, N, rng)
    
    # Add margin offset
    lx += margin; ly += margin
    px += margin; py += margin
    
    # Map portrait points to logo points
    lx, ly = map_points(px, py, lx, ly)
    
    # We want logo to be cyan/primary colored, or derived from logo
    # But since it's a solid logo often, let's use the primary color from config
    primary_color = hex_to_rgb(anim["particle_color_primary"])
    l_colors = np.array([primary_color for _ in range(N)])
    
    # Disperse positions
    disp_x = px + rng.uniform(-40, 40, N)
    disp_y = py + rng.uniform(-40, 40, N)
    
    # Multi-scale particles
    # 70% micro, 20% small, 8% medium, 2% large
    r_min = anim["particle_radius_min"]
    r_max = anim["particle_radius_max"]
    
    radii = np.zeros(N)
    micro_idx = int(N * 0.7)
    small_idx = int(N * 0.9)
    med_idx = int(N * 0.98)
    
    radii[:micro_idx] = rng.uniform(r_min, r_min + (r_max-r_min)*0.3, micro_idx)
    radii[micro_idx:small_idx] = rng.uniform(r_min + (r_max-r_min)*0.3, r_min + (r_max-r_min)*0.6, small_idx - micro_idx)
    radii[small_idx:med_idx] = rng.uniform(r_min + (r_max-r_min)*0.6, r_min + (r_max-r_min)*0.85, med_idx - small_idx)
    radii[med_idx:] = rng.uniform(r_min + (r_max-r_min)*0.85, r_max, N - med_idx)
    rng.shuffle(radii)
    
    opacities = rng.uniform(anim["particle_opacity_min"], anim["particle_opacity_max"], N)
    noise_ox = rng.uniform(0, 100, N)
    noise_oy = rng.uniform(0, 100, N)
    
    frames = []
    durations = []
    
    for fi in range(TOTAL):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img, "RGBA")
        
        if fi < APPEAR:
            t = ease_in_out_cubic(fi / max(APPEAR - 1, 1))
            cur_x = lx
            cur_y = ly
            cur_c = l_colors
            alpha_mult = t
        elif fi < APPEAR + LOGO_HOLD:
            cur_x = lx
            cur_y = ly
            cur_c = l_colors
            alpha_mult = 1.0
        elif fi < APPEAR + LOGO_HOLD + DISPERSE:
            t = ease_in_out_cubic((fi - APPEAR - LOGO_HOLD) / max(DISPERSE - 1, 1))
            cur_x = lx + (disp_x - lx) * t
            cur_y = ly + (disp_y - ly) * t
            
            # Transition color from logo to portrait
            cur_c = l_colors + (p_colors - l_colors) * t
            alpha_mult = 1.0
        elif fi < APPEAR + LOGO_HOLD + DISPERSE + FORM:
            t = ease_in_out_cubic((fi - APPEAR - LOGO_HOLD - DISPERSE) / max(FORM - 1, 1))
            cur_x = disp_x + (px - disp_x) * t
            cur_y = disp_y + (py - disp_y) * t
            cur_c = p_colors
            alpha_mult = 1.0
        else:
            drift = (fi - APPEAR - LOGO_HOLD - DISPERSE - FORM) / max(FINAL, 1)
            # Only drift a subset of particles (the smaller ones) for subtle ambient motion
            ambient_mask = radii < (r_min + (r_max-r_min)*0.4)
            cur_x = px.copy()
            cur_y = py.copy()
            cur_x[ambient_mask] = px[ambient_mask] + np.sin(drift * 4 + noise_ox[ambient_mask]) * NOISE * 0.5
            cur_y[ambient_mask] = py[ambient_mask] + np.cos(drift * 4 + noise_oy[ambient_mask]) * NOISE * 0.5
            cur_c = p_colors
            alpha_mult = 1.0
        
        # Add micro noise during transitions
        if APPEAR + LOGO_HOLD <= fi < APPEAR + LOGO_HOLD + DISPERSE + FORM:
            t_noise = np.sin(fi * 0.5 + noise_ox) * NOISE
            cur_x = cur_x + t_noise
            cur_y = cur_y + np.cos(fi * 0.5 + noise_oy) * NOISE
            
        # Draw particles
        for i in range(N):
            alpha = int(opacities[i] * alpha_mult * 255)
            alpha = max(0, min(255, alpha))
            if alpha == 0:
                continue
                
            r = radii[i]
            x, y = cur_x[i], cur_y[i]
            c = cur_c[i]
            draw.ellipse([x - r, y - r, x + r, y + r], fill=(int(c[0]), int(c[1]), int(c[2]), alpha))
        
        # Quantize for smaller GIF
        img_q = img.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
        frames.append(img_q)
        
        # Timing
        if fi == TOTAL - 1:
            durations.append(2500)  # Hold final frame
        elif fi >= APPEAR + LOGO_HOLD + DISPERSE + FORM:
            durations.append(int(1000 / FPS * 1.3))
        elif fi < APPEAR + LOGO_HOLD and fi >= APPEAR:
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
