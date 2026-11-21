"""
Professional Arabic work-contract PDF — single A4 page, full height.
ReportLab (canvas) + Amiri font + arabic-reshaper + python-bidi.
"""
import os, io
from datetime import date

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdf_canvas

# ── Paths ──────────────────────────────────────────────────────────────────
_HERE   = os.path.dirname(__file__)
_STATIC = os.path.join(_HERE, "static_files")
HEADER_PATH  = os.path.join(_STATIC, "header.png")
FONT_REGULAR = os.path.join(_STATIC, "Amiri-Regular.ttf")
FONT_BOLD    = os.path.join(_STATIC, "Amiri-Bold.ttf")

# ── Colors ─────────────────────────────────────────────────────────────────
GREEN       = colors.HexColor("#017B6A")
GREEN_LIGHT = colors.HexColor("#1BA078")
TEAL_BG     = colors.HexColor("#edf7f4")
GRAY_BG     = colors.HexColor("#f5f5f5")
GRAY_LINE   = colors.HexColor("#dddddd")
WHITE       = colors.white
TEXT_DARK   = colors.HexColor("#1a1a1a")
TEXT_GRAY   = colors.HexColor("#666666")
ART_BG      = colors.HexColor("#f9fffe")


def _register_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    try:
        pdfmetrics.registerFont(TTFont("Amiri", FONT_REGULAR))
        pdfmetrics.registerFont(TTFont("AmiriBold", FONT_BOLD))
    except Exception:
        pass


def ar(text: str) -> str:
    """Reshape + bidi Arabic text so ReportLab (LTR canvas) renders it correctly."""
    if not text:
        return "—"
    return get_display(arabic_reshaper.reshape(str(text)))


def _month_ar(dt: date) -> str:
    months = ["يناير","فبراير","مارس","أبريل","مايو","يونيو",
              "يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"]
    return f"{dt.day} {months[dt.month - 1]} {dt.year}"


def _wrap(c, raw_text: str, max_w: float, font: str, size: float) -> list[str]:
    """Split raw Arabic (pre-reshape) text into display lines fitting max_w."""
    words = raw_text.split()
    lines, cur = [], []
    for w in words:
        trial = ar(" ".join(cur + [w]))
        if c.stringWidth(trial, font, size) <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(ar(" ".join(cur)))
            cur = [w]
    if cur:
        lines.append(ar(" ".join(cur)))
    return lines or [ar(raw_text)]


