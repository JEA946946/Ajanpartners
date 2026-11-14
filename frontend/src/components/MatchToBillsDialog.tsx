import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Button, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Autocomplete, Alert, CircularProgress, IconButton, Paper, Divider, Chip,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { formatNumber } from '../utils/format';

interface Txn { id: string; description: string; date?: string; debit: string; credit: string; currency?: string; }
interface Bill {
  id: string; bill_number: string; supplier_name: string | null;
  date: string; total: string; balance_due: string; status: string;
}

interface Props {
  open: boolean;
  initialTxns: Txn[];
  allTxns: Txn[];
  linkedIds: Set<string>;
  onClose: () => void;
  onDone: (succeededTxnIds: string[]) => void;
}

const amountOf = (t: Txn) => (parseFloat(t.credit || '0') || parseFloat(t.debit || '0')) || 0;
const money = (n: number) => formatNumber(n);

/**
 * Match bank transactions against supplier invoices with both sides editable and
 * shown opposite each other. Add/remove transactions (left) and bills (right); the
 * transaction amounts are allocated greedily across the bills (each up to its balance
 * due), recording a payment per (bill, transaction) allocation via the existing
 * /bills/:id/record-payment endpoint. Covers many→one, one→many and N→M.
 */
const MatchToBillsDialog: React.FC<Props> = ({ open, initialTxns, allTxns, linkedIds, onClose, onDone }) => {
  const { t } = useTranslation();
  const [selTxns, setSelTxns] = useState<Txn[]>([]);
  const [selBills, setSelBills] = useState<Bill[]>([]);
  const [billOptions, setBillOptions] = useState<Bill[]>([]);
  const [billSearch, setBillSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // Initialise ONLY when the dialog opens. `initialTxns` is a fresh array every
  // parent render, so depending on it would reset selBills on every render (the bug
  // that made "nothing happens" — the chosen bills were wiped before Match could run).
  useEffect(() => {
    if (open) { setSelTxns(initialTxns); setSelBills([]); setBillSearch(''); setError(''); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    const q = billSearch ? `&search=${encodeURIComponent(billSearch)}` : '';
    api.get(`/bills?page_size=50&sort=date&sort_dir=desc${q}`)
      .then(r => {
        if (r.data.success) {
          setBillOptions((r.data.data.bills || [])
            .filter((b: Bill) => parseFloat(b.balance_due) > 0.001 && b.status !== 'paid'));
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [open, billSearch]);

  const txnTotal = selTxns.reduce((s, x) => s + amountOf(x), 0);
  const billTotal = selBills.reduce((s, b) => s + parseFloat(b.balance_due), 0);
  const currency = 'kr.';
  const diff = Math.round((txnTotal - billTotal) * 100) / 100;

  const txnAddOptions = allTxns.filter(x => !linkedIds.has(x.id) && !selTxns.some(s => s.id === x.id));

  const handleMatch = async () => {
    if (selTxns.length === 0 || selBills.length === 0) {
      setError(t('billMatching.selectBothRequired')); return;
    }
    setSaving(true); setError('');
    const txnRem = selTxns.map(x => ({ id: x.id, rem: amountOf(x) }));
    const billRem = selBills.map(b => ({ id: b.id, rem: parseFloat(b.balance_due) }));
    const done = new Set<string>();
    let ok = 0, failed = 0;
    for (const tr of txnRem) {
      for (const br of billRem) {
        if (tr.rem <= 0.001) break;
        if (br.rem <= 0.001) continue;
        const amt = Math.round(Math.min(tr.rem, br.rem) * 100) / 100;
        if (amt <= 0) continue;
        try {
          const res = await api.post(`/bills/${br.id}/record-payment`, {
            journal_entry_line_id: tr.id, amount: amt,
          });
          if (res.data.success) { tr.rem -= amt; br.rem -= amt; ok += 1; done.add(tr.id); }
          else failed += 1;
        } catch { failed += 1; }
      }
    }
    setSaving(false);
    if (done.size === 0) {
      // Nothing matched — keep the dialog open so the error is visible.
      setError(failed > 0 ? t('billMatching.matchPartial', { ok, failed }) : t('billMatching.nothingAllocated'));
      return;
    }
    if (failed > 0) setError(t('billMatching.matchPartial', { ok, failed }));
    onDone([...done]);
  };

  const balanced = Math.abs(diff) < 0.01;
  const sideTotal = (label: string, total: number, count: number) => (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', px: 0.5 }}>
      <Typography variant="caption" color="text.secondary">{label} ({count})</Typography>
      <Typography variant="body2" sx={{ fontWeight: 700, fontFamily: 'monospace', color: balanced ? 'success.main' : 'error.main' }}>
        {money(total)} {currency}
      </Typography>
    </Box>
  );

  const rowSx = { display: 'flex', alignItems: 'center', gap: 0.5, px: 0.5, py: 0.3, borderBottom: '1px solid #eee' };

  return (
    <Dialog open={open} onClose={saving ? undefined : onClose} maxWidth="lg" fullWidth
      PaperProps={{ sx: { fontSize: 11 } }}>
      <DialogTitle>{t('billMatching.matchToBillsTitle', { count: selTxns.length })}</DialogTitle>
      <DialogContent>
        {error && <Alert severity="warning" sx={{ mb: 1.5 }} onClose={() => setError('')}>{error}</Alert>}

        <Box sx={{
          display: 'flex', gap: 2, flexDirection: { xs: 'column', md: 'row' }, alignItems: 'stretch',
          '& .MuiTypography-caption': { fontSize: '10.5px', lineHeight: 1.3 },
          '& .MuiTypography-subtitle2': { fontSize: '12px' },
        }}>
          {/* Left: transactions */}
          <Paper variant="outlined" sx={{ flex: 1, minWidth: 0, p: 1, display: 'flex', flexDirection: 'column' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>{t('billMatching.transactionsLabel')}</Typography>
            <Box sx={{ maxHeight: 260, overflow: 'auto', mb: 1 }}>
              {selTxns.map(x => (
                <Box key={x.id} sx={rowSx}>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="caption" noWrap sx={{ display: 'block' }} title={x.description}>{x.description}</Typography>
                    {x.date && <Typography variant="caption" color="text.secondary">{x.date}</Typography>}
                  </Box>
                  <Typography variant="caption" sx={{ fontFamily: 'monospace', whiteSpace: 'nowrap' }}>{money(amountOf(x))}</Typography>
                  <IconButton size="small" onClick={() => setSelTxns(p => p.filter(s => s.id !== x.id))} sx={{ p: 0.2 }}>
                    <CloseIcon sx={{ fontSize: 15 }} />
                  </IconButton>
                </Box>
              ))}
              {selTxns.length === 0 && <Typography variant="caption" color="text.secondary" sx={{ p: 1, display: 'block' }}>—</Typography>}
            </Box>
            <Autocomplete
              size="small"
              options={txnAddOptions}
              value={null}
              blurOnSelect clearOnBlur autoHighlight
              onChange={(_e, v) => { if (v) setSelTxns(p => [...p, v]); }}
              getOptionLabel={(x) => `${x.description || ''} · ${money(amountOf(x))}`}
              filterOptions={(opts, state) => {
                const q = state.inputValue.trim().toLowerCase();
                const matched = q
                  ? opts.filter(o =>
                      (o.description || '').toLowerCase().includes(q) ||
                      (o.date || '').includes(q) ||
                      money(amountOf(o)).includes(q) ||
                      String(amountOf(o)).includes(q))
                  : opts;
                return matched.slice(0, 100);
              }}
              renderOption={(props, x) => (
                <li {...props} key={x.id} style={{ fontSize: 12, display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{x.description}</span>
                  <span style={{ fontFamily: 'monospace', whiteSpace: 'nowrap' }}>{money(amountOf(x))}</span>
                </li>
              )}
              isOptionEqualToValue={(o, v) => o.id === v.id}
              ListboxProps={{ style: { maxHeight: 240 } }}
              renderInput={(p) => <TextField {...p} size="small" label={t('billMatching.addTransaction')} placeholder={t('common.search')} />}
            />
            <Divider sx={{ my: 1 }} />
            {sideTotal(t('billMatching.transactionsLabel'), txnTotal, selTxns.length)}
          </Paper>

          {/* Right: bills */}
          <Paper variant="outlined" sx={{ flex: 1, minWidth: 0, p: 1, display: 'flex', flexDirection: 'column' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>{t('billMatching.billsLabel')}</Typography>
            <Box sx={{ maxHeight: 260, overflow: 'auto', mb: 1 }}>
              {selBills.map(b => (
                <Box key={b.id} sx={rowSx}>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="caption" noWrap sx={{ display: 'block' }} title={b.supplier_name || ''}>
                      <b>{b.bill_number}</b> · {b.supplier_name || '—'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">{b.date}</Typography>
                  </Box>
                  <Typography variant="caption" sx={{ fontFamily: 'monospace', whiteSpace: 'nowrap' }}>{money(parseFloat(b.balance_due))}</Typography>
                  <IconButton size="small" onClick={() => setSelBills(p => p.filter(s => s.id !== b.id))} sx={{ p: 0.2 }}>
                    <CloseIcon sx={{ fontSize: 15 }} />
                  </IconButton>
                </Box>
              ))}
              {selBills.length === 0 && <Typography variant="caption" color="text.secondary" sx={{ p: 1, display: 'block' }}>—</Typography>}
            </Box>
            <Autocomplete
              size="small"
              options={billOptions.filter(b => !selBills.some(s => s.id === b.id))}
              value={null}
              blurOnSelect clearOnBlur
              onChange={(_e, v) => { if (v) setSelBills(p => [...p, v]); }}
              filterOptions={(x) => x}
              onInputChange={(_e, v) => setBillSearch(v)}
              getOptionLabel={(b) => `${b.bill_number} — ${b.supplier_name || '—'} · ${money(parseFloat(b.balance_due))}`}
              isOptionEqualToValue={(o, v) => o.id === v.id}
              loading={loading}
              ListboxProps={{ style: { maxHeight: 240 } }}
              renderInput={(p) => <TextField {...p} size="small" label={t('billMatching.addBill')} placeholder={t('billMatching.searchBills')} />}
            />
            <Divider sx={{ my: 1 }} />
            {sideTotal(t('billMatching.billsLabel'), billTotal, selBills.length)}
          </Paper>
        </Box>

        <Box sx={{ mt: 1.5, display: 'flex', justifyContent: 'center' }}>
          <Chip
            label={`${t('billMatching.matchDiff')}: ${money(diff)} ${currency}`}
            color={Math.abs(diff) < 0.01 ? 'success' : 'error'}
            variant="filled"
            size="small"
            sx={{ fontWeight: 700 }}
          />
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
          {t('billMatching.matchHint')}
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>{t('common.cancel')}</Button>
        <Button
          variant="contained"
          onClick={handleMatch}
          disabled={saving || selTxns.length === 0 || selBills.length === 0}
          startIcon={saving ? <CircularProgress size={16} /> : undefined}
          sx={{ bgcolor: '#2e7d32' }}
        >
          {t('billMatching.match')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MatchToBillsDialog;
