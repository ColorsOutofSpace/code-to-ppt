# code-to-ppt 代码参考 / Code Reference

> 本文档是 `code-to-ppt` skill 的代码参考层（第三层，按需加载）。
> 包含完整的 helper 函数实现、配色方法论、排版参考范围、布局尺寸速查和卡片容量计算。
> 主工作流见 `SKILL.md`（中文）或 `SKILL_EN.md`（英文）。

---

## 1. Helper 函数完整代码 / Complete Helper Functions

以下函数基于 `python-pptx` 构建，操作单位均为英寸（Inches）。16:9 画布 = 10 × 5.625"。

所有函数均可直接复制到 PPT 生成脚本中使用。

### 1.1 基础设施 / Infrastructure

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from PIL import Image
import os

SW, SH = 10.0, 5.625          # 16:9 画布尺寸

prs = Presentation()           # 宽屏默认已是 16:9
```

### 1.2 图片工具 / Image Utilities

```python
IMG_CACHE = {}
def get_img_size(name):
    """用 PIL 预读图片像素尺寸，缓存结果。所有图片操作的前置步骤。"""
    if name not in IMG_CACHE:
        p = os.path.join(FIG, name)
        if os.path.exists(p):
            im = Image.open(p); IMG_CACHE[name] = im.size
        else:
            IMG_CACHE[name] = None
    return IMG_CACHE[name]

def img_ratio(name):
    """返回图片宽高比 (width/height)，缺失时返回 1.0。"""
    sz = get_img_size(name)
    return sz[0] / sz[1] if sz else 1.0

def img_fit(sl, name, l, t, max_w, max_h, align="center"):
    """
    等比缩放放置图片，不超出 max_w × max_h 边界框。
    align: "center"（默认）/ "left" / "right"
    图片在框内垂直居中。
    缺失图片时渲染红色占位符 "[缺图: name]"。
    返回实际渲染尺寸 (w, h)。
    """
    sz = get_img_size(name)
    if sz is None:
        tx(sl, l, t, max_w, 0.2, "[缺图: " + name + "]", fs=7, cl=RED)
        return (0, 0)
    pw, ph = sz
    ratio = pw / ph
    w = max_w; h = w / ratio
    if h > max_h:
        h = max_h; w = h * ratio
    if align == "right": x = l + max_w - w
    elif align == "center": x = l + (max_w - w) / 2
    else: x = l
    y = t + (max_h - h) / 2
    try:
        sl.shapes.add_picture(os.path.join(FIG, name), Inches(x), Inches(y), Inches(w), Inches(h))
    except Exception as e:
        print(f"Warning: Failed to add image {name}: {e}")
    return (w, h)

def img_top(sl, name, l, t, w):
    """
    固定宽度放置图片，高度由宽高比决定（无上限约束）。
    返回实际渲染高度（英寸），便于后续元素错开排列。
    """
    sz = get_img_size(name)
    if sz is None:
        tx(sl, l, t, w, 0.2, "[缺图: " + name + "]", fs=7, cl=RED)
        return 0
    h = w / (sz[0] / sz[1])
    sl.shapes.add_picture(os.path.join(FIG, name), Inches(l), Inches(t), Inches(w), Inches(h))
    return h

def plot_card(sl, l, t, w, h, name, title="", accent=None):
    """
    图片卡片：白底 + 顶部强调线（0.03" 厚）+ 可选标题 + 等比图片。
    图片周围有 0.05" 内边距。
    """
    if accent is None: accent = BLU
    _rect(sl, l, t, w, h, WHT)
    _line(sl, l, t, w, accent, 0.03)
    img_t = t + 0.08
    img_h = h - 0.16
    if title:
        tx(sl, l + 0.1, t + 0.05, w - 0.2, 0.25, title, fs=9, cl=GRY, al=PP_ALIGN.CENTER, bd=True)
        img_t += 0.25
        img_h -= 0.3
    img_fit(sl, name, l + 0.05, img_t, w - 0.1, img_h, align="center")
