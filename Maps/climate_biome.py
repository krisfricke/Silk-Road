#!/usr/bin/env python3
"""
climate_biome.py — data-driven biome classifier for the Silk Road / Amber Road maps.
(Fadak, Amber Road step 2. Ends at the step-3 validation gate — Kris signs off before
anything repaints.)

Purpose
-------
Replaces the eyeballed "forest belt boxes" (the hand-tuned FB list in
master_biomes.py) with a classifier derived from real climate rasters:

    BIO1  = mean annual temperature   (deg C)    Maps/Climate Information/bio1_meantemp_SilkRoad.tif
    BIO12 = annual precipitation      (mm/yr)     Maps/Climate Information/bio12_precip_SilkRoad.tif

Both cover [-5,125]E x [20,65]N at 10 arc-minutes (780x270, ~18 km cells) — the whole
game master [8,123]x[24,52] and the Amber band [5,42]x[52,62] sit inside with margin.

Method  (the sunset-push "method 3" ruling)
-------------------------------------------
    De Martonne aridity index      I = P / (T + 10)
    + absolute precipitation floors (keep cold-DRY country out of the forest classes,
      which a bare De Martonne over-credits because a low T inflates the index)
    + a cold TREELINE limit on temperature (forest -> taiga -> tundra going north/up).

Six classes: desert, steppe, forest-steppe, forest, taiga, tundra.
The FOREST-STEPPE class is an ECOTONE, never a hard line: it is rendered as a dithered
mosaic of steppe and forest, the forest fraction graded across the band (steppe-heavy on
the dry edge, forest-heavy on the humid edge).

Elevation note (from step-1 QA): 18 km cells are coarser than our relief, so mountain
microclimates are NOT in this data — alpine cooling stays the job of the DEM lapse-rate
logic already in the bake. This classifier gives the base climatic biome; the relief bake
layers elevation on top.

Standalone + reusable
---------------------
    demartonne(T, P)                 -> aridity index
    classify(T, P)                   -> integer class codes (see CODES)
    forest_fraction(T, P)            -> 0..1 forest probability, for dithering the ecotone
    sample_climate(w,e,s,n,W,H)      -> (T, P, ocean_mask) bilinearly sampled onto any grid
    classify_bbox(w,e,s,n,W,H)       -> (codes, T, P, ocean) for a bbox at any resolution
    render(codes, T, P, ocean, ...)  -> RGB ndarray (forest-steppe dithered)

CLI
    python climate_biome.py --panels   # step-3 validation panels (Ukraine / Kazakh / Scandinavia)
    python climate_biome.py --whole    # whole-domain overview, sanity check

Requires: rasterio, numpy, scipy, pillow
"""

import os, sys, argparse
import numpy as np
from scipy.ndimage import map_coordinates, gaussian_filter

HERE = os.path.dirname(os.path.abspath(__file__))
CLIM = os.path.join(HERE, "Climate Information")
BIO1 = os.path.join(CLIM, "bio1_meantemp_SilkRoad.tif")   # mean annual temp, deg C
BIO12 = os.path.join(CLIM, "bio12_precip_SilkRoad.tif")   # annual precip, mm/yr

# ----------------------------------------------------------------------------------------
# Class codes
# ----------------------------------------------------------------------------------------
OCEAN, DESERT, STEPPE, FSTEP, FOREST, TAIGA, TUNDRA = 0, 1, 2, 3, 4, 5, 6
CODES = {"ocean": OCEAN, "desert": DESERT, "steppe": STEPPE, "forest-steppe": FSTEP,
         "forest": FOREST, "taiga": TAIGA, "tundra": TUNDRA}
CODE_NAME = {v: k for k, v in CODES.items()}

# ----------------------------------------------------------------------------------------
# Thresholds  — ALL TUNABLE.  Defaults chosen to fit the step-1 ground-truth sites:
#   Baghdad 22.8C/153mm -> desert ;  S.Ukraine ~430mm/9.5C & Kazakh Astana ~320mm/3.5C -> steppe ;
#   Kharkiv ~530mm/8C -> forest-steppe ;  Stockholm 590/6.3 & Moscow ~700/4 -> forest ;
#   Lapland cold-wet -> taiga ;  Scandes high cold -> tundra.
# ----------------------------------------------------------------------------------------
# De Martonne index breakpoints
I_DESERT = 8.0     # I < 8              -> desert
I_STEPPE = 24.0    # 8  <= I < 24       -> steppe
I_FSTEP = 33.0     # 24 <= I < 33       -> forest-steppe (ecotone) ;  I >= 33 -> forest

