import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert, Autocomplete, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Divider,
  GlobalStyles, IconButton, MenuItem, Paper, Table, TableBody, TableCell, TableContainer, TableHead,
  TablePagination, TableRow, TextField, Tooltip, Typography,
} from '@mui/material';
import {
  Add as AddIcon, AddCircleOutline as AddLineIcon, CheckCircle as PostIcon, Delete as DeleteIcon,
  Download as DownloadIcon, Edit as EditIcon, Notes as TextLineIcon, Print as PrintIcon,
  RemoveCircleOutline as RemoveLineIcon, RemoveRedEye as ViewIcon, Search as SearchIcon, Send as SendIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { downloadBlob } from '../utils/csvExport';
import { formatDate, formatMoney, formatNumber, parseAmount } from '../utils/format';
import { BASE_CURRENCY, isResultAccount } from '../utils/chart';
import EInvoiceSendButton from '../components/EInvoiceSendButton';

/* ─── Typer ─────────────────────────────────────────────────────────── */

export interface Customer {
  id: string; code: string; name: string; address?: string; tax_id?: string; currency?: string;
  payment_terms_code?: string; vat_zone?: string; is_public?: boolean; ean?: string;
}
export interface Account { id: string; code: string; name: string; is_header?: boolean; is_active?: boolean }
export interface TaxCode { id: string; code: string; name: string; rate: string; type: string; is_active: boolean }

export interface DocLine {
  description: string; quantity: string; unit: string; unit_price: string;
  account_id: string; tax_code_id: string; is_text?: boolean;
}

interface PrintData {
  seller: Record<string, string>;
  buyer: Record<string, string>;
  delivery_date: string;
  payment_terms: string;
  vat_specification: { rate: string; base: string; vat: string; text: string }[];
  vat_dkk: string;
  reverse_charge: boolean;
  legal_notes: string[];
  fi_line: string;
  footer: string;
}

interface Invoice {
  id: string; invoice_number: string; is_draft_number: boolean; customer_id: string; customer_name: string;
  date: string; delivery_date: string | null; due_date: string; payment_terms_code: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  subtotal: string; tax_amount: string; total: string; paid_amount: string; balance_due: string;
  currency: string; exchange_rate: string; customer_reference: string; order_reference: string;
  notes: string; reminders: number; journal_entry_id: string | null;
  lines?: (DocLine & { id: string; amount: string; tax_code_code?: string; tax_code_rate?: string })[];
  print?: PrintData; compliance_errors?: string[];
}

export const PAYMENT_TERMS: { code: string; key: string; label: string }[] = [
  { code: 'net8', key: 'invoices.terms.net8', label: 'Netto 8 dage' },
  { code: 'net14', key: 'invoices.terms.net14', label: 'Netto 14 dage' },
  { code: 'net30', key: 'invoices.terms.net30', label: 'Netto 30 dage' },
  { code: 'lm15', key: 'invoices.terms.lm15', label: 'Løbende måned + 15 dage' },
  { code: 'lm30', key: 'invoices.terms.lm30', label: 'Løbende måned + 30 dage' },
  { code: 'cash', key: 'invoices.terms.cash', label: 'Kontant' },
];

const STATUS_COLOR: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
  draft: 'default', sent: 'info', paid: 'success', overdue: 'error', cancelled: 'warning',
};
const STATUS_LABEL: Record<string, string> = {
  draft: 'Udkast', sent: 'Udstedt', paid: 'Betalt', overdue: 'Forfalden', cancelled: 'Annulleret',
};

export const emptyLine = (taxCodeId = ''): DocLine => ({
  description: '', quantity: '1', unit: 'stk.', unit_price: '', account_id: '', tax_code_id: taxCodeId,
});

const today = () => new Date().toISOString().slice(0, 10);

/* ─── Linjeeditor (bruges også af tilbud) ─────────────────────────── */

interface LinesEditorProps {
  lines: DocLine[];
  onChange: (lines: DocLine[]) => void;
  accounts: Account[];
  taxCodes: TaxCode[];
  currency: string;
}

