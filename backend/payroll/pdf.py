"""Lønsedler og lønliste som PDF (reportlab, ingen systemafhængigheder)."""

from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

Z = Decimal("0")


def kr(value):
    """1234.5 → '1.234,50'."""
    s = f"{Decimal(value or 0):,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def dk_date(d):
    return d.strftime("%d-%m-%Y") if d else ""


def _company():
    from core.models import CompanySettings
    c = CompanySettings.objects.first()
    if not c:
        return {"name": "", "lines": []}
    lines = [escape(x) for x in (c.address, c.city, f"CVR {c.tax_id}" if c.tax_id else "") if x]
    return {"name": escape(c.company_name), "lines": lines}


_TABLE = TableStyle([
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.grey),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
])


def _payslip_story(line, styles):
    run, emp = line.payroll_run, line.employee
    company = _company()
    story = [
        Paragraph(f"<b>{company['name']}</b>", styles["Title"]),
        Paragraph("<br/>".join(company["lines"]), styles["Normal"]),
        Spacer(1, 6 * mm),
        Paragraph(f"<b>Lønseddel</b> — periode {dk_date(run.period_start)} til {dk_date(run.period_end)}, "
                  f"udbetales {dk_date(run.pay_date)}", styles["Heading3"]),
        Paragraph(f"{escape(emp.name)} (nr. {escape(emp.employee_number)})<br/>CPR {emp.cpr_masked}<br/>"
                  f"Skattekort: {dict(emp.TAX_CARDS).get(line.tax_card, line.tax_card)}, "
                  f"trækprocent {line.tax_rate} %", styles["Normal"]),
        Spacer(1, 5 * mm),
    ]
    rows = [["Tekst", "Grundlag", "Beløb"]]

    def add(text, amount, basis=""):
        if Decimal(amount or 0) != 0:
            rows.append([text, basis, kr(amount)])

    add("Løn", line.base_salary, f"{line.hours} timer" if line.hours else "")
    add("Tillæg og overtid", line.supplements)
    add("Ferietillæg", line.holiday_allowance_paid)
    add("Udbetalte feriepenge", line.holiday_payout)
    add("A-indkomst uden AM-bidrag", line.a_income_no_am)
    add("Fri bil (skattepligtig værdi)", line.car_benefit)
    add("Fri telefon (skattepligtig værdi)", line.phone_benefit)
    add("Andre personalegoder", line.other_benefits)
    add("ATP", -line.atp_employee)
    add("Pension, eget bidrag", -line.pension_employee)
    add("AM-bidrag 8 %", -line.am_contribution, kr(line.am_base))
    add("A-skat", -line.a_tax, kr(line.tax_base - line.deduction_used))
    add("Personalegoder modregnet", -line.benefits)
    add("B-indkomst (ingen skat trukket)", line.b_income)
    rows.append(["Til udbetaling", "", kr(line.net_pay)])
    t = Table(rows, colWidths=[90 * mm, 40 * mm, 40 * mm])
    t.setStyle(_TABLE)
    t.setStyle(TableStyle([("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                           ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.black)]))
    story += [t, Spacer(1, 6 * mm)]
    info = [["Arbejdsgiverbetalt", "", ""]]
    for text, amount in (("ATP, arbejdsgiver", line.atp_employer), ("Pension, arbejdsgiver", line.pension_employer),
                         ("Ferietillæg hensat", line.holiday_allowance_accrued),
                         ("Feriepenge 12,5 % hensat", line.holiday_pay_accrued)):
        if amount:
            info.append([text, "", kr(amount)])
    info.append(["Fradrag brugt", "", kr(line.deduction_used)])
    if line.frikort_used:
        info.append(["Frikort brugt", "", kr(line.frikort_used)])
    if emp.pension_company:
        info.append(["Pensionsselskab", "", emp.pension_company])
    if emp.bank_account:
        info.append(["Udbetales til", "", f"{emp.bank_reg} {emp.bank_account}"])
    t2 = Table(info, colWidths=[90 * mm, 40 * mm, 40 * mm])
    t2.setStyle(_TABLE)
    story.append(t2)
    return story


def payslips_pdf(lines):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm, title="Lønseddel")
    styles = getSampleStyleSheet()
    story = []
    for i, line in enumerate(lines):
        if i:
            story.append(PageBreak())
        story += _payslip_story(line, styles)
    doc.build(story)
    return buf.getvalue()


def payroll_list_pdf(run):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm, title="Lønliste")
    styles = getSampleStyleSheet()
    company = _company()
    head = ["Nr.", "Navn", "Løn", "Goder", "ATP", "Pension", "AM-grundl.", "AM", "A-skat", "Ferie",
            "B-indk.", "Netto"]
    rows = [head]
    lines = list(run.lines.select_related("employee"))
    for l in lines:
        rows.append([l.employee.employee_number, l.employee.name, kr(l.gross_cash + l.a_income_no_am),
                     kr(l.benefits), kr(l.atp_employee), kr(l.pension_employee), kr(l.am_base),
                     kr(l.am_contribution), kr(l.a_tax),
                     kr(l.holiday_allowance_paid + l.holiday_allowance_accrued + l.holiday_pay_accrued),
                     kr(l.b_income), kr(l.net_pay)])

    def tot(f):
        return kr(sum((f(l) for l in lines), Z))

    rows.append(["", "I alt", tot(lambda l: l.gross_cash + l.a_income_no_am), tot(lambda l: l.benefits),
                 tot(lambda l: l.atp_employee), tot(lambda l: l.pension_employee), tot(lambda l: l.am_base),
                 tot(lambda l: l.am_contribution), tot(lambda l: l.a_tax),
                 tot(lambda l: l.holiday_allowance_paid + l.holiday_allowance_accrued + l.holiday_pay_accrued),
                 tot(lambda l: l.b_income), tot(lambda l: l.net_pay)])
    t = Table(rows, repeatRows=1)
    t.setStyle(_TABLE)
    t.setStyle(TableStyle([("ALIGN", (0, 0), (1, -1), "LEFT"), ("FONTSIZE", (0, 0), (-1, -1), 8),
                           ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                           ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.black)]))
    status = dict(run.STATUS_CHOICES).get(run.status, run.status)
    story = [Paragraph(f"<b>{company['name']}</b> — Lønliste {run.label}", styles["Heading2"]),
             Paragraph(f"Periode {dk_date(run.period_start)}–{dk_date(run.period_end)}, udbetaling "
                       f"{dk_date(run.pay_date)}, status: {status}", styles["Normal"]),
             Spacer(1, 4 * mm), t]
    doc.build(story)
    return buf.getvalue()
