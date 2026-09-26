# 真上から見下ろしたダンジョン用のタイルセット（アルベド＋ノーマルマップ）を生成する
# 使い方: pip install numpy scipy pillow && python3 Tools/Sprites/dungeon_tileset.py Assets/Sprite/Maps [preview.png]
# 出力: DungeonTileset.png（アルベド）と DungeonTileset_Normal.png（タンジェント空間ノーマルマップ、Y+ が上）
#       .meta がまだなければ、128px ごとに切り分けてノーマルマップを _NormalMap に設定した .meta も書き出す。
# 高さマップを先に作り、そこからアルベドの陰影（AO）とノーマルマップの両方を作る。
# 各タイルの周りには PAD px ずつ端の色を引き延ばした余白があり、バイリニア補間で隣のタイルがにじまない。
import hashlib
import os
import struct
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

T = 128          # タイルの大きさ (px) = PPU 128 で 1 ユニット
COLS, ROWS = 8, 4
PAD = 2          # タイルの周りの余白 (px)
CELL = T + PAD * 2
SEED = 20260926

yy, xx = np.mgrid[0:T, 0:T].astype(np.float64) + 0.5   # ピクセル中心の座標（y は下向き = 南）


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def noise(rng, scale):
    """タイルの端でループするノイズ（FFT で白色ノイズをぼかす）。平均 0、標準偏差 1。"""
    f = np.fft.fftfreq(T)
    fr = np.sqrt(f[None, :] ** 2 + f[:, None] ** 2)
    spec = np.fft.fft2(rng.standard_normal((T, T))) * np.exp(-(fr * scale) ** 2)
    n = np.real(np.fft.ifft2(spec))
    return (n - n.mean()) / (n.std() + 1e-9)


def fbm(rng, scales=(24, 10, 4, 1.5), weights=(1, 0.5, 0.25, 0.12)):
    return sum(w * noise(rng, s) for s, w in zip(scales, weights))


def mix(a, b, t):
    t = np.asarray(t)[..., None] if np.ndim(t) else t
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


# ---------------------------------------------------------------- 床

SLAB_LAYOUTS = [
    [(0, 0, 64, 64), (64, 0, 64, 64), (0, 64, 64, 64), (64, 64, 64, 64)],
    [(0, 0, 128, 64), (0, 64, 64, 64), (64, 64, 64, 64)],
    [(0, 0, 64, 128), (64, 0, 64, 64), (64, 64, 64, 64)],
    [(0, 0, 64, 64), (64, 0, 64, 128), (0, 64, 64, 64)],
]


def slabs(rng, layout=0, top=4.0, tilt=0.8):
    """板石の床。タイルの端は必ず目地になるので、どの床タイルとも継ぎ目が合う。"""
    rects = SLAB_LAYOUTS[layout]
    idx = np.zeros((T, T), int)
    d = np.zeros((T, T))
    u = np.zeros((T, T))
    v = np.zeros((T, T))
    for i, (x0, y0, w, h) in enumerate(rects):
        m = (xx >= x0) & (xx < x0 + w) & (yy >= y0) & (yy < y0 + h)
        idx[m] = i
        u[m], v[m] = (xx[m] - x0 - w / 2) / 64, (yy[m] - y0 - h / 2) / 64
        d[m] = np.minimum.reduce([xx[m] - x0, yy[m] - y0, x0 + w - xx[m], y0 + h - yy[m]])
    d = d + noise(rng, 3) * 1.1          # 縁の欠け
    edge = smoothstep(0.6, 5.0, d)
    n = len(rects)
    off, ax, ay = rng.uniform(-0.6, 0.6, n), rng.uniform(-tilt, tilt, n), rng.uniform(-tilt, tilt, n)
    tone = rng.uniform(-0.06, 0.06, n)
    surf = top + off[idx] + ax[idx] * u + ay[idx] * v + fbm(rng) * 0.45
    h = edge * surf + noise(rng, 1.2) * 0.25
    base = np.array([122, 115, 106]) / 255
    grout = np.array([74, 69, 63]) / 255
    col = base * (1 + tone[idx] + 0.06 * fbm(rng, (16, 5, 1.5), (1, 0.5, 0.3)))[..., None]
    col = mix(grout, col, edge)
    return h, col, edge