export const LinesEditor: React.FC<LinesEditorProps> = ({ lines, onChange, accounts, taxCodes, currency }) => {
  const { t } = useTranslation();
  const salesCodes = taxCodes.filter(c => c.is_active && (c.type === 'sales' || c.type === 'both'));
  const revenueAccounts = accounts.filter(a => !a.is_header && a.is_active !== false && isResultAccount(a.code));
  const set = (i: number, patch: Partial<DocLine>) => onChange(lines.map((l, j) => (j === i ? { ...l, ...patch } : l)));
  const amount = (l: DocLine) => (l.is_text ? 0 : parseAmount(l.quantity) * parseAmount(l.unit_price));
  const vatOf = (l: DocLine) => {
    const tc = salesCodes.find(c => c.id === l.tax_code_id);
    return tc ? Math.round(amount(l) * parseFloat(tc.rate)) / 100 : 0;
  };
  const subtotal = lines.reduce((s, l) => s + amount(l), 0);
  const vat = lines.reduce((s, l) => s + vatOf(l), 0);
  const defaultCode = salesCodes.find(c => c.code === 'S01')?.id || '';

  return (
    <Box>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={{ minWidth: 220 }}>{t('invoices.lineDescription', 'Beskrivelse (varens/ydelsens art)')}</TableCell>
            <TableCell width={90}>{t('invoices.quantity', 'Antal')}</TableCell>
            <TableCell width={90}>{t('invoices.unit', 'Enhed')}</TableCell>
            <TableCell width={130}>{t('invoices.unitPriceExVat', 'Pris ekskl. moms')}</TableCell>
            <TableCell width={220}>{t('invoices.vatCode', 'Momskode')}</TableCell>
            <TableCell width={220}>{t('invoices.revenueAccount', 'Omsætningskonto')}</TableCell>
            <TableCell width={120} align="right">{t('invoices.amount', 'Beløb')}</TableCell>
            <TableCell width={40} />
          </TableRow>
        </TableHead>
        <TableBody>
          {lines.map((l, i) => (
            <TableRow key={i}>
              <TableCell colSpan={l.is_text ? 6 : 1}>
                <TextField size="small" fullWidth value={l.description}
                  placeholder={l.is_text ? t('invoices.textLine', 'Tekstlinje') : ''}
                  onChange={e => set(i, { description: e.target.value })} />
              </TableCell>
              {!l.is_text && (
                <>
                  <TableCell><TextField size="small" value={l.quantity} onChange={e => set(i, { quantity: e.target.value })} /></TableCell>
                  <TableCell><TextField size="small" value={l.unit} onChange={e => set(i, { unit: e.target.value })} /></TableCell>
                  <TableCell><TextField size="small" value={l.unit_price} onChange={e => set(i, { unit_price: e.target.value })} /></TableCell>
                  <TableCell>
                    <TextField select size="small" fullWidth value={l.tax_code_id} required
                      error={!l.tax_code_id} onChange={e => set(i, { tax_code_id: e.target.value })}>
                      {salesCodes.map(c => <MenuItem key={c.id} value={c.id}>{c.code} — {c.name}</MenuItem>)}
                    </TextField>
                  </TableCell>
                  <TableCell>
                    <Autocomplete size="small" options={revenueAccounts}
                      value={revenueAccounts.find(a => a.id === l.account_id) || null}
                      getOptionLabel={a => `${a.code} ${a.name}`}
                      onChange={(_, a) => set(i, { account_id: a?.id || '' })}
                      renderInput={p => <TextField {...p} placeholder={t('invoices.accountAuto', 'Automatisk efter momskode')} />} />
                  </TableCell>
                  <TableCell align="right">{formatNumber(amount(l))}</TableCell>
                </>
              )}
              <TableCell>
                <IconButton size="small" onClick={() => onChange(lines.filter((_, j) => j !== i))}><RemoveLineIcon fontSize="small" /></IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
        <Button size="small" startIcon={<AddLineIcon />} onClick={() => onChange([...lines, emptyLine(defaultCode)])}>
          {t('invoices.addLine', 'Tilføj linje')}
        </Button>
        <Button size="small" startIcon={<TextLineIcon />} onClick={() => onChange([...lines, { ...emptyLine(), is_text: true }])}>
          {t('invoices.addTextLine', 'Tilføj tekstlinje')}
        </Button>
        <Box sx={{ flex: 1 }} />
        <Typography variant="body2" sx={{ textAlign: 'right' }}>
          {t('invoices.subtotal', 'Subtotal')}: {formatMoney(subtotal, currency)}<br />
          {t('invoices.vat', 'Moms')}: {formatMoney(vat, currency)}<br />
          <b>{t('invoices.total', 'Total')}: {formatMoney(subtotal + vat, currency)}</b>
        </Typography>
      </Box>
    </Box>
  );
};

export const linesPayload = (lines: DocLine[]) => lines.map(l => (l.is_text
  ? { description: l.description, is_text: true }
  : {
    description: l.description, quantity: String(parseAmount(l.quantity)), unit: l.unit,
    unit_price: String(parseAmount(l.unit_price)), tax_code_id: l.tax_code_id || null, account_id: l.account_id || null,
  }));

export const errorMessage = (e: any, fallback: string) => e?.response?.data?.message || fallback;

/* ─── Udskrift (momsbekendtgørelsens § 58) ─────────────────────────── */

const InvoicePrint: React.FC<{ invoice: Invoice; logo?: string }> = ({ invoice, logo }) => {
  const { t } = useTranslation();
  const p = invoice.print;
  if (!p) return null;
  const cur = invoice.currency || BASE_CURRENCY;
  return (
    <Box className="invoice-print-area" sx={{ p: 3, color: '#000', bgcolor: '#fff' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          {logo && <img src={logo} alt="" style={{ maxHeight: 60, marginBottom: 8 }} />}
          <Typography fontWeight={700}>{p.seller.name}</Typography>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>{p.seller.address}{p.seller.city ? `\n${p.seller.city}` : ''}</Typography>
          <Typography variant="body2">{t('invoices.cvr', 'CVR-nr.')} {p.seller.cvr}</Typography>
          {p.seller.email && <Typography variant="body2">{p.seller.email}</Typography>}
        </Box>
        <Box sx={{ textAlign: 'right' }}>
          <Typography variant="h5" fontWeight={700}>{t('invoices.invoiceTitle', 'Faktura')}</Typography>
          <Typography variant="body2">{t('invoices.number', 'Fakturanr.')}: <b>{invoice.invoice_number}</b></Typography>
          <Typography variant="body2">{t('invoices.date', 'Fakturadato')}: {formatDate(invoice.date)}</Typography>
          <Typography variant="body2">{t('invoices.deliveryDate', 'Leveringsdato')}: {formatDate(p.delivery_date)}</Typography>
          <Typography variant="body2">{t('invoices.dueDate', 'Forfaldsdato')}: {formatDate(invoice.due_date)}</Typography>
        </Box>
      </Box>
      <Box sx={{ mb: 3 }}>
        <Typography fontWeight={700}>{p.buyer.name}</Typography>
        <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>{p.buyer.address}</Typography>
        <Typography variant="body2">{[p.buyer.postal_code, p.buyer.city].filter(Boolean).join(' ')} {p.buyer.country && p.buyer.country !== 'DK' ? p.buyer.country : ''}</Typography>
        {p.buyer.vat_number && <Typography variant="body2">{t('invoices.buyerVat', 'CVR/momsnr.')}: {p.buyer.vat_number}</Typography>}
        {p.buyer.ean && <Typography variant="body2">EAN: {p.buyer.ean}</Typography>}
        {invoice.customer_reference && <Typography variant="body2">{t('invoices.customerReference', 'Jeres reference')}: {invoice.customer_reference}</Typography>}
        {invoice.order_reference && <Typography variant="body2">{t('invoices.orderReference', 'Ordrenummer')}: {invoice.order_reference}</Typography>}
      </Box>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>{t('invoices.lineDescription', 'Beskrivelse (varens/ydelsens art)')}</TableCell>
            <TableCell align="right">{t('invoices.quantity', 'Antal')}</TableCell>
            <TableCell>{t('invoices.unit', 'Enhed')}</TableCell>
            <TableCell align="right">{t('invoices.unitPriceExVat', 'Pris ekskl. moms')}</TableCell>
            <TableCell align="right">{t('invoices.vatRate', 'Moms %')}</TableCell>
            <TableCell align="right">{t('invoices.amount', 'Beløb')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {(invoice.lines || []).map(l => (l.is_text
            ? <TableRow key={l.id}><TableCell colSpan={6}><i>{l.description}</i></TableCell></TableRow>
            : (
              <TableRow key={l.id}>
                <TableCell>{l.description}</TableCell>
                <TableCell align="right">{formatNumber(l.quantity)}</TableCell>
                <TableCell>{l.unit}</TableCell>
                <TableCell align="right">{formatNumber(l.unit_price)}</TableCell>
                <TableCell align="right">{l.tax_code_rate ? formatNumber(l.tax_code_rate) : ''}</TableCell>
                <TableCell align="right">{formatNumber(l.amount)}</TableCell>
              </TableRow>
            )))}
        </TableBody>
      </Table>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
        <Table size="small" sx={{ width: 360 }}>
          <TableBody>
            <TableRow><TableCell>{t('invoices.subtotalExVat', 'I alt ekskl. moms')}</TableCell><TableCell align="right">{formatMoney(invoice.subtotal, cur)}</TableCell></TableRow>
            {p.vat_specification.map(v => (
              <TableRow key={v.rate + v.text}>
                <TableCell>{t('invoices.vatOf', 'Moms {{rate}} % af {{base}}', { rate: formatNumber(v.rate), base: formatNumber(v.base) })}</TableCell>
                <TableCell align="right">{formatMoney(v.vat, cur)}</TableCell>
              </TableRow>
            ))}
            <TableRow><TableCell><b>{t('invoices.totalInclVat', 'I alt inkl. moms')}</b></TableCell><TableCell align="right"><b>{formatMoney(invoice.total, cur)}</b></TableCell></TableRow>
            {cur !== BASE_CURRENCY && (
              <TableRow><TableCell>{t('invoices.vatInDkk', 'Moms i DKK (kurs {{rate}})', { rate: formatNumber(invoice.exchange_rate) })}</TableCell><TableCell align="right">{formatMoney(p.vat_dkk)}</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </Box>
      {p.reverse_charge && (
        <Typography sx={{ mt: 2, fontWeight: 700 }}>{t('invoices.reverseCharge', 'Omvendt betalingspligt')}</Typography>
      )}
      {p.legal_notes.filter(n => !(p.reverse_charge && n === 'Omvendt betalingspligt')).map(n => (
        <Typography key={n} variant="body2">{n}</Typography>
      ))}
      <Divider sx={{ my: 2 }} />
      <Typography variant="body2">{t('invoices.paymentTerms', 'Betalingsbetingelser')}: {p.payment_terms}</Typography>
      {(p.seller.bank_reg_no || p.seller.iban) && (
        <Typography variant="body2">
          {p.seller.bank_reg_no && <>{t('invoices.bankAccount', 'Bankkonto')}: {p.seller.bank_reg_no} {p.seller.bank_account_no} </>}
          {p.seller.iban && <>· IBAN {p.seller.iban} {p.seller.bic && `· BIC ${p.seller.bic}`}</>}
        </Typography>
      )}
      <Typography variant="body2">{t('invoices.payReference', 'Angiv fakturanummer {{n}} ved betaling', { n: invoice.invoice_number })}</Typography>
      {p.fi_line && (
        <Box sx={{ mt: 2, p: 1.5, border: '1px solid #000', fontFamily: 'monospace', fontSize: 16 }}>
          {t('invoices.fiCard', 'FI-kort')}: {p.fi_line}
        </Box>
      )}
      {p.footer && <Typography variant="caption" sx={{ display: 'block', mt: 2, whiteSpace: 'pre-line' }}>{p.footer}</Typography>}
    </Box>
  );
};

/* ─── Side ─────────────────────────────────────────────────────────── */

interface FormState {
  customer_id: string; date: string; delivery_date: string; payment_terms_code: string; due_date: string;
  currency: string; exchange_rate: string; customer_reference: string; order_reference: string; notes: string;
  lines: DocLine[];
}

const Invoices: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [taxCodes, setTaxCodes] = useState<TaxCode[]>([]);
  const [logo, setLogo] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState | null>(null);
  const [formError, setFormError] = useState('');
  const [viewing, setViewing] = useState<Invoice | null>(null);

  const reload = useCallback(() => {
    const qs = new URLSearchParams();
    if (statusFilter === 'overdue') qs.set('overdue', 'true');
    else if (statusFilter) qs.set('status', statusFilter);
    if (search) qs.set('search', search);
    api.get(`/invoices?${qs}`).then(r => setInvoices(r.data.invoices || [])).catch(() => setError(t('invoices.loadError', 'Fakturaerne kunne ikke hentes')));
  }, [statusFilter, search, t]);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    api.get('/customers?is_active=true').then(r => setCustomers(r.data.customers || []));
    api.get('/accounts?is_active=true').then(r => setAccounts(r.data.data?.accounts || []));
    api.get('/tax-codes').then(r => setTaxCodes(r.data.data?.tax_codes || []));
    api.get('/settings').then(r => setLogo(r.data.data?.settings?.logo2 || '')).catch(() => undefined);
  }, []);

  const defaultCode = useMemo(() => taxCodes.find(c => c.code === 'S01')?.id || '', [taxCodes]);

  const openNew = () => {
    setEditingId(null);
    setForm({
      customer_id: '', date: today(), delivery_date: '', payment_terms_code: 'net14', due_date: '',
      currency: BASE_CURRENCY, exchange_rate: '1', customer_reference: '', order_reference: '', notes: '',
      lines: [emptyLine(defaultCode)],
    });
    setFormError('');
    setFormOpen(true);
  };

  const openEdit = async (inv: Invoice) => {
    const r = await api.get(`/invoices/${inv.id}`);
    const full: Invoice = r.data.invoice;
    setEditingId(full.id);
    setForm({
      customer_id: full.customer_id, date: full.date, delivery_date: full.delivery_date || '',
      payment_terms_code: full.payment_terms_code, due_date: full.due_date, currency: full.currency,
      exchange_rate: full.exchange_rate, customer_reference: full.customer_reference,
      order_reference: full.order_reference, notes: full.notes,
      lines: (full.lines || []).map(l => ({
        description: l.description, quantity: l.quantity, unit: l.unit || 'stk.', unit_price: l.unit_price,
        account_id: l.account_id || '', tax_code_id: l.tax_code_id || '', is_text: l.is_text,
      })),
    });
    setFormError('');
    setFormOpen(true);
  };

  const pickCustomer = (c: Customer | null) => {
    if (!form) return;
    setForm({ ...form, customer_id: c?.id || '', payment_terms_code: c?.payment_terms_code || form.payment_terms_code,
      currency: c?.currency || form.currency });
  };

  const save = async () => {
    if (!form) return;
    if (form.lines.some(l => !l.is_text && !l.tax_code_id)) {
      setFormError(t('invoices.vatCodeRequired', 'Hver linje skal have en momskode (også momsfrie linjer)'));
      return;
    }
    const payload: any = {
      customer_id: form.customer_id, date: form.date, delivery_date: form.delivery_date || null,
      payment_terms_code: form.payment_terms_code, currency: form.currency,
      exchange_rate: form.currency === BASE_CURRENCY ? '1' : String(parseAmount(form.exchange_rate)),
      customer_reference: form.customer_reference, order_reference: form.order_reference, notes: form.notes,
      lines: linesPayload(form.lines),
    };
    if (form.due_date && editingId) payload.due_date = form.due_date;
    try {
      if (editingId) await api.put(`/invoices/${editingId}`, payload);
      else await api.post('/invoices', payload);
      setFormOpen(false);
      reload();
    } catch (e) {
      setFormError(errorMessage(e, t('invoices.saveError', 'Fakturaen kunne ikke gemmes')));
    }
  };

  const view = async (inv: Invoice) => {
    const r = await api.get(`/invoices/${inv.id}`);
    setViewing(r.data.invoice);
  };

  const issue = async (inv: Invoice) => {
    if (!window.confirm(t('invoices.confirmIssue', 'Udsted og bogfør fakturaen? Den får et fortløbende fakturanummer og kan derefter ikke ændres.'))) return;
    try {
      const r = await api.post(`/invoices/${inv.id}/post`);
      setInfo(r.data.message);
      setViewing(r.data.invoice);
      reload();
    } catch (e) {
      setError(errorMessage(e, t('invoices.issueError', 'Fakturaen kunne ikke udstedes')));
    }
  };

  const markSent = async (inv: Invoice) => {
    try { await api.post(`/invoices/${inv.id}/send`); reload(); } catch (e) {
      setError(errorMessage(e, t('invoices.sendError', 'Fakturaen kunne ikke markeres som sendt')));
    }
  };

  const remove = async (inv: Invoice) => {
    if (!window.confirm(t('invoices.confirmDelete', 'Slet udkastet?'))) return;
    try { await api.delete(`/invoices/${inv.id}`); reload(); } catch (e) {
      setError(errorMessage(e, t('invoices.deleteError', 'Udkastet kunne ikke slettes')));
    }
  };

  const exportCsv = async () => {
    const res = await api.get('/invoices/export', { responseType: 'blob' });
    downloadBlob(res.data, 'fakturaer.csv');
  };

  const issued = (inv: Invoice) => !!inv.journal_entry_id;
  const rows = invoices.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  const customer = form ? customers.find(c => c.id === form.customer_id) || null : null;

  return (
    <Box>
      <GlobalStyles styles={{
        '@media print': {
          'body *': { visibility: 'hidden' },
          '.invoice-print-area, .invoice-print-area *': { visibility: 'visible' },
          '.invoice-print-area': { position: 'absolute', left: 0, top: 0, width: '100%' },
        },
      }} />
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1, flexWrap: 'wrap' }}>
        <Typography variant="h5" sx={{ flex: 1 }}>{t('invoices.title', 'Fakturaer')}</Typography>
        <Button startIcon={<DownloadIcon />} onClick={exportCsv}>{t('invoices.export', 'Eksportér')}</Button>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openNew}>{t('invoices.new', 'Ny faktura')}</Button>
      </Box>
      {error && <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>{error}</Alert>}
      {info && <Alert severity="success" onClose={() => setInfo('')} sx={{ mb: 2 }}>{info}</Alert>}
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <TextField size="small" placeholder={t('invoices.search', 'Søg nummer, kunde …')} value={search}
          onChange={e => setSearch(e.target.value)} InputProps={{ startAdornment: <SearchIcon fontSize="small" /> }} />
        <TextField select size="small" label={t('invoices.status', 'Status')} value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)} sx={{ minWidth: 160 }}>
          <MenuItem value="">{t('invoices.all', 'Alle')}</MenuItem>
          {Object.keys(STATUS_LABEL).map(s => <MenuItem key={s} value={s}>{t(`invoices.statusLabel.${s}`, STATUS_LABEL[s])}</MenuItem>)}
        </TextField>
      </Box>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>{t('invoices.number', 'Fakturanr.')}</TableCell>
              <TableCell>{t('invoices.customer', 'Kunde')}</TableCell>
              <TableCell>{t('invoices.date', 'Fakturadato')}</TableCell>
              <TableCell>{t('invoices.dueDate', 'Forfaldsdato')}</TableCell>
              <TableCell align="right">{t('invoices.total', 'Total')}</TableCell>
              <TableCell align="right">{t('invoices.balanceDue', 'Restbeløb')}</TableCell>
              <TableCell>{t('invoices.status', 'Status')}</TableCell>
              <TableCell align="right">{t('invoices.actions', 'Handlinger')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map(inv => (
              <TableRow key={inv.id} hover>
                <TableCell>{inv.is_draft_number ? <i>{t('invoices.draftNumber', 'Udkast')} ({inv.invoice_number})</i> : inv.invoice_number}</TableCell>
                <TableCell>{inv.customer_name}</TableCell>
                <TableCell>{formatDate(inv.date)}</TableCell>
                <TableCell>{formatDate(inv.due_date)}</TableCell>
                <TableCell align="right">{formatMoney(inv.total, inv.currency)}</TableCell>
                <TableCell align="right">{formatMoney(inv.balance_due, inv.currency)}</TableCell>
                <TableCell>
                  <Chip size="small" color={STATUS_COLOR[inv.status]} label={t(`invoices.statusLabel.${inv.status}`, STATUS_LABEL[inv.status])} />
                  {inv.reminders > 0 && <Chip size="small" sx={{ ml: 0.5 }} label={t('invoices.reminderCount', '{{n}} rykker', { n: inv.reminders })} />}
                </TableCell>
                <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                  <Tooltip title={t('invoices.view', 'Vis')}><IconButton size="small" onClick={() => view(inv)}><ViewIcon fontSize="small" /></IconButton></Tooltip>
                  {!issued(inv) && (
                    <>
                      <Tooltip title={t('invoices.edit', 'Rediger')}><IconButton size="small" onClick={() => openEdit(inv)}><EditIcon fontSize="small" /></IconButton></Tooltip>
                      <Tooltip title={t('invoices.issue', 'Udsted og bogfør')}><IconButton size="small" color="primary" onClick={() => issue(inv)}><PostIcon fontSize="small" /></IconButton></Tooltip>
                      <Tooltip title={t('invoices.delete', 'Slet')}><IconButton size="small" onClick={() => remove(inv)}><DeleteIcon fontSize="small" /></IconButton></Tooltip>
                    </>
                  )}
                  {issued(inv) && (
                    <EInvoiceSendButton documentId={inv.id} status={inv.status} onSent={() => reload()} />
                  )}
                </TableCell>
              </TableRow>
            ))}
            {rows.length === 0 && <TableRow><TableCell colSpan={8} align="center">{t('invoices.none', 'Ingen fakturaer')}</TableCell></TableRow>}
          </TableBody>
        </Table>
        <TablePagination component="div" count={invoices.length} page={page} rowsPerPage={rowsPerPage}
          onPageChange={(_, p) => setPage(p)} onRowsPerPageChange={e => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
          labelRowsPerPage={t('invoices.rowsPerPage', 'Rækker pr. side')} />
      </TableContainer>

      {/* Opret/rediger udkast */}
      <Dialog open={formOpen} onClose={() => setFormOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>{editingId ? t('invoices.editDraft', 'Rediger fakturaudkast') : t('invoices.new', 'Ny faktura')}</DialogTitle>
        <DialogContent>
          {form && (
            <Box sx={{ display: 'grid', gap: 2, pt: 1 }}>
              {formError && <Alert severity="error">{formError}</Alert>}
              <Alert severity="info">{t('invoices.draftInfo', 'Udkastet får sit fortløbende fakturanummer, når det udstedes og bogføres.')}</Alert>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 2 }}>
                <Autocomplete options={customers} value={customer} getOptionLabel={c => `${c.code} ${c.name}`}
                  onChange={(_, c) => pickCustomer(c)} sx={{ gridColumn: { md: 'span 2' } }}
                  renderInput={p => <TextField {...p} required label={t('invoices.customer', 'Kunde')} />} />
                <TextField type="date" label={t('invoices.date', 'Fakturadato')} InputLabelProps={{ shrink: true }}
                  value={form.date} onChange={e => setForm({ ...form, date: e.target.value })} />
                <TextField type="date" label={t('invoices.deliveryDate', 'Leveringsdato')} InputLabelProps={{ shrink: true }}
                  helperText={t('invoices.deliveryDateHelp', 'Tom = samme som fakturadatoen')}
                  value={form.delivery_date} onChange={e => setForm({ ...form, delivery_date: e.target.value })} />
                <TextField select label={t('invoices.paymentTerms', 'Betalingsbetingelser')} value={form.payment_terms_code}
                  onChange={e => setForm({ ...form, payment_terms_code: e.target.value, due_date: '' })}>
                  {PAYMENT_TERMS.map(p => <MenuItem key={p.code} value={p.code}>{t(p.key, p.label)}</MenuItem>)}
                </TextField>
                <TextField label={t('invoices.currency', 'Valuta')} value={form.currency}
                  onChange={e => setForm({ ...form, currency: e.target.value.toUpperCase().slice(0, 3) })} />
                {form.currency !== BASE_CURRENCY && (
                  <TextField label={t('invoices.exchangeRateDkk', 'Kurs (DKK pr. 1 {{cur}})', { cur: form.currency })}
                    value={form.exchange_rate} onChange={e => setForm({ ...form, exchange_rate: e.target.value })} />
                )}
                <TextField label={t('invoices.customerReference', 'Jeres reference')} value={form.customer_reference}
                  onChange={e => setForm({ ...form, customer_reference: e.target.value })} />
                <TextField label={t('invoices.orderReference', 'Ordrenummer')} value={form.order_reference}
                  onChange={e => setForm({ ...form, order_reference: e.target.value })} />
              </Box>
              {customer?.is_public && !customer.ean && (
                <Alert severity="warning">{t('invoices.publicNeedsEan', 'Kunden er offentlig og mangler EAN-nummer. Fakturaen kan ikke udstedes uden.')}</Alert>
              )}
              {customer?.vat_zone === 'eu' && (
                <Alert severity="info">{t('invoices.euHint', 'EU-kunde: brug S21/S22 (varer) eller S23 (ydelser) for B2B-salg uden moms. Kundens momsnummer skal være udfyldt.')}</Alert>
              )}
              <LinesEditor lines={form.lines} onChange={lines => setForm({ ...form, lines })} accounts={accounts}
                taxCodes={taxCodes} currency={form.currency} />
              <TextField label={t('invoices.notes', 'Bemærkning')} multiline minRows={2} value={form.notes}
                onChange={e => setForm({ ...form, notes: e.target.value })} />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFormOpen(false)}>{t('common.cancel', 'Annuller')}</Button>
          <Button variant="contained" onClick={save} disabled={!form?.customer_id}>{t('invoices.saveDraft', 'Gem udkast')}</Button>
        </DialogActions>
      </Dialog>

      {/* Visning og udskrift */}
      <Dialog open={!!viewing} onClose={() => setViewing(null)} maxWidth="md" fullWidth>
        <DialogContent>
          {viewing && (
            <>
              {viewing.compliance_errors && viewing.compliance_errors.length > 0 && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <b>{t('invoices.complianceTitle', 'Det mangler, før fakturaen kan udstedes (momsbekendtgørelsens § 58):')}</b>
                  <ul style={{ margin: 0 }}>{viewing.compliance_errors.map(e => <li key={e}>{e}</li>)}</ul>
                </Alert>
              )}
              {issued(viewing) && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  {t('invoices.issuedLocked', 'Fakturaen er udstedt og kan ikke ændres. Ret den med en kreditnota.')}
                  <Button size="small" sx={{ ml: 1 }} onClick={() => navigate('/credit-notes')}>{t('invoices.makeCreditNote', 'Lav kreditnota')}</Button>
                </Alert>
              )}
              <InvoicePrint invoice={viewing} logo={logo} />
            </>
          )}
        </DialogContent>
        <DialogActions>
          {viewing && !issued(viewing) && (
            <Button variant="contained" startIcon={<PostIcon />} onClick={() => issue(viewing)}>{t('invoices.issue', 'Udsted og bogfør')}</Button>
          )}
          {viewing && issued(viewing) && (
            <>
              <EInvoiceSendButton documentId={viewing.id} status={viewing.status} onSent={() => reload()} />
              <Button startIcon={<SendIcon />} onClick={() => markSent(viewing)}>{t('invoices.markSent', 'Markér som sendt')}</Button>
            </>
          )}
          <Button startIcon={<PrintIcon />} onClick={() => window.print()}>{t('invoices.print', 'Udskriv')}</Button>
          <Button onClick={() => setViewing(null)}>{t('common.close', 'Luk')}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Invoices;
