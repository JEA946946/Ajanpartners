"""Dansk løn – regneeksempler, bogføring og eIndkomst.

Kør: DB_NAME=ap_payroll TEST_DB_NAME=test_ap_payroll manage.py test payroll.tests_dk

Hvert regneeksempel viser udregningen trin for trin, så en revisor kan følge den.
Satser: payroll/rates.py (AM 8 %, ATP A-sats 2026 99,00/198,00 kr., ferietillæg 1 %,
feriepenge 12,5 %, bruttotræk 55 %, fri telefon 3.500 kr./år i 2026). A-skat
afrundes nedad til hele kroner, AM-bidrag til øre.
"""

from datetime import date
from decimal import Decimal as D
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django.utils import timezone
from django_tenants.test.cases import TenantTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .calculations_dk import (PayInput, TaxCard, calculate_a_tax, calculate_pay, fortnight_deduction,
                              free_phone_month)
from .crypto import decrypt, mask_cpr, normalize_cpr
from .holidays import danish_holidays, easter_sunday, working_days
from .rates import MissingRate, atp_amounts


class CalculationTests(SimpleTestCase):
    def test_funktionaer_hovedkort_pension_og_loebende_ferietillaeg(self):
        """Månedsløn 30.000 kr., 37 timer/uge, pension 4 % + 8 %, hovedkort 37 % med 4.600 kr. fradrag.

        Ferietillæg 1 % × 30.000                     =    300,00 (udbetales med lønnen)
        Kontant løn 30.000 + 300                     = 30.300,00
        ATP (160,33 timer ≥ 117)                     −     99,00   (arbejdsgiver 198,00)
        Pension 4 % × 30.000                         −  1.200,00   (arbejdsgiver 8 % = 2.400,00)
        AM-grundlag                                  = 29.001,00
        AM-bidrag 8 % × 29.001,00                    −  2.320,08
        Skattegrundlag                               = 26.680,92
        A-skat 37 % × (26.680,92 − 4.600) = 8.169,94 → 8.169 (hele kr. nedad)
        Nettoløn 30.300 − 99 − 1.200 − 2.320,08 − 8.169 = 18.511,92
        """
        r = calculate_pay(PayInput(
            year=2026, base_salary=D("30000"), hours=D("160.33"), pension_employee_pct=D("4"),
            pension_employer_pct=D("8"), holiday_type="with_pay", holiday_allowance_mode="monthly",
            tax_card=TaxCard("main", D("37"), D("4600"))))
        self.assertEqual(r.holiday_allowance_paid, D("300.00"))
        self.assertEqual(r.gross_cash, D("30300.00"))
        self.assertEqual((r.atp_employee, r.atp_employer), (D("99.00"), D("198.00")))
        self.assertEqual((r.pension_employee, r.pension_employer), (D("1200.00"), D("2400.00")))
        self.assertEqual(r.am_base, D("29001.00"))
        self.assertEqual(r.am_contribution, D("2320.08"))
        self.assertEqual(r.tax_base, D("26680.92"))
        self.assertEqual(r.deduction_used, D("4600"))
        self.assertEqual(r.a_tax, D("8169"))
        self.assertEqual(r.net_pay, D("18511.92"))
        # Arbejdsgiverens samlede udgift: 30.300 + 198 + 2.400
        self.assertEqual(r.employer_cost, D("32898.00"))

    def test_fri_bil_og_fri_telefon_hensat_ferietillaeg(self):
        """Månedsløn 40.000 kr., fri bil 5.000 kr./md., fri telefon, hovedkort 40 %, fradrag 4.000 kr.

        Fri telefon 2026: 3.500 / 12                 =    291,67
        Personalegoder 5.000 + 291,67                =  5.291,67
        AM-grundlag 40.000 + 5.291,67 − ATP 99       = 45.192,67
        AM-bidrag 8 %                                =  3.615,41 (3.615,4136)
        Skattegrundlag 45.192,67 − 3.615,41          = 41.577,26
        A-skat 40 % × (41.577,26 − 4.000) = 15.030,90 → 15.030
        Nettoløn 40.000 − 99 − 3.615,41 − 15.030     = 21.255,59 (goderne udbetales ikke)
        Ferietillæg 1 % = 400,00 hensættes (ikke udbetalt).
        """
        self.assertEqual(free_phone_month(2026), D("291.67"))
        r = calculate_pay(PayInput(
            year=2026, base_salary=D("40000"), hours=D("160.33"), car_benefit=D("5000"),
            phone_benefit=free_phone_month(2026), holiday_allowance_mode="accrue",
            tax_card=TaxCard("main", D("40"), D("4000"))))
        self.assertEqual(r.benefits, D("5291.67"))
        self.assertEqual(r.am_base, D("45192.67"))
        self.assertEqual(r.am_contribution, D("3615.41"))
        self.assertEqual(r.a_tax, D("15030"))
        self.assertEqual(r.net_pay, D("21255.59"))
        self.assertEqual((r.holiday_allowance_paid, r.holiday_allowance_accrued), (D("0"), D("400.00")))

    def test_timeloen_bikort_feriepenge(self):
        """Timeløn 150 kr. × 60 timer, bikort 38 %, ferie uden løn (egen ordning).

        Løn 150 × 60                                 =  9.000,00
        Feriepenge 12,5 % × 9.000                    =  1.125,00 (hensættes)
        ATP 60 timer (39–77 timer: 1/3 sats)         −     33,00 (arbejdsgiver 66,00)
        AM-grundlag                                  =  8.967,00
        AM-bidrag 8 %                                −    717,36
        A-skat 38 % × 8.249,64 = 3.134,86 → 3.134 (bikort: intet fradrag)
        Nettoløn 9.000 − 33 − 717,36 − 3.134         =  5.115,64
        """
        r = calculate_pay(PayInput(
            year=2026, base_salary=D("9000"), hours=D("60"), holiday_type="without_pay",
            tax_card=TaxCard("secondary", D("38"), D("4600"))))
        self.assertEqual(r.holiday_pay_accrued, D("1125.00"))
        self.assertEqual((r.atp_employee, r.atp_employer), (D("33.00"), D("66.00")))
        self.assertEqual(r.am_contribution, D("717.36"))
        self.assertEqual(r.deduction_used, D("0"))
        self.assertEqual(r.a_tax, D("3134"))
        self.assertEqual(r.net_pay, D("5115.64"))

    def test_frikort_opbruges_og_resten_beskattes_55(self):
        """Frikort med 10.000 kr. tilbage. Løn 12.000, 80 timer (2/3 ATP-sats).

        AM-grundlag 12.000 − 66                      = 11.934,00
        AM-bidrag 8 %                                =    954,72
        Skattegrundlag                               = 10.979,28
        Frikort brugt                                = 10.000,00
        A-skat 55 % × 979,28 = 538,60 → 538
        Nettoløn 12.000 − 66 − 954,72 − 538          = 10.441,28
        """
        r = calculate_pay(PayInput(year=2026, base_salary=D("12000"), hours=D("80"), holiday_type="without_pay",
                                   tax_card=TaxCard("free", free_remaining=D("10000"))))
        self.assertEqual(r.atp_employee, D("66.00"))
        self.assertEqual(r.frikort_used, D("10000"))
        self.assertEqual(r.a_tax, D("538"))
        self.assertEqual(r.net_pay, D("10441.28"))

    def test_frikort_rigeligt_ingen_skat(self):
        tax, ded, free = calculate_a_tax(2026, D("5000"), TaxCard("free", free_remaining=D("40000")))
        self.assertEqual((tax, ded, free), (D("0"), D("0"), D("5000")))

    def test_intet_skattekort_bruttotraek_55(self):
        """Uden skattekort: 55 % uden fradrag. Løn 10.000, ingen ATP (klasse 0).
        AM 800,00; A-skat 55 % × 9.200 = 5.060; netto 10.000 − 800 − 5.060 = 4.140."""
        r = calculate_pay(PayInput(year=2025, base_salary=D("10000"), atp_class="0",
                                   holiday_type="without_pay", tax_card=TaxCard("none", D("37"), D("4600"))))
        self.assertEqual((r.am_contribution, r.a_tax, r.net_pay), (D("800.00"), D("5060"), D("4140.00")))

    def test_fradrag_stoerre_end_grundlag(self):
        """Fradraget kan ikke gøre skatten negativ: lille løn 3.000, fradrag 4.600 → A-skat 0, fradrag brugt 2.760."""
        r = calculate_pay(PayInput(year=2026, base_salary=D("3000"), atp_class="0",
                                   holiday_type="without_pay", tax_card=TaxCard("main", D("37"), D("4600"))))
        self.assertEqual(r.am_contribution, D("240.00"))
        self.assertEqual(r.a_tax, D("0"))
        self.assertEqual(r.deduction_used, D("2760.00"))

    def test_b_indkomst_ingen_traek(self):
        """B-indkomst 5.000 (honorar): ingen A-skat, intet AM-træk hos arbejdsgiveren, ingen ATP."""
        r = calculate_pay(PayInput(year=2026, b_income=D("5000"), tax_card=TaxCard("main", D("37"), D("4600"))))
        self.assertEqual((r.am_contribution, r.a_tax, r.atp_employee, r.net_pay),
                         (D("0"), D("0"), D("0"), D("5000.00")))

    def test_a_indkomst_uden_am(self):
        """A-indkomst uden AM-bidrag 1.000 beskattes, men indgår ikke i AM-grundlaget.
        Bikort 40 %: A-skat 40 % × 1.000 = 400."""
        r = calculate_pay(PayInput(year=2026, a_income_no_am=D("1000"), atp_class="0",
                                   tax_card=TaxCard("secondary", D("40"))))
        self.assertEqual((r.am_base, r.a_tax, r.net_pay), (D("0"), D("400"), D("600.00")))

    def test_14_dage(self):
        """14-dagesløn: fradrag 4.600 × 12/26 = 2.123,08 → 2.123; ATP 70 timer ≥ 54 → 45,70."""
        self.assertEqual(fortnight_deduction(D("4600")), D("2123"))
        self.assertEqual(atp_amounts(2026, "fortnight", D("70")), (D("45.70"), D("91.40")))

    def test_atp_satser(self):
        self.assertEqual(atp_amounts(2026, "month", D("117")), (D("99.00"), D("198.00")))
        self.assertEqual(atp_amounts(2026, "month", D("116.99")), (D("66.00"), D("132.00")))
        self.assertEqual(atp_amounts(2026, "month", D("38")), (D("0"), D("0")))
        with self.assertRaises(MissingRate):
            atp_amounts(2026, "month", D("160"), "B")
        with self.assertRaises(MissingRate):
            atp_amounts(2019, "month", D("160"))

    def test_sygedagpengerefusion_paavirker_ikke_nettoloen(self):
        a = calculate_pay(PayInput(year=2026, base_salary=D("20000"), hours=D("160"),
                                   tax_card=TaxCard("main", D("37"), D("4600"))))
        b = calculate_pay(PayInput(year=2026, base_salary=D("20000"), hours=D("160"), sick_pay_refund=D("4000"),
                                   tax_card=TaxCard("main", D("37"), D("4600"))))
        self.assertEqual(a.net_pay, b.net_pay)
        self.assertEqual(b.sick_pay_refund, D("4000.00"))