```

### 1.3 文本工具 / Text Utilities

```python
def _tb(sl, l, t, w, h):
    """（内部）创建文本框。"""
    return sl.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))

def tx(sl, l, t, w, h, text, **kw):
    """
    单段文本块。
    参数（均有默认值）：
        fn="Microsoft YaHei"  |  fs=14  |  bd=False  |  cl=BLK
        al=PP_ALIGN.LEFT      |  it=False  |  ls=1.2
    """
    fn = kw.get("fn", "Microsoft YaHei"); fs = kw.get("fs", 14)
    bd = kw.get("bd", False); cl = kw.get("cl", BLK)
    al = kw.get("al", PP_ALIGN.LEFT); it = kw.get("it", False)
    ls = kw.get("ls", 1.2)
    box = _tb(sl, l, t, w, h); box.text_frame.word_wrap = True
    p = box.text_frame.paragraphs[0]
    p.alignment = al; p.line_spacing = Pt(int(fs * ls))
    r = p.add_run(); r.text = text
    r.font.name = fn; r.font.size = Pt(fs); r.font.bold = bd
    r.font.color.rgb = cl; r.font.italic = it
    rPr = r._r.get_or_add_rPr(); rPr.set(qn("a:eaTypeface"), fn)
    # ↑ 关键：设置东亚字体回退，确保中文以正确字体渲染

def ri(sl, l, t, w, h, runs, al=PP_ALIGN.LEFT, ls=1.3):
    """
    多段文本（混合格式）。runs = [(text, {kw}), ...]
    每个 run 一个段落，可独立设置字体、大小、颜色、粗体等。
    """
    box = _tb(sl, l, t, w, h); box.text_frame.word_wrap = True; tf = box.text_frame
    for i, (text, kw) in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = al
        fs = kw.get("fs", 14); p.line_spacing = Pt(int(fs * ls))
        r = p.add_run(); r.text = text
        fn = kw.get("fn", "Microsoft YaHei"); r.font.name = fn; r.font.size = Pt(fs)
        r.font.bold = kw.get("bd", False); r.font.color.rgb = kw.get("cl", BLK)
        r.font.italic = kw.get("it", False)
        rPr = r._r.get_or_add_rPr(); rPr.set(qn("a:eaTypeface"), fn)

def bu(sl, l, t, w, h, items, fs=13, cl=None, ls=1.5):
    """
    项目符号列表。items = ["列表项1", "列表项2", ...]
    项目符号为蓝色圆点 (◦, Unicode 8226)，颜色 #4A90D9。
    """
    if cl is None: cl = BLK
    box = _tb(sl, l, t, w, h); box.text_frame.word_wrap = True; tf = box.text_frame
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.line_spacing = Pt(int(fs * ls))
        pPr = p._p.get_or_add_pPr()
        bc = pPr.makeelement(qn("a:buChar"), {"char": chr(8226)})
        pPr.append(bc)
        bcl = pPr.makeelement(qn("a:buClr"), {})
        sc = bcl.makeelement(qn("a:srgbClr"), {"val": "4A90D9"})
        bcl.append(sc); pPr.append(bcl)
        r = p.add_run(); r.text = item
        r.font.name = "Microsoft YaHei"; r.font.size = Pt(fs); r.font.color.rgb = cl
        rPr = r._r.get_or_add_rPr(); rPr.set(qn("a:eaTypeface"), "Microsoft YaHei")
```

### 1.4 图形与背景 / Shapes & Background

```python
def setbg(sl, c):
    """设置幻灯片纯色背景。"""
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = c

def ns(prs, bgc=None):
    """新建空白幻灯片（layout index 6），可选背景色。"""
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    if bgc: setbg(sl, bgc)
    return sl

def _rect(sl, l, t, w, h, fill_color):
    """（内部）纯色矩形，无边框。"""
    shape = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    shape.fill.solid(); shape.fill.fore_color.rgb = fill_color; shape.line.fill.background()

