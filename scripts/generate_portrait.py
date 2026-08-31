"""
Portrait Animation Generator — Phase 5
======================================
Generates a highly-detailed particle animation: Logo → Dispersion → Portrait
Features:
- Structured pixel grid for gapless portrait rendering
- Edge-aware density masking
- Perceptual color quantization
- Multi-scale pixels
- Coherent particle identity mapping
"""

import json
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import binary_closing, binary_dilation

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

def get_portrait_pixels(img_rgb, img_gray, pixel_size, edge_weight, rng):
    w, h = img_rgb.size
    
    # Use Canny-like edge detection for feature preservation
    edges = np.array(img_gray.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1)), dtype=np.float64) / 255.0
    gray_arr = np.array(img_gray, dtype=np.float64) / 255.0
    
    # We want a mask of occupied pixels. 
    # Assume dark background, so luminance > threshold is the portrait.
    # To avoid holes inside the face, we use morphological closing.
    base_mask = gray_arr > 0.08
    closed_mask = binary_closing(base_mask, iterations=2)
    
    # Ensure edges are fully included
    final_mask = closed_mask | (edges > 0.1)
    
    # Create grid
    xs = np.arange(pixel_size // 2, w, pixel_size)
    ys = np.arange(pixel_size // 2, h, pixel_size)
    grid_x, grid_y = np.meshgrid(xs, ys)
    
    flat_x = grid_x.flatten()
    flat_y = grid_y.flatten()
    
    # Keep only points inside the mask
    mask_vals = final_mask[flat_y, flat_x]
    
    valid_x = flat_x[mask_vals]
    valid_y = flat_y[mask_vals]
    
    # Quantize colors perceptually
    quantized_img = img_rgb.quantize(colors=16, method=Image.Quantize.MEDIANCUT).convert("RGB")
    q_arr = np.array(quantized_img)
    
    colors = q_arr[valid_y, valid_x, :]
    edges_val = edges[valid_y, valid_x]
    
    return valid_x.astype(np.float64), valid_y.astype(np.float64), colors, edges_val

def get_logo_pixels(img_gray, num_points, rng):
    w, h = img_gray.size
    gray_arr = np.array(img_gray, dtype=np.float64) / 255.0
    mask = gray_arr > 0.1
    
    y_idx, x_idx = np.where(mask)
    if len(x_idx) == 0:
        return np.zeros(num_points), np.zeros(num_points)
        
    # We need exactly num_points from the logo.
    # Randomly sample from valid pixels.
    indices = rng.choice(len(x_idx), size=num_points, replace=True)
    return x_idx[indices].astype(np.float64), y_idx[indices].astype(np.float64)

def map_points(px, py, lx, ly):
    # Sort by a spatial heuristic to minimize crossovers
    p_sort = np.argsort(px + py * 1.5)
    l_sort = np.argsort(lx + ly * 1.5)
    
    lx_mapped = np.zeros_like(lx)
    ly_mapped = np.zeros_like(ly)
    lx_mapped[p_sort] = lx[l_sort]
    ly_mapped[p_sort] = ly[l_sort]
    return lx_mapped, ly_mapped

def generate_portrait_animation():
    config = load_config()
    anim = config["animation"]
    
    WW = anim.get("working_width", 600)
    WH = anim.get("working_height", 600)
    DW = anim.get("display_width", 300)
    DH = anim.get("display_height", 300)
    PIXEL_SIZE = anim.get("pixel_size", 2)
    FPS = anim["fps"]
    BG = hex_to_rgb(anim["background_color"])
    SEED = anim["random_seed"]
    NOISE = anim["movement_noise"]
    EDGE_WEIGHT = anim.get("edge_weight", 0.7)
    
    APPEAR = anim.get("logo_appearance_frames", 15)
    LOGO_HOLD = anim.get("logo_hold_frames", 25)
    DISSOLVE = anim.get("logo_dissolve_frames", 15)
    DISPERSE = anim.get("dispersion_frames", 25)
    FORM = anim.get("formation_frames", 35)
    FINAL = anim.get("final_hold_frames", 50)
    TOTAL = APPEAR + LOGO_HOLD + DISSOLVE + DISPERSE + FORM + FINAL
    
    rng = np.random.default_rng(SEED)
    margin = 32
    rw, rh = WW - 2 * margin, WH - 2 * margin
    
    logo_img = Image.open(LOGO_SRC).convert("L").resize((rw, rh), Image.LANCZOS)
    port_img = Image.open(PORTRAIT_SRC).convert("RGB").resize((rw, rh), Image.LANCZOS)
    port_gray = port_img.convert("L")
    
    # 1. Sample Portrait Pixels
    px, py, p_colors, p_edges = get_portrait_pixels(port_img, port_gray, PIXEL_SIZE, EDGE_WEIGHT, rng)
    N = len(px)
    print(f"Generated {N} structural pixels for portrait.")
    
    # 2. Sample Logo Pixels
    lx, ly = get_logo_pixels(logo_img, N, rng)
    
    lx += margin; ly += margin
    px += margin; py += margin
    
    lx, ly = map_points(px, py, lx, ly)
    
    primary_color = hex_to_rgb(anim["particle_color_primary"])
    l_colors = np.array([primary_color for _ in range(N)])
    
    # Disperse positions
    disp_x = px + rng.uniform(-60, 60, N)
    disp_y = py + rng.uniform(-60, 60, N)
    
    # Multi-scale particles based on edges
    r_min = PIXEL_SIZE * 0.5
    radii = np.full(N, r_min)
    
    # Slightly larger pixels in flat areas
    flat_mask = p_edges < 0.05
    radii[flat_mask] = r_min * 1.5
    
    # Occasional medium/large highlights
    med_idx = rng.choice(N, size=int(N * 0.08), replace=False)
    radii[med_idx] = r_min * 2.0
    large_idx = rng.choice(N, size=int(N * 0.02), replace=False)
    radii[large_idx] = r_min * 3.0
    
    opacities = rng.uniform(anim["particle_opacity_min"], anim["particle_opacity_max"], N)
    noise_ox = rng.uniform(0, 100, N)
    noise_oy = rng.uniform(0, 100, N)
    
    frames = []
    durations = []
    
    for fi in range(TOTAL):
        img = Image.new("RGB", (WW, WH), BG)
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
        elif fi < APPEAR + LOGO_HOLD + DISSOLVE:
            t = ease_in_out_cubic((fi - APPEAR - LOGO_HOLD) / max(DISSOLVE - 1, 1))
            # Start moving away slightly and fading to dispersion
            cur_x = lx + (disp_x - lx) * (t * 0.2)
            cur_y = ly + (disp_y - ly) * (t * 0.2)
            cur_c = l_colors
            alpha_mult = 1.0
        elif fi < APPEAR + LOGO_HOLD + DISSOLVE + DISPERSE:
            t = ease_in_out_cubic((fi - APPEAR - LOGO_HOLD - DISSOLVE) / max(DISPERSE - 1, 1))
            # Travel to dispersion points
            cur_x = lx + (disp_x - lx) * (0.2 + t * 0.8)
            cur_y = ly + (disp_y - ly) * (0.2 + t * 0.8)
            cur_c = l_colors + (p_colors - l_colors) * t
            alpha_mult = 1.0
        elif fi < APPEAR + LOGO_HOLD + DISSOLVE + DISPERSE + FORM:
            t = ease_in_out_cubic((fi - APPEAR - LOGO_HOLD - DISSOLVE - DISPERSE) / max(FORM - 1, 1))
            cur_x = disp_x + (px - disp_x) * t
            cur_y = disp_y + (py - disp_y) * t
            cur_c = p_colors
            alpha_mult = 1.0
        else:
            drift = (fi - APPEAR - LOGO_HOLD - DISSOLVE - DISPERSE - FORM) / max(FINAL, 1)
            ambient_mask = radii < r_min * 1.2
            cur_x = px.copy()
            cur_y = py.copy()
            cur_x[ambient_mask] = px[ambient_mask] + np.sin(drift * 4 + noise_ox[ambient_mask]) * NOISE
            cur_y[ambient_mask] = py[ambient_mask] + np.cos(drift * 4 + noise_oy[ambient_mask]) * NOISE
            cur_c = p_colors
            alpha_mult = 1.0
        
        # Add micro noise during transitions
        if APPEAR + LOGO_HOLD <= fi < APPEAR + LOGO_HOLD + DISSOLVE + DISPERSE + FORM:
            t_noise = np.sin(fi * 0.5 + noise_ox) * NOISE * 2.0
            cur_x = cur_x + t_noise
            cur_y = cur_y + np.cos(fi * 0.5 + noise_oy) * NOISE * 2.0
            
        # Draw particles as tiny squares for pixel-perfect look
        for i in range(N):
            alpha = int(opacities[i] * alpha_mult * 255)
            alpha = max(0, min(255, alpha))
            if alpha == 0:
                continue
            r = radii[i]
            x, y = cur_x[i], cur_y[i]
            c = cur_c[i]
            # Use rectangles to create a dense pixel grid
            draw.rectangle([x - r, y - r, x + r, y + r], fill=(int(c[0]), int(c[1]), int(c[2]), alpha))
        
        # Resize down to display size to increase perceived density
        if WW != DW or WH != DH:
            img = img.resize((DW, DH), Image.LANCZOS)
            
        img_q = img.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
        frames.append(img_q)
        
        if fi == TOTAL - 1:
            durations.append(2500)
        elif fi >= APPEAR + LOGO_HOLD + DISSOLVE + DISPERSE + FORM:
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
    print(f"     {len(frames)} frames, {size_kb:.0f} KB, {DW}x{DH}, {N} particles")
    
    return OUTPUT_PATH

if __name__ == "__main__":
    generate_portrait_animation()