# absolute precip floors (mm/yr) — a cold place can score a high index on little rain;
# these keep genuinely dry country in the dry classes.
P_DESERT = 150.0   # below this: desert regardless of index
P_STEPPE = 280.0   # below this: at most steppe
P_FOREST = 400.0   # RETIRED as a floor: cold boreal forest grows on 350-450mm; the index
                   # already credits cold. Kept only for reference / possible warm-zone reuse.

# temperature (treeline) limits, deg C — mean-annual proxies for the boreal/arctic limits
T_TAIGA = 3.0      # forest colder than this -> taiga (boreal conifer)
T_TUNDRA = -2.0    # would-be-treed but colder than this -> tundra (above the treeline)


# ----------------------------------------------------------------------------------------
# Core classification
# ----------------------------------------------------------------------------------------
def demartonne(T, P):
    """De Martonne aridity index I = P/(T+10). Denominator floored at 1 so very cold
    cells don't blow up or go negative (they are handled by the treeline limit anyway)."""
    T = np.asarray(T, np.float64)
    P = np.asarray(P, np.float64)
    return P / np.maximum(T + 10.0, 1.0)


def classify(T, P):
    """Return an integer class-code array. Ocean is NOT set here (no mask available);
    callers overlay OCEAN separately (classify_bbox does)."""
    T = np.asarray(T, np.float64)
    P = np.asarray(P, np.float64)
    I = demartonne(T, P)

    # Moisture ladder: start optimistic (forest) and demote. Each stricter test wins.
    code = np.full(T.shape, FOREST, np.uint8)
    code[(I < I_FSTEP)] = FSTEP
    code[(I < I_STEPPE) | (P < P_STEPPE)] = STEPPE
    code[(I < I_DESERT) | (P < P_DESERT)] = DESERT

    # Cold overlay (treeline). Only classes that WOULD carry trees can become tundra;
    # cold-dry steppe/desert stay as they are (cold steppe, cold/polar desert).
    treed = (code == FOREST) | (code == FSTEP)
    code[treed & (T < T_TUNDRA)] = TUNDRA
    code[(code == FOREST) & (T < T_TAIGA)] = TAIGA
    return code


def forest_fraction(T, P):
    """Continuous 0..1 forest probability used to dither the forest-steppe ecotone:
    0 at the steppe edge of the band, 1 at the forest edge. (Meaningful mainly inside FSTEP.)"""
    I = demartonne(T, P)
    f = (I - I_STEPPE) / (I_FSTEP - I_STEPPE)
    return np.clip(f, 0.0, 1.0)


# ----------------------------------------------------------------------------------------
# Raster sampling (bilinear onto an arbitrary lon/lat grid)
# ----------------------------------------------------------------------------------------
_CACHE = {}


def _load():
    """Load the two rasters once. Returns (T, P, bounds) with nodata -> NaN.
    bounds = (W, E, S, N, ncols, nrows)."""
    if "T" not in _CACHE:
        import rasterio
        with rasterio.open(BIO1) as s:
            T = s.read(1).astype(np.float32)
            b = s.bounds
            bounds = (b.left, b.right, b.bottom, b.top, s.width, s.height)
        with rasterio.open(BIO12) as s:
            P = s.read(1).astype(np.float32)
        # WorldClim ocean nodata is a large negative sentinel (~-3.4e38)
        T[T < -1e30] = np.nan
        P[P < -1e30] = np.nan
        _CACHE.update(T=T, P=P, bounds=bounds)
    return _CACHE["T"], _CACHE["P"], _CACHE["bounds"]


def sample_climate(w, e, s, n, W, H):
    """Bilinearly sample (T, P) onto a W x H grid spanning lon [w,e], lat [s,n]
    (north at row 0). Returns (T_grid, P_grid, ocean_mask)."""
    T, P, (BW, BE, BS, BN, SW, SH) = _load()
    res_x = (BE - BW) / SW
    res_y = (BN - BS) / SH
    lons = np.linspace(w, e, W)
    lats = np.linspace(n, s, H)                 # row 0 = north
    cc = (lons - BW) / res_x - 0.5              # fractional source columns (pixel centres)
    rr = (BN - lats) / res_y - 0.5              # fractional source rows
    CC, RR = np.meshgrid(cc, rr)

    valid = np.isfinite(T).astype(np.float32)
    Tn = np.nan_to_num(T, nan=0.0)
    Pn = np.nan_to_num(P, nan=0.0)
    Ts = map_coordinates(Tn, [RR, CC], order=1, mode="nearest")
    Ps = map_coordinates(Pn, [RR, CC], order=1, mode="nearest")
    Vs = map_coordinates(valid, [RR, CC], order=1, mode="nearest")
    ocean = Vs < 0.5
    return Ts, Ps, ocean