def _line(sl, l, t, w, color, thickness=0.005):
    """（内部）水平细线（实为超薄矩形）。"""
    shape = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(thickness))
    shape.fill.solid(); shape.fill.fore_color.rgb = color; shape.line.fill.background()

def band(sl, l, t, w, h, color):
    """全宽/半宽色带。用于强调区域或打断视觉节奏。"""
    _rect(sl, l, t, w, h, color)

def cn(sl, x, y, num, color=None):
    """
    圆形编号标记（直径 0.5"）。
    num: 字符串（数字或文字），白色居中显示。
    """
    if color is None: color = BLU
    c = sl.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(0.5), Inches(0.5))
    c.fill.solid(); c.fill.fore_color.rgb = color; c.line.fill.background()
    cr = c.text_frame.paragraphs[0]; cr.alignment = PP_ALIGN.CENTER
    rr = cr.add_run()
    rr.text = num; rr.font.size = Pt(17); rr.font.bold = True
    rr.font.color.rgb = WHT; rr.font.name = "Arial"

def hero(sl, l, t, w, h, number, label, accent=None):
    """
    大字统计卡：上部 55% 为 42pt 数字，下部 45% 为 11pt 标签。
    用于关键指标锚点展示。
    """
    if accent is None: accent = ACC
    tx(sl, l, t, w, 0.55, str(number), fs=42, bd=True, cl=accent, fn="Arial", al=PP_ALIGN.LEFT)
    tx(sl, l, t + h * 0.55, w, h * 0.45, label, fs=11, cl=GRY, al=PP_ALIGN.LEFT)

def cd(sl, l, t, w, h, title, body, accent=None):
    """
    内容卡片：白底 + 顶部强调线（0.03" 厚）+ 标题（12pt 粗体）+ 正文（9.5pt）。
    accent: 强调线颜色，语义化选择（见配色方法论）。
    正文区域：宽 = w - 0.28"，高 = h - 0.42"。
    """
    if accent is None: accent = BLU
    _rect(sl, l, t, w, h, WHT)
    _line(sl, l, t, w, accent, 0.03)
    if title: tx(sl, l + 0.15, t + 0.08, w - 0.28, 0.26, title, fs=12, bd=True, cl=NAV)
    if body: tx(sl, l + 0.15, t + 0.36, w - 0.28, h - 0.42, body, fs=9.5, cl=GRY, ls=1.45)
```

### 1.5 页面模板 / Page Templates

```python
def ft(sl, n):
    """
    标准页脚：左端短装饰线（1.8"）+ 机构名（7pt）+ 右端页码（9pt Arial）。
    页脚线位于 y=5.25"，确保页面内容底部不超出此线。
    """
    _line(sl, 0.5, 5.25, 1.8, GLT, 0.004)
    tx(sl, 0.5, 5.3, 6, 0.25, "机构名称（由 Phase 1 确认）", fs=7, cl=GLT)
    tx(sl, 9.0, 5.3, 0.6, 0.25, str(n), fs=9, cl=GLT, fn="Arial", al=PP_ALIGN.RIGHT)

def st(sl, title):
    """
    页面顶部章节标签：全宽细线（0.015"）+ 8pt 灰色标题。
    用于内容页顶部标识当前所在章节。
    """
    _line(sl, 0, 0, 10, PRIMARY, 0.015)  # PRIMARY 替换为实际主色
    tx(sl, 0.5, 0.08, 9, 0.28, title, fs=8, cl=GRY)

def sT(sl, title, sub=""):
    """
    页面主标题（27pt 深色粗体）+ 可选副标题（11pt 灰色）。
    """
    tx(sl, 0.5, 0.22, 9, 0.55, title, fs=27, bd=True, cl=NAV)
    if sub: tx(sl, 0.5, 0.72, 9, 0.28, sub, fs=11, cl=GRY)

