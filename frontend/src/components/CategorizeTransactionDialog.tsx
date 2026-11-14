import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Button, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, MenuItem, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Paper, Autocomplete, IconButton, Alert, ToggleButton, ToggleButtonGroup,
} from '@mui/material';
import { Add as AddIcon, RemoveCircleOutline as RemoveLineIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { formatDate } from '../utils/dateFormat';
import { formatMoney } from '../utils/format';
import api from '../services/api';

interface Txn {
  id: string;
  date: string;
  description: string;
  reference: string;
  debit: string;
  credit: string;
  bank_account_code?: string;
  currency?: string;
}

interface Account { id: string; code: string; name: string; }
interface TaxCode {
  id: string; code: string; name?: string; rate: number | string; account_id?: string; type?: string;
  is_active?: boolean; reverse_charge?: string; energy_tax?: boolean; deduction_rate?: string;
}
interface Line { description: string; account_id: string; amount: string; tax_code_id: string; }
interface OpenInvoice {
  id: string; invoice_number: string; customer_name: string; due_date: string; total: string;
  balance_due: string; currency: string; status: string; journal_entry_id: string | null;
}
interface InvoiceLine { invoice_id: string; amount: string; }

interface Props {
  open: boolean;
  txn: Txn | null;
  onClose: () => void;
  onDone: () => void;
}

const acctLabel = (a: Account) => `${a.code} — ${a.name}`;

const txnAmount = (txn: Txn) =>
  (parseFloat(txn.credit || '0') || parseFloat(txn.debit || '0')) || 0;

/**
 * Afstem en banklinje ved at bogføre den direkte på en eller flere konti (uden
 * kreditor). Kalder /transactions/:id/categorize, som flytter beløbet fra
 * mellemregningskontoen (chart.SUSPENSE, "Uafklarede poster") til kontiene.
 * Beløbet er inkl. moms; momsen udskilles efter momskoden.
 */
const CategorizeTransactionDialog: React.FC<Props> = ({ open, txn, onClose, onDone }) => {
  const { t } = useTranslation();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [taxCodes, setTaxCodes] = useState<TaxCode[]>([]);
  const [lines, setLines] = useState<Line[]>([{ description: '', account_id: '', amount: '', tax_code_id: '' }]);
  const [saving, setSaving] = useState(false);
  const [mode, setMode] = useState<'account' | 'invoice'>('account');
  const [openInvoices, setOpenInvoices] = useState<OpenInvoice[]>([]);
  const [invLines, setInvLines] = useState<InvoiceLine[]>([{ invoice_id: '', amount: '' }]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!open) return;
    api.get('/accounts?is_active=true').then(r => {
      if (r.data.success) {
        const list: Account[] = [...r.data.data.accounts].sort((a, b) => a.code.localeCompare(b.code));
        setAccounts(list);
      }
    }).catch(() => {});
    api.get('/tax-codes').then(r => { if (r.data.success) setTaxCodes(r.data.data.tax_codes); }).catch(() => {});
    api.get('/invoices').then(r => {
      if (r.data.success) {
        setOpenInvoices((r.data.invoices || []).filter((inv: OpenInvoice) =>
          inv.journal_entry_id && parseFloat(inv.balance_due || '0') > 0 && !['paid', 'cancelled'].includes(inv.status)));
      }
    }).catch(() => { /* fakturering indgår ikke i pakken */ });
  }, [open]);

  useEffect(() => {
    if (open && txn) {
      setError('');
      setLines([{ description: txn.description || '', account_id: '', amount: String(txnAmount(txn) || ''), tax_code_id: '' }]);
      setInvLines([{ invoice_id: '', amount: String(txnAmount(txn) || '') }]);
      setMode('account');
    }
  }, [open, txn]);

  // Ved en indbetaling: foreslå åbne fakturaer, hvis restbeløb eller nummer/kunde passer med banklinjen.
  const incomingTxn = !!txn && !(parseFloat(txn.credit || '0') > 0);
  const suggestions = !txn || !incomingTxn ? [] : openInvoices.filter(inv => {
    const desc = (txn.description || '').toLowerCase();
    const sameAmount = Math.abs(parseFloat(inv.balance_due) - txnAmount(txn)) < 0.005;
    const named = (inv.invoice_number && desc.includes(inv.invoice_number.toLowerCase()))
      || (inv.customer_name && desc.includes(inv.customer_name.toLowerCase()));
    return sameAmount || named;
  });

  useEffect(() => {
    if (open && incomingTxn && suggestions.length > 0 && mode === 'account' && !invLines[0].invoice_id) {
      setMode('invoice');
      setInvLines([{ invoice_id: suggestions[0].id,
        amount: String(Math.min(parseFloat(suggestions[0].balance_due), txnAmount(txn!))) }]);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps -- foreslå én gang, når fakturaerne er hentet
  }, [open, openInvoices.length]);

  const updateInvLine = (i: number, field: keyof InvoiceLine, value: string) =>
    setInvLines(prev => prev.map((l, idx) => {
      if (idx !== i) return l;
      const next = { ...l, [field]: value };
      if (field === 'invoice_id') {
        const inv = openInvoices.find(x => x.id === value);
        if (inv && txn) {
          const others = prev.reduce((s2, x, j) => (j === i ? s2 : s2 + (parseFloat(x.amount || '0') || 0)), 0);
          next.amount = String(Math.max(0, Math.min(parseFloat(inv.balance_due), txnAmount(txn) - others)).toFixed(2));
        }
      }
      return next;
    }));
  const invLabel = (inv: OpenInvoice) =>
    `${inv.invoice_number} — ${inv.customer_name} · ${t('categorize.balanceDue', 'rest')} ${formatMoney(inv.balance_due)}`;

  const updateLine = (i: number, field: keyof Line, value: string) =>
    setLines(prev => prev.map((l, idx) => (idx === i ? { ...l, [field]: value } : l)));
  const addLine = () => setLines(prev => [...prev, { description: '', account_id: '', amount: '', tax_code_id: '' }]);
  const removeLine = (i: number) => setLines(prev => (prev.length <= 1 ? prev : prev.filter((_, idx) => idx !== i)));

  // Bank payments are VAT-inclusive: the entered amount IS the gross amount.
  // The total must equal the transaction amount; any selected tax code is
  // split out of (not added to) that amount by the backend.
  const total = mode === 'invoice'
    ? invLines.reduce((sum, l) => sum + (parseFloat(l.amount || '0') || 0), 0)
    : lines.reduce((sum, l) => sum + (parseFloat(l.amount || '0') || 0), 0);
  const vatIncluded = lines.reduce((sum, l) => {
    const gross = parseFloat(l.amount || '0') || 0;
    const tc = taxCodes.find(c => c.id === l.tax_code_id);
    // Omvendt betalingspligt og energiafgift: ingen moms i bankbeløbet.
    const rate = tc && !tc.reverse_charge && !tc.energy_tax ? Number(tc.rate) : 0;
    return sum + (rate ? gross * rate / (100 + rate) : 0);
  }, 0);

  if (!txn) return null;
  const amount = txnAmount(txn);
  const outgoing = parseFloat(txn.credit || '0') > 0;
  const codesForDirection = taxCodes.filter(tc =>
    tc.is_active !== false && (!tc.type || tc.type === 'both' || tc.type === (outgoing ? 'purchase' : 'sales')));
  const mismatch = total.toFixed(2) !== amount.toFixed(2);

  const handleSave = async () => {
    const validLines = lines.filter(l => l.account_id && l.amount);
    const validInv = invLines.filter(l => l.invoice_id && l.amount);
    if (mode === 'invoice') {
      if (validInv.length === 0) { setError(t('categorize.invoiceRequired', 'Vælg mindst én faktura')); return; }
      const over = validInv.find(l => {
        const inv = openInvoices.find(x => x.id === l.invoice_id);
        return inv && parseFloat(l.amount) > parseFloat(inv.balance_due) + 0.005;
      });
      if (over) { setError(t('categorize.exceedsBalance', 'Beløbet er større end fakturaens restbeløb')); return; }
    } else if (validLines.length === 0) { setError(t('bankTransactions.accountRequired')); return; }
    if (mismatch) { setError(t('billMatching.amountMismatch')); return; }
    setSaving(true);
    setError('');
    try {
      const res = await api.post(`/transactions/${txn.id}/categorize`, {
        date: txn.date,
        description: txn.description || '',
        reference: txn.reference || '',
        lines: mode === 'invoice'
          ? validInv.map(l => ({
            invoice_id: l.invoice_id, amount: l.amount,
            description: `${t('categorize.invoicePayment', 'Betaling af faktura')} ${openInvoices.find(x => x.id === l.invoice_id)?.invoice_number || ''}`.trim(),
          }))
          : validLines.map(l => ({
            description: l.description, account_id: l.account_id, amount: l.amount, tax_code_id: l.tax_code_id || '',
          })),
      });
      if (res.data.success) {
        onDone();
      } else {
        setError(res.data.message || t('common.error'));
      }
    } catch (err: any) {
      setError(err.response?.data?.message || t('common.error'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{mode === 'invoice' && incomingTxn ? t('categorize.invoicePayment', 'Betaling af faktura') : t('billMatching.bookToAccount')}</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2, mt: 1, p: 1, bgcolor: '#f5f5f5', borderRadius: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {formatDate(txn.date)} · {txn.description || '—'} · {txn.bank_account_code}
          </Typography>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

        {incomingTxn && (
          <ToggleButtonGroup
            exclusive size="small" value={mode} sx={{ mb: 2 }}
            onChange={(_e, v) => { if (v) setMode(v); }}
          >
            <ToggleButton value="invoice">{t('categorize.invoicePayment', 'Betaling af faktura')}</ToggleButton>
            <ToggleButton value="account">{t('billMatching.bookToAccount')}</ToggleButton>
          </ToggleButtonGroup>
        )}

        {mode === 'invoice' && incomingTxn ? (
          <>
            {suggestions.length > 0 && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                {t('categorize.suggested', 'Forslag ud fra beløb og tekst')}: {suggestions.map(s2 => s2.invoice_number).join(', ')}
              </Typography>
            )}
            {openInvoices.length === 0 && (
              <Alert severity="info" sx={{ mb: 1 }}>{t('categorize.noOpenInvoices', 'Der er ingen åbne, udstedte fakturaer.')}</Alert>
            )}
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                    <TableCell sx={{ fontWeight: 600 }}>{t('categorize.invoice', 'Faktura')}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, width: 140 }}>{t('common.amount')}</TableCell>
                    <TableCell sx={{ width: 40 }} />
                  </TableRow>
                </TableHead>
                <TableBody>
                  {invLines.map((l, i) => (
                    <TableRow key={i}>
                      <TableCell sx={{ p: 0.5 }}>
                        <Autocomplete
                          size="small" fullWidth
                          options={[...suggestions, ...openInvoices.filter(x => !suggestions.includes(x))]}
                          value={openInvoices.find(x => x.id === l.invoice_id) || null}
                          onChange={(_e, v) => updateInvLine(i, 'invoice_id', v?.id || '')}
                          getOptionLabel={invLabel}
                          groupBy={(o) => (suggestions.includes(o)
                            ? t('categorize.suggestedGroup', 'Forslag') : t('categorize.otherInvoices', 'Andre åbne fakturaer'))}
                          isOptionEqualToValue={(o, v) => o.id === v.id}
                          renderInput={(p) => <TextField {...p} placeholder={t('categorize.pickInvoice', 'Vælg faktura')} />}
                        />
                      </TableCell>
                      <TableCell sx={{ p: 0.5 }}>
                        <TextField value={l.amount} size="small" type="number" sx={{ width: 130 }}
                          onChange={(e) => updateInvLine(i, 'amount', e.target.value)}
                          inputProps={{ min: 0, step: '0.01', style: { textAlign: 'right' } }} />
                      </TableCell>
                      <TableCell sx={{ p: 0.5 }}>
                        <IconButton size="small" disabled={invLines.length <= 1}
                          onClick={() => setInvLines(prev => prev.filter((_, idx) => idx !== i))}>
                          <RemoveLineIcon sx={{ fontSize: 16 }} />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow sx={{ bgcolor: '#e8f5e9' }}>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>{t('common.total')}:</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700, color: mismatch ? 'warning.main' : undefined }}>
                      {formatMoney(total)}
                    </TableCell>
                    <TableCell />
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
              <Button startIcon={<AddIcon sx={{ fontSize: 18 }} />} size="small"
                onClick={() => setInvLines(prev => [...prev, { invoice_id: '', amount: '' }])}>
                {t('categorize.addInvoice', 'Tilføj faktura')}
              </Button>
              <Typography variant="caption" color={mismatch ? 'warning.main' : 'text.secondary'}>
                {t('bankTransactions.txnAmount')}: {formatMoney(amount)}
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              {t('categorize.invoicePaymentHint', 'Beløbet bogføres på debitorkontoen hos kunden, fakturaens restbeløb nedskrives, og fakturaen udlignes, når den er betalt.')}
            </Typography>
          </>
        ) : (
        <>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                <TableCell sx={{ fontWeight: 600, width: '28%' }}>{t('common.description')}</TableCell>
                <TableCell sx={{ fontWeight: 600, width: '32%' }}>{t('common.account')}</TableCell>
                <TableCell sx={{ fontWeight: 600, width: '18%' }}>{t('bills.taxCode')}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600, width: 120 }}>{t('common.amount')}</TableCell>
                <TableCell sx={{ width: 40 }} />
              </TableRow>
            </TableHead>
            <TableBody>
              {lines.map((line, i) => (
                <TableRow key={i}>
                  <TableCell sx={{ p: 0.5 }}>
                    <TextField value={line.description} size="small" fullWidth placeholder={t('common.description')}
                      onChange={(e) => updateLine(i, 'description', e.target.value)} />
                  </TableCell>
                  <TableCell sx={{ p: 0.5 }}>
                    <Autocomplete
                      size="small" fullWidth options={accounts}
                      value={accounts.find((a) => a.id === line.account_id) || null}
                      onChange={(_e, v) => updateLine(i, 'account_id', v?.id || '')}
                      getOptionLabel={acctLabel}
                      filterOptions={(opts, st) => {
                        const q = st.inputValue.toLowerCase();
                        return q ? opts.filter((a) => a.name.toLowerCase().includes(q) || a.code.toLowerCase().includes(q)) : opts;
                      }}
                      ListboxProps={{ style: { maxHeight: 320 } }}
                      isOptionEqualToValue={(o, v) => o.id === v.id}
                      renderInput={(p) => <TextField {...p} placeholder="—" />}
                    />
                  </TableCell>
                  <TableCell sx={{ p: 0.5 }}>
                    <TextField select value={line.tax_code_id} size="small" fullWidth
                      onChange={(e) => updateLine(i, 'tax_code_id', e.target.value)}>
                      <MenuItem value="">{t('common.none')}</MenuItem>
                      {codesForDirection.map((tc) => (
                        <MenuItem key={tc.id} value={tc.id}>{tc.code}{tc.name ? ` — ${tc.name}` : ` (${tc.rate}%)`}</MenuItem>
                      ))}
                    </TextField>
                  </TableCell>
                  <TableCell sx={{ p: 0.5 }}>
                    <TextField value={line.amount} size="small" type="number" sx={{ width: 110 }}
                      onChange={(e) => updateLine(i, 'amount', e.target.value)}
                      inputProps={{ min: 0, step: '0.01', style: { textAlign: 'right' } }} />
                  </TableCell>
                  <TableCell sx={{ p: 0.5 }}>
                    <IconButton size="small" onClick={() => removeLine(i)} disabled={lines.length <= 1}>
                      <RemoveLineIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              <TableRow sx={{ bgcolor: '#e8f5e9' }}>
                <TableCell colSpan={3} align="right" sx={{ fontWeight: 700 }}>{t('common.total')}:</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700, color: mismatch ? 'warning.main' : undefined }}>
                  {formatMoney(total)}
                </TableCell>
                <TableCell />
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
          <Button startIcon={<AddIcon sx={{ fontSize: 18 }} />} onClick={addLine} size="small">
            {t('expenses.addLine')}
          </Button>
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="caption" display="block" color={mismatch ? 'warning.main' : 'text.secondary'}>
              {t('bankTransactions.txnAmount')}: {formatMoney(amount)}
            </Typography>
            {vatIncluded > 0 && (
              <Typography variant="caption" display="block" color="text.secondary">
                {t('billMatching.vatIncluded')}: {formatMoney(vatIncluded)}
              </Typography>
            )}
          </Box>
        </Box>
        </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('common.cancel')}</Button>
        <Button variant="contained" onClick={handleSave} disabled={saving} sx={{ bgcolor: '#2e7d32' }}>
          {mode === 'invoice' && incomingTxn ? t('categorize.registerPayment', 'Registrér betaling') : t('billMatching.bookToAccount')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CategorizeTransactionDialog;