def classify_bbox(w, e, s, n, W, H):
    """Classify a bbox at an arbitrary output resolution. Returns (codes, T, P, ocean).
    This is the reusable hook for the master ecotone repaint and the Amber-band bake."""
    T, P, ocean = sample_climate(w, e, s, n, W, H)
    codes = classify(T, P)
    codes[ocean] = OCEAN
    return codes, T, P, ocean


# ----------------------------------------------------------------------------------------
# Rendering  (forest-steppe dithered as a mosaic)
# ----------------------------------------------------------------------------------------
# Diagnostic legend palette. FOREST/TAIGA match the game bake (master_biomes.py:
# broadleaf [78,108,50], conifer [48,82,52]); the rest are readable biome tones. Final
# integration paints these over the relief base rather than as flat fills.
PALETTE = {
    OCEAN:  (150, 170, 188),
    DESERT: (222, 206, 160),
    STEPPE: (198, 184, 118),
    FSTEP:  (150, 160, 92),    # only shown if a FSTEP pixel is left un-dithered
    FOREST: (78, 108, 50),
    TAIGA:  (48, 82, 52),
    TUNDRA: (166, 158, 146),
}


def _smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def render(codes, T, P, ocean, seed=7, dither_sigma=1.1):
    """Render class codes to an RGB image, dithering the forest-steppe ecotone into a
    steppe/forest mosaic whose forest fraction follows forest_fraction()."""
    H, Wd = codes.shape
    img = np.zeros((H, Wd, 3), np.uint8)
    for c, col in PALETTE.items():
        img[codes == c] = col

    mask = codes == FSTEP
    if mask.any():
        rng = np.random.default_rng(seed)
        noise = gaussian_filter(rng.random((H, Wd)).astype(np.float32), dither_sigma)
        noise = (noise - noise.min()) / (np.ptp(noise) + 1e-9)   # clumps ~dither_sigma wide
        p = _smoothstep(forest_fraction(T, P))                   # forest probability
        forest_here = mask & (noise < p)
        steppe_here = mask & ~forest_here
        # the forest half of the mosaic goes conifer where it is cold enough for taiga
        cold = (np.asarray(T) < T_TAIGA)
        img[forest_here & cold] = PALETTE[TAIGA]
        img[forest_here & ~cold] = PALETTE[FOREST]
        img[steppe_here] = PALETTE[STEPPE]

    img[ocean] = PALETTE[OCEAN]
    return img


# ----------------------------------------------------------------------------------------
# Validation panels (step 3)
# ----------------------------------------------------------------------------------------
# Reference cities to orient the eye — dotted onto whichever panel contains them.
CITIES = {
    # Ukraine / Pontic ecotone
    "Kyiv": (30.52, 50.45), "Kharkiv": (36.23, 49.99), "Lviv": (24.03, 49.84),
    "Odesa": (30.73, 46.48), "Rostov": (39.72, 47.23), "Volgograd": (44.52, 48.72),
    "Voronezh": (39.20, 51.67),
    # Kazakh belt
    "Astana": (71.43, 51.17), "Almaty": (76.89, 43.24), "Aral": (61.67, 46.80),
    "Balkhash": (74.98, 46.84), "Orenburg": (55.10, 51.77), "Atyrau": (51.92, 47.10),
    "Karaganda": (73.10, 49.80),
    # Scandinavia / Baltic
    "Stockholm": (18.07, 59.33), "Uppsala": (17.64, 59.86), "Copenhagen": (12.57, 55.68),
    "Oslo": (10.75, 59.91), "Sundsvall": (17.31, 62.39), "Umea": (20.26, 63.83),
    "Helsinki": (24.94, 60.17), "Bergen": (5.32, 60.39), "Riga": (24.11, 56.95),
    "Gdansk": (18.65, 54.35),
}

PANELS = {
    "ukraine_ecotone": dict(
        bbox=(22, 44, 43, 54),
        title="Ukraine / Pontic ecotone  -  steppe -> forest-steppe -> forest  (south to north)"),
    "kazakh_belt": dict(
        bbox=(48, 82, 40, 54),
        title="Kazakh belt  -  desert -> semi-desert -> steppe  (a dry gradient)"),
    "scandinavia_taiga": dict(
        bbox=(5, 32, 54, 65),
        title="Scandinavia / Baltic  -  temperate forest -> taiga -> tundra  (south to north)"),
}

PPD = 34   # output pixels per degree for the panels


