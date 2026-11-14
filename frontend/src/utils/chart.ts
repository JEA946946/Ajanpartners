// Account codes the UI relies on. Must match backend/accounts/chart.py (PCGM).

/** Bank (514x) and cash (516x) accounts that hold money — sub-accounts only, not the class headers. */
export const isTreasury = (code: string) => /^51[46]\d{2,}/.test(code);

/** Salary expense accounts (6171x Rémunérations du personnel). */
export const isSalaryAccount = (code: string) => code.startsWith('6171') && code.length > 4;
