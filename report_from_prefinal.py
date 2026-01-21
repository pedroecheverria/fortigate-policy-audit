#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, LongTable, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors


# ---------- Rules / Checks ----------
def is_all_token(value: str) -> bool:
    """
    True si el campo contiene el token 'all' (case-insensitive) como elemento
    en lista separada por comas: 'all', 'ALL', 'all,foo', 'foo,all', etc.
    """
    if value is None:
        return False
    s = str(value).strip()
    if not s or s == "N/A":
        return False
    parts = [p.strip().lower() for p in s.split(",")]
    return any(p == "all" for p in parts)

def is_potentially_permissive(row: dict) -> bool:
    if should_skip_permissive(row):
        return False

    return (
        is_all_token(row.get("srcaddr", "")) or
        is_all_token(row.get("dstaddr", "")) or
        is_all_token(row.get("services", ""))
    )


def fmt_dt(v) -> str:
    """
    Best-effort: '2026-01-21T10:07:39+01:00' -> '2026-01-21 10:07:39'
    Mantiene 'N/A' si no hay valor.
    """
    if v is None:
        return "N/A"
    s = str(v).strip()
    if not s or s == "N/A":
        return "N/A"
    s = s.replace("T", " ")
    for sep in ["+", "Z"]:
        if sep in s:
            s = s.split(sep, 1)[0]
    return s

def should_skip_permissive(row: dict) -> bool:
    """
    Excluye policies que NO queremos evaluar como "permisivas".
    - policy_id == 0 suele ser implícita / sistema (deny/implicit), según tu salida monitor.
    """
    try:
        return int(row.get("policy_id", -1)) == 0
    except Exception:
        return False

# ---------- PDF helpers ----------
def build_table(data, col_widths, header_bg=colors.HexColor("#0B3D91")):
    t = LongTable(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), header_bg),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9.2),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#D0D7DE")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.HexColor("#F7F9FB")]),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    return t


