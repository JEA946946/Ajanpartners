// Fælles typer og formatering for lønmodulet.

export const kr = (v: string | number | null | undefined): string => {
  const n = typeof v === 'number' ? v : parseFloat(v || '0');
  return `${n.toLocaleString('da-DK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} kr.`;
};

export const apiError = (e: any, fallback = 'Der opstod en fejl.'): string =>
  e?.response?.data?.message || e?.response?.data?.detail || fallback;

export const MONTHS = ['januar', 'februar', 'marts', 'april', 'maj', 'juni', 'juli', 'august',
  'september', 'oktober', 'november', 'december'];

export const PAY_FORMS: Record<string, string> = {
  month: 'Månedsløn', fortnight: '14-dagesløn', hourly: 'Timeløn (månedsvis)',
};
export const TAX_CARDS: Record<string, string> = {
  main: 'Hovedkort', secondary: 'Bikort', free: 'Frikort', none: 'Intet skattekort (55 %)',
};
export const HOLIDAY_SCHEMES: Record<string, string> = { feriekonto: 'FerieKonto', own: 'Egen ordning' };
export const HOLIDAY_TYPES: Record<string, string> = {
  with_pay: 'Ferie med løn + ferietillæg', without_pay: 'Ferie uden løn (12,5 % feriepenge)',
};
export const ALLOWANCE_MODES: Record<string, string> = { monthly: 'Udbetales løbende', accrue: 'Hensættes' };
export const ATP_CLASSES: Record<string, string> = {
  A: 'A-sats (standard)', B: 'B-sats', C: 'C-sats', D: 'D-sats', E: 'E-sats', F: 'F-sats', '0': 'Ingen ATP',
};

export const RUN_STATUS: Record<string, { label: string; color: 'default' | 'info' | 'warning' | 'success' }> = {
  draft: { label: 'Kladde', color: 'default' },
  calculated: { label: 'Beregnet', color: 'info' },
  approved: { label: 'Godkendt', color: 'warning' },
  posted: { label: 'Bogført', color: 'success' },
};

export interface Employee {
  id: string;
  employee_number: string;
  first_name: string;
  last_name: string;
  name: string;
  cpr_masked: string;
  has_cpr: boolean;
  address: string;
  email: string;
  bank_reg: string;
  bank_account: string;
  start_date: string | null;
  end_date: string | null;
  pay_form: string;
  monthly_salary: string;
  hourly_rate: string;
  hours_per_week: string;
  tax_card: string;
  tax_rate: string;
  deduction_month: string;
  deduction_fortnight: string | null;
  free_card_amount: string;
  tax_card_year: number | null;
  tax_card_fetched_at: string | null;
  holiday_scheme: string;
  holiday_type: string;
  holiday_allowance_pct: string;
  holiday_allowance_mode: string;
  pension_employee_pct: string;
  pension_employer_pct: string;
  pension_company: string;
  atp_class: string;
  car_benefit_month: string;
  free_phone: boolean;
  is_active: boolean;
  notes: string;
}

export interface PayrollLine {
  id: string;
  employee_id: string;
  employee_number: string;
  employee_name: string;
  pay_form: string;
  hours: string;
  base_salary: string;
  supplements: string;
  holiday_payout: string;
  a_income_no_am: string;
  car_benefit: string;
  phone_benefit: string;
  other_benefits: string;
  b_income: string;
  b_income_am: boolean;
  sick_pay_refund: string;
  note: string;
  tax_card: string;
  tax_rate: string;
  holiday_allowance_paid: string;
  holiday_allowance_accrued: string;
  holiday_pay_accrued: string;
  gross_cash: string;
  benefits: string;
  atp_employee: string;
  atp_employer: string;
  pension_employee: string;
  pension_employer: string;
  am_base: string;
  am_contribution: string;
  tax_base: string;
  deduction_used: string;
  frikort_used: string;
  a_tax: string;
  net_pay: string;
  employer_cost: string;
  calculated: boolean;
  warnings: string[];
}

export interface PayrollRun {
  id: string;
  frequency: string;
  year: number;
  month: number;
  label: string;
  period_start: string;
  period_end: string;
  pay_date: string;
  status: string;
  is_editable: boolean;
  journal_entry_id: string | null;
  approved_by: string;
  eindkomst_status: string;
  eindkomst_reference: string;
  eindkomst_submitted_at: string | null;
  line_count: number;
  total_gross: string;
  total_benefits: string;
  total_am: string;
  total_a_tax: string;
  total_atp_employee: string;
  total_atp_employer: string;
  total_pension_employee: string;
  total_pension_employer: string;
  total_holiday: string;
  total_b_income: string;
  total_net: string;
  lines?: PayrollLine[];
}

export const openBlob = (data: BlobPart, type: string, filename: string, download = false) => {
  const url = URL.createObjectURL(new Blob([data], { type }));
  if (download) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
  } else {
    window.open(url, '_blank');
  }
  setTimeout(() => URL.revokeObjectURL(url), 60000);
};