class HolidayTests(SimpleTestCase):
    def test_paaske(self):
        self.assertEqual(easter_sunday(2024), date(2024, 3, 31))
        self.assertEqual(easter_sunday(2025), date(2025, 4, 20))
        self.assertEqual(easter_sunday(2026), date(2026, 4, 5))

    def test_helligdage_2026(self):
        days = {d: n for d, n, _ in danish_holidays(2026, "none")}
        self.assertEqual(days[date(2026, 4, 2)], "Skærtorsdag")
        self.assertEqual(days[date(2026, 4, 3)], "Langfredag")
        self.assertEqual(days[date(2026, 4, 6)], "2. påskedag")
        self.assertEqual(days[date(2026, 5, 14)], "Kristi himmelfartsdag")
        self.assertEqual(days[date(2026, 5, 24)], "Pinsedag")
        self.assertEqual(days[date(2026, 5, 25)], "2. pinsedag")
        self.assertNotIn("Store bededag", days.values())
        self.assertNotIn(date(2026, 6, 5), days)
        self.assertEqual(len(days), 10)

    def test_store_bededag_kun_foer_2024(self):
        self.assertIn((date(2023, 5, 5), "Store bededag", D("1")), danish_holidays(2023))
        self.assertFalse([d for d in danish_holidays(2024) if d[1] == "Store bededag"])

    def test_grundlovsdag(self):
        self.assertIn((date(2026, 6, 5), "Grundlovsdag", D("0.5")), danish_holidays(2026, "half"))
        self.assertIn((date(2026, 6, 5), "Grundlovsdag", D("1")), danish_holidays(2026, "full"))
        # Juni 2026: 22 hverdage, grundlovsdag fredag 5/6 som halv dag → 21,5
        self.assertEqual(working_days(2026, 6, "half"), D("21.5"))

    def test_arbejdsdage_maj_2026(self):
        # 21 hverdage − Kristi himmelfart (tor 14/5) − 2. pinsedag (man 25/5) = 19
        self.assertEqual(working_days(2026, 5), D("19"))


