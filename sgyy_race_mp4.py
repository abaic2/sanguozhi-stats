# -*- coding: utf-8 -*-
"""《三国演义》人物出场频率 · 120回动态排名赛跑（Bar Chart Race, 1080p H.264 MP4）

数据：corpus_sgyy/chapter 毛宗岗百二十回白文 + stats_sgyy.json 名号别称表（正文笔法提取）。
口径：全别称表跨人物长名优先占位去重计数，条形为「截至当前章回累计出现次数」。
用法：
  py -3.10 sgyy_race_mp4.py --stills   # 只出核对静帧（片头/第1/36/60/100/120回）
  py -3.10 sgyy_race_mp4.py            # 全量渲染 + 合成配乐 + 混流输出 MP4
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.stdout.reconfigure(encoding="utf8")

# ============================ 配置区（可一键修改） ============================
VIDEO_TITLE = "《三国演义》"
VIDEO_SUBTITLE_TITLE = "人物出场频率排行榜"
SUBTITLE = "从桃园结义到三国归晋　120回人物命运动态赛跑"
SMALL_NOTE = "基于《三国演义》全文人物提及频率统计 · 语料：毛宗岗评改本一百二十回白文"
END_QUESTION = "从桃园结义，到三国归晋，谁才是真正贯穿全书的人物？"

CORPUS_DIR = "corpus_sgyy/chapter"
NAMES_JSON = "stats_sgyy.json"           # nameCounts: [[人物, [[别称, 回数]…]]…]，别称自正文笔法提取
CHAPTER_COUNT = 120
TOP_N = 10
FPS = 30
VIDEO_WIDTH, VIDEO_HEIGHT = 1920, 1080
BAR_HEIGHT = 56
BAR_GAP = 18
ANIMATION_DURATION = 0.0                 # 预留：数值/名次过渡贯穿整回
CHAPTER_DURATION = 1.5                   # 普通回秒数
IMPORTANT_CHAPTER_DURATION = 2.5         # 重要回秒数
INTRO_SECONDS = 4.0
OUTRO_SECONDS = 8.0

IMPORTANT_CHAPTERS = {                   # 减速播放的重要回
    1: "桃园结义", 5: "三英战吕布", 30: "官渡之战", 37: "三顾茅庐", 42: "长坂坡",
    49: "赤壁之战", 50: "华容道", 65: "刘备入蜀", 76: "关羽败走麦城", 84: "夷陵之战",
    85: "白帝城托孤", 90: "七擒孟获", 91: "六出祁山", 103: "五丈原", 120: "三国归晋",
}
ABBREV = dict(IMPORTANT_CHAPTERS)        # 水印下方简称；未列的回显示对仗回目
ABBREV[80] = "曹丕称帝"

SEGMENTS = [                              # 六段剧情（与看板口径一致）
    ("桃园结义", 1, 9), ("群雄逐鹿", 10, 29), ("官渡三顾", 30, 42),
    ("赤壁鏖兵", 43, 57), ("取蜀失荆", 58, 77), ("北伐归晋", 78, 120),
]

BACKGROUND_COLOR = "#0c0709"
FONT_COLOR = "#e8ddc8"
ACCENT_COLOR = "#d4af37"

CHARACTER_COLORS = {                      # 同一人物全程同色
    "刘备": "#e6b422", "曹操": "#b03030", "孙权": "#2fa8c8", "诸葛亮": "#39b57a",
    "关羽": "#2f7d4f", "张飞": "#8a5fc0", "赵云": "#8fb8d8", "吕布": "#c08a2a",
    "司马懿": "#6a4fa0", "周瑜": "#e06a2e", "董卓": "#8a5a33", "袁绍": "#4a90a4",
    "袁术": "#a08030", "庞统": "#4f9e8f", "马超": "#a7bdd4", "姜维": "#35b06f",
    "鲁肃": "#c8b273", "陆逊": "#2e8b8b", "许褚": "#9a6a6a", "典韦": "#7d5a44",
    "荀彧": "#7f9b86", "郭嘉": "#b0a060", "贾诩": "#6e6e8a", "张辽": "#5a7fb5",
    "徐晃": "#b58a5a", "魏延": "#c96a1b", "黄忠": "#b8860b", "甘宁": "#3aa0a0",
    "曹丕": "#c05a72", "孙坚": "#d1751f", "孙策": "#e08a3c", "太史慈": "#a05a5a",
    "华雄": "#96603c", "貂蝉": "#d87fa0", "司马徽": "#6f8f6f",
}
CHARACTER_ALIASES = None                  # None=采用 stats_sgyy.json 别称表；可覆盖为 {人物: [别称…]}
CHARACTER_ZI = {
    "刘备": "玄德", "曹操": "孟德", "诸葛亮": "孔明", "关羽": "云长", "张飞": "翼德",
    "赵云": "子龙", "吕布": "奉先", "孙权": "仲谋", "周瑜": "公瑾", "司马懿": "仲达",
    "董卓": "仲颖", "袁绍": "本初", "袁术": "公路", "庞统": "士元", "马超": "孟起",
    "姜维": "伯约", "鲁肃": "子敬", "陆逊": "伯言", "许褚": "仲康", "典韦": "恶来",
    "荀彧": "文若", "郭嘉": "奉孝", "贾诩": "文和", "张辽": "文远", "徐晃": "公明",
    "魏延": "文长", "黄忠": "汉升", "甘宁": "兴霸", "曹丕": "子桓", "孙坚": "文台",
    "孙策": "伯符", "太史慈": "子义", "司马徽": "水镜", "华雄": "", "貂蝉": "",
}
CHARACTER_IMAGES = {}                     # {人物: 头像路径}；缺省用同色姓氏徽章
MUSIC_PATH = "sgyy_race_music.wav"        # 存在则直接用；否则程序合成写入
USE_GENERATED_MUSIC = True
OUTPUT_PATH = "sgyy_race_top10.mp4"
TEMP_VIDEO = "_sgyy_race_video_only.mp4"
CRF, X264_PRESET = "19", "medium"         # --draft 时改 23/veryfast

FONTS = {
    "hei": "C:/Windows/Fonts/msyhbd.ttc", "hei2": "C:/Windows/Fonts/msyh.ttc",
    "kai": "C:/Windows/Fonts/STKAITI.TTF", "xi": "C:/Windows/Fonts/STXIHEI.TTF",
}
T2S = {"後": "后", "來": "来", "裏": "里", "裡": "里", "風": "风", "雲": "云", "龍": "龙",
       "馬": "马", "鳥": "鸟", "槍": "枪", "陣": "阵", "說": "说", "話": "话", "經": "经",
       "餘": "余", "馀": "余"}
# ============================================================================

os.chdir(os.path.dirname(os.path.abspath(__file__)))
PLOT_X0, PLOT_W, PLOT_Y0 = 352, 1288, 210
_FONT_CACHE = {}


def font(key, size):
    k = (key, size)
    if k not in _FONT_CACHE:
        _FONT_CACHE[k] = ImageFont.truetype(FONTS[key], size)
    return _FONT_CACHE[k]


def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def shade(rgb, f):
    return tuple(max(0, min(255, int(c * f))) for c in rgb)


def tint(rgb, a):
    return mixrgb(rgb, (255, 255, 255), a)


def mixrgb(t, b, a):
    return tuple(int(r * (1 - a) + c * a) for r, c in zip(t, b))


def ease(t):
    return 3 * t * t - 2 * t * t * t                       # smoothstep ~ easeInOutCubic 观感


# ---------------------------------- 数据 -----------------------------------
def load_data():
    files = sorted(f for f in os.listdir(CORPUS_DIR) if f[:3].isdigit() and f.endswith(".txt"))
    assert len(files) == CHAPTER_COUNT, len(files)
    chaps = []
    for f in files:
        raw = [s.strip() for s in open(os.path.join(CORPUS_DIR, f), encoding="utf8").read().splitlines() if s.strip()]
        head = raw[0]
        title = head.split("回", 1)[1].strip() if "回" in head[:6] else head
        text = "".join(T2S.get(ch, ch) for ch in "\n".join(raw[1:]))
        chaps.append({"j": int(f[:3]), "title": title, "text": text})
    S = json.load(open(NAMES_JSON, encoding="utf8"))
    persons = {}
    for name, det in S["nameCounts"]:
        persons[name] = CHARACTER_ALIASES[name] if CHARACTER_ALIASES else sorted({v for v, _ in det})
    pairs = sorted([(v, p) for p, vs in persons.items() for v in vs], key=lambda x: -len(x[0]))
    per = {p: [0] * CHAPTER_COUNT for p in persons}
    for i, c in enumerate(chaps):
        taken = bytearray(len(c["text"]))
        for v, p in pairs:
            start = 0
            while True:
                k = c["text"].find(v, start)
                if k < 0:
                    break
                if not any(taken[k:k + len(v)]):
                    per[p][i] += 1
                    taken[k:k + len(v)] = b"\x01" * len(v)
                start = k + len(v)
    cum = {p: np.cumsum(v).astype(np.float64) for p, v in per.items()}
    total = {p: float(sum(v)) for p, v in per.items()}
    order = sorted(persons, key=lambda p: -total[p])
    pools = [set(sorted(order, key=lambda p: (-cum[p][i], -total[p]))[:TOP_N]) for i in range(CHAPTER_COUNT)]
    return chaps, persons, per, cum, total, pools, order


# -------------------------------- 静态背景 ----------------------------------
def make_background():
    W, H = VIDEO_WIDTH, VIDEO_HEIGHT
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = 0.55 + 0.45 * (yy / H)
    br, bgg, bb = hex2rgb(BACKGROUND_COLOR)
    red = np.clip((yy - H * 0.72) / (H * 0.28), 0, 1) ** 1.6
    px = np.dstack([(br / 255) * g + 0.10 * red, (bgg / 255) * g + 0.028 * red, (bb / 255) * g]) * 255
    rng = np.random.default_rng(3)
    tex = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    tex = np.array(Image.fromarray(((tex - tex.min()) / (tex.max() - tex.min())) * 255).resize((W, H)).convert("L"),
                   dtype=np.float32)
    px += (tex - 128)[..., None] * 0.055 * (1 - yy / H)[..., None]
    vign = 1 - 0.15 * ((xx - W / 2) ** 2 / (W / 2) ** 2 + (yy - H / 2) ** 2 / (H / 2) ** 2)
    px *= np.clip(vign, 0.55, 1)[..., None]
    img = Image.fromarray(np.clip(px, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA")
    mtn = Image.new("L", (W, H), 0)
    pts = [(x, H - 38 - 60 * math.sin(x / 480) * math.sin(x / 133 + 1.7) - 26 * math.sin(x / 71 + 4))
           for x in range(0, W + 1, 8)]
    ImageDraw.Draw(mtn).polygon([(0, H), (W, H)] + pts, fill=26)
    d.bitmap((0, 0), mtn.filter(ImageFilter.GaussianBlur(3)), fill=(70, 52, 44, 255))
    for gx in range(240, W, 120):
        d.line([(gx, 96), (gx, 918)], fill=(255, 240, 215, 5))
    d.line([(40, 118), (W - 40, 118)], fill=hex2rgb(ACCENT_COLOR) + (46,))
    return img


# ------------------------------- 精灵缓存 -----------------------------------
def badge_sprite(name):
    col = hex2rgb(CHARACTER_COLORS.get(name, "#888888"))
    S = BAR_HEIGHT
    sp = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    d.ellipse([2, 2, S - 3, S - 3], fill=shade(col, 0.42), outline=tint(col, 0.55) + (230,), width=2)
    f = font("kai", int(S * 0.52))
    bb = d.textbbox((0, 0), name[0], font=f)
    d.text(((S - bb[2] + bb[0]) / 2 - bb[0], (S - bb[3] + bb[1]) / 2 - bb[1]), name[0], font=f,
           fill=(245, 238, 220, 255))
    img_path = CHARACTER_IMAGES.get(name)
    if img_path and os.path.exists(img_path):
        av = Image.open(img_path).convert("RGBA").resize((S - 10, S - 10))
        m = Image.new("L", (S - 10, S - 10), 0)
        ImageDraw.Draw(m).ellipse([0, 0, S - 11, S - 11], fill=255)
        sp.paste(av, (5, 5), m)
    return sp


class Label:
    """名次右侧的「名·字」标签，右对齐到条形起点前。"""
    W_ = 200

    def __init__(self, name):
        col = hex2rgb(CHARACTER_COLORS.get(name, "#888888"))
        zi = CHARACTER_ZI.get(name, "")
        txt = name + ("·" + zi if zi else "")
        sp = Image.new("RGBA", (self.W_, BAR_HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(sp)
        f = font("hei", 25)
        bb = d.textbbox((0, 0), txt, font=f)
        x = self.W_ - (bb[2] - bb[0]) - 6
        d.text((x + 2, 14), txt, font=f, fill=(0, 0, 0, 150))
        d.text((x, 12), txt, font=f, fill=tint(col, 0.72) + (255,))
        self.img = sp


class Watermark:
    def __init__(self, idx, chaps):
        c = chaps[idx]
        self.img = Image.new("RGBA", (880, 470), (0, 0, 0, 0))
        d = ImageDraw.Draw(self.img)

        def ctr(txt, f, y, fill):
            bb = d.textbbox((0, 0), txt, font=f)
            d.text(((880 - bb[2] + bb[0]) / 2 - bb[0], y), txt, font=f, fill=fill)

        ctr("第 %03d 回" % c["j"], font("hei", 172), 6, (228, 196, 140, 46))
        y = 216
        ab = ABBREV.get(c["j"])
        if ab:
            ctr(ab, font("kai", 44), y, hex2rgb(ACCENT_COLOR) + (138,))
            y += 64
        t = c["title"]
        for line in (t[:len(t) // 2], t[len(t) // 2:]) if len(t) >= 8 else (t,):
            ctr(line, font("kai", 30), y, hex2rgb(FONT_COLOR) + (92,))
            y += 40


# --------------------------------- 单帧渲染 ----------------------------------
def race_frame(c, frac, data, bg, cache, frozen=False):
    tv = 0.0 if frozen else ease(frac)
    chaps, per, cum, total, pools, order = (data[k] for k in ("chaps", "per", "cum", "total", "pools", "order"))
    W, H = VIDEO_WIDTH, VIDEO_HEIGHT
    prev_pool = pools[c - 1] if c > 0 else set()
    cur_pool = pools[c]
    pv = {}
    for p in order:
        base = cum[p][c - 1] if c > 0 else 0.0
        pv[p] = base + (cum[p][c] - base) * tv
    shown = sorted(cur_pool | prev_pool, key=lambda p: (-pv[p], -total[p]))
    alphas = {}
    for p in shown:
        if p in cur_pool and p in prev_pool:
            alphas[p] = 1.0
        elif p in cur_pool:
            alphas[p] = min(1.0, frac / 0.5)
        elif p in prev_pool:
            alphas[p] = max(0.0, 1 - frac / 0.35)
    shown = [p for p in shown if alphas[p] > 0.02 and pv[p] >= 1.0][:TOP_N]
    smax = max(10.0, max((pv[p] for p in shown), default=10.0) * 1.14)

    img = bg.copy()
    # 章节水印（跨回淡换）
    fade = min(1.0, frac / 0.18) if frac < 0.18 else 1.0
    for idx, a in (([(c - 1, 1 - fade)] if (frac < 0.18 and c > 0) else []) + [(c, fade)]):
        if idx not in cache["wm"]:
            cache["wm"] = {idx: Watermark(idx, chaps).img}
        wm = cache["wm"][idx]
        if a > 0.99:
            img.paste(wm, (W - 920, 120), wm)
        else:
            r, g, b, al = wm.split()
            faded = Image.merge("RGBA", (r, g, b, al.point(lambda v: int(v * a))))
            img.paste(faded, (W - 920, 120), faded)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((40, 44), VIDEO_TITLE, font=font("hei", 34), fill=hex2rgb(FONT_COLOR) + (255,))
    d.text((40 + d.textlength(VIDEO_TITLE, font=font("hei", 34)) + 14, 54), VIDEO_SUBTITLE_TITLE,
           font=font("kai", 26), fill=hex2rgb(ACCENT_COLOR) + (215,))
    d.text((W - 40, 58), SMALL_NOTE, font=font("hei2", 15), fill=(200, 185, 160, 120), anchor="ra")
    if not frozen and frac < 0.30 and chaps[c]["j"] in IMPORTANT_CHAPTERS:
        k = 1 - frac / 0.30
        d.rectangle([3, 3, W - 4, H - 4], outline=hex2rgb(ACCENT_COLOR) + (int(70 * k),), width=6)
        d.text((W // 2, 152), "· " + IMPORTANT_CHAPTERS[chaps[c]["j"]] + " ·", font=font("kai", 34),
               fill=hex2rgb(ACCENT_COLOR) + (int(60 + 170 * k),), anchor="ma")
    glow = Image.new("RGBA", (W // 4, H // 4), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r, p in enumerate(shown):
        a = alphas[p]
        col = hex2rgb(CHARACTER_COLORS.get(p, "#888888"))
        y = PLOT_Y0 + r * (BAR_HEIGHT + BAR_GAP)
        L = max(6.0, PLOT_W * pv[p] / smax)
        gd.rounded_rectangle([PLOT_X0 / 4, y / 4, (PLOT_X0 + L) / 4, (y + BAR_HEIGHT) / 4], radius=4,
                             fill=col + (int(150 * a),))
        d.rounded_rectangle([PLOT_X0, y, PLOT_X0 + L, y + BAR_HEIGHT], radius=10, fill=col + (int(255 * a),))
        ov = Image.new("RGBA", (max(1, int(L)), BAR_HEIGHT // 2), (255, 255, 255, int(26 * a)))
        img.paste(ov, (PLOT_X0, y), ov)
        tip = Image.new("RGBA", (24, BAR_HEIGHT), tint(col, 0.9) + (int(95 * a),))
        img.paste(tip, (PLOT_X0 + int(L) - 24, y), tip)
        slide = int((1 - a) * 80)
        bdg = cache["badges"][p] if p in cache["badges"] else cache["badges"].setdefault(p, badge_sprite(p))
        lbl = cache["labels"][p] if p in cache["labels"] else cache["labels"].setdefault(p, Label(p).img)
        if a < 0.99:
            bdg = bdg.copy()
            bdg.putalpha(bdg.split()[3].point(lambda v: int(v * a)))
            lbl = lbl.copy()
            lbl.putalpha(lbl.split()[3].point(lambda v: int(v * a)))
        d = ImageDraw.Draw(img, "RGBA")
        img.paste(bdg, (86 + slide, y), bdg)
        img.paste(lbl, (PLOT_X0 - 8 - Label.W_ + slide, y), lbl)
        d.text((44, y + BAR_HEIGHT / 2), "%d" % (r + 1), font=font("hei", 26),
               fill=(150, 138, 120, int(210 * a)), anchor="lm")
        d.text((W - 60, y + BAR_HEIGHT / 2 - 4), "%d" % round(pv[p]), font=font("hei", 38),
               fill=tint(col, 0.75) + (int(255 * a),), anchor="rm")
    ga = np.asarray(glow.filter(ImageFilter.GaussianBlur(2)).resize((W, H), Image.BILINEAR), dtype=np.int32)
    if os.environ.get("RACE_DEBUG"):
        img.save("_dbg_before_glow.png")
        glow.filter(ImageFilter.GaussianBlur(2)).resize((W, H), Image.BILINEAR).save("_dbg_glow.png")
    base = np.asarray(img.convert("RGB"), dtype=np.int32)
    base = np.clip(base + (ga[..., :3] * ga[..., 3:4]) // 255 * 0.55, 0, 255).astype(np.uint8)
    img = Image.fromarray(base)
    d = ImageDraw.Draw(img, "RGBA")
    # 左下角实时数据
    acc = int(sum(pv[p] for p in shown))
    newn = int(round(tv * sum(per[p][c] for p in cur_pool)))
    lines = [("当前章节", "第 %03d 回" % chaps[c]["j"], hex2rgb(FONT_COLOR)),
             ("Top10累计", "%d 次" % acc, hex2rgb(ACCENT_COLOR)),
             ("当前第一", shown[0] if shown else "—",
              hex2rgb(CHARACTER_COLORS.get(shown[0], "#ffffff")) if shown else hex2rgb(FONT_COLOR)),
             ("本回新增", "%d 次" % newn, (170, 158, 138))]
    for i, (k, val, cl) in enumerate(lines):
        d.text((40, 940 + i * 31), k, font=font("hei2", 17), fill=(150, 138, 120, 200))
        d.text((136, 937 + i * 31), val, font=font("hei", 21), fill=cl + (235,))
    # 底部六段进度轴
    tx0, tx1, ty = 560, W - 60, 958
    j = chaps[c]["j"]
    cur_seg = SEGMENTS[min([i for i in range(6) if j <= SEGMENTS[i][2]], default=5)][0]
    for name, a0, b0 in SEGMENTS:
        xa = tx0 + (tx1 - tx0) * (a0 - 1) / CHAPTER_COUNT
        xb = tx0 + (tx1 - tx0) * b0 / CHAPTER_COUNT
        d.rounded_rectangle([xa, ty, xb, ty + 10], radius=3,
                            fill=(150, 110, 70, 200) if name == cur_seg else (120, 90, 60, 70))
        d.text(((xa + xb) / 2, ty + 22), name, font=font("hei2", 15),
               fill=(230, 210, 170, 235) if name == cur_seg else (200, 185, 160, 90), anchor="ma")
    for k in IMPORTANT_CHAPTERS:
        xk = tx0 + (tx1 - tx0) * (k - 0.5) / CHAPTER_COUNT
        d.line([(xk, ty - 3), (xk, ty + 13)], fill=hex2rgb(ACCENT_COLOR) + (150,), width=2)
    cx = tx0 + (tx1 - tx0) * (c + tv) / CHAPTER_COUNT
    d.ellipse([cx - 6, ty - 1, cx + 6, ty + 11], fill=hex2rgb(FONT_COLOR))
    d.text((W - 60, 1042), "统计口径：名与字号·别称并计，长名优先占位不重复计数 · 条形为截至本回累计出现次数",
           font=font("hei2", 14), fill=(150, 138, 120, 130), anchor="ra")
    return img


def intro_frame(k, bg):
    img = Image.blend(bg.convert("RGB"), Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (2, 1, 1)), 0.55)
    d = ImageDraw.Draw(img, "RGBA")
    W, H = VIDEO_WIDTH, VIDEO_HEIGHT

    def ctr(txt, f, y, a, fill=(232, 221, 200)):
        if a <= 0:
            return
        bb = d.textbbox((0, 0), txt, font=f)
        d.text(((W - bb[2] + bb[0]) / 2 - bb[0], y), txt, font=f, fill=fill + (int(255 * min(1, a)),))

    d.rectangle([W * 0.32, H * 0.5 + 2, W * 0.68, H * 0.5 + 5], fill=hex2rgb(ACCENT_COLOR) + (int(140 * k),))
    ctr(VIDEO_TITLE, font("xi", 118), H * 0.28, k * 1.5)
    ctr(VIDEO_SUBTITLE_TITLE, font("kai", 52), H * 0.55, k * 1.5 - 0.3, hex2rgb(ACCENT_COLOR))
    ctr(SUBTITLE, font("kai", 26), H * 0.65, k * 1.5 - 0.55)
    ctr(SMALL_NOTE, font("hei2", 17), H * 0.73, k * 1.5 - 0.8, (190, 175, 150))
    return img


# ------------------------------- 帧调度生成 ---------------------------------
def chapter_frames(c):
    return int(round((IMPORTANT_CHAPTER_DURATION if (c + 1) in IMPORTANT_CHAPTERS else CHAPTER_DURATION) * FPS))


def gen_frames(data, bg):
    cache = {"labels": {}, "badges": {}, "wm": {}}
    n_intro, n_outro = int(INTRO_SECONDS * FPS), int(OUTRO_SECONDS * FPS)
    for f in range(n_intro):
        yield intro_frame(min(1.0, f / (n_intro * 0.55)), bg)
    last = None
    for c in range(CHAPTER_COUNT):
        for fr in range(chapter_frames(c)):
            img = race_frame(c, fr / chapter_frames(c), data, bg, cache)
            last = img
            yield img
    for f in range(n_outro):
        img = last.copy()
        d = ImageDraw.Draw(img, "RGBA")
        W, H = VIDEO_WIDTH, VIDEO_HEIGHT
        a = min(1.0, f / (FPS * 1.2))
        d.rectangle([0, 0, W, 116], fill=(10, 6, 6, int(200 * a)))
        t = "《三国演义》人物出场频率最终排行榜"
        bb = d.textbbox((0, 0), t, font=font("hei", 40))
        d.text(((W - bb[2] + bb[0]) / 2, 30), t, font=font("hei", 40),
               fill=hex2rgb(ACCENT_COLOR) + (int(255 * a),))
        a2 = min(1.0, max(0.0, (f - FPS * 1.5) / (FPS * 1.5)))
        q = END_QUESTION
        bb = d.textbbox((0, 0), q, font=font("kai", 30))
        d.text(((W - bb[2] + bb[0]) / 2 - bb[0], 142), q, font=font("kai", 30),
               fill=hex2rgb(FONT_COLOR) + (int(235 * a2),))
        k0 = n_outro - int(FPS * 0.8)
        if f >= k0:
            d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * (f - k0) / (n_outro - k0))))
        yield img


# --------------------------------- 配乐 -------------------------------------
def synth_music(path, chapter_times):
    import soundfile as sf
    sr = 44100
    total_sec = chapter_times[-1] + OUTRO_SECONDS
    N = int(sr * total_sec)
    L = np.zeros(N)
    R = np.zeros(N)
    rng = np.random.default_rng(7)

    def add(sig, at, gl=1.0, pan=0.5):
        i0 = int(at * sr)
        if i0 >= N:
            return
        n = min(len(sig), N - i0)
        L[i0:i0 + n] += sig[:n] * gl * math.sqrt(1 - pan)
        R[i0:i0 + n] += sig[:n] * gl * math.sqrt(pan)

    def e(n, k=6.0):
        return np.exp(-np.arange(n) * k / n)

    def kick(gl=1.0):
        n = int(sr * 0.4)
        t = np.arange(n) / sr
        f = 88 * np.exp(-t * 26) + 38
        body = np.sin(2 * np.pi * np.cumsum(f) / sr) * e(n, 7)
        click = rng.normal(0, 1, int(0.012 * sr)) * e(int(0.012 * sr), 240) * 0.4
        s = np.zeros(n)
        s[:len(click)] = click
        return (body + s) * gl

    def gong(gl=1.0, dur=4.5, f0=70.0):
        n = int(sr * dur)
        t = np.arange(n) / sr
        s = np.zeros(n)
        for k, (ratio, dec) in enumerate([(1, 5.5), (2.02, 6), (2.91, 7), (4.12, 8.5), (5.46, 10), (6.8, 12)]):
            s += np.sin(2 * np.pi * f0 * ratio * t) * e(n, dec) * (0.5 ** k)
        return s * gl

    def pluck(freq, gl=1.0, dur=1.1):
        P = max(2, int(sr / freq))
        periods = int(sr * dur) // P + 1
        buf = rng.uniform(-1, 1, P)
        chunks = np.empty((periods, P))
        decay = 0.996 if freq < 400 else 0.993
        for k in range(periods):
            chunks[k] = buf
            buf = decay * 0.5 * (buf + np.roll(buf, -1))
        y = chunks.ravel()[: int(sr * dur)]
        return y * e(len(y), 2.2) * gl

    PENTA = [220.0, 261.63, 293.66, 329.63, 392.0, 440.0, 523.25, 587.33]
    segs = [(a, b) for (_, a, b) in SEGMENTS]
    seg_energy = [0.35, 0.55, 0.72, 0.92, 0.85, 0.78]
    roots = [55.0, 49.0, 55.0, 61.65, 49.0, 41.2]
    t_all = np.arange(N) / sr
    seg_idx = np.zeros(N, int)
    for si, (a, b) in enumerate(segs):
        i0 = int(chapter_times[a - 1] * sr)
        i1 = int(chapter_times[b] * sr) if b < CHAPTER_COUNT else N
        seg_idx[i0:i1] = si
    seg_idx[:int(chapter_times[0] * sr)] = 0
    seg_idx[int(chapter_times[CHAPTER_COUNT] * sr):] = 5
    sad = t_all > chapter_times[102]
    drone = np.zeros(N)
    for si in range(6):
        m = (seg_idx == si).astype(float)
        f = roots[si]
        ph = 2 * np.pi * f * t_all
        g = m * seg_energy[si] * 0.16 * (1 + 0.25 * np.sin(2 * np.pi * 0.13 * t_all))
        drone += (np.sin(ph) + 0.6 * np.sin(ph * 1.5 + 1) + 0.35 * np.sin(ph * 2)) * g
        drone += np.sin(2 * np.pi * f * 1.189 * t_all) * m * sad * 0.07
    add(drone, 0, 1.0, 0.5)
    for at in [chapter_times[0]] + [chapter_times[a - 1] for a, b in segs[1:]] + [chapter_times[CHAPTER_COUNT - 1]]:
        add(gong(0.55), max(0, at - 0.08), 1, 0.5)
    for ci in range(0, CHAPTER_COUNT, 2):
        add(kick(0.5 + (0.5 if (ci + 1) in IMPORTANT_CHAPTERS else 0)), chapter_times[ci], 1, 0.5)
        if (ci + 1) in IMPORTANT_CHAPTERS:
            add(kick(0.6), chapter_times[ci] + 0.62, 1, 0.5)
            add(gong(0.3, 3.0, 90), chapter_times[ci] + 0.1, 1, 0.5)
    for si, (a, b) in enumerate(segs):
        gap = [1.7, 1.0, 0.66, 0.45, 0.5, 0.9][si]
        tt = chapter_times[a - 1]
        tend = chapter_times[b]
        while tt < tend:
            f = PENTA[int(np.clip(rng.normal(2.6 + (si % 3) * 0.8, 1.6), 0, len(PENTA) - 1))]
            add(pluck(f, 0.14 + 0.05 * si), tt, 1, float(rng.uniform(0.2, 0.8)))
            if si >= 2:
                add(pluck(f * 1.5, 0.06), tt + gap * 0.5, 1, float(rng.uniform(0.2, 0.8)))
            tt += gap
    for i, f in enumerate([440, 392, 329.63, 293.66, 261.63, 220, 196, 220, 261.63, 220]):
        add(pluck(f, 0.28, 1.8), chapter_times[102] + i * 2.4, 1, 0.5 + 0.2 * (i % 2))
    add(gong(0.6, 6.0), chapter_times[CHAPTER_COUNT] + 1.0, 1, 0.5)
    # 空间感：三次 pre-echo
    for delay, g in [(0.19, 0.16), (0.41, 0.09), (0.83, 0.05)]:
        off = int(delay * sr)
        Lb, Rb = L.copy(), R.copy()
        L[off:] += Lb[:-off] * g
        R[off:] += Rb[:-off] * g
    mix = np.stack([L, R], 1)
    fi = int(1.2 * sr)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = int(4 * sr)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    mix = np.tanh(mix * 1.4)
    mix *= 0.86 / np.abs(mix).max()
    sf.write(path, mix.astype(np.float32), sr)
    print("配乐已合成：%s（%.0f 秒）" % (path, total_sec))


# --------------------------------- 编码 -------------------------------------
def encode(frames_iter, total_frames):
    import imageio_ffmpeg
    gen = imageio_ffmpeg.write_frames(TEMP_VIDEO, (VIDEO_WIDTH, VIDEO_HEIGHT), fps=FPS, codec="libx264",
                                      macro_block_size=1, pix_fmt_out="yuv420p",
                                      output_params=["-crf", CRF, "-preset", X264_PRESET])
    gen.send(None)
    n = 0
    for img in frames_iter:
        gen.send(np.asarray(img.convert("RGB"), dtype=np.uint8).tobytes())
        n += 1
        if n % 600 == 0:
            print("  帧 %d / %d (%.0f%%)" % (n, total_frames, n * 100 / total_frames), flush=True)
    gen.close()
    return n


def mix_audio():
    if USE_GENERATED_MUSIC and not os.path.exists(MUSIC_PATH):
        return False
    exe = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    subprocess.run([exe, "-y", "-i", TEMP_VIDEO, "-i", MUSIC_PATH, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUTPUT_PATH],
                   check=True, capture_output=True)
    return True


def probe(path):
    exe = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    out = subprocess.run([exe, "-hide_banner", "-i", path], capture_output=True, text=True)
    for ln in out.stderr.splitlines():
        if "Duration" in ln or "Stream" in ln:
            print(" ", ln.strip())


# --------------------------------- 主流程 -----------------------------------
def main():
    args = sys.argv[1:]
    global CRF, X264_PRESET
    if "--draft" in args:
        CRF, X264_PRESET = "23", "veryfast"
    chaps, persons, per, cum, total, pools, order = load_data()
    top = sorted(persons, key=lambda x: -total[x])
    print("语料 %d 回｜人物 %d｜累计前五：%s" % (len(chaps), len(persons),
          "、".join("%s %d" % (p, total[p]) for p in top[:5])))
    data = {"chaps": chaps, "per": per, "cum": cum, "total": total, "pools": pools, "order": order}
    bg = make_background()
    if "--stills" in args:
        cache = {"labels": {}, "badges": {}, "wm": {}}
        for c in (0, 35, 59, 99, 119):
            race_frame(c, 1.0, data, bg, cache).save("_mp4_p%03d.png" % chaps[c]["j"])
        intro_frame(1.0, bg).save("_mp4_intro.png")
        print("静帧已输出 _mp4_*.png")
        return
    chapter_times = [INTRO_SECONDS]
    for c in range(CHAPTER_COUNT):
        chapter_times.append(chapter_times[-1] + chapter_frames(c) / FPS)
    total_frames = int((chapter_times[-1] + OUTRO_SECONDS) * FPS)
    print("总帧数 %d｜成片约 %.0f 秒" % (total_frames, total_frames / FPS))
    if USE_GENERATED_MUSIC and not os.path.exists(MUSIC_PATH):
        synth_music(MUSIC_PATH, chapter_times)
    n = encode(gen_frames(data, bg), total_frames)
    print("视频帧完成 %d，混流…" % n)
    if mix_audio():
        print("混流完成：", OUTPUT_PATH)
    else:
        os.replace(TEMP_VIDEO, OUTPUT_PATH)
        print("无配乐，直出：", OUTPUT_PATH)
    probe(OUTPUT_PATH)


if __name__ == "__main__":
    main()
