"""Dansk løn: medarbejdere, lønkørsler og lønlinjer."""

import uuid
from decimal import Decimal

from django.db import models

from .crypto import EncryptedTextField, mask_cpr
from .rates import ATP_CLASSES

Z = Decimal("0")


def _money(**kw):
    return models.DecimalField(max_digits=12, decimal_places=2, default=Z, **kw)


class PayrollSettings(models.Model):
    """Lønindstillinger for virksomheden (én række)."""

    GRUNDLOVSDAG = [("none", "Arbejdsdag"), ("half", "Halv fridag"), ("full", "Hel fridag")]

    id = models.AutoField(primary_key=True)
    se_number = models.CharField(max_length=8, blank=True, default="",
                                 help_text="SE-nummer til eIndkomst (oftest = CVR)")
    grundlovsdag = models.CharField(max_length=4, choices=GRUNDLOVSDAG, default="half")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payroll_settings"

    @classmethod
    def get(cls):
        obj = cls.objects.order_by("id").first()
        return obj or cls.objects.create()


class Employee(models.Model):
    PAY_FORMS = [("month", "Månedsløn"), ("fortnight", "14-dagesløn"), ("hourly", "Timeløn (månedsvis)")]
    TAX_CARDS = [("main", "Hovedkort"), ("secondary", "Bikort"), ("free", "Frikort"), ("none", "Intet skattekort")]
    HOLIDAY_SCHEMES = [("feriekonto", "FerieKonto"), ("own", "Egen ordning")]
    HOLIDAY_TYPES = [("with_pay", "Ferie med løn (+ ferietillæg)"), ("without_pay", "Ferie uden løn (12,5 % feriepenge)")]
    ALLOWANCE_MODES = [("monthly", "Udbetales løbende"), ("accrue", "Hensættes")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    cpr = EncryptedTextField(blank=True, default="", help_text="Krypteret; vises aldrig i API'et")
    cpr_last4 = models.CharField(max_length=4, blank=True, default="")
    address = models.TextField(blank=True, default="")
    email = models.EmailField(blank=True, default="")
    bank_reg = models.CharField(max_length=4, blank=True, default="")
    bank_account = models.CharField(max_length=10, blank=True, default="")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Løn
    pay_form = models.CharField(max_length=10, choices=PAY_FORMS, default="month")
    monthly_salary = _money(help_text="Fast månedsløn (eller fast 14-dagesløn)")
    hourly_rate = _money()
    hours_per_week = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("37"))

    # Skattekort (fra eSkattekort)
    tax_card = models.CharField(max_length=10, choices=TAX_CARDS, default="main")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Z, help_text="Trækprocent")
    deduction_month = _money(help_text="Månedsfradrag")
    deduction_fortnight = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                              help_text="14-dagesfradrag (tom: månedsfradrag × 12/26)")
    free_card_amount = _money(help_text="Frikortbeløb for året")
    tax_card_year = models.IntegerField(null=True, blank=True)
    tax_card_fetched_at = models.DateTimeField(null=True, blank=True)

    # Ferie
    holiday_scheme = models.CharField(max_length=10, choices=HOLIDAY_SCHEMES, default="own")
    holiday_type = models.CharField(max_length=12, choices=HOLIDAY_TYPES, default="with_pay")
    holiday_allowance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("1"))
    holiday_allowance_mode = models.CharField(max_length=8, choices=ALLOWANCE_MODES, default="monthly")

    # Pension og ATP
    pension_employee_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Z)
    pension_employer_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Z)
    pension_company = models.CharField(max_length=200, blank=True, default="")
    atp_class = models.CharField(max_length=1, choices=ATP_CLASSES, default="A")

    # Faste personalegoder pr. måned
    car_benefit_month = _money(help_text="Skattepligtig værdi af fri bil pr. måned")
    free_phone = models.BooleanField(default=False, help_text="Fri telefon/multimedier")

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "employees"
        ordering = ["employee_number"]

    def __str__(self):
        return f"{self.employee_number} — {self.first_name} {self.last_name}"

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def cpr_masked(self):
        return mask_cpr(self.cpr_last4) if self.cpr_last4 else ""

    def set_cpr(self, digits):
        self.cpr = digits
        self.cpr_last4 = digits[-4:] if digits else ""


