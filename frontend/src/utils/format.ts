// Danske formater: datoer dd-mm-åååå og beløb 1.234,56 kr.

const nf = new Intl.NumberFormat('da-DK', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** 1234.5 → "1.234,50" */
export function formatNumber(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '';
  const n = typeof value === 'number' ? value : parseFloat(value);
  if (Number.isNaN(n)) return String(value);
  return nf.format(n);
}

/** 1234.5 → "1.234,50 kr." (DKK) eller "1.234,50 EUR". */
export function formatMoney(value: string | number | null | undefined, currency = 'DKK'): string {
  const s = formatNumber(value);
  if (s === '') return '';
  return currency === 'DKK' ? `${s} kr.` : `${s} ${currency}`;
}

/** Bagudkompatibelt navn. */
export const formatAmount = formatMoney;

/** "1.234,56" eller "1234.56" → 1234.56 (accepterer dansk input). */
export function parseAmount(input: string): number {
  const s = (input || '').trim().replace(/\s/g, '');
  if (!s) return 0;
  const normalized = s.includes(',') ? s.replace(/\./g, '').replace(',', '.') : s;
  const n = parseFloat(normalized);
  return Number.isNaN(n) ? 0 : n;
}

export { formatDate } from './dateFormat';