class CprTests(SimpleTestCase):
    def test_normalize_and_mask(self):
        self.assertEqual(normalize_cpr("010190-1234"), "0101901234")
        self.assertEqual(mask_cpr("1234"), "XXXXXX-1234")
        from django.core.exceptions import ValidationError
        for bad in ("123", "320190-1234", "011390-1234", "abcdefghij"):
            with self.assertRaises(ValidationError):
                normalize_cpr(bad)


# ─── Database: bogføring, låsning, API ────────────────────────────────────────

def ensure_dk_accounts():
    """Opretter de DK_*-konti, testene bruger (uafhængigt af kontoplanens seed)."""
    from accounts import chart
    from accounts.models import Account, AccountType
    exp, _ = AccountType.objects.get_or_create(name="Expense", defaults={"normal_balance": "debit"})
    lia, _ = AccountType.objects.get_or_create(name="Liability", defaults={"normal_balance": "credit"})
    names = [n for n in dir(chart) if n.startswith("DK_")]
    for n in names:
        kind = lia if n.endswith("_PAYABLE") else exp
        Account.objects.get_or_create(code=getattr(chart, n), defaults={"name": n, "account_type": kind})
    return names


class PostingTests(TenantTestCase):
    @classmethod
    def get_test_schema_name(cls):
        return "c_payrolltest"

    @classmethod
    def setup_tenant(cls, tenant):
        from tenancy.models import Firm, Package
        from tenancy.services import seed_packages
        seed_packages()
        tenant.firm = Firm.current()
        tenant.package = Package.objects.get(code="pro")
        tenant.name = "Løntest ApS"
        tenant.slug = "loentest"

    def setUp(self):
        from .models import Employee
        ensure_dk_accounts()
        self.emp = Employee.objects.create(
            employee_number="1", first_name="Sara", last_name="Hansen", monthly_salary=D("30000"),
            hours_per_week=D("37"), tax_card="main", tax_rate=D("37"), deduction_month=D("4600"),
            pension_employee_pct=D("4"), pension_employer_pct=D("8"), car_benefit_month=D("2000"))
        self.emp.set_cpr("0101901234")
        self.emp.save()
        self.hourly = Employee.objects.create(
            employee_number="2", first_name="Ali", last_name="Jensen", pay_form="hourly", hourly_rate=D("150"),
            hours_per_week=D("15"), tax_card="secondary", tax_rate=D("38"), holiday_scheme="feriekonto",
            holiday_type="without_pay")
        self.hourly.set_cpr("0202951235")
        self.hourly.save()

    def _run(self):
        from . import services
        run = services.create_run(frequency="month", year=2026, month=3, created_by="test")
        line = run.lines.get(employee=self.emp)
        services.update_line(run, line, {"sick_pay_refund": "1500", "b_income": "1000"})
        services.calculate_run(run)
        services.approve_run(run, "test")
        return run

    def test_cpr_encrypted_at_rest(self):
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute("SELECT cpr FROM employees WHERE id = %s", [self.emp.id])
            raw = cur.fetchone()[0]
        self.assertNotIn("0101901234", raw)
        self.assertEqual(decrypt(raw), "0101901234")
        from .models import Employee
        self.assertEqual(Employee.objects.get(id=self.emp.id).cpr_masked, "XXXXXX-1234")

    def test_post_run_is_balanced_and_uses_dk_accounts(self):
        from accounts import chart
        from . import services
        run = self._run()
        run, entry = services.post_run(run, "test")
        self.assertEqual(run.status, "posted")
        self.assertEqual(entry.source, "payroll")
        lines = {}
        for l in entry.lines.select_related("account"):
            d, c = lines.get(l.account.code, (D("0"), D("0")))
            lines[l.account.code] = (d + l.debit, c + l.credit)
        self.assertEqual(sum(d for d, _ in lines.values()), sum(c for _, c in lines.values()))
        self.assertEqual(lines[chart.DK_SALARIES_PAYABLE][1], run.total_net)
        self.assertEqual(lines[chart.DK_A_TAX_PAYABLE][1], run.total_a_tax)
        self.assertEqual(lines[chart.DK_AM_PAYABLE][1], run.total_am)
        self.assertEqual(lines[chart.DK_ATP_PAYABLE][1], run.total_atp_employee + run.total_atp_employer)
        self.assertEqual(lines[chart.DK_PENSION_PAYABLE][1], D("3600.00"))  # 4 % + 8 % af 30.000
        self.assertEqual(lines[chart.DK_SALARY_REFUNDS][1], D("1500.00"))
        self.assertEqual(lines[chart.DK_OTHER_PAYROLL_PAYABLE][0], D("1500.00"))
        # Timelønnet på FerieKonto: 150 × 65 timer (15 × 52 / 12) = 9.750 → feriepenge 12,5 % = 1.218,75
        hl = run.lines.get(employee=self.hourly)
        self.assertEqual((hl.hours, hl.base_salary, hl.holiday_pay_accrued), (D("65.00"), D("9750.00"), D("1218.75")))
        # Sara får ferietillægget (300,00) udbetalt løbende, så kun feriepengene hensættes.
        self.assertEqual(lines[chart.DK_HOLIDAY_PAY_PAYABLE][1], D("1218.75"))
        self.assertEqual(lines[chart.DK_HOLIDAY_PAY_EXPENSE][0], D("1518.75"))
        # Lønninger = grundløn 30.000 + 9.750 + B-indkomst 1.000
        self.assertEqual(lines[chart.DK_SALARIES][0], D("40750.00"))

    def test_locked_after_approval_and_closed_period(self):
        from journals.models import Period
        from . import services
        run = self._run()
        with self.assertRaises(services.PayrollError):
            services.update_line(run, run.lines.first(), {"supplements": "100"})
        with self.assertRaises(services.PayrollError):
            services.calculate_run(run)
        Period.objects.create(year=2026, month=3, closed_at=timezone.now())
        with self.assertRaises(services.PayrollError):
            services.post_run(run, "test")
        run.refresh_from_db()
        self.assertEqual(run.status, "approved")

    def test_missing_account_is_reported(self):
        from accounts import chart
        from accounts.models import Account
        from . import services
        run = self._run()
        Account.objects.filter(code=chart.DK_AM_PAYABLE).delete()
        with self.assertRaisesRegex(services.PayrollError, chart.DK_AM_PAYABLE):
            services.post_run(run, "test")

    def test_frikort_carried_over_runs(self):
        from . import services
        self.emp.tax_card, self.emp.free_card_amount = "free", D("30000")
        self.emp.save()
        jan = services.create_run(frequency="month", year=2026, month=1)
        services.calculate_run(jan)
        services.approve_run(jan, "t")
        used = jan.lines.get(employee=self.emp).frikort_used
        self.assertGreater(used, 0)
        feb = services.create_run(frequency="month", year=2026, month=2)
        services.calculate_run(feb)
        line = feb.lines.get(employee=self.emp)
        self.assertEqual(line.frikort_used, min(D("30000") - used, line.tax_base))
        self.assertGreater(line.a_tax, 0)  # frikortet er brugt op i februar

    def test_eindkomst_export_and_mock_submit(self):
        from . import eindkomst
        from .models import PayrollSettings
        run = self._run()
        ps = PayrollSettings.get()
        ps.se_number = "12345678"
        ps.save()
        data = eindkomst.build_export(run)
        rec = next(e for e in data["employees"] if e["employee_number"] == "1")
        line = run.lines.get(employee=self.emp)
        self.assertEqual(rec["cpr"], "0101901234")
        self.assertEqual(rec["fields"]["0015"], f"{line.a_tax:.2f}")
        self.assertEqual(rec["fields"]["0016"], f"{line.am_contribution:.2f}")
        self.assertEqual(rec["fields"]["0046"], "297.00")
        self.assertEqual(rec["fields"]["0068"], "2000.00")
        self.assertEqual(D(rec["fields"]["0013"]), line.am_base - D("2000"))
        res = eindkomst.submit(run)
        self.assertEqual(res.status, "accepted")
        self.assertTrue(res.reference.startswith("MOCK-"))
        with self.assertRaises(NotImplementedError):
            eindkomst.SkatSystemToSystemClient().submit(run)
        with self.assertRaises(NotImplementedError):
            eindkomst.SkatESkattekortClient().fetch("0101901234", 2026)

    def test_pdfs(self):
        from .pdf import payroll_list_pdf, payslips_pdf
        run = self._run()
        self.assertTrue(payslips_pdf(list(run.lines.select_related("employee", "payroll_run"))).startswith(b"%PDF"))
        self.assertTrue(payroll_list_pdf(run).startswith(b"%PDF"))

    def test_api_flow_hides_cpr(self):
        from . import views
        user = get_user_model().objects.create_user("lon@x.dk", "lon@x.dk", "x")
        rf = APIRequestFactory()

        def call(view, method, path, data=None, **kw):
            req = getattr(rf, method)(path, data, format="json")
            req.client_access = SimpleNamespace(role="accountant", can_write=True, is_firm=False)
            force_authenticate(req, user=user)
            return view(req, **kw)

        r = call(views.employees_list_create, "post", "/x", {"first_name": "Mette", "last_name": "Lund",
                                                            "cpr": "030303-3333", "monthly_salary": "25000"})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["employee"]["cpr_masked"], "XXXXXX-3333")
        self.assertNotIn("cpr", r.data["employee"])
        self.assertNotIn("0303033333", str(r.data))
        r = call(views.runs_list_create, "post", "/x", {"frequency": "month", "year": 2026, "month": 4})
        self.assertEqual(r.status_code, 201, r.data)
        rid = r.data["payroll_run"]["id"]
        self.assertEqual(call(views.run_approve, "post", "/x", pk=rid).status_code, 400)  # ikke beregnet
        self.assertEqual(call(views.run_calculate, "post", "/x", pk=rid).status_code, 200)
        self.assertEqual(call(views.run_approve, "post", "/x", pk=rid).status_code, 200)
        self.assertEqual(call(views.runs_detail, "delete", "/x", pk=rid).status_code, 400)  # låst
        r = call(views.run_post, "post", "/x", pk=rid)
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["payroll_run"]["status"], "posted")
        from core.models import AuditLog
        self.assertTrue(AuditLog.objects.filter(model_name="PayrollRun", action="post").exists())
        self.assertFalse(AuditLog.objects.filter(changes__icontains="0303033333").exists())