class PayrollRun(models.Model):
    """Lønkørsel: kladde → beregnet → godkendt → bogført."""

    STATUS_CHOICES = [
        ("draft", "Kladde"),
        ("calculated", "Beregnet"),
        ("approved", "Godkendt"),
        ("posted", "Bogført"),
    ]
    FREQUENCIES = [("month", "Måned"), ("fortnight", "14 dage")]
    EDITABLE = ("draft", "calculated")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    frequency = models.CharField(max_length=10, choices=FREQUENCIES, default="month")
    year = models.IntegerField()
    month = models.IntegerField(help_text="Måned for udbetalingen (1-12)")
    period_start = models.DateField()
    period_end = models.DateField()
    pay_date = models.DateField(help_text="Udbetalingsdato (bogføres på denne dato)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    total_gross = _money()
    total_benefits = _money()
    total_am = _money()
    total_a_tax = _money()
    total_atp_employee = _money()
    total_atp_employer = _money()
    total_pension_employee = _money()
    total_pension_employer = _money()
    total_holiday = _money()
    total_b_income = _money()
    total_net = _money()

    journal_entry = models.ForeignKey("journals.JournalEntry", on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name="payroll_runs")
    approved_by = models.CharField(max_length=200, blank=True, default="")
    approved_at = models.DateTimeField(null=True, blank=True)
    eindkomst_status = models.CharField(max_length=20, blank=True, default="")
    eindkomst_reference = models.CharField(max_length=100, blank=True, default="")
    eindkomst_submitted_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_by = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payroll_runs"
        unique_together = [("frequency", "period_start")]
        ordering = ["-period_start"]

    def __str__(self):
        return f"Løn {self.period_start}–{self.period_end} ({self.status})"

    @property
    def label(self):
        if self.frequency == "month":
            return f"{self.year}-{self.month:02d}"
        return f"{self.period_start.isoformat()}–{self.period_end.isoformat()}"

    @property
    def is_editable(self):
        return self.status in self.EDITABLE


class PayrollLine(models.Model):
    """Én medarbejder i en lønkørsel. Inddata kan rettes i kladde; resultatet
    beregnes af calculations_dk og fryses ved godkendelse."""

    INPUT_FIELDS = ("hours", "base_salary", "supplements", "holiday_payout", "a_income_no_am",
                    "car_benefit", "phone_benefit", "other_benefits", "b_income", "b_income_am",
                    "sick_pay_refund", "note")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name="lines")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="payroll_lines")

    # Inddata
    hours = models.DecimalField(max_digits=7, decimal_places=2, default=Z)
    base_salary = _money()
    supplements = _money(help_text="Tillæg og overtid")
    holiday_payout = _money(help_text="Udbetaling af hensatte feriepenge/ferietillæg")
    a_income_no_am = _money()
    car_benefit = _money()
    phone_benefit = _money()
    other_benefits = _money()
    b_income = _money()
    b_income_am = models.BooleanField(default=True, help_text="B-indkomsten er AM-bidragspligtig")
    sick_pay_refund = _money(help_text="Sygedagpengerefusion fra kommunen (manuel)")
    note = models.CharField(max_length=500, blank=True, default="")

    # Skattekort brugt ved beregningen
    tax_card = models.CharField(max_length=10, blank=True, default="")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Z)

    # Resultat
    holiday_allowance_paid = _money()
    holiday_allowance_accrued = _money()
    holiday_pay_accrued = _money()
    gross_cash = _money()
    benefits = _money()
    atp_employee = _money()
    atp_employer = _money()
    pension_employee = _money()
    pension_employer = _money()
    am_base = _money()
    am_contribution = _money()
    tax_base = _money()
    deduction_used = _money()
    frikort_used = _money()
    a_tax = _money()
    net_pay = _money()
    employer_cost = _money()
    calculated = models.BooleanField(default=False)
    warnings = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "payroll_lines"
        ordering = ["employee__employee_number"]
        unique_together = [("payroll_run", "employee")]

    def __str__(self):
        return f"{self.employee} — netto {self.net_pay}"
