// Kontonumre, som brugerfladen bruger. Skal svare til backend/accounts/chart.py
// (Erhvervsstyrelsens standardkontoplan). Kontonumre må ikke stå andre steder.

export const BASE_CURRENCY = 'DKK';

// Likvider
export const CASH = '6470';
export const BANK = '6480';
export const TREASURY_STANDARD_CODES = ['6470', '6480'];
export const CASH_STANDARD_CODES = ['6470'];

// Debitorer og kreditorer
export const RECEIVABLE = '6190';
export const CUSTOMER_PREPAYMENTS = '7410';
export const PAYABLE = '7440';
export const SUSPENSE = '6335';

// Moms og afgifter
export const VAT_OUTPUT = '7680';
export const VAT_EU_GOODS = '7700';
export const VAT_EU_SERVICES = '7720';
export const VAT_INPUT = '7740';
export const TAX_OIL = '7760';
export const TAX_ELECTRICITY = '7780';
export const TAX_GAS = '7800';
export const TAX_COAL = '7810';
export const TAX_WATER = '7820';
export const TAX_CO2 = '7830';
export const VAT_SETTLEMENT = '7840';
export const VAT_ACCOUNTS = [VAT_OUTPUT, VAT_EU_GOODS, VAT_EU_SERVICES, VAT_INPUT, TAX_OIL, TAX_ELECTRICITY,
  TAX_GAS, TAX_COAL, TAX_WATER, TAX_CO2];

// Resultat
export const REVENUE = '1010';
export const PURCHASES = '1610';
export const OTHER_EXTERNAL = '2810';
export const BANK_FEES = '2390';
export const REMINDER_FEES = '3490';
export const FX_GAIN = '3535';
export const FX_LOSS = '3610';

// Egenkapital
export const RETAINED_EARNINGS = '6940';
export const OWNER_RESULT = '6916';

// Løn (navnene er faste, se backend/accounts/chart.py DK_*)
export const DK_SALARIES = '2845';
export const DK_HOLIDAY_PAY_EXPENSE = '2860';
export const DK_PENSION_EXPENSE = '2910';
export const DK_ATP_EXPENSE = '2898';
export const DK_BENEFITS_EXPENSE = '2887';
export const DK_SALARY_REFUNDS = '2885';
export const DK_SALARIES_PAYABLE = '7860';
export const DK_A_TAX_PAYABLE = '7920';
export const DK_AM_PAYABLE = '7940';
export const DK_ATP_PAYABLE = '7960';
export const DK_PENSION_PAYABLE = '8000';
export const DK_HOLIDAY_PAY_PAYABLE = '7900';
export const DK_OTHER_PAYROLL_PAYABLE = '8010';

/** Konti, systemet selv bogfører på (tilbydes ikke som modkonto). */
export const SYSTEM_ACCOUNTS = [RECEIVABLE, CUSTOMER_PREPAYMENTS, PAYABLE, VAT_OUTPUT, VAT_EU_GOODS,
  VAT_EU_SERVICES, VAT_INPUT, VAT_SETTLEMENT];

interface AccountLike { code: string; standard_code?: string; is_header?: boolean }

/** Bank- og kassekonti (efter standardkontoplanens nummer 6470/6480), kun konti der kan bogføres på. */
export const isTreasury = (a: AccountLike | string): boolean => {
  if (typeof a === 'string') return TREASURY_STANDARD_CODES.includes(a);
  if (a.is_header) return false;
  return TREASURY_STANDARD_CODES.includes(a.code) || TREASURY_STANDARD_CODES.includes(a.standard_code || '');
};

/** Kassekonti. */
export const isCash = (a: AccountLike): boolean =>
  CASH_STANDARD_CODES.includes(a.code) || CASH_STANDARD_CODES.includes(a.standard_code || '');

/** Lønkonti (std. 2845-2898: lønninger). */
export const isSalaryAccount = (code: string): boolean => /^28[4-9]\d$/.test(code);

/** Resultatkonto (std. 1000-4999). */
export const isResultAccount = (code: string): boolean => {
  const n = parseInt(code.slice(0, 4), 10);
  return n >= 1000 && n <= 4999;
};