def section_divider(prs, num, title, subtitle=""):
    """
    章节过渡页：深色全屏 + 顶部强调线 + 大号章节号（72pt）+ 章节标题（30pt 白）。
    深色背景和强调线颜色由配色方案决定。
    """
    s = ns(prs, NAV)         # NAV 替换为实际主深色
    _line(s, 0, 0, 10, ACC, 0.055)  # ACC 替换为实际强调色
    tx(s, 0.6, 1.5, 1.5, 1.2, num, fs=72, bd=True, cl=ACC, fn="Arial")
    tx(s, 2.2, 1.65, 7.0, 0.7, title, fs=30, bd=True, cl=WHT)
    if subtitle: tx(s, 2.2, 2.3, 7.0, 0.5, subtitle, fs=13, cl=ICE)
    return s
```

---

## 2. 配色方法论 / Color Scheme Methodology

### 2.1 配色决策流程

```
PPT 用途 ──→ 色调方向 ──→ 4 层色板
   +
受众/氛围 ──→ 对比度强度
   +
机构/品牌 ──→ 主色来源（如有 Logo/VI 色则优先沿用）
```

### 2.2 四层色板结构

| 层级 | 数量 | 用途 | 选择原则 |
|------|------|------|----------|
| **主色** | 1-2 个 | 封面背景、章节过渡页、页面标题 | 用途决定色调（医学=深青、金融=藏蓝、科技=深蓝紫） |
| **辅色** | 2-3 个 | 卡片顶部强调线、图表主色调 | 与主色协调，明度拉开差距 |
| **中性色** | 3-4 个 | 正文黑 `#1A1A1A`、灰色 `#6B7B8D`、浅底 `#EDF2F8`、白 `#FFFFFF` | 通常不变的通用色 |
| **功能色** | 3-4 个 | 正面/增长 → 绿，警告/局限 → 红/橙，对比/背景 → 金 | 语义固定，跨场景保持一致性 |

### 2.3 场景启发示例（非强制，LLM 自主判断）

| 场景 | 主色 | 辅色 | 功能色 | 氛围关键词 |
|------|------|------|--------|------------|
| 医学/健康 | `#1A3C4A` 深青 | `#2EA6D3` 青蓝、`#27AE60` 绿 | 红 `#C0392B`、金 `#D4A84B` | 冷静、专业 |
| 金融/商务 | `#1B2A4A` 藏蓝 | `#D4A84B` 金、`#C0392B` 红 | 绿 `#27AE60`、橙 `#E67E22` | 稳重、权威 |
| 科技/互联网 | `#1A1A2E` 深蓝紫 | `#4A90D9` 蓝、`#E67E22` 橙 | 绿 `#27AE60`、红 `#C0392B` | 现代、锐利 |
| 教育/学术 | `#2C3E50` 灰蓝 | `#3498DB` 蓝、`#F39C12` 暖黄 | 绿 `#27AE60`、红 `#C0392B` | 沉静、理性 |
| 创意/设计 | `#2D1B69` 深紫 | `#E74C3C` 红、`#F1C40F` 黄 | 青 `#2EA6D3` | 大胆、活力 |

### 2.4 卡片强调线颜色语义映射

同一页面内，不同卡片的顶部强调线颜色暗示其信息类型：

| 信息类型 | 颜色 | 语义 |
|----------|------|------|
| 通用内容 / 方法描述 | 辅色（中性蓝等） | 常规信息 |
| 核心创新 / 贡献 / 收益 | 功能色-正面（绿）或主色加亮 | 正面、亮点 |
| 对比 / 已有研究 / 背景 | 功能色-对比（金/橙） | 对照、差异化 |
| 局限 / 问题 / 代价 | 功能色-警告（红） | 需要关注 |

---

## 3. 排版层级参考 / Typography Reference

以下为参考范围，具体数值可根据内容密度微调。

