"""
Daily financial report (التقرير اليومي) as PDF — same layout as the former pdfmake print
of the Angular /dailly page, but rendered server-side so Arabic text, numbers and
brackets are ordered correctly (arabic-reshaper + python-bidi).
"""
import io
import os
import re
import unicodedata

import arabic_reshaper
from bidi.algorithm import get_display
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, SimpleDocTemplate, Spacer, Table, TableStyle

_STATIC = os.path.join(os.path.dirname(__file__), "static_files")
HEADER_IMG = os.path.join(_STATIC, "report_header.png")   # 2400 x 163 banner
FONT_PATH = os.path.join(_STATIC, "ExpoArabic-Book.ttf")
FONT = "ExpoArabic"

GREEN = colors.HexColor("#1BA078")
ROW_LIGHT = colors.HexColor("#f9fafb")
ROW_TOTAL = colors.HexColor("#e5e7eb")

PAGE_MARGIN = 40                       # same as pdfmake's default page margins
CONTENT_W = A4[0] - 2 * PAGE_MARGIN    # 515pt
# visual column order (left → right): bank out | bank in | bank | fund out | fund in | details | date
COL_W = [50, 50, 56, 50, 50, None, 58]
COL_W[5] = CONTENT_W - sum(w for w in COL_W if w)
CELL_PAD_X = 4


_font_chars = None


def _register_font():
    global _font_chars
    if FONT not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT, FONT_PATH))
    if _font_chars is None:
        _font_chars = set(pdfmetrics.getFont(FONT).face.charToGlyph)


def _fallback_missing_forms(text: str) -> str:
    """ExpoArabic has no isolated presentation forms (U+FE8D ا, U+FEAD ر, …): its base letters
    already carry the isolated shape, so swap any presentation form the font lacks for its base letter."""
    out = []
    for ch in text:
        if 0xFB50 <= ord(ch) <= 0xFEFF and ord(ch) not in _font_chars:
            decomp = unicodedata.decomposition(ch).split()
            base = [c for c in decomp if not c.startswith("<")]
            out.append("".join(chr(int(c, 16)) for c in base) if base else ch)
        else:
            out.append(ch)
    return "".join(out)


# Dates / times / decimals such as 2026-10-01, 08-2026, 17:37, 1500.50: inside Arabic text the bidi
# algorithm would reorder their parts ("01-10-2026"), so they are kept as one left-to-right unit.
_NUMBER_GROUP = re.compile(r"\d+(?:[-/.:]\d+)+")


def ar(text) -> str:
    """Logical Arabic/mixed text → visual order for ReportLab's left-to-right canvas."""
    if text is None or text == "":
        return ""
    _register_font()
    kept = []

    def _hold(m):
        kept.append(m.group(0))
        return chr(0xE000 + len(kept) - 1)     # private-use placeholder = one strong LTR character

    s = _NUMBER_GROUP.sub(_hold, str(text))
    s = get_display(_fallback_missing_forms(arabic_reshaper.reshape(s)), base_dir="R")
    for i, original in enumerate(kept):
        s = s.replace(chr(0xE000 + i), original)
    return s


def _wrap(text: str, max_w: float, size: float) -> str:
    """Wrap logical text into lines that fit max_w, then convert each line to visual order."""
    lines, cur = [], []
    for word in str(text).split():
        trial = " ".join(cur + [word])
        if cur and pdfmetrics.stringWidth(ar(trial), FONT, size) > max_w:
            lines.append(ar(" ".join(cur)))
            cur = [word]
        else:
            cur.append(word)
    if cur:
        lines.append(ar(" ".join(cur)))
    return "\n".join(lines)


def _money(v) -> str:
    try:
        return f"{float(v or 0):.2f}"
    except (TypeError, ValueError):
        return "0.00"


def _contact_phone(tx: dict) -> str:
    """Agent → student's agent → student → employee (same rule as the Angular page)."""
    agent = tx.get("agent") or {}
    student = tx.get("student") or {}
    s_agent = student.get("agent") or {}
    employee = tx.get("employee") or {}
    for p in (agent.get("phone"), agent.get("whatsapp_phone"),
              s_agent.get("phone"), s_agent.get("whatsapp_phone"),
              student.get("phone"), employee.get("phone")):
        if isinstance(p, str) and p.strip():
            return p.strip()
    return ""


def _tx_date(value) -> str:
    dt = parse_datetime(value) if isinstance(value, str) else value
    if not dt:
        return ""
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return dt.strftime("%Y/%m/%d | %H:%M")


