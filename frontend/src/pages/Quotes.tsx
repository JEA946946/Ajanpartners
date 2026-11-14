import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Autocomplete, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, MenuItem,
  Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Tooltip, Typography,
} from '@mui/material';
import {
  Add as AddIcon, Delete as DeleteIcon, Edit as EditIcon, ReceiptLong as InvoiceIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { formatDate, formatMoney } from '../utils/format';
import { BASE_CURRENCY } from '../utils/chart';
import {
  Account, Customer, DocLine, LinesEditor, TaxCode, emptyLine, errorMessage, linesPayload,
} from './Invoices';

interface Quote {
  id: string; quote_number: string; customer_id: string; customer_name: string; date: string;
  valid_until: string | null; status: string; currency: string; subtotal: string; tax_amount: string;
  total: string; notes: string; invoice_id: string | null;
  lines?: (DocLine & { id: string })[];
}

const STATUS: Record<string, { label: string; color: 'default' | 'info' | 'success' | 'error' | 'warning' }> = {
  draft: { label: 'Kladde', color: 'default' },
  sent: { label: 'Sendt', color: 'info' },
  accepted: { label: 'Accepteret', color: 'success' },
  rejected: { label: 'Afvist', color: 'error' },
  invoiced: { label: 'Faktureret', color: 'warning' },
};

interface FormState { customer_id: string; date: string; valid_until: string; currency: string; notes: string; lines: DocLine[] }

const today = () => new Date().toISOString().slice(0, 10);

const Quotes: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [taxCodes, setTaxCodes] = useState<TaxCode[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [error, setError] = useState('');
  const [formError, setFormError] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState | null>(null);

  const reload = useCallback(() => {
    api.get(`/quotes${statusFilter ? `?status=${statusFilter}` : ''}`)
      .then(r => setQuotes(r.data.quotes || []))
      .catch(e => setError(errorMessage(e, t('quotes.loadError', 'Tilbuddene kunne ikke hentes'))));
  }, [statusFilter, t]);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    api.get('/customers?is_active=true').then(r => setCustomers(r.data.customers || []));
    api.get('/accounts?is_active=true').then(r => setAccounts(r.data.data?.accounts || []));
    api.get('/tax-codes').then(r => setTaxCodes(r.data.data?.tax_codes || []));
  }, []);

  const openNew = () => {
    setEditingId(null);
    setFormError('');
    setForm({ customer_id: '', date: today(), valid_until: '', currency: BASE_CURRENCY, notes: '',
      lines: [emptyLine(taxCodes.find(c => c.code === 'S01')?.id || '')] });
  };

  const openEdit = async (q: Quote) => {
    const r = await api.get(`/quotes/${q.id}`);
    const full: Quote = r.data.quote;
    setEditingId(full.id);
    setFormError('');
    setForm({
      customer_id: full.customer_id, date: full.date, valid_until: full.valid_until || '', currency: full.currency,
      notes: full.notes,
      lines: (full.lines || []).map(l => ({
        description: l.description, quantity: l.quantity, unit: l.unit || 'stk.', unit_price: l.unit_price,
        account_id: l.account_id || '', tax_code_id: l.tax_code_id || '', is_text: l.is_text,
      })),
    });
  };

  const save = async () => {
    if (!form) return;
    const payload = { customer_id: form.customer_id, date: form.date, valid_until: form.valid_until || null,
      currency: form.currency, notes: form.notes, lines: linesPayload(form.lines) };
    try {
      if (editingId) await api.put(`/quotes/${editingId}`, payload);
      else await api.post('/quotes', payload);
      setForm(null);
      reload();
    } catch (e) {
      setFormError(errorMessage(e, t('quotes.saveError', 'Tilbuddet kunne ikke gemmes')));
    }
  };

  const setStatus = async (q: Quote, status: string) => {
    try { await api.post(`/quotes/${q.id}/status`, { status }); reload(); } catch (e) {
      setError(errorMessage(e, t('quotes.statusError', 'Status kunne ikke ændres')));
    }
  };

  const toInvoice = async (q: Quote) => {
    if (!window.confirm(t('quotes.confirmInvoice', 'Lav et fakturaudkast ud fra tilbuddet?'))) return;
    try {
      await api.post(`/quotes/${q.id}/invoice`, { date: today() });
      navigate('/invoices');
    } catch (e) {
      setError(errorMessage(e, t('quotes.invoiceError', 'Fakturaen kunne ikke oprettes')));
    }
  };

  const remove = async (q: Quote) => {
    if (!window.confirm(t('quotes.confirmDelete', 'Slet tilbuddet?'))) return;
    try { await api.delete(`/quotes/${q.id}`); reload(); } catch (e) {
      setError(errorMessage(e, t('quotes.deleteError', 'Tilbuddet kunne ikke slettes')));
    }
  };

  const customer = form ? customers.find(c => c.id === form.customer_id) || null : null;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
        <Typography variant="h5" sx={{ flex: 1 }}>{t('quotes.title', 'Tilbud')}</Typography>
        <TextField select size="small" label={t('quotes.status', 'Status')} value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)} sx={{ minWidth: 160 }}>
          <MenuItem value="">{t('quotes.all', 'Alle')}</MenuItem>
          {Object.entries(STATUS).map(([k, v]) => <MenuItem key={k} value={k}>{t(`quotes.statusLabel.${k}`, v.label)}</MenuItem>)}
        </TextField>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openNew}>{t('quotes.new', 'Nyt tilbud')}</Button>
      </Box>
      {error && <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>{error}</Alert>}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>{t('quotes.number', 'Tilbudsnr.')}</TableCell>
              <TableCell>{t('quotes.customer', 'Kunde')}</TableCell>
              <TableCell>{t('quotes.date', 'Dato')}</TableCell>
              <TableCell>{t('quotes.validUntil', 'Gyldigt til')}</TableCell>
              <TableCell align="right">{t('quotes.total', 'Total inkl. moms')}</TableCell>
              <TableCell>{t('quotes.status', 'Status')}</TableCell>
              <TableCell align="right">{t('quotes.actions', 'Handlinger')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {quotes.map(q => (
              <TableRow key={q.id} hover>
                <TableCell>{q.quote_number}</TableCell>
                <TableCell>{q.customer_name}</TableCell>
                <TableCell>{formatDate(q.date)}</TableCell>
                <TableCell>{formatDate(q.valid_until)}</TableCell>
                <TableCell align="right">{formatMoney(q.total, q.currency)}</TableCell>
                <TableCell>
                  {q.status === 'invoiced'
                    ? <Chip size="small" color={STATUS.invoiced.color} label={t('quotes.statusLabel.invoiced', STATUS.invoiced.label)} />
                    : (
                      <TextField select size="small" variant="standard" value={q.status} onChange={e => setStatus(q, e.target.value)}>
                        {['draft', 'sent', 'accepted', 'rejected'].map(k => (
                          <MenuItem key={k} value={k}>{t(`quotes.statusLabel.${k}`, STATUS[k].label)}</MenuItem>
                        ))}
                      </TextField>
                    )}
                </TableCell>
                <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                  {q.status !== 'invoiced' && (
                    <>
                      <Tooltip title={t('quotes.edit', 'Rediger')}><IconButton size="small" onClick={() => openEdit(q)}><EditIcon fontSize="small" /></IconButton></Tooltip>
                      <Tooltip title={t('quotes.toInvoice', 'Lav faktura')}><IconButton size="small" color="primary" onClick={() => toInvoice(q)}><InvoiceIcon fontSize="small" /></IconButton></Tooltip>
                      <Tooltip title={t('quotes.delete', 'Slet')}><IconButton size="small" onClick={() => remove(q)}><DeleteIcon fontSize="small" /></IconButton></Tooltip>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {quotes.length === 0 && <TableRow><TableCell colSpan={7} align="center">{t('quotes.none', 'Ingen tilbud')}</TableCell></TableRow>}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={!!form} onClose={() => setForm(null)} maxWidth="lg" fullWidth>
        <DialogTitle>{editingId ? t('quotes.editTitle', 'Rediger tilbud') : t('quotes.new', 'Nyt tilbud')}</DialogTitle>
        <DialogContent>
          {form && (
            <Box sx={{ display: 'grid', gap: 2, pt: 1 }}>
              {formError && <Alert severity="error">{formError}</Alert>}
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '2fr 1fr 1fr 1fr' }, gap: 2 }}>
                <Autocomplete options={customers} value={customer} getOptionLabel={c => `${c.code} ${c.name}`}
                  onChange={(_, c) => setForm({ ...form, customer_id: c?.id || '', currency: c?.currency || form.currency })}
                  renderInput={p => <TextField {...p} required label={t('quotes.customer', 'Kunde')} />} />
                <TextField type="date" label={t('quotes.date', 'Dato')} InputLabelProps={{ shrink: true }}
                  value={form.date} onChange={e => setForm({ ...form, date: e.target.value })} />
                <TextField type="date" label={t('quotes.validUntil', 'Gyldigt til')} InputLabelProps={{ shrink: true }}
                  helperText={t('quotes.validHelp', 'Tom = 30 dage')}
                  value={form.valid_until} onChange={e => setForm({ ...form, valid_until: e.target.value })} />
                <TextField label={t('quotes.currency', 'Valuta')} value={form.currency}
                  onChange={e => setForm({ ...form, currency: e.target.value.toUpperCase().slice(0, 3) })} />
              </Box>
              <LinesEditor lines={form.lines} onChange={lines => setForm({ ...form, lines })} accounts={accounts}
                taxCodes={taxCodes} currency={form.currency} />
              <TextField label={t('quotes.notes', 'Bemærkning')} multiline minRows={2} value={form.notes}
                onChange={e => setForm({ ...form, notes: e.target.value })} />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setForm(null)}>{t('common.cancel', 'Annuller')}</Button>
          <Button variant="contained" onClick={save} disabled={!form?.customer_id}>{t('quotes.save', 'Gem tilbud')}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Quotes;