| 角色 | 字号参考 | 粗细 | 颜色 | 使用位置 |
|------|----------|------|------|----------|
| 章节号（过渡页） | 60–72 pt | Bold | 强调色 | `section_divider()` |
| 封面主标题 | 30–36 pt | Bold | 白（深底）/ 主色（浅底） | 封面 |
| 页面主标题 | 24–30 pt | Bold | 主色 | `sT()` |
| Hero 统计数字 | 36–48 pt | Bold | 强调色 | `hero()` |
| 内容卡片标题 | 11–13 pt | Bold | 主色 | `cd()` title |
| 正文（卡片内） | 9–11 pt | Normal | 灰/黑 | `cd()` body |
| 正文（色带内） | 10–12 pt | Normal | 深色 | `band()` 内文字 |
| 章节标签 | 7–9 pt | Normal | 灰色 | `st()` |
| 副标题/描述 | 10–12 pt | Normal | 灰色 | `sT()` sub |
| Hero 标签 | 10–12 pt | Normal | 灰色 | `hero()` label |
| 页脚 | 6–8 pt | Normal | 浅灰 | `ft()` |

**字体设置规则：**
- 中文字体：`"Microsoft YaHei"`（微软雅黑）
- 数字/英文：`"Arial"`
- **每条文本都必须设置东亚字体回退**：`rPr.set(qn("a:eaTypeface"), fn)` —— 否则中文可能以宋体渲染
- 行距默认：正文 `ls=1.2`，卡片内 `ls=1.45`

---

## 4. 布局尺寸速查 / Layout Dimensions

### 4.1 画布基准

```
画布: 10.0 × 5.625"（16:9 宽屏）
左边距（内容）: 0.5"
右边距（页码）: 9.0" 起
页脚线 y: 5.25"（内容底部不可超出此线）
内容有效高度: ~4.2"（从 y≈1.0 到 y≈5.2）
```

### 4.2 常用双栏尺寸

```
等宽双栏（均分）:
  左: l=0.4, w=4.4  |  右: l=5.2, w=4.4  |  间隙: 0.4"

非对称双栏（左宽右窄）:
  左: l=0.5, w=5.5  |  右: l=6.4, w=3.1  |  间隙: 0.5"

非对称双栏（左窄右宽）:
  左: l=0.4, w=3.5  |  右: l=4.2, w=5.3  |  间隙: 0.3"
```

### 4.3 常用三栏尺寸

```
三图并排:
  左: l=0.4, w=3.0  |  中: l=3.5, w=3.0  |  右: l=6.6, w=3.0  |  间隙: 0.1"
```

### 4.4 卡片/图片内边距

```
cd() 内部:
  标题左/上 padding: 0.15" / 0.08"
  正文左 padding: 0.15"，上 padding: 0.36"（标题下方）
  正文区域: w - 0.28", h - 0.42"

plot_card() 内部:
  图片 padding: 0.05"（四边）
  标题占用: 顶部 0.25" + 额外 0.05"
  顶部强调线: 0.03" 厚
```

---

## 5. cd() 容量计算 / Content Card Capacity

### 5.1 核心公式

```
可用 body 高度:  h_body = h_card - 0.42  (英寸)
每行占用高度:    h_line = fs × ls / 72   (英寸)
最大行数:        N_max = floor(h_body / h_line)
```

### 5.2 常见卡片容量对照表

`cd()` body 默认 `fs=9.5, ls=1.45`，每行 ≈ 0.191 英寸。

| 卡片高度 h_card | body 高度 h_body | 最大行数 |
|-----------------|------------------|----------|
| 0.8" | 0.38" | 2 行 |
| 1.0" | 0.58" | 3 行 |
| 1.2" | 0.78" | 4 行 |
| 1.4" | 0.98" | 5 行 |
| 1.6" | 1.18" | 6 行 |
| 1.8" | 1.38" | 7 行 |
| 2.0" | 1.58" | 8 行 |

### 5.3 验证方法

编写代码后、运行生成前，对每个 `cd()` 调用的 body 文本数行数：
1. 统计 `\n` 数量 + 1 = 逻辑行数
2. 对每行估算：按卡片宽度 `w - 0.28` 和 9.5pt 字号，中文约每行容纳 25-30 字。超过则自动换行，实际行数翻倍
3. 对照上表确认 `h_card` 足够

