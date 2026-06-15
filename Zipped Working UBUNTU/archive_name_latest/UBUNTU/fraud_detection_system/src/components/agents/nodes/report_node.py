import os
import json
import re
from pathlib import Path
from datetime import datetime

# ReportLab Layout & Styling Engine
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


def clean_text_for_pdf(text: str) -> str:
    """Cleans up raw LLM markdown artifacts so they render beautifully in standard PDF text objects."""
    if not text:
        return "No analysis data recorded."
    
    # Safe construction avoids multi-line backtick string literal breaking text parsers
    triple_ticks = "`" * 3
    text = text.replace(f"{triple_ticks}json", "").replace(triple_ticks, "")
    
    # Convert Markdown bold (**text**) to HTML bold tags (<b>text</b>) for ReportLab Paragraphs
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)  
    text = text.replace("\n", "<br/>")
    return text.strip()


def report_node(state):
    tx = state["transaction"]
    tx_id = tx["transaction_id"]
    decision_data = state.get("decision_result", {})
    
    # Safely unpack the unified reasoning object
    raw_reasoning = state.get("reasoning_result", "{}")
    try:
        parsed_reasoning = json.loads(raw_reasoning)
    except Exception:
        parsed_reasoning = {"risk": "UNKNOWN", "confidence": 0.0, "summary": raw_reasoning}

    pdf_path = REPORT_DIR / f"{tx_id}.pdf"
    
    # 1. Setup Document Core (0.5 inch safety margins for data density)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    
    # 2. Setup Typography Stylesheet & Custom Color Palette
    styles = getSampleStyleSheet()
    
    # Custom Brand Colors
    PRIMARY_DARK = colors.HexColor("#0F172A")  # Deep Slate Blue
    TEXT_MUTED = colors.HexColor("#64748B")    # Slate Muted Gray
    BG_LIGHT = colors.HexColor("#F8FAFC")      # Soft White Gray
    BORDER_COLOR = colors.HexColor("#E2E8F0")  # Border Line Gray
    
    # Dynamic Verdict Colors
    is_approved = decision_data.get("approved", True)
    VERDICT_COLOR = colors.HexColor("#10B981") if is_approved else colors.HexColor("#EF4444")
    VERDICT_BG = colors.HexColor("#ECFDF5") if is_approved else colors.HexColor("#FEF2F2")

    # Typography Implementations (Explicit leading configurations prevent overlapping)
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=PRIMARY_DARK
    )
    meta_style = ParagraphStyle(
        'MetaText', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=12, textColor=TEXT_MUTED, alignment=TA_RIGHT
    )
    section_heading = ParagraphStyle(
        'SectionHeading', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=PRIMARY_DARK, spaceAfter=6
    )
    grid_label = ParagraphStyle(
        'GridLabel', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=TEXT_MUTED
    )
    grid_val = ParagraphStyle(
        'GridValue', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=11, textColor=PRIMARY_DARK
    )
    body_style = ParagraphStyle(
        'BodyTextCustom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor("#334155")
    )
    verdict_style = ParagraphStyle(
        'VerdictText', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=VERDICT_COLOR, alignment=TA_CENTER
    )

    # ----------------------------------------------------
    # HEADER SECTION
    # ----------------------------------------------------
    header_data = [
        [Paragraph("FRAUD INVESTIGATION AUDIT REPORT", title_style),
         Paragraph(f"<b>Generated:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br/><b>Analysis ID:</b> {state.get('analysis_id', 'N/A')}", meta_style)]
    ]
    header_table = Table(header_data, colWidths=[300, 240])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # ----------------------------------------------------
    # SYSTEM ACTION / VERDICT CALLOUT BOX
    # ----------------------------------------------------
    verdict_text = f"SYSTEM DECISION: {decision_data.get('system_action', 'REVIEW')} — STATUS: {'AUTHORIZED' if is_approved else 'BLOCKED'}"
    verdict_p = Paragraph(verdict_text, verdict_style)
    verdict_table = Table([[verdict_p]], colWidths=[540])
    verdict_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), VERDICT_BG),
        ('BOX', (0, 0), (-1, -1), 1.5, VERDICT_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(verdict_table)
    story.append(Spacer(1, 15))

    # ----------------------------------------------------
    # TRANSACTION INFORMATION METRICS GRID
    # ----------------------------------------------------
    story.append(Paragraph("1. TRANSACTION TELEMETRY PROFILE", section_heading))
    
    tx_grid_data = [
        [Paragraph("Transaction ID", grid_label), Paragraph(str(tx.get("transaction_id")), grid_val),
         Paragraph("Timestamp", grid_label), Paragraph(str(tx.get("transaction_timestamp")), grid_val)],
        [Paragraph("Customer ID", grid_label), Paragraph(str(tx.get("customer_id")), grid_val),
         Paragraph("Payment Method", grid_label), Paragraph(str(tx.get("payment_method")), grid_val)],
        [Paragraph("Device Fingerprint", grid_label), Paragraph(str(tx.get("device_id")), grid_val),
         Paragraph("IP Address", grid_label), Paragraph(str(tx.get("ip_address")), grid_val)],
        [Paragraph("Amount / Currency", grid_label), Paragraph(f"{tx.get('transaction_amount')} {tx.get('currency')}", grid_val),
         Paragraph("International", grid_label), Paragraph(str(tx.get("is_international")), grid_val)],
        [Paragraph("Origin Country", grid_label), Paragraph(str(tx.get("origin_country")), grid_val),
         Paragraph("Destination Country", grid_label), Paragraph(str(tx.get("destination_country")), grid_val)]
    ]
    
    tx_table = Table(tx_grid_data, colWidths=[110, 160, 110, 160])
    tx_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(tx_table)
    story.append(Spacer(1, 15))

    # ----------------------------------------------------
    # AI AGENT ANALYTICS REASONING EXPLANATIONS
    # ----------------------------------------------------
    story.append(Paragraph("2. SPECIALIZED FRAUD AGENTS INDEPENDENT VERDICTS", section_heading))
    
    # Clean output analysis fields for display
    behavioral_clean = clean_text_for_pdf(state.get('behavioral_result', {}).get('analysis', ''))
    network_clean = clean_text_for_pdf(state.get('network_result', {}).get('analysis', ''))
    compliance_clean = clean_text_for_pdf(state.get('compliance_result', {}).get('analysis', ''))

    agents_data = [
        [Paragraph("<b>BEHAVIORAL ENGINE FINDINGS</b>", grid_label)],
        [Paragraph(behavioral_clean, body_style)],
        [Spacer(1, 4)],
        [Paragraph("<b>NETWORK GRAPH LINKAGE ANALYSIS</b>", grid_label)],
        [Paragraph(network_clean, body_style)],
        [Spacer(1, 4)],
        [Paragraph("<b>LEGAL & SANCTIONS COMPLIANCE AUDIT</b>", grid_label)],
        [Paragraph(compliance_clean, body_style)]
    ]
    
    agents_table = Table(agents_data, colWidths=[540])
    agents_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0, 0), (0, 0), BG_LIGHT),
        ('BACKGROUND', (0, 3), (0, 3), BG_LIGHT),
        ('BACKGROUND', (0, 6), (0, 6), BG_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(agents_table)
    story.append(Spacer(1, 15))

    # ----------------------------------------------------
    # CENTRAL ORCHESTRATOR SUMMARY SYNTHESIS
    # ----------------------------------------------------
    conclusion_elements = [
        Paragraph("3. CENTRAL ORCHESTRATOR SUMMARY SYNTHESIS", section_heading),
        Paragraph(f"<b>Assessed Risk Level:</b> {parsed_reasoning.get('risk', 'MEDIUM')}  |  <b>Consensus Confidence:</b> {parsed_reasoning.get('confidence', 0.0)}", grid_val),
        Spacer(1, 6),
        Paragraph(clean_text_for_pdf(parsed_reasoning.get("summary", "")), body_style)
    ]
    
    # KeepTogether preserves elements on the same page layout split boundary seamlessly
    story.append(KeepTogether(conclusion_elements))

    # Build and write the final document file stream artifact
    doc.build(story)
    print(f"✅ Executed clean visual dashboard PDF generation -> saved to path: {pdf_path}")
    
    return {"report_result": {"report_path": str(pdf_path)}}