def carve_cracks(rng, h, col, mask, count=3):
    for _ in range(count):
        p = rng.uniform(10, T - 10, 2)
        a = rng.uniform(0, 2 * np.pi)
        pts = [p.copy()]
        for _ in range(rng.integers(8, 16)):
            a += rng.normal(0, 0.5)
            p = p + 4 * np.array([np.cos(a), np.sin(a)])
            pts.append(p.copy())
        dist = np.full((T, T), 1e9)
        for q0, q1 in zip(pts[:-1], pts[1:]):
            dq = q1 - q0
            t = np.clip(((xx - q0[0]) * dq[0] + (yy - q0[1]) * dq[1]) / (dq @ dq), 0, 1)
            dist = np.minimum(dist, np.hypot(xx - q0[0] - t * dq[0], yy - q0[1] - t * dq[1]))
        c = (1 - smoothstep(0.3, 1.6, dist)) * mask
        h -= c * 2.5
        col *= (1 - 0.45 * c)[..., None]


def floor_slab(layout):
    def make(rng):
        h, col, _ = slabs(rng, layout)
        return h, col
    return make


def floor_cracked(rng):
    h, col, edge = slabs(rng)
    carve_cracks(rng, h, col, edge, count=4)
    return h, col


def floor_rubble(rng):
    h, col, _ = slabs(rng)
    for _ in range(14):
        cx, cy = rng.uniform(0, T, 2)
        r = rng.uniform(3, 8)
        dx = (xx - cx + T / 2) % T - T / 2   # 端をまたいでもループさせる
        dy = (yy - cy + T / 2) % T - T / 2
        dd = np.hypot(dx * rng.uniform(0.8, 1.2), dy)
        bump = np.sqrt(np.clip(1 - (dd / r) ** 2, 0, 1))
        top = 4.5 + r * 0.5
        h = np.maximum(h, bump * top)
        stone = np.array([105, 99, 92]) / 255 * rng.uniform(0.8, 1.15)
        col = mix(col, stone, (bump > 0.05).astype(float) * (0.6 + 0.4 * bump))
    return h, col


def floor_moss(rng):
    h, col, edge = slabs(rng)
    m = smoothstep(0.1, 0.9, fbm(rng, (20, 8, 3), (1, 0.5, 0.25)) + (1 - edge) * 0.8)
    moss = np.array([64, 88, 46]) / 255 * (1 + 0.15 * noise(rng, 2))[..., None]
    col = mix(col, moss, m * 0.9)
    h = h + m * noise(rng, 1.5) * 0.4 + m * 0.6
    return h, col


def floor_cobble(rng, n=16):
    pts = rng.uniform(0, T, (n, 2))
    d1 = np.full((T, T), 1e9)
    d2 = np.full((T, T), 1e9)
    near = np.zeros((T, T), int)
    for i, (px, py) in enumerate(pts):
        for ox in (-T, 0, T):
            for oy in (-T, 0, T):
                d = np.hypot(xx - px - ox, yy - py - oy)
                closer = d < d1
                d2 = np.where(closer, d1, np.minimum(d2, d))
                near = np.where(closer, i, near)
                d1 = np.where(closer, d, d1)
    e = d2 - d1 + noise(rng, 2.5) * 1.2
    dome = np.sqrt(np.clip(e / 14, 0, 1))
    h = dome * 5 + fbm(rng) * 0.35 * dome
    tone = rng.uniform(-0.12, 0.12, n)
    stone = np.array([112, 106, 98]) / 255 * (1 + tone[near] + 0.05 * fbm(rng, (12, 4, 1.5), (1, 0.5, 0.3)))[..., None]
    col = mix(np.array([52, 48, 44]) / 255, stone, smoothstep(0.5, 3.0, e))
    return h, col


# ---------------------------------------------------------------- 壁

WALL_H = 18.0     # 壁の上面の高さ
BEVEL = 22.0      # 壁の縁の斜面の幅 (px)