def _draw_panels(which=None, outdir=None):
    from PIL import Image, ImageDraw, ImageFont
    outdir = outdir or HERE
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 13)
        fontb = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
        fonts = ImageFont.truetype("DejaVuSans.ttf", 11)
    except Exception:
        font = fontb = fonts = ImageFont.load_default()

    legend_items = [(DESERT, "desert"), (STEPPE, "steppe"), (FSTEP, "forest-steppe (dithered)"),
                    (FOREST, "forest"), (TAIGA, "taiga"), (TUNDRA, "tundra"), (OCEAN, "sea")]
    out_paths = []
    names = [which] if which else list(PANELS.keys())
    for name in names:
        spec = PANELS[name]
        w, e, s, n = spec["bbox"]
        W = int(round((e - w) * PPD))
        H = int(round((n - s) * PPD))
        codes, T, P, ocean = classify_bbox(w, e, s, n, W, H)
        rgb = render(codes, T, P, ocean)

        TITLE_H, LEG_H, PAD = 30, 34, 10
        canvas = Image.new("RGB", (W + 2 * PAD, H + TITLE_H + LEG_H + 2 * PAD), (250, 248, 242))
        canvas.paste(Image.fromarray(rgb), (PAD, TITLE_H))
        d = ImageDraw.Draw(canvas)
        d.text((PAD, 8), spec["title"], fill=(30, 30, 30), font=fontb)

        def px(lon, lat):
            return PAD + (lon - w) / (e - w) * W, TITLE_H + (n - lat) / (n - s) * H
        for lon in range(int(np.ceil(w / 5) * 5), int(e) + 1, 5):
            x = PAD + (lon - w) / (e - w) * W
            d.line([(x, TITLE_H), (x, TITLE_H + H)], fill=(255, 255, 255), width=1)
            d.text((x + 2, TITLE_H + 2), f"{lon}E", fill=(90, 90, 90), font=fonts)
        for lat in range(int(np.ceil(s / 5) * 5), int(n) + 1, 5):
            y = TITLE_H + (n - lat) / (n - s) * H
            d.line([(PAD, y), (PAD + W, y)], fill=(255, 255, 255), width=1)
            d.text((PAD + 2, y + 1), f"{lat}N", fill=(90, 90, 90), font=fonts)
        for cname, (lon, lat) in CITIES.items():
            if w <= lon <= e and s <= lat <= n:
                x, y = px(lon, lat)
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(20, 20, 20), outline=(255, 255, 255))
                d.text((x + 5, y - 7), cname, fill=(15, 15, 15), font=font)

        lx, ly = PAD, TITLE_H + H + 8
        for code, label in legend_items:
            d.rectangle([lx, ly, lx + 16, ly + 16], fill=PALETTE[code], outline=(60, 60, 60))
            d.text((lx + 20, ly + 1), label, fill=(30, 30, 30), font=font)
            lx += 24 + int(d.textlength(label, font=font)) + 16

        outp = os.path.join(outdir, f"_climate_panel_{name}.png")
        canvas.save(outp)
        out_paths.append(outp)
        land = ~ocean
        tot = max(1, int(land.sum()))
        mix = {CODE_NAME[c]: round(100 * int(((codes == c) & land).sum()) / tot, 1)
               for c in (DESERT, STEPPE, FSTEP, FOREST, TAIGA, TUNDRA)}
        print(f"{name}: {W}x{H}px  land-class mix % -> {mix}")
        print(f"  saved {outp}")
    return out_paths


def _draw_whole(outdir=None):
    from PIL import Image
    outdir = outdir or HERE
    w, e, s, n = -5, 125, 20, 65
    W = int(round((e - w) * 6))
    H = int(round((n - s) * 6))
    codes, T, P, ocean = classify_bbox(w, e, s, n, W, H)
    rgb = render(codes, T, P, ocean)
    outp = os.path.join(outdir, "_climate_whole_domain.png")
    Image.fromarray(rgb).save(outp)
    print(f"whole domain {W}x{H}px saved {outp}")
    return [outp]


def main():
    ap = argparse.ArgumentParser(description="Silk Road / Amber Road climate biome classifier")
    ap.add_argument("--panels", action="store_true", help="render the 3 step-3 validation panels")
    ap.add_argument("--whole", action="store_true", help="render a whole-domain overview")
    ap.add_argument("--panel", help="render a single named panel: " + ", ".join(PANELS))
    ap.add_argument("--outdir", default=HERE)
    args = ap.parse_args()
    if args.panel:
        _draw_panels(which=args.panel, outdir=args.outdir)
    if args.panels:
        _draw_panels(outdir=args.outdir)
    if args.whole:
        _draw_whole(outdir=args.outdir)
    if not (args.panels or args.whole or args.panel):
        ap.print_help()


if __name__ == "__main__":
    main()