**快速检查：** 如果 `cd()` 的 body 文本中 `\n` 超过 4 个，至少需要 `h_card ≥ 1.2"`。

---

## 6. 文本换行行数估算 / Text Wrapping Estimation

这是**最容易出错**的环节。`\n` 数量不等于实际渲染行数——长文本在固定宽度内会自动换行。

### 6.1 核心公式

以 `cd()` body 默认 `fs=9.5` 微软雅黑为例：

```
字符宽度:
  中文字符 ≈ 9.5/72 ≈ 0.132"
  英文/数字 ≈ 0.066"（中文的一半宽）

每行容纳中文字符数: chars_per_line = floor((w_card - 0.28) / 0.132)

等效字符数 (eq_chars):
  每个中文字符 = 1.0
  每个英文/数字 = 0.5
  每个标点符号 ≈ 0.5（半角）或 1.0（全角）

每个逻辑行的等效字符数 = Σ(eq_char for char in line)

实际渲染行数 = Σ ceil(该逻辑行等效字符数 / chars_per_line)
                for line in body_text.split('\n')
```

### 6.2 常见卡片宽度的速查表

| 卡片宽度 w | body 宽度 (w-0.28) | 每行容纳中文 | 备注 |
|------------|-------------------|-------------|------|
| 4.8" | 4.52" | ~34 字 | 半宽卡片 |
| 4.4" | 4.12" | ~31 字 | 标准双栏 |
| 4.0" | 3.72" | ~28 字 | 略窄双栏 |
| 3.1" | 2.82" | ~21 字 | 窄栏（右栏） |
| 2.8" | 2.52" | ~19 字 | 极窄栏 |
| 5.8" | 5.52" | ~41 字 | 大半宽 |
| 9.2" | 8.92" | ~67 字 | 全宽 |

### 6.3 手动估算示例

body 文本：
```
基于Flask的轻量级B/S辅助诊断原型，前端三栏布局：
1. 分级结果展示：DR等级概率分布的环形图
2. 病灶分割可视化：六类病灶的预测掩码叠加显示
3. 可解释性热力图：Grad-CAM生成的模型关注区域

后端推理流水线：预处理→分割→分级→Grad-CAM生成
```

在宽度 w=4.8" 的 cd() 中（body 宽 4.52"，约 34 字/行）：

| 逻辑行 | 实际字数 | 等效字符* | 渲染行数 | 说明 |
|--------|---------|-----------|---------|------|
| "基于Flask的轻量级B/S辅助诊断原型，前端三栏布局：" | 26 字 | ~26 | 1 行 | 26 ≤ 34 |
| "1. 分级结果展示：DR等级概率分布的环形图" | 22 字 | ~22 | 1 行 | 22 ≤ 34 |
| "2. 病灶分割可视化：六类病灶的预测掩码叠加显示" | 24 字 | ~24 | 1 行 | 24 ≤ 34 |
| "3. 可解释性热力图：Grad-CAM生成的模型关注区域" | 28 字 | ~30 | 1 行 | 30 ≤ 34 |
| ""（空行） | 0 | 0 | 1 行 | 空行也占一行 |
| "后端推理流水线：预处理→分割→分级→Grad-CAM生成" | 26 字 | ~26 | 1 行 | 26 ≤ 34 |

**总渲染行数 = 6 行** → 最小 `h_card = 0.42 + 6 × 0.191 + 0.05 = 1.62"` → 建议 `h_card = 1.7"`

*\*英文/数字按 0.5 等效字符计*

### 6.4 常见错误

| 错误 | 后果 | 纠正 |
|------|------|------|
| 只数 `\n`，不考虑自动换行 | 高度严重不足 | 长行必须按每行容纳字数折算额外行 |
| 忽略英文/数字宽度 | 混合文本估算偏少 | 英文/数字算 0.5 等效字符 |
| 忘记空行也占高度 | 少算一行 | `\n\n` = 中间有空行 |
| 卡片太窄（w < 3"） | 中英文混合时换行频繁 | 优先加宽卡片，其次减小字号 |
