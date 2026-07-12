#!/usr/bin/env python3
"""
master_ecotone.py  (Fadak, Amber Road step 4)
Repaint the biome (forest / taiga / dithered forest-steppe) layer of the existing master
strips from the climate classifier, replacing the eyeballed FB forest boxes. Rivers baked
into the current strip are preserved exactly (copied back), so no flow recompute is needed.

Per strip i (bounds from manifest):
  new = relief_base + classifier_forest ; then restore river pixels from the current strip.

Usage:
  python master_ecotone.py --strip 2 --preview      # writes previews, does NOT overwrite
  python master_ecotone.py --strip 2 --commit       # backs up strip_02.png -> _pre_ecotone, overwrites
  python master_ecotone.py --strips 1,2,3,4,5 --commit
"""
import os, sys, json, argparse
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
import climate_biome as cb

HERE = os.path.dirname(os.path.abspath(__file__))
MST = os.path.join(HERE, "master1271")
MAN = json.load(open(os.path.join(MST, "manifest.json")))
MW, ME, MS, MN = MAN["bounds"]
STEP = MAN["step"]; N = MAN["n"]

COL_BROAD = np.array([78, 108, 50], np.float32)   # matches master_biomes.py
COL_CONIF = np.array([48, 82, 52], np.float32)


def _smooth(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def build_strip(i, seed=7):
    W = MW + i * STEP; E = MW + (i + 1) * STEP
    relief = np.array(Image.open(os.path.join(MST, "strip_%02d_relief.png" % i)).convert("RGB")).astype(np.float32)
    cur = np.array(Image.open(os.path.join(MST, "strip_%02d.png" % i)).convert("RGB")).astype(np.float32)
    H, Wpx = relief.shape[:2]

    codes, T, P, ocean = cb.classify_bbox(W, E, MS, MN, Wpx, H)

    # Forest ALPHA from the classifier. Solid forest/taiga -> near-uniform dense green
    # (A_FOR calibrated to the established master: G-R lift ~+24). Forest-STEPPE -> a
    # dithered mosaic whose forest fraction follows forest_fraction() (the ecotone).
    A_FOR = 0.62
    rng = np.random.default_rng(seed)
    pres = np.zeros((H, Wpx), np.float32)
    pres[(codes == cb.FOREST) | (codes == cb.TAIGA)] = 1.0
    mfs = codes == cb.FSTEP
    if mfs.any():
        ff = _smooth(cb.forest_fraction(T, P))
        mnoise = gaussian_filter(rng.random((H, Wpx)).astype(np.float32), 2.2)
        mnoise = (mnoise - mnoise.min()) / (np.ptp(mnoise) + 1e-9)
        pres[mfs & (mnoise < ff)] = 1.0                       # dithered ecotone mosaic
    pres = gaussian_filter(pres, 1.6)                          # soften climate-cell blocks & mosaic
    blotch = gaussian_filter(rng.random((H, Wpx)).astype(np.float32), 4)
    blotch = (blotch - blotch.min()) / (np.ptp(blotch) + 1e-9)
    pres = pres * A_FOR * (0.85 + 0.15 * blotch)              # dense but gently textured

    # only paint on vegetable land: not sea, not snow/ice, not classifier ocean
    water = relief[:, :, 2] > relief[:, :, 0] + 8            # blue-dominant = water in relief
    snow = relief.min(2) > 195                                # bright = snow/ice/glacier
    paintable = (~water) & (~snow) & (~ocean)
    pres *= paintable

    conif = (codes == cb.TAIGA)[:, :, None]
    col = np.where(conif, COL_CONIF, COL_BROAD)
    fm = pres[:, :, None]
    out = relief * (1 - fm) + col * fm

    # restore rivers exactly as baked: pixels the current strip painted bluer than relief
    bluer = cur[:, :, 2] - relief[:, :, 2]
    greener = cur[:, :, 1] - relief[:, :, 1]
    river = (bluer > 4) & (bluer >= greener)
    out[river] = cur[river]

    out = np.clip(out + rng.normal(0, 1.2, (H, Wpx, 1)), 0, 255)
    return out.astype(np.uint8), relief.astype(np.uint8), cur.astype(np.uint8), codes, ocean


def preview(i):
    out, relief, cur, codes, ocean = build_strip(i)
    H, Wpx = out.shape[:2]
    # (a) full strip, before vs after, downscaled
    scale = 900.0 / Wpx
    sz = (int(Wpx * scale), int(H * scale))
    b = Image.fromarray(cur).resize(sz); a = Image.fromarray(out).resize(sz)
    comp = Image.new("RGB", (sz[0], sz[1] * 2 + 10), (255, 255, 255))
    comp.paste(b, (0, 0)); comp.paste(a, (0, sz[1] + 10))
    p1 = os.path.join(HERE, "_ecotone_strip%02d_fullcompare.png" % i)
    comp.save(p1)
    # (b) northern belt crop (lat 45-52 -> top 25% of strip), before/after
    band = int(H * 0.25)
    bc = Image.fromarray(cur[:band]); ac = Image.fromarray(out[:band])
    sc = 1400.0 / Wpx
    bcz = bc.resize((int(Wpx * sc), int(band * sc))); acz = ac.resize((int(Wpx * sc), int(band * sc)))
    comp2 = Image.new("RGB", (bcz.size[0], bcz.size[1] * 2 + 8), (255, 255, 255))
    comp2.paste(bcz, (0, 0)); comp2.paste(acz, (0, bcz.size[1] + 8))
    p2 = os.path.join(HERE, "_ecotone_strip%02d_beltcompare.png" % i)
    comp2.save(p2)
    # change stat
    land = ~ocean
    fnow = ((np.array(Image.fromarray(cur)).astype(int)[:, :, 1] - np.array(Image.fromarray(relief)).astype(int)[:, :, 1]) > 3)
    print("strip %02d: %dx%d  preview -> %s , %s" % (i, Wpx, H, os.path.basename(p1), os.path.basename(p2)))
    return p1, p2


def commit(i):
    out, relief, cur, codes, ocean = build_strip(i)
    src = os.path.join(MST, "strip_%02d.png" % i)
    bak = os.path.join(MST, "strip_%02d_pre_ecotone.png" % i)
    if not os.path.exists(bak):
        Image.fromarray(cur).save(bak)
    Image.fromarray(out).save(src)
    print("strip %02d committed (backup %s)" % (i, os.path.basename(bak)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strip", type=int)
    ap.add_argument("--strips", help="comma list e.g. 1,2,3,4,5")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--commit", action="store_true")
    a = ap.parse_args()
    idxs = []
    if a.strip is not None: idxs = [a.strip]
    if a.strips: idxs = [int(x) for x in a.strips.split(",")]
    for i in idxs:
        if a.preview: preview(i)
        if a.commit: commit(i)


if __name__ == "__main__":
    main()
