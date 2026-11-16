"""Tests af fristberegningen (rene funktioner, ingen database)."""

from datetime import date

from django.test import SimpleTestCase

from firm import deadlines as dl


class CalendarTests(SimpleTestCase):
    def test_easter(self):
        self.assertEqual(dl.easter(2024), date(2024, 3, 31))
        self.assertEqual(dl.easter(2025), date(2025, 4, 20))
        self.assertEqual(dl.easter(2026), date(2026, 4, 5))

    def test_holidays(self):
        h = dl.public_holidays(2026)
        self.assertIn(date(2026, 4, 3), h)    # langfredag
        self.assertIn(date(2026, 5, 14), h)   # Kristi himmelfart
        self.assertIn(date(2026, 5, 25), h)   # 2. pinsedag
        self.assertNotIn(date(2026, 5, 1), h)
        # Store bededag er afskaffet fra 2024
        self.assertIn(date(2023, 5, 5), dl.public_holidays(2023))
        self.assertNotIn(date(2024, 4, 26), dl.public_holidays(2024))

    def test_bank_days(self):
        # Kristi himmelfart torsdag + banklukket fredag → mandag
        self.assertEqual(dl.next_bank_day(date(2026, 5, 14)), date(2026, 5, 18))
        self.assertFalse(dl.is_bank_day(date(2026, 6, 5)))   # grundlovsdag
        self.assertFalse(dl.is_bank_day(date(2026, 12, 24)))
        self.assertTrue(dl.is_weekday(date(2026, 6, 5)))     # men en hverdag
        self.assertEqual(dl.last_bank_day(2026, 5), date(2026, 5, 29))


class VatTests(SimpleTestCase):
    def test_month(self):
        self.assertEqual(dl.vat_due("month", 2026, 1), date(2026, 2, 25))
        self.assertEqual(dl.vat_due("month", 2026, 12), date(2027, 1, 25))
        self.assertEqual(dl.vat_due("month", 2025, 6), date(2025, 8, 17))  # sommerfrist

    def test_quarter(self):
        self.assertEqual(dl.vat_due("quarter", 2026, 1), date(2026, 6, 1))
        self.assertEqual(dl.vat_due("quarter", 2026, 2), date(2026, 9, 1))
        self.assertEqual(dl.vat_due("quarter", 2026, 3), date(2026, 12, 1))
        self.assertEqual(dl.vat_due("quarter", 2025, 4), date(2026, 3, 1))

    def test_half(self):
        self.assertEqual(dl.vat_due("half", 2026, 1), date(2026, 9, 1))
        self.assertEqual(dl.vat_due("half", 2025, 2), date(2026, 3, 1))

    def test_shift_to_bank_day(self):
        p = dl.Profile(vat_period="quarter", has_payroll=False)
        items = [d for d in dl.deadlines_for(p, date(2026, 1, 1), date(2026, 12, 31)) if d.kind == "moms"]
        q4 = items[0]
        self.assertEqual(q4.period, "4. kvartal 2025")
        self.assertEqual(q4.due, date(2026, 3, 1))     # søndag
        self.assertEqual(q4.date, date(2026, 3, 2))
        self.assertTrue(q4.shifted)
        self.assertEqual([d.date for d in items],
                         [date(2026, 3, 2), date(2026, 6, 1), date(2026, 9, 1), date(2026, 12, 1)])

    def test_june_month_shift(self):
        p = dl.Profile(vat_period="month", has_payroll=False)
        june = [d for d in dl.deadlines_for(p, date(2025, 8, 1), date(2025, 8, 31)) if d.kind == "moms"]
        self.assertEqual(june[0].date, date(2025, 8, 18))  # 17. august 2025 er en søndag

    def test_not_registered(self):
        p = dl.Profile(vat_period="none", has_payroll=False)
        self.assertFalse([d for d in dl.deadlines_for(p, date(2026, 1, 1), date(2026, 12, 31)) if d.kind == "moms"])