def generate_pdf(prefinal_csv: Path, out_pdf: Path) -> None:
    if not prefinal_csv.exists():
        raise FileNotFoundError(f"No encuentro el archivo: {prefinal_csv.resolve()}")

    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold",
                           fontSize=20, leading=24, spaceAfter=12)
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontName="Helvetica-Bold",
                        fontSize=14, leading=18, spaceBefore=12, spaceAfter=8,
                        textColor=colors.HexColor("#0B3D91"))
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                        fontSize=12, leading=15, spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, leading=13)
    small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=9, leading=12,
                           textColor=colors.HexColor("#444444"))
    tiny = ParagraphStyle("tiny", parent=styles["BodyText"], fontSize=8.6, leading=11,
                          textColor=colors.HexColor("#444444"))

    df = pd.read_csv(prefinal_csv, keep_default_na=False)
    df["policy_name"] = df["policy_name"].replace("", "N/A")


    # Asegura columnas mínimas esperadas
    needed = ["policy_id","policy_name","bytes","packets","first_used","last_used",
              "srcintf","dstintf","srcaddr","dstaddr","services","status"]
    for c in needed:
        if c not in df.columns:
            df[c] = "N/A"

    df["bytes"] = pd.to_numeric(df["bytes"], errors="coerce").fillna(0).astype(int)
    df["packets"] = pd.to_numeric(df["packets"], errors="coerce").fillna(0).astype(int)
    df["first_used"] = df["first_used"].apply(fmt_dt)
    df["last_used"] = df["last_used"].apply(fmt_dt)

    with_traffic = df[df["bytes"] > 0].copy()
    no_traffic = df[df["bytes"] == 0].copy()
    permissive = df[df.apply(lambda r: is_potentially_permissive(r.to_dict()), axis=1)].copy()

    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    doc = SimpleDocTemplate(
        str(out_pdf),
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=1.8*cm,
        bottomMargin=1.6*cm
    )

    story = [
        Paragraph("FortiGate Firewall Policy Audit Report", title),
        Paragraph(f"Generated: {generated}", small),
        Spacer(1, 10),
        Paragraph(
            f"<b>Total policies:</b> {len(df)} | "
            f"<b>With traffic:</b> {len(with_traffic)} | "
            f"<b>No traffic:</b> {len(no_traffic)} | "
            f"<b>Potentially permissive:</b> {len(permissive)}",
            body
        ),
        Spacer(1, 14),
    ]

    # -------- Section 1: Traffic / No traffic --------
    story += [
        Paragraph("1. Traffic Usage Overview", h1),
        Paragraph("Policies grouped by whether traffic has been observed (based on the <b>bytes</b> counter).", body),
        Paragraph("1.1 Policies with traffic", h2),
    ]

    if len(with_traffic) == 0:
        story.append(Paragraph("No policies with traffic were found.", body))
    else:
        data = [["ID","Policy","Bytes","Pkts","First used","Last used"]]
        for _, r in with_traffic.sort_values("policy_id").iterrows():
            data.append([
                str(r["policy_id"]),
                Paragraph(str(r["policy_name"]), tiny),
                f'{int(r["bytes"]):,}',
                f'{int(r["packets"]):,}',
                Paragraph(str(r["first_used"]), tiny),
                Paragraph(str(r["last_used"]), tiny),
            ])
        # 17 cm de ancho útil aprox (A4 - márgenes)
        story.append(build_table(data, [1.2*cm, 5.6*cm, 2.0*cm, 1.6*cm, 3.3*cm, 3.3*cm]))

    story += [
        Spacer(1, 12),
        Paragraph("1.2 Policies with no traffic", h2),
        Paragraph("Policies below have <b>bytes = 0</b> and should be reviewed.", body),
    ]

    if len(no_traffic) == 0:
        story.append(Paragraph("No policies with zero traffic were found.", body))
    else:
        data = [["ID","Policy","Bytes","Notes"]]
        for _, r in no_traffic.sort_values("policy_id").iterrows():
            data.append([
                str(r["policy_id"]),
                Paragraph(str(r["policy_name"]), tiny),
                f'{int(r["bytes"]):,}',
                Paragraph("No traffic observed in current counters.", tiny),
            ])
        story.append(build_table(data, [1.2*cm, 8.5*cm, 2.0*cm, 5.3*cm]))

    # -------- Section 2: Permissive --------
    story.append(PageBreak())
    story += [
        Paragraph("2. Potentially Permissive Rules", h1),
        Paragraph(
            "Flagged when <b>srcaddr</b>, <b>dstaddr</b>, or <b>services</b> contains <b>all</b>. "
            "Requires administrator review.",
            body
        ),
        Spacer(1, 10),
    ]

    if len(permissive) == 0:
        story.append(Paragraph("No potentially permissive policies were found.", body))
    else:
        data = [["ID","Policy","St","In","Out","Src","Dst","Svc","Finding"]]
        for _, r in permissive.sort_values("policy_id").iterrows():
            data.append([
                str(r["policy_id"]),
                Paragraph(str(r["policy_name"]), tiny),
                Paragraph(str(r.get("status","N/A")), tiny),
                Paragraph(str(r.get("srcintf","N/A")), tiny),
                Paragraph(str(r.get("dstintf","N/A")), tiny),
                Paragraph(str(r.get("srcaddr","N/A")), tiny),
                Paragraph(str(r.get("dstaddr","N/A")), tiny),
                Paragraph(str(r.get("services","N/A")), tiny),
                Paragraph("Potentially permissive - requires administrator analysis.", tiny),
            ])
        story.append(build_table(
            data,
            [1.0*cm, 3.6*cm, 0.9*cm, 1.1*cm, 1.1*cm, 2.6*cm, 2.6*cm, 1.7*cm, 2.4*cm]
        ))

    def on_page(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(doc_.leftMargin, 1.1*cm, "FortiGate Policy Audit Report")
        canvas.drawRightString(A4[0]-doc_.rightMargin, 1.1*cm, f"Page {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)


if __name__ == "__main__":
    in_csv = Path("pre_final.csv")          # <- tu archivo real
    out_pdf = Path("policy_audit_report.pdf")
    generate_pdf(in_csv, out_pdf)
    print(f"OK -> {out_pdf.resolve()}")
