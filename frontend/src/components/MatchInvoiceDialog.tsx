import React, { useEffect, useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, Box, Typography, Alert, Table, TableHead,
  TableRow, TableCell, TableBody, CircularProgress, TextField, Chip, Radio,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { formatDate } from '../utils/dateFormat';
import api from '../services/api';

interface Txn { id: string; date: string; description: string; reference: string; debit: string; credit: string; }

interface Suggestion {
  cmr_invoice_id: string;
  invoice_number: string;
  customer_name: string | null;
  trip_reference: string | null;
  currency: string;
  total: string;
  open: string;
  invoice_date: string | null;
  score: number;
  why: string[];
}

interface Waiting {
  id: string;
  invoice_number: string;
  customer_name: string;
  trip_reference: string;
  waiting: string;
  received_on: string;
}

interface Props {
  open: boolean;
  txn: Txn | null;
  onClose: () => void;
  onDone: () => void;
  /** Book the line to an account instead (the old categorise dialog). */
  onBookToAccount: () => void;
}

const isMad = (c: string) => ['MAD', 'DH', 'DHS', ''].includes((c || '').toUpperCase());
const n = (v: string | number) => (typeof v === 'number' ? v : parseFloat(v || '0')) || 0;

/**
 * Match money that came in to a CRM invoice. The invoice is worth the MAD that
 * arrived: for an EUR invoice the rate is simply MAD received ÷ euros covered.
 */
const MatchInvoiceDialog: React.FC<Props> = ({ open, txn, onClose, onDone, onBookToAccount }) => {
  const { t, i18n } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [rows, setRows] = useState<Suggestion[]>([]);
  const [unallocated, setUnallocated] = useState(0);
  const [selected, setSelected] = useState<Suggestion | null>(null);
  const [amountMad, setAmountMad] = useState('');
  const [covered, setCovered] = useState('');
  const [search, setSearch] = useState('');
  const [eurAccount, setEurAccount] = useState(false);
  const [waiting, setWaiting] = useState<Waiting[]>([]);
  const [pickedWaiting, setPickedWaiting] = useState<Waiting | null>(null);

  useEffect(() => {
    if (!open || !txn) return;
    setError(''); setRows([]); setSelected(null); setPickedWaiting(null); setSearch(''); setLoading(true);
    api.get(`/transactions/${txn.id}/invoice-suggestions`)
      .then(res => {
        const d = res.data.data;
        setRows(d.suggestions || []);
        setWaiting(d.waiting_exchange || []);
        setEurAccount(!!d.eur_account);
        setUnallocated(n(d.unallocated));
        setAmountMad(String(n(d.unallocated)));
      })
      .catch(err => setError(err.response?.data?.message || t('matchInvoice.errorLoading')))
      .finally(() => setLoading(false));
  }, [open, txn, t]);

  const pick = (s: Suggestion) => {
    setSelected(s); setPickedWaiting(null);
    if (eurAccount) { setCovered(Math.min(unallocated, n(s.open)).toFixed(2)); return; }
    const mad = Math.min(unallocated, isMad(s.currency) ? n(s.open) : unallocated);
    setAmountMad(mad.toFixed(2));
    setCovered(isMad(s.currency) ? mad.toFixed(2) : n(s.open).toFixed(2));
  };

  const pickWaiting = (w: Waiting) => {
    setPickedWaiting(w); setSelected(null);
    setCovered(n(w.waiting).toFixed(2));
    setAmountMad(unallocated.toFixed(2));
  };

  const fmt = (v: number) => v.toLocaleString(i18n.language, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const foreign = (!!selected && !isMad(selected.currency)) || !!pickedWaiting;
  const rate = !eurAccount && foreign && n(covered) > 0 ? n(amountMad) / n(covered) : null;
  const unit = eurAccount ? 'EUR' : 'MAD';
  const shown = rows.filter(r => !search
    || `${r.invoice_number} ${r.customer_name || ''} ${r.trip_reference || ''}`.toLowerCase().includes(search.toLowerCase()));

  const save = async () => {
    if (!txn || (!selected && !pickedWaiting)) return;
    setSaving(true); setError('');
    try {
      const body = pickedWaiting
        ? { exchanged_from: pickedWaiting.id, euros: covered, amount_mad: amountMad }
        : eurAccount
          ? { cmr_invoice_id: selected!.cmr_invoice_id, covered_amount: covered }
          : { cmr_invoice_id: selected!.cmr_invoice_id, amount_mad: amountMad,
              covered_amount: isMad(selected!.currency) ? amountMad : covered };
      await api.post(`/transactions/${txn.id}/match-invoice`, body);
      onDone();
    } catch (err: any) {
      setError(err.response?.data?.message || t('matchInvoice.errorSaving'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{t('matchInvoice.title')}</DialogTitle>
      <DialogContent>
        {txn && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2">{formatDate(txn.date)} — {txn.description}</Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {t('matchInvoice.received')}: {fmt(n(txn.debit))} {unit}
              {unallocated < n(txn.debit) && ` · ${t('matchInvoice.left')}: ${fmt(unallocated)} ${unit}`}
            </Typography>
          </Box>
        )}
        <Alert severity="info" sx={{ mb: 2 }}>{t(eurAccount ? 'matchInvoice.explainEur' : 'matchInvoice.explain')}</Alert>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {loading ? <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress size={24} /></Box> : (
          <>
            <TextField size="small" fullWidth placeholder={t('matchInvoice.search')} value={search}
              onChange={e => setSearch(e.target.value)} sx={{ mb: 1 }} />
            <Box sx={{ maxHeight: 320, overflow: 'auto', mb: 2 }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox" />
                    <TableCell>{t('matchInvoice.invoice')}</TableCell>
                    <TableCell>{t('matchInvoice.customer')}</TableCell>
                    <TableCell align="right">{t('matchInvoice.open')}</TableCell>
                    <TableCell>{t('matchInvoice.why')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {shown.map(s => (
                    <TableRow key={s.cmr_invoice_id} hover selected={selected?.cmr_invoice_id === s.cmr_invoice_id}
                      onClick={() => pick(s)} sx={{ cursor: 'pointer' }}>
                      <TableCell padding="checkbox"><Radio size="small" checked={selected?.cmr_invoice_id === s.cmr_invoice_id} /></TableCell>
                      <TableCell>
                        <b>{s.invoice_number}</b>
                        <Typography variant="caption" display="block" color="text.secondary">
                          {s.trip_reference} {s.invoice_date ? `· ${formatDate(s.invoice_date)}` : ''}
                        </Typography>
                      </TableCell>
                      <TableCell>{s.customer_name}</TableCell>
                      <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>{fmt(n(s.open))} {s.currency}</TableCell>
                      <TableCell>
                        {s.why.map(w => <Chip key={w} size="small" label={w} sx={{ mr: 0.5, mb: 0.5 }} />)}
                      </TableCell>
                    </TableRow>
                  ))}
                  {shown.length === 0 && (
                    <TableRow><TableCell colSpan={5} align="center">{t('matchInvoice.none')}</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </Box>
            {!eurAccount && waiting.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 0.5 }}>{t('matchInvoice.waitingTitle')}</Typography>
                <Table size="small">
                  <TableBody>
                    {waiting.map(w => (
                      <TableRow key={w.id} hover selected={pickedWaiting?.id === w.id} onClick={() => pickWaiting(w)}
                        sx={{ cursor: 'pointer' }}>
                        <TableCell padding="checkbox"><Radio size="small" checked={pickedWaiting?.id === w.id} /></TableCell>
                        <TableCell><b>{w.invoice_number}</b> — {w.customer_name} {w.trip_reference ? `(${w.trip_reference})` : ''}</TableCell>
                        <TableCell>{formatDate(w.received_on)}</TableCell>
                        <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>{fmt(n(w.waiting))} EUR</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Box>
            )}
            {(selected || pickedWaiting) && (
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                {!eurAccount && (
                  <TextField size="small" type="number" label={t('matchInvoice.madAmount')} value={amountMad}
                    onChange={e => { setAmountMad(e.target.value); if (selected && isMad(selected.currency)) setCovered(e.target.value); }}
                    sx={{ width: 180 }} />
                )}
                {(eurAccount || foreign) && (
                  <TextField size="small" type="number"
                    label={`${t(pickedWaiting ? 'matchInvoice.eurExchanged' : 'matchInvoice.covered')} (${pickedWaiting ? 'EUR' : selected!.currency})`}
                    value={covered} onChange={e => setCovered(e.target.value)} sx={{ width: 220 }} />
                )}
                {rate !== null && (
                  <Typography variant="body2">
                    {t('matchInvoice.rate')}: <b>{rate.toFixed(4)}</b> MAD / {pickedWaiting ? 'EUR' : selected!.currency}
                  </Typography>
                )}
                {eurAccount && <Typography variant="body2" color="text.secondary">{t('matchInvoice.heldNote')}</Typography>}
              </Box>
            )}
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onBookToAccount}>{t('billMatching.bookToAccount')}</Button>
        <Box sx={{ flex: 1 }} />
        <Button onClick={onClose}>{t('common.cancel')}</Button>
        <Button variant="contained" onClick={save}
          disabled={(!selected && !pickedWaiting) || saving || (eurAccount ? n(covered) <= 0 : n(amountMad) <= 0)}>
          {saving ? <CircularProgress size={16} /> : t('matchInvoice.match')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MatchInvoiceDialog;
