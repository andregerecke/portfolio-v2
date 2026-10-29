"""Build the downloadable CV from content/cv.json with ReportLab."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
NAVY = colors.HexColor('#10253e')
TEAL = colors.HexColor('#176e70')
MUTED = colors.HexColor('#526278')
RULE = colors.HexColor('#dce4eb')


def build(output: Path) -> None:
    cv = json.loads((ROOT / 'content/cv.json').read_text(encoding='utf-8'))
    font_root = Path('/usr/share/fonts/truetype/dejavu')
    if (font_root / 'DejaVuSans.ttf').exists():
        pdfmetrics.registerFont(TTFont('CV', str(font_root / 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('CV-Bold', str(font_root / 'DejaVuSans-Bold.ttf')))
        pdfmetrics.registerFontFamily('CV', normal='CV', bold='CV-Bold')
        font, bold = 'CV', 'CV-Bold'
    else:
        font, bold = 'Helvetica', 'Helvetica-Bold'
    base = ParagraphStyle('Body', fontName=font, fontSize=8.8, leading=12.8,
                          textColor=NAVY, spaceAfter=5, alignment=TA_LEFT)
    styles = {
        'body': base,
        'small': ParagraphStyle('Small', parent=base, fontSize=8, leading=11.5, textColor=MUTED),
        'heading': ParagraphStyle('Heading', parent=base, fontName=bold,
                                  fontSize=9.2, leading=13, textColor=TEAL,
                                  spaceBefore=15, spaceAfter=7, keepWithNext=True),
        'role': ParagraphStyle('Role', parent=base, fontName=bold, fontSize=10.2,
                               leading=14, spaceAfter=3, keepWithNext=True),
        'meta': ParagraphStyle('Meta', parent=base, fontSize=8, leading=11.5,
                               textColor=MUTED, spaceAfter=7, keepWithNext=True),
        'bullet': ParagraphStyle('Bullet', parent=base, leftIndent=10, bulletIndent=0,
                                 bulletFontName=font, bulletFontSize=7, spaceAfter=5),
        'name': ParagraphStyle('Name', parent=base, fontName=bold, fontSize=27,
                               leading=33, spaceAfter=4),
        'subtitle': ParagraphStyle('Subtitle', parent=base, fontName=bold,
                                   fontSize=10.5, leading=15, textColor=TEAL, spaceAfter=5),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=46, leftMargin=46,
                            topMargin=45, bottomMargin=40,
                            title=f"{cv['name']} - Curriculum Vitae",
                            author=cv['name'], subject=cv['positioning'])
    story = []

    def p(text, style='body'):
        return Paragraph(escape(text), styles[style])

    def heading(text):
        story.append(p(text.upper(), 'heading'))

    def bullets(items):
        for item in items:
            story.append(Paragraph(escape(item), styles['bullet'], bulletText='\u2022'))

    def role(job):
        story.append(p(job['role'], 'role'))
        story.append(p(f"{job['company']}, {job['location']} | {job['dates']}", 'meta'))
        bullets(job['bullets'])

    story.append(p(cv['name'], 'name'))
    story.append(p(cv['title'], 'subtitle'))
    story.append(p(cv['positioning'], 'small'))
    story.append(Paragraph(
        f'<link href="mailto:{cv["email"]}" color="#176e70">{escape(cv["email"])}</link>'
        f' &nbsp; | &nbsp; <link href="{cv["website"]}" color="#176e70">Portfolio</link>'
        f' &nbsp; | &nbsp; {escape(cv["updated"])}', styles['small']))
    story.append(Spacer(1, 7))
    story.append(HRFlowable(width='100%', thickness=1.3, color=TEAL, spaceAfter=1))

    heading('Profile')
    story.append(p(cv['profile']))
    heading('Core competencies')
    bullets(cv['competencies'])
    heading('Professional experience')
    role(cv['experience'][0])

    story.append(PageBreak())
    compact = ParagraphStyle('Compact', parent=base, fontSize=8.2, leading=11.8, spaceAfter=5)
    compact_role = ParagraphStyle('CompactRole', parent=styles['role'], fontSize=9.3, leading=12.7, spaceAfter=4)
    compact_meta = ParagraphStyle('CompactMeta', parent=styles['meta'], fontSize=7.5, leading=10.5, spaceAfter=7)
    compact_bullet = ParagraphStyle('CompactBullet', parent=compact, leftIndent=9, bulletIndent=0,
                                   bulletFontName=font, bulletFontSize=7, spaceAfter=5)
    column_heading = ParagraphStyle('ColumnHeading', parent=styles['heading'], spaceBefore=0, spaceAfter=12)
    career = [Paragraph('EARLIER EXPERIENCE', column_heading)]
    education_column = [Paragraph('EDUCATION', column_heading)]
    for job in cv['experience'][1:]:
        career.append(Paragraph(escape(job['role']), compact_role))
        career.append(Paragraph(escape(f"{job['company']}, {job['location']}") + '<br/>' + escape(job['dates']), compact_meta))
        career.extend(Paragraph(escape(item), compact_bullet, bulletText='\u2022') for item in job['bullets'])
        career.append(Spacer(1, 14))
    for education in cv['education']:
        education_column.append(Paragraph(escape(education['qualification']), compact_role))
        education_column.append(Paragraph(escape(education['institution']) + '<br/>' + escape(education['dates']), compact_meta))
        if education.get('detail'):
            education_column.append(Paragraph(escape(education['detail']), compact))
        education_column.append(Spacer(1, 12))
    education_column.append(Paragraph('CERTIFICATIONS', column_heading))
    for item in cv['certifications']:
        education_column.append(Paragraph(escape(item), compact_bullet, bulletText='\u2022'))
    column_width = (A4[0] - 92 - 25) / 2
    columns = Table([[career, education_column]], colWidths=[column_width + 12.5, column_width + 12.5])
    columns.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 12.5),
        ('LEFTPADDING', (1, 0), (1, 0), 12.5),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(columns)
    heading('Skills and languages')
    skill_rows = []
    for skill in cv['skills']:
        skill_rows.append([
            Paragraph(escape(skill['category']), ParagraphStyle('SkillLabel', parent=styles['small'], fontName=bold, textColor=NAVY)),
            p(skill['detail'], 'small'),
        ])
    table = Table(skill_rows, colWidths=[111, A4[0] - 92 - 111], hAlign='LEFT')
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (0, -1), 12),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -2), .35, RULE),
    ]))
    story.append(table)

    def page_chrome(canvas, document):
        canvas.saveState()
        width, height = A4
        canvas.setFillColor(TEAL)
        canvas.rect(46, height - 25, 29, 2, fill=1, stroke=0)
        if document.page > 1:
            canvas.setFont(bold, 8)
            canvas.setFillColor(NAVY)
            canvas.drawString(84, height - 25, cv['name'])
            canvas.setFont(font, 7.4)
            canvas.setFillColor(MUTED)
            canvas.drawRightString(width - 46, height - 25, 'Curriculum Vitae')
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(.4)
        canvas.line(46, 30, width - 46, 30)
        canvas.setFont(font, 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(46, 18, f"{cv['name']} | {cv['updated']}")
        canvas.drawRightString(width - 46, 18, str(document.page))
        canvas.restoreState()

    doc.build(story, onFirstPage=page_chrome, onLaterPages=page_chrome)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'assets/Andre_Gerecke_CV_2026.pdf')
    args = parser.parse_args()
    build(args.output)
    print(args.output.resolve())