class PayrollTests(SimpleTestCase):
    def test_a_tax(self):
        self.assertEqual(dl.a_tax_due(2026, 11), date(2026, 12, 10))
        self.assertEqual(dl.a_tax_due(2026, 12), date(2027, 1, 17))
        p = dl.Profile(vat_period="none", legal_form="enk")
        april = [d for d in dl.deadlines_for(p, date(2026, 5, 1), date(2026, 5, 31)) if d.kind == "a_skat"]
        self.assertEqual(april[0].date, date(2026, 5, 11))  # 10. maj 2026 er en søndag

    def test_without_payroll(self):
        p = dl.Profile(has_payroll=False)
        self.assertFalse([d for d in dl.deadlines_for(p, date(2026, 1, 1), date(2026, 12, 31)) if d.kind == "a_skat"])


class AnnualTests(SimpleTestCase):
    def test_fiscal_year_end(self):
        self.assertEqual(dl.fiscal_year_end(1, 2026), date(2026, 12, 31))
        self.assertEqual(dl.fiscal_year_end(7, 2026), date(2026, 6, 30))
        self.assertEqual(dl.fiscal_year_start(7, date(2026, 6, 30)), date(2025, 7, 1))

    def test_annual_report_class_b(self):
        self.assertEqual(dl.annual_report_due(date(2025, 12, 31), "B"), date(2026, 6, 30))
        self.assertEqual(dl.annual_report_due(date(2026, 6, 30), "B"), date(2026, 12, 31))
        self.assertEqual(dl.annual_report_due(date(2025, 9, 30), "B"), date(2026, 3, 31))
        self.assertEqual(dl.annual_report_due(date(2025, 12, 31), "C"), date(2026, 6, 30))
        self.assertEqual(dl.annual_report_due(date(2025, 12, 31), "D"), date(2026, 4, 30))

    def test_annual_report_shift(self):
        p = dl.Profile(vat_period="none", fiscal_year_start_month=12, has_payroll=False)
        items = [d for d in dl.deadlines_for(p, date(2026, 5, 1), date(2026, 6, 30)) if d.kind == "aarsrapport"]
        self.assertEqual(items[0].due, date(2026, 5, 31))   # søndag (6 mdr. efter 30/11 2025)
        self.assertEqual(items[0].date, date(2026, 6, 1))
        self.assertEqual(items[0].period, "Regnskabsår 2024/25")

    def test_company_tax_return(self):
        self.assertEqual(dl.company_tax_return_due(date(2025, 12, 31)), date(2026, 6, 30))
        self.assertEqual(dl.company_tax_return_due(date(2026, 3, 31)), date(2026, 9, 1))
        self.assertEqual(dl.company_tax_return_due(date(2026, 2, 28)), date(2026, 8, 31))
        self.assertEqual(dl.company_tax_return_due(date(2026, 6, 30)), date(2026, 12, 31))

    def test_personal_business(self):
        p = dl.Profile(vat_period="none", legal_form="enk", accounting_class="A", has_payroll=False)
        items = dl.deadlines_for(p, date(2027, 1, 1), date(2027, 12, 31))
        kinds = {d.kind for d in items}
        self.assertNotIn("aarsrapport", kinds)
        self.assertNotIn("acontoskat", kinds)
        oply = [d for d in items if d.kind == "oplysningsskema"]
        self.assertEqual(oply[0].date, date(2027, 7, 1))
        self.assertEqual(oply[0].period, "Indkomstår 2026")

    def test_offset_year_label(self):
        p = dl.Profile(vat_period="none", fiscal_year_start_month=7, has_payroll=False)
        items = [d for d in dl.deadlines_for(p, date(2026, 11, 1), date(2026, 12, 31)) if d.kind == "aarsrapport"]
        self.assertEqual(items[0].period, "Regnskabsår 2025/26")
        self.assertEqual(items[0].date, date(2026, 12, 31))

    def test_aconto(self):
        p = dl.Profile(vat_period="none", has_payroll=False)
        items = [d for d in dl.deadlines_for(p, date(2026, 1, 1), date(2026, 12, 31)) if d.kind == "acontoskat"]
        self.assertEqual([d.date for d in items], [date(2026, 3, 20), date(2026, 11, 20)])

    def test_sorted_and_next(self):
        p = dl.Profile(vat_period="quarter")
        items = dl.deadlines_for(p, date(2026, 1, 1), date(2026, 12, 31))
        self.assertEqual([d.date for d in items], sorted(d.date for d in items))
        nxt = dl.next_deadline(p, date(2026, 11, 14))
        self.assertEqual(nxt.date, date(2026, 11, 20))  # acontoskat 2. rate