def generate_contract_pdf(employee) -> bytes:
    _register_fonts()

    buf = io.BytesIO()
    W, H = A4          # 595.28 × 841.89 pt
    c = pdf_canvas.Canvas(buf, pagesize=A4)

    today     = date.today()
    date_str  = _month_ar(today)
    start_raw = employee.subscription_date
    start_str = _month_ar(start_raw) if start_raw else "—"
    salary_str  = f"{int(employee.salary):,}".replace(",", " ") if employee.salary else "—"
    job_title   = (getattr(employee.job, "display_title", None)
                   or getattr(employee.job, "title", "—")) if employee.job else "—"
    branch_name = employee.branche.nom if employee.branche else "—"
    emp_name    = employee.full_name or "—"
    emp_phone   = employee.phone or "—"
    emp_id_num  = employee.id_number or "—"
    contract_num = f"{today.year}-{today.month:02d}-{employee.id or 0:03d}"

    # ── layout constants ───────────────────────────────────────────────────
    MX  = 1.4 * cm          # horizontal margin
    IW  = W - 2 * MX        # inner width  ≈ 511 pt
    TOP = H - 1.2 * cm      # start drawing from here downward

    # Header image: keep natural aspect ratio at full inner width
    HEADER_RATIO = 2473 / 475          # px width / px height
    LOGO_H       = IW / HEADER_RATIO   # ≈ 98 pt ≈ 3.46 cm

    # ── FIXED TOP HEIGHT (cumulative) ─────────────────────────────────────
    META_H      = 0.65 * cm
    TITLE_H     = 1.0 * cm
    PREAMBLE_H  = 0.65 * cm
    COLS_H      = 2.95 * cm
    DIV_H       = 0.75 * cm

    TOP_BLOCK = LOGO_H + META_H + TITLE_H + PREAMBLE_H + COLS_H + DIV_H  # ≈ 8.6 cm

    # ── FIXED BOTTOM HEIGHT ───────────────────────────────────────────────
    SIG_H    = 1.9 * cm
    FOOTER_H = 0.9 * cm
    BOT_BLOCK = SIG_H + FOOTER_H  # ≈ 2.8 cm

    # ── Space available for 5 articles ────────────────────────────────────
    TOTAL_H       = H - 1.2 * cm - 0.8 * cm   # top + bottom margin ≈ 827 pt
    ART_POOL      = TOTAL_H - TOP_BLOCK - BOT_BLOCK
    ART_SLOT      = ART_POOL / 5               # height per article

    # ══════════════════════════════════════════════════════════════════════
    # 1 ▸ LOGO
    # ══════════════════════════════════════════════════════════════════════
    y = TOP
    if os.path.exists(HEADER_PATH):
        c.drawImage(HEADER_PATH, MX, y - LOGO_H,
                    width=IW, height=LOGO_H,
                    preserveAspectRatio=False, mask='auto')
    y -= LOGO_H

    # ══════════════════════════════════════════════════════════════════════
    # 2 ▸ META BAR
    # ══════════════════════════════════════════════════════════════════════
    c.setFillColor(TEAL_BG)
    c.rect(MX, y - META_H, IW, META_H, fill=1, stroke=0)
    c.setFont("AmiriBold", 8)
    c.setFillColor(GREEN)
    c.drawCentredString(W / 2, y - META_H + 2.5 * mm, ar("عقد عمل إلكتروني"))
    c.setFont("Amiri", 7.5)
    c.setFillColor(TEXT_GRAY)
    c.drawString(MX + 3 * mm, y - META_H + 2.5 * mm, ar(f"التاريخ: {date_str}"))
    c.drawRightString(W - MX - 3 * mm, y - META_H + 2.5 * mm, ar(f"رقم العقد: {contract_num}"))
    y -= META_H

    # ══════════════════════════════════════════════════════════════════════
    # 3 ▸ TITLE BAR
    # ══════════════════════════════════════════════════════════════════════
    c.setFillColor(GREEN)
    c.rect(MX, y - TITLE_H, IW, TITLE_H, fill=1, stroke=0)
    c.setFont("AmiriBold", 17)
    c.setFillColor(WHITE)
    c.drawCentredString(W / 2, y - TITLE_H + 3.5 * mm, ar("عـقـد عـمـل"))
    y -= TITLE_H

    # ══════════════════════════════════════════════════════════════════════
    # 4 ▸ PREAMBLE
    # ══════════════════════════════════════════════════════════════════════
    c.setFont("Amiri", 8.5)
    c.setFillColor(TEXT_GRAY)
    preamble = ar(
        f"تمّ إبرام هذا العقد بين الطرفين الآتي ذكرهما وفق الشروط والبنود المحددة أدناه، "
        f"بتاريخ {date_str}، واستناداً إلى أحكام قانون العمل المعمول به."
    )
    c.drawCentredString(W / 2, y - PREAMBLE_H + 2.5 * mm, preamble)
    y -= PREAMBLE_H

    # ══════════════════════════════════════════════════════════════════════
    # 5 ▸ TWO-COLUMN PARTY BOXES
    # ══════════════════════════════════════════════════════════════════════
    gap      = 4 * mm
    col_w    = (IW - gap) / 2
    box_top  = y
    box_btm  = y - COLS_H

    # ── RIGHT: Employer (gray) ──
    rx = W - MX - col_w
    c.setFillColor(GRAY_BG)
    c.setStrokeColor(GRAY_LINE)
    c.setLineWidth(0.5)
    c.roundRect(rx, box_btm, col_w, COLS_H, 4, fill=1, stroke=1)

    lbl_y = box_top - 5 * mm
    c.setFont("AmiriBold", 8)
    c.setFillColor(TEXT_GRAY)
    c.drawCentredString(rx + col_w / 2, lbl_y, ar("الطرف الأول — صاحب العمل"))
    c.setFont("AmiriBold", 10.5)
    c.setFillColor(GREEN)
    c.drawCentredString(rx + col_w / 2, lbl_y - 7 * mm, ar("محضرة المنارة والرباط"))
    c.setFont("Amiri", 9)
    c.setFillColor(TEXT_GRAY)
    c.drawCentredString(rx + col_w / 2, lbl_y - 13 * mm, ar(f"الفرع: {branch_name}"))
    c.setFont("AmiriBold", 9.5)
    c.setFillColor(GREEN)
    c.drawCentredString(rx + col_w / 2, lbl_y - 19 * mm, ar(f"الراتب: {salary_str} أوقية"))

    # ── LEFT: Employee (green) ──
    lx = MX
    # green header strip
    hdr_h = 0.9 * cm
    c.setFillColor(GREEN)
    c.roundRect(lx, box_btm, col_w, COLS_H, 4, fill=1, stroke=0)
    # white content area
    c.setFillColor(colors.HexColor("#f0faf7"))
    c.rect(lx, box_btm, col_w, COLS_H - hdr_h, fill=1, stroke=0)
    # border
    c.setStrokeColor(GREEN_LIGHT)
    c.setLineWidth(0.8)
    c.roundRect(lx, box_btm, col_w, COLS_H, 4, fill=0, stroke=1)

    # employee name in white header
    c.setFont("AmiriBold", 11)
    c.setFillColor(WHITE)
    c.drawCentredString(lx + col_w / 2, box_top - hdr_h + 2 * mm, ar(emp_name))

    # detail rows
    det_start = box_top - hdr_h - 5 * mm
    details = [
        (ar("رقم الهوية:"), ar(emp_id_num),   ar("الهاتف:"),      ar(emp_phone)),
        (ar("المنصب:"),     ar(job_title),     ar("الفرع:"),       ar(branch_name)),
        (ar("تاريخ الالتحاق:"), ar(start_str), "",                ""),
    ]
    half = col_w / 2
    dy = det_start
    for rl, rv, ll, lv in details:
        c.setFont("Amiri", 7.5)
        c.setFillColor(TEXT_GRAY)
        rw = c.stringWidth(rl, "Amiri", 7.5)
        c.drawRightString(lx + col_w - 3 * mm, dy, rl)
        c.setFont("Amiri", 7.5)
        c.setFillColor(TEXT_DARK)
        c.drawRightString(lx + col_w - 3 * mm - rw - 1 * mm, dy, rv)
        if ll:
            c.setFont("Amiri", 7.5)
            c.setFillColor(TEXT_GRAY)
            lw = c.stringWidth(ll, "Amiri", 7.5)
            c.drawRightString(lx + half, dy, ll)
            c.setFont("Amiri", 7.5)
            c.setFillColor(TEXT_DARK)
            c.drawRightString(lx + half - lw - 1 * mm, dy, lv)
        dy -= 6 * mm

    y -= COLS_H

    # ══════════════════════════════════════════════════════════════════════
    # 6 ▸ SECTION DIVIDER
    # ══════════════════════════════════════════════════════════════════════
    y -= 4 * mm
    div_label = ar("بنود العقد")
    dw = c.stringWidth(div_label, "AmiriBold", 10)
    dx = (W - dw) / 2
    c.setStrokeColor(GREEN_LIGHT)
    c.setLineWidth(0.8)
    c.line(MX, y - 2 * mm, dx - 4 * mm, y - 2 * mm)
    c.line(dx + dw + 4 * mm, y - 2 * mm, W - MX, y - 2 * mm)
    c.setFont("AmiriBold", 10)
    c.setFillColor(GREEN)
    c.drawString(dx, y - 1 * mm - 2.5, div_label)
    y -= DIV_H

    # ══════════════════════════════════════════════════════════════════════
    # 7 ▸ ARTICLES (fill ART_POOL evenly)
    # ══════════════════════════════════════════════════════════════════════
    articles_raw = [
        ("المادة الأولى", "طبيعة العمل",
         f"يلتزم الطرف الثاني بالعمل لدى الطرف الأول بمنصب {job_title}، ويمارس مهامه وفق اللوائح "
         f"والأنظمة الداخلية المعمول بها لدى محضرة المنارة والرباط، ويخضع لإشراف الإدارة المباشرة."),
        ("المادة الثانية", "الراتب والتعويضات",
         f"يستحق الطرف الثاني راتباً شهرياً إجمالياً قدره {salary_str} أوقية، يُصرف في نهاية كل شهر "
         f"ميلادي وفق إجراءات الصرف المعتمدة، ويخضع للمراجعة الدورية وفق سياسة المؤسسة."),
        ("المادة الثالثة", "الالتزامات والواجبات",
         "يلتزم الموظف بأداء مهامه بأمانة وإخلاص، والمحافظة على أسرار المؤسسة وممتلكاتها، "
         "والامتثال لجميع التعليمات الصادرة عن الإدارة، والحضور في المواعيد المحددة وعدم الغياب "
         "إلا بإذن مسبق من المسؤول المباشر."),
        ("المادة الرابعة", "مدة العقد",
         f"يُعدّ هذا العقد سارياً اعتباراً من تاريخ {start_str}، ويستمر ما لم يُخطَر "
         "أحد الطرفين الآخر بالرغبة في إنهائه وفق الإجراءات القانونية المعمول بها."),
        ("المادة الخامسة", "إنهاء العقد",
         "يحق لكلا الطرفين إنهاء هذا العقد بإشعار مسبق لا يقل عن ثلاثين (30) يوماً، "
         "مع الوفاء بجميع الالتزامات المترتبة وفق قانون العمل. في حال الإخلال ببنود العقد "
         "يحق للطرف المتضرر المطالبة بالتعويض."),
    ]

    BODY_SIZE   = 9.5
    TITLE_SIZE  = 10
    LINE_H      = BODY_SIZE * 1.65   # body line height
    TITLE_H_PT  = TITLE_SIZE * 1.4
    ART_INNER_W = IW - 8 * mm        # text area inside the accent bar
    ART_PADDING = 4 * mm             # internal padding

    for num_ar, title_ar, body_raw in articles_raw:
        body_lines = _wrap(c, body_raw, ART_INNER_W - 2 * ART_PADDING, "Amiri", BODY_SIZE)
        n_lines    = len(body_lines)
        content_h  = TITLE_H_PT + n_lines * LINE_H + 2 * ART_PADDING

        # background box
        c.setFillColor(ART_BG)
        c.setStrokeColor(colors.HexColor("#d6f0ea"))
        c.setLineWidth(0.4)
        c.roundRect(MX, y - content_h, IW, content_h, 3, fill=1, stroke=1)

        # green left-side accent strip
        c.setFillColor(GREEN_LIGHT)
        c.rect(W - MX - 4 * mm, y - content_h, 4 * mm, content_h, fill=1, stroke=0)
        # round top-right corner of strip
        c.setFillColor(ART_BG)
        c.rect(MX, y - content_h, IW - 4 * mm, content_h, fill=0, stroke=0)

        # title line
        ty = y - ART_PADDING - TITLE_H_PT + 3
        c.setFont("AmiriBold", TITLE_SIZE)
        c.setFillColor(GREEN)
        heading = ar(f"{num_ar} — {title_ar}")
        c.drawRightString(W - MX - 6 * mm, ty, heading)

        # body lines
        by = ty - LINE_H
        c.setFont("Amiri", BODY_SIZE)
        c.setFillColor(TEXT_DARK)
        for line in body_lines:
            c.drawRightString(W - MX - 6 * mm, by, line)
            by -= LINE_H

        # bottom margin + gap to next article
        gap_between = (ART_SLOT - content_h) / 2  # centre vertically in slot
        y -= content_h + (ART_SLOT - content_h)   # move down by full slot

    # ══════════════════════════════════════════════════════════════════════
    # 8 ▸ SIGNATURES (2 boxes, no seal)
    # ══════════════════════════════════════════════════════════════════════
    y -= 4 * mm
    c.setStrokeColor(GRAY_LINE)
    c.setLineWidth(0.5)
    c.line(MX, y, W - MX, y)
    y -= 4 * mm

    sig_w  = (IW - 6 * mm) / 2
    sig_bh = SIG_H

    # Employee box (right side)
    ex = W - MX - sig_w
    c.setFillColor(colors.HexColor("#fafffe"))
    c.setStrokeColor(GREEN_LIGHT)
    c.setLineWidth(0.6)
    c.roundRect(ex, y - sig_bh, sig_w, sig_bh, 4, fill=1, stroke=1)
    c.setFont("AmiriBold", 9)
    c.setFillColor(GREEN)
    c.drawCentredString(ex + sig_w / 2, y - 7 * mm, ar("توقيع الموظف"))
    c.setFont("Amiri", 8.5)
    c.setFillColor(TEXT_GRAY)
    c.drawCentredString(ex + sig_w / 2, y - 13 * mm, ar(emp_name))
    # signature line
    c.setStrokeColor(GRAY_LINE)
    c.setLineWidth(0.7)
    c.line(ex + 6 * mm, y - sig_bh + 7 * mm, ex + sig_w - 6 * mm, y - sig_bh + 7 * mm)

    # Employer box (left side)
    ox = MX
    c.setFillColor(colors.HexColor("#fafffe"))
    c.setStrokeColor(GREEN_LIGHT)
    c.setLineWidth(0.6)
    c.roundRect(ox, y - sig_bh, sig_w, sig_bh, 4, fill=1, stroke=1)
    c.setFont("AmiriBold", 9)
    c.setFillColor(GREEN)
    c.drawCentredString(ox + sig_w / 2, y - 7 * mm, ar("توقيع صاحب العمل"))
    c.setFont("Amiri", 8.5)
    c.setFillColor(TEXT_GRAY)
    c.drawCentredString(ox + sig_w / 2, y - 13 * mm, ar("محضرة المنارة والرباط"))
    c.setStrokeColor(GRAY_LINE)
    c.setLineWidth(0.7)
    c.line(ox + 6 * mm, y - sig_bh + 7 * mm, ox + sig_w - 6 * mm, y - sig_bh + 7 * mm)

    y -= sig_bh + 4 * mm

    # ══════════════════════════════════════════════════════════════════════
    # 9 ▸ FOOTER
    # ══════════════════════════════════════════════════════════════════════
    c.setStrokeColor(GRAY_LINE)
    c.setLineWidth(0.3)
    c.line(MX, y, W - MX, y)
    c.setFont("Amiri", 7.5)
    c.setFillColor(colors.HexColor("#aaaaaa"))
    footer = ar(f"وثيقة رسمية صادرة عن نظام الإدارة الإلكترونية — محضرة المنارة والرباط — {date_str}")
    c.drawCentredString(W / 2, y - 5 * mm, footer)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