def generate_dailly_pdf(transactions, totals, before, start_date, end_date, username=None) -> bytes:
    """
    transactions: serialized TransactionSerializer data (list of dicts)
    totals / before: the same dicts returned by /api/daillys/filter/
    """
    _register_font()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN, topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN,
        title="التقرير اليومي",
    )
    story = []

    # ── Banner ────────────────────────────────────────────────────────────
    story.append(Image(HEADER_IMG, width=CONTENT_W, height=CONTENT_W * 163 / 2400))
    story.append(Spacer(1, 5))

    # ── Print date (left) + title (right) ─────────────────────────────────
    now = timezone.localtime()
    head = Table(
        [[ar(f"بتاريخ: {now:%Y/%m/%d} | {now:%H:%M}"), ar("التقريـــــــــــر اليومـــــــــــي")]],
        colWidths=[CONTENT_W * 0.36, CONTENT_W * 0.64],
    )
    head.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (0, 0), 7),
        ("FONTSIZE", (1, 0), (1, 0), 13),
        ("TEXTCOLOR", (1, 0), (1, 0), GREEN),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(head)

    # ── From / to (/ user) ────────────────────────────────────────────────
    to_txt, from_txt = ar(f"إلـــــــــــى: {end_date}"), ar(f"مـــــــــــن: {start_date}")
    if username:
        row = [ar(f"اسم المستخــــــــــدم: {username}"), to_txt, from_txt]
        aligns = [("ALIGN", (0, 0), (0, 0), "LEFT"), ("ALIGN", (1, 0), (1, 0), "CENTER"),
                  ("ALIGN", (2, 0), (2, 0), "RIGHT")]
    else:
        row = [to_txt, from_txt]
        aligns = [("ALIGN", (0, 0), (0, 0), "LEFT"), ("ALIGN", (1, 0), (1, 0), "RIGHT")]
    period = Table([row], colWidths=[CONTENT_W / len(row)] * len(row))
    period.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), FONT), ("FONTSIZE", (0, 0), (-1, -1), 8)] + aligns))
    story.append(period)
    story.append(Spacer(1, 4))

    # ── Main table ────────────────────────────────────────────────────────
    data = [
        [ar("البنوك"), "", "", ar("الصندوق"), "", ar("التفاصيل"), ar("بتاريخ")],
        [ar("الخارج"), ar("الداخل"), ar("البنك"), ar("الخارج"), ar("الداخل"), "", ""],
        [_money(before.get("bank")), "", ar(before.get("bank_name") or ""),
         _money(before.get("fund")), "", ar(f"الرصيد قبل: {start_date}"), str(start_date or "")],
    ]
    style = [
        ("FONT", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), CELL_PAD_X),
        ("RIGHTPADDING", (0, 0), (-1, -1), CELL_PAD_X),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        # header rows
        ("SPAN", (0, 0), (2, 0)), ("SPAN", (3, 0), (4, 0)), ("SPAN", (5, 0), (5, 1)), ("SPAN", (6, 0), (6, 1)),
        ("BACKGROUND", (0, 0), (-1, 1), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 1), colors.white),
        ("FONTSIZE", (0, 0), (-1, 1), 10),
        ("ALIGN", (0, 0), (-1, 1), "CENTER"),
        # opening balance row
        ("SPAN", (0, 2), (1, 2)), ("SPAN", (3, 2), (4, 2)),
        ("BACKGROUND", (0, 2), (-1, 2), ROW_LIGHT),
        ("ALIGN", (0, 2), (4, 2), "CENTER"),
        ("ALIGN", (2, 2), (2, 2), "RIGHT"),
        ("ALIGN", (5, 2), (5, 2), "RIGHT"),
        ("ALIGN", (6, 2), (6, 2), "CENTER"),
    ]

    details_w = COL_W[5] - 2 * CELL_PAD_X
    for tx in transactions:
        bank = tx.get("bank") or {}
        is_fund = bool(bank) and bank.get("category") == 1
        is_plus, is_minus = tx.get("type") == "plus", tx.get("type") == "minus"
        amount = _money(tx.get("paid_amount"))
        parts = [
            (tx.get("employee") or {}).get("full_name"),
            tx.get("description"),
            _contact_phone(tx),
            f"رقم الوصل: {tx['receipt_id']}" if tx.get("receipt_id") else None,
        ]
        details = " • ".join(p for p in parts if p)
        r = len(data)
        data.append([
            amount if (is_minus and not is_fund) else "",
            amount if (is_plus and not is_fund) else "",
            ar(bank.get("bank_name")) if (bank and not is_fund) else "",
            amount if (is_minus and is_fund) else "",
            amount if (is_plus and is_fund) else "",
            _wrap(details, details_w, 7),
            _tx_date(tx.get("date")),
        ])
        style += [
            ("FONTSIZE", (0, r), (5, r), 7),
            ("FONTSIZE", (6, r), (6, r), 5.2),
            ("ALIGN", (0, r), (1, r), "CENTER"),
            ("ALIGN", (2, r), (2, r), "RIGHT"),
            ("ALIGN", (3, r), (4, r), "CENTER"),
            ("ALIGN", (5, r), (5, r), "RIGHT"),
            ("ALIGN", (6, r), (6, r), "CENTER"),
        ]

    fund, bank_t = totals.get("fund") or {}, totals.get("bank") or {}
    r = len(data)
    data.append([_money(bank_t.get("minus")), _money(bank_t.get("plus")), ar("المجاميع"),
                 _money(fund.get("minus")), _money(fund.get("plus")), ar("المجاميع"), ""])
    style += [("SPAN", (5, r), (6, r)), ("BACKGROUND", (0, r), (-1, r), ROW_LIGHT),
              ("ALIGN", (0, r), (1, r), "CENTER"), ("ALIGN", (2, r), (2, r), "RIGHT"),
              ("ALIGN", (3, r), (6, r), "CENTER")]

    r = len(data)
    data.append([
        _money((before.get("bank") or 0) + (bank_t.get("balance") or 0)), "", "",
        _money((before.get("fund") or 0) + (fund.get("balance") or 0)), "",
        ar("الرصيد الكلي"), "",
    ])
    style += [("SPAN", (0, r), (1, r)), ("SPAN", (3, r), (4, r)), ("SPAN", (5, r), (6, r)),
              ("BACKGROUND", (0, r), (-1, r), ROW_TOTAL), ("ALIGN", (0, r), (-1, r), "CENTER")]

    table = Table(data, colWidths=COL_W, repeatRows=2)
    table.setStyle(TableStyle(style))
    story.append(table)

    doc.build(story)
    return buf.getvalue()