def wall_top(seed):
    """壁の上面（石組み）。すべての壁タイルで同じものを使い、タイルをまたいで模様をつなげる。"""
    rng = np.random.default_rng(seed)
    bh, bw = 32, 64
    row = (yy // bh).astype(int)
    u = (xx + (row % 2) * bw / 2) % bw
    v = yy % bh
    d = np.minimum(np.minimum(u, v), np.minimum(bw - u, bh - v)) + noise(rng, 2.5) * 1.3
    edge = smoothstep(1.0, 5.0, d)
    bid = row * 4 + ((xx + (row % 2) * bw / 2) // bw).astype(int) % 2
    off = rng.uniform(-0.8, 0.8, 32)
    tone = rng.uniform(-0.07, 0.07, 32)
    h = WALL_H - 3 + edge * (3 + off[bid] + fbm(rng) * 0.5)
    col = np.array([96, 90, 98]) / 255 * (1 + tone[bid] + 0.07 * fbm(rng, (14, 5, 1.5), (1, 0.5, 0.3)))[..., None]
    col = mix(np.array([44, 40, 46]) / 255, col, edge)
    face = np.array([86, 80, 88]) / 255 * (1 + 0.08 * fbm(rng, (5, 1.5), (1, 0.5)))[..., None]
    rough = fbm(rng, (10, 4, 1.5), (1, 0.4, 0.15))
    return h, col, face, rough


WALL = wall_top(SEED + 999)

# 壁の縁までの距離。N/E/S/W は床がある側。
DN, DS, DW, DE = yy, T - yy, xx, T - xx
BIG = np.full((T, T), 1e9)


def wall_tile(dist):
    top_h, top_col, face_col, rough = WALL
    t = smoothstep(0.0, BEVEL, dist + rough * 1.5)
    h = top_h * t + rough * 3.0 * t * (1 - t)   # 斜面はごつごつさせる
    col = mix(face_col, top_col, smoothstep(0.75, 1.0, t))
    col *= (0.7 + 0.3 * t)[..., None]   # 下の方ほど暗く
    return h, col


def outer(*sides):
    return lambda: wall_tile(np.minimum.reduce([*sides, BIG]))


def inner(a, b):
    return lambda: wall_tile(np.maximum(a, b))


# ---------------------------------------------------------------- その他

def stairs_down(rng):
    """南に向かって下りる階段。両側に縁石がある。"""
    steps = 6
    sh = T / steps
    k = np.floor(yy / sh)
    lip = smoothstep(sh - 3, sh, yy % sh)          # 段鼻の丸み
    h = -(k * 5 + lip * 5) + fbm(rng, (8, 2), (1, 0.5)) * 0.3
    col = np.array([108, 102, 94]) / 255 * (1 - (k / steps) * 0.75 - lip * 0.3)[..., None]
    side = np.minimum(xx, T - xx)
    curb = smoothstep(14, 10, side)
    h = h * (1 - curb) + (3.0 + noise(rng, 2) * 0.3) * curb
    col = mix(col, np.array([90, 84, 78]) / 255, curb)
    return h, col


def pit(rng):
    h, col, _ = slabs(rng)
    cx = cy = T / 2
    d = np.maximum(np.abs(xx - cx), np.abs(yy - cy)) + noise(rng, 3) * 1.5
    r = 46
    rim = smoothstep(r + 4, r - 10, d)           # 0: 床, 1: 穴の中
    depth = -30 * smoothstep(r + 2, r - 26, d)
    h = h * (1 - rim) + depth * rim
    col = mix(col, np.array([14, 12, 16]) / 255 * (1 + 3 * smoothstep(r - 20, r, d))[..., None], rim)
    return h, col


def grate(rng):
    h, col, _ = slabs(rng)
    cx = cy = T / 2
    d = np.maximum(np.abs(xx - cx), np.abs(yy - cy))
    inside = d < 36
    frame = (d >= 30) & inside
    bars = ((np.abs((xx - cx) % 12 - 6) > 3.5) | (np.abs((yy - cy) % 12 - 6) > 3.5)) & (d < 30)
    iron = np.array([66, 56, 50]) / 255 * (1 + 0.25 * fbm(rng, (6, 2), (1, 0.6)))[..., None]
    rust = np.array([112, 62, 34]) / 255
    iron = mix(iron, rust, smoothstep(0.4, 1.4, noise(rng, 5)) * 0.6)
    h = np.where(inside, -12.0, h)
    col = np.where(inside[..., None], np.array([10, 9, 10]) / 255, col)
    metal = frame | bars
    h = np.where(metal, 3.0 + noise(rng, 1.5) * 0.2, h)
    col = np.where(metal[..., None], iron, col)
    return h, col


# ---------------------------------------------------------------- 配置

LAYOUT = [
    # 1 行目: 床
    [("Floor_Slab_0", floor_slab(0)), ("Floor_Slab_1", floor_slab(1)), ("Floor_Slab_2", floor_slab(2)),
     ("Floor_Slab_3", floor_slab(3)), ("Floor_Cracked", floor_cracked), ("Floor_Rubble", floor_rubble),
     ("Floor_Moss", floor_moss), ("Floor_Cobble", floor_cobble)],
    # 2〜4 行目の左 3 列: 壁の塊（3x3 で並べると島になる）。4〜5 列目: 内側の角。
    [("Wall_Outer_NW", outer(DN, DW)), ("Wall_Edge_N", outer(DN)), ("Wall_Outer_NE", outer(DN, DE)),
     ("Wall_Inner_NW", inner(DN, DW)), ("Wall_Inner_NE", inner(DN, DE)),
     ("Wall_Pillar", outer(DN, DS, DW, DE)), ("Wall_Thin_H", outer(DN, DS)), ("Stairs_Down", stairs_down)],
    [("Wall_Edge_W", outer(DW)), ("Wall_Fill", outer()), ("Wall_Edge_E", outer(DE)),
     ("Wall_Inner_SW", inner(DS, DW)), ("Wall_Inner_SE", inner(DS, DE)),
     ("Wall_End_N", outer(DN, DW, DE)), ("Wall_Thin_V", outer(DW, DE)), ("Pit", pit)],
    [("Wall_Outer_SW", outer(DS, DW)), ("Wall_Edge_S", outer(DS)), ("Wall_Outer_SE", outer(DS, DE)),
     ("Wall_End_W", outer(DN, DS, DW)), ("Wall_End_E", outer(DN, DS, DE)),
     ("Wall_End_S", outer(DS, DW, DE)), ("Grate", grate), (None, None)],
]
FLOOR_LIKE = {"Floor_Slab_0", "Floor_Slab_1", "Floor_Slab_2", "Floor_Slab_3",
              "Floor_Cracked", "Floor_Rubble", "Floor_Moss", "Floor_Cobble"}


def normals(h, wrap):
    mode = "wrap" if wrap else "nearest"
    dx = ndimage.sobel(h, axis=1, mode=mode) / 8
    dy = ndimage.sobel(h, axis=0, mode=mode) / 8     # 画像の下向き
    # Unity のノーマルマップは Y+ が上。画像の y は下向きなので符号が逆になる。
    n = np.dstack([-dx, dy, np.ones_like(h)])
    return n / np.linalg.norm(n, axis=2, keepdims=True)


def ambient_occlusion(h, wrap):
    blur = ndimage.gaussian_filter(h, 5, mode="wrap" if wrap else "nearest")
    return np.clip(1 - (blur - h) * 0.05, 0.6, 1.0)


def build():
    """{名前: (行, 列, アルベド RGB, ノーマル RGB)} を返す。"""
    tiles = {}
    for r, row in enumerate(LAYOUT):
        for c, (name, fn) in enumerate(row):
            if name is None:
                continue
            rng = np.random.default_rng(SEED + r * COLS + c)
            h, col = fn(rng) if fn.__code__.co_argcount else fn()
            wrap = name in FLOOR_LIKE
            col = np.clip(col * ambient_occlusion(h, wrap)[..., None], 0, 1)
            tiles[name] = (r, c, col, normals(h, wrap) * 0.5 + 0.5)
    return tiles


def pack(tiles, index):
    sheet = np.zeros((ROWS * CELL, COLS * CELL, 4))
    sheet[..., :] = (0, 0, 0, 0) if index == 2 else (0.5, 0.5, 1.0, 1.0)
    for r, c, *images in tiles.values():
        img = np.pad(images[index - 2], ((PAD, PAD), (PAD, PAD), (0, 0)), mode="edge")
        sheet[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL, :3] = img
        sheet[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL, 3] = 1
    return Image.fromarray((sheet * 255 + 0.5).astype(np.uint8))


def lit_preview(tiles, path):
    """タイルを並べた小さな部屋に点光源を当てたプレビュー（確認用）。"""
    M = [
        "NW N  N  N  N  N  N  NE",
        "W  F  F  F  F  F  F  E",
        "W  F  F  F  C  F  F  E",
        "W  F  R  P  F  F  S  E",
        "W  F  F  F  F  M  F  E",
        "W  K  F  F  G  F  F  E",
        "SW S  S  S  S  S  S  SE",
    ]
    key = {"F": "Floor_Slab_0", "C": "Floor_Cracked", "R": "Floor_Rubble", "M": "Floor_Moss",
           "K": "Floor_Cobble", "G": "Grate", "S": "Stairs_Down", "P": "Wall_Pillar",
           "N": "Wall_Edge_S", "E": "Wall_Edge_W", "W": "Wall_Edge_E", "NW": "Wall_Inner_SE",
           "NE": "Wall_Inner_SW", "SW": "Wall_Inner_NE", "SE": "Wall_Inner_NW"}
    grid = [row.split() for row in M]
    # 1 行目の S は「南側が壁」なので Wall_Edge_N に置き換える
    grid[-1] = ["Wall_Inner_NE"] + ["Wall_Edge_N"] * (len(grid[-1]) - 2) + ["Wall_Inner_NW"]
    floors = ["Floor_Slab_0", "Floor_Slab_1", "Floor_Slab_2", "Floor_Slab_3"]
    rng = np.random.default_rng(1)
    H, W = len(grid) * T, len(grid[0]) * T
    a = np.zeros((H, W, 3))
    n = np.zeros((H, W, 3))
    for gy, row in enumerate(grid):
        for gx, k in enumerate(row):
            name = key.get(k, k)
            if name == "Floor_Slab_0":
                name = floors[rng.integers(4)]
            _, _, a[gy * T:(gy + 1) * T, gx * T:(gx + 1) * T], n[gy * T:(gy + 1) * T, gx * T:(gx + 1) * T] = tiles[name]
    nv = n * 2 - 1
    nv[..., 1] *= -1                     # 画像座標（y 下向き）に戻す
    py, px = np.mgrid[0:H, 0:W] + 0.5
    out = np.zeros_like(a) + a * 0.12    # 環境光
    for lx, ly, col, rad in [(2.2 * T, 2.0 * T, (1.0, 0.75, 0.45), 4.5 * T),
                             (6.0 * T, 4.8 * T, (0.45, 0.6, 1.0), 3.5 * T)]:
        L = np.dstack([lx - px, ly - py, np.full_like(px, 1.2 * T)])
        dist = np.linalg.norm(L[..., :2], axis=2)
        L /= np.linalg.norm(L, axis=2, keepdims=True)
        diff = np.clip((nv * L).sum(2), 0, 1) * np.clip(1 - dist / rad, 0, 1) ** 2 * 2.6
        out += a * diff[..., None] * np.array(col)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(path)


# ---------------------------------------------------------------- .meta

def guid(name):
    return hashlib.md5(f"zenith/{name}".encode()).hexdigest()   # 何度生成し直しても同じ GUID になる


def file_id(name):
    return struct.unpack("<q", hashlib.md5(f"zenith/sprite/{name}".encode()).digest()[:8])[0]


def sprite_id(fid):
    # Unity がスライスしたスプライトと同じ形式（internalID のバイト列をニブル単位で入れ替えたもの）
    return "".join(f"{b:02x}"[::-1] for b in struct.pack("<q", fid)) + "0800000000000000"


PLATFORMS = ("DefaultTexturePlatform", "Standalone", "WebGL")


def texture_meta(g, texture_type, srgb, sprite_mode, sprites="    sprites: []\n", table="", secondary="[]", names="{}"):
    platforms = "".join(f"""  - serializedVersion: 4
    buildTarget: {p}
    maxTextureSize: 2048
    resizeAlgorithm: 0
    textureFormat: -1
    textureCompression: 1
    compressionQuality: 50
    crunchedCompression: 0
    allowsAlphaSplitting: 0
    overridden: 0
    ignorePlatformSupport: 0
    androidETC2FallbackOverride: 0
    forceMaximumCompressionQuality_BC6H_BC7: 0
""" for p in PLATFORMS)
    return f"""fileFormatVersion: 2
guid: {g}
TextureImporter:
  internalIDToNameTable:{table or " []"}
  externalObjects: {{}}
  serializedVersion: 13
  mipmaps:
    mipMapMode: 0
    enableMipMap: 0
    sRGBTexture: {srgb}
    linearTexture: 0
    fadeOut: 0
    borderMipMap: 0
    mipMapsPreserveCoverage: 0
    alphaTestReferenceValue: 0.5
    mipMapFadeDistanceStart: 1
    mipMapFadeDistanceEnd: 3
  bumpmap:
    convertToNormalMap: 0
    externalNormalMap: 0
    heightScale: 0.25
    normalMapFilter: 0
    flipGreenChannel: 0
  isReadable: 0
  streamingMipmaps: 0
  streamingMipmapsPriority: 0
  vTOnly: 0
  ignoreMipmapLimit: 0
  grayScaleToAlpha: 0
  generateCubemap: 6
  cubemapConvolution: 0
  seamlessCubemap: 0
  textureFormat: 1
  maxTextureSize: 2048
  textureSettings:
    serializedVersion: 2
    filterMode: 1
    aniso: 1
    mipBias: 0
    wrapU: 1
    wrapV: 1
    wrapW: 1
  nPOTScale: 0
  lightmap: 0
  compressionQuality: 50
  spriteMode: {sprite_mode}
  spriteExtrude: 1
  spriteMeshType: 0
  alignment: 0
  spritePivot: {{x: 0.5, y: 0.5}}
  spritePixelsToUnits: {T}
  spriteBorder: {{x: 0, y: 0, z: 0, w: 0}}
  spriteGenerateFallbackPhysicsShape: 1
  alphaUsage: 1
  alphaIsTransparency: {1 if sprite_mode else 0}
  spriteTessellationMethod: 0
  spriteTessellationDetail: -1
  spriteGeometrySubdivision: -1
  textureType: {texture_type}
  textureShape: 1
  singleChannelComponent: 0
  flipbookRows: 1
  flipbookColumns: 1
  maxTextureSizeSet: 0
  compressionQualitySet: 0
  textureFormatSet: 0
  ignorePngGamma: 0
  applyGammaDecoding: 0
  swizzle: 50462976
  cookieLightType: 0
  platformSettings:
{platforms}  spriteSheet:
    serializedVersion: 2
{sprites}    outline: []
    customData: 
    physicsShape: []
    bones: []
    spriteID: 
    internalID: 0
    vertices: []
    indices: 
    edges: []
    weights: []
    secondaryTextures: {secondary}
    spriteCustomMetadata:
      entries: []
    nameFileIdTable: {names}
  mipmapLimitGroupName: 
  pSDRemoveMatte: 0
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""


def write_metas(tiles, albedo_path, normal_path):
    if not os.path.exists(normal_path + ".meta"):
        with open(normal_path + ".meta", "w", encoding="utf-8", newline="\n") as f:
            f.write(texture_meta(guid("DungeonTileset_Normal"), texture_type=1, srgb=0, sprite_mode=0))
    if os.path.exists(albedo_path + ".meta"):
        return
    ordered = sorted(tiles.items(), key=lambda kv: (kv[1][0], kv[1][1]))
    sprites, table, names = "    sprites:\n", "", ""
    for name, (r, c, *_) in ordered:
        fid = file_id(name)
        sprites += f"""    - serializedVersion: 2
      name: {name}
      rect:
        serializedVersion: 2
        x: {c * CELL + PAD}
        y: {(ROWS - 1 - r) * CELL + PAD}
        width: {T}
        height: {T}
      alignment: 0
      pivot: {{x: 0.5, y: 0.5}}
      border: {{x: 0, y: 0, z: 0, w: 0}}
      customData: 
      outline: []
      physicsShape: []
      tessellationDetail: -1
      bones: []
      spriteID: {sprite_id(fid)}
      internalID: {fid}
      vertices: []
      indices: 
      edges: []
      weights: []
"""
        table += f"\n  - first:\n      213: {fid}\n    second: {name}"
    for name in sorted(tiles):
        names += f"\n      {name}: {file_id(name)}"
    secondary = f"\n    - name: _NormalMap\n      texture: {{fileID: 2800000, guid: {guid('DungeonTileset_Normal')}, type: 3}}"
    with open(albedo_path + ".meta", "w", encoding="utf-8", newline="\n") as f:
        f.write(texture_meta(guid("DungeonTileset"), texture_type=8, srgb=1, sprite_mode=2,
                             sprites=sprites, table=table, secondary=secondary, names=names))


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    tiles = build()
    albedo_path = os.path.join(out_dir, "DungeonTileset.png")
    normal_path = os.path.join(out_dir, "DungeonTileset_Normal.png")
    pack(tiles, 2).save(albedo_path)
    pack(tiles, 3).save(normal_path)
    write_metas(tiles, albedo_path, normal_path)
    if len(sys.argv) > 2:
        lit_preview(tiles, sys.argv[2])
