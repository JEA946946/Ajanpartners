import React, { useEffect, useState } from 'react';
import { formatDate } from '../utils/dateFormat';
import {
  Box, Typography, Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Chip, FormControlLabel, Switch, InputAdornment,
  Alert, MenuItem,
} from '@mui/material';
import {
  Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon,
  Search as SearchIcon, Receipt as StatementIcon,
  Upload as UploadIcon, Download as DownloadIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { exportToCSV } from '../utils/csvExport';
import ImportDialog from '../components/ImportDialog';
import { PAYMENT_TERMS } from './Invoices';
import { formatMoney } from '../utils/format';

interface Customer {
  id: string;
  code: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  postal_code: string;
  city: string;
  country: string;
  tax_id: string;
  vat_zone: string;
  is_business: boolean;
  is_public: boolean;
  ean: string;
  currency: string;
  payment_terms: number;
  payment_terms_code: string;
  credit_limit: string;
  notes: string;
  is_active: boolean;
}

interface StatementLine {
  id: string;
  date: string;
  type: string;
  reference: string;
  amount: string;
  balance: string;
}


const CURRENCY_OPTIONS = ['DKK', 'EUR', 'SEK', 'NOK', 'USD', 'GBP'];
const VAT_ZONES = [
  { value: 'dk', key: 'customers.vatZone.dk', label: 'Danmark' },
  { value: 'eu', key: 'customers.vatZone.eu', label: 'EU (uden for Danmark)' },
  { value: 'abroad', key: 'customers.vatZone.abroad', label: 'Uden for EU' },
];

const EMPTY_FORM = {
  code: '',
  name: '',
  email: '',
  phone: '',
  address: '',
  postal_code: '',
  city: '',
  country: 'DK',
  tax_id: '',
  vat_zone: 'dk',
  is_business: true,
  is_public: false,
  ean: '',
  currency: 'DKK',
  payment_terms_code: 'net14',
  credit_limit: '0',
  notes: '',
};

const Customers: React.FC = () => {
  const { t } = useTranslation();

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState('');
  const [showInactive, setShowInactive] = useState(false);

  // Add/Edit dialog
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });

  // Statement dialog
  const [statementOpen, setStatementOpen] = useState(false);
  const [statementCustomer, setStatementCustomer] = useState<Customer | null>(null);
  const [statementLines, setStatementLines] = useState<StatementLine[]>([]);

  const fetchCustomers = () => {
    const params = new URLSearchParams();
    if (!showInactive) params.set('is_active', 'true');
    if (search.trim()) params.set('search', search.trim());
    const qs = params.toString() ? `?${params.toString()}` : '';
    api.get(`/customers${qs}`).then(res => {
      if (res.data.success) setCustomers(res.data.customers);
    });
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps -- refetch only when 'show inactive' flips; the search box applies on Enter
  useEffect(() => { fetchCustomers(); }, [showInactive]);

  const handleSearch = () => {
    fetchCustomers();
  };

  const handleOpen = (customer?: Customer) => {
    if (customer) {
      setEditing(customer);
      setForm({
        code: customer.code,
        name: customer.name,
        email: customer.email || '',
        phone: customer.phone || '',
        address: customer.address || '',
        postal_code: customer.postal_code || '',
        city: customer.city || '',
        country: customer.country || 'DK',
        tax_id: customer.tax_id || '',
        vat_zone: customer.vat_zone || 'dk',
        is_business: customer.is_business ?? true,
        is_public: !!customer.is_public,
        ean: customer.ean || '',
        currency: customer.currency || 'DKK',
        payment_terms_code: customer.payment_terms_code || 'net14',
        credit_limit: customer.credit_limit || '0',
        notes: customer.notes || '',
      });
    } else {
      setEditing(null);
      setForm({ ...EMPTY_FORM });
    }
    setFormError('');
    setDialogOpen(true);
  };

  const [formError, setFormError] = useState('');

  const handleSave = async () => {
    if (form.is_public && !/^\d{13}$/.test(form.ean)) {
      setFormError(t('customers.eanRequired', 'En offentlig kunde skal have et EAN-/GLN-nummer på 13 cifre'));
      return;
    }
    if (form.ean && !/^\d{13}$/.test(form.ean)) {
      setFormError(t('customers.eanInvalid', 'EAN-/GLN-nummeret skal være 13 cifre'));
      return;
    }
    const payload = {
      ...form,
      credit_limit: parseFloat(form.credit_limit) || 0,
    };
    try {
      if (editing) {
        await api.put(`/customers/${editing.id}`, payload);
      } else {
        await api.post('/customers', payload);
      }
      setDialogOpen(false);
      fetchCustomers();
    } catch (err: any) {
      setFormError(err.response?.data?.message || t('customers.errorSaving'));
    }
  };

  const handleDelete = async (customer: Customer) => {
    if (!confirm(t('customers.deactivateConfirm', { name: customer.name }))) return;
    try {
      await api.delete(`/customers/${customer.id}`);
      fetchCustomers();
    } catch (err: any) {
      alert(err.response?.data?.message || t('customers.errorDeleting'));
    }
  };

  const openStatement = (customer: Customer) => {
    setStatementCustomer(customer);
    setStatementOpen(true);
    api.get(`/customers/${customer.id}/statement`).then(res => {
      if (res.data.success) {
        // Kontoudtog: fakturaer (debet) og kreditnotaer (kredit) med løbende saldo.
        const items = [
          ...(res.data.invoices || []).filter((i: any) => !i.is_draft_number).map((i: any) => ({
            id: i.id, date: i.date, type: 'invoice', reference: i.invoice_number, amount: parseFloat(i.total) })),
          ...(res.data.credit_notes || []).filter((c: any) => c.status === 'applied').map((c: any) => ({
            id: c.id, date: c.date, type: 'credit_note', reference: c.credit_note_number, amount: -parseFloat(c.total) })),
        ].sort((a, b) => a.date.localeCompare(b.date));
        let bal = 0;
        setStatementLines(items.map(x => { bal += x.amount; return { ...x, amount: String(x.amount), balance: String(bal) }; }));
      }
    }).catch(() => {
      setStatementLines([]);
    });
  };

  const closeStatement = () => {
    setStatementOpen(false);
    setStatementCustomer(null);
    setStatementLines([]);
  };


  // Import/Export
  const [importOpen, setImportOpen] = useState(false);

  const handleExportCustomers = () => {
    const headers = ['code', 'name', 'email', 'phone', 'address', 'postal_code', 'city', 'country', 'tax_id', 'ean', 'currency', 'payment_terms_code', 'credit_limit', 'notes'];
    const rows = customers.map(c => [
      c.code, c.name, c.email, c.phone, c.address, c.postal_code, c.city, c.country, c.tax_id, c.ean,
      c.currency, c.payment_terms_code, c.credit_limit, c.notes,
    ]);
    exportToCSV('customers.csv', headers, rows);
  };

  const filteredCustomers = search.trim()
    ? customers.filter(c =>
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.code.toLowerCase().includes(search.toLowerCase())
      )
    : customers;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>{t('customers.title')}</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<DownloadIcon />} onClick={handleExportCustomers} size="small">
            {t('importExport.export')}
          </Button>
          <Button variant="outlined" startIcon={<UploadIcon />} onClick={() => setImportOpen(true)} size="small">
            {t('importExport.import')}
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpen()} sx={{ bgcolor: '#2e7d32' }}>
            {t('customers.addCustomer')}
          </Button>
        </Box>
      </Box>

      {/* Filter Bar */}
      <Paper sx={{ p: 1.5, mb: 2, display: 'flex', gap: 1.5, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField
          label={t('common.search')}
          value={search}
          size="small"
          onChange={e => setSearch(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          sx={{ width: 260 }}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton size="small" onClick={handleSearch} sx={{ p: 0.3 }}>
                  <SearchIcon sx={{ fontSize: 18 }} />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        <FormControlLabel
          control={
            <Switch
              checked={showInactive}
              onChange={e => setShowInactive(e.target.checked)}
              size="small"
            />
          }
          label={<Typography variant="body2">{t('common.showInactive')}</Typography>}
        />
      </Paper>

      {/* Customer Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.code')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.name')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.email')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.phone')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.currency')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('customers.paymentTerms')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.status')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredCustomers.map(customer => (
              <TableRow key={customer.id} hover sx={{ opacity: customer.is_active ? 1 : 0.5 }}>
                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 500 }}>
                    {customer.code}
                  </Typography>
                </TableCell>
                <TableCell>{customer.name}</TableCell>
                <TableCell>{customer.email}</TableCell>
                <TableCell>{customer.phone}</TableCell>
                <TableCell>{customer.currency}</TableCell>
                <TableCell>{t(PAYMENT_TERMS.find(p => p.code === customer.payment_terms_code)?.key || '', PAYMENT_TERMS.find(p => p.code === customer.payment_terms_code)?.label || '')}</TableCell>
                <TableCell>
                  <Chip
                    label={customer.is_active ? t('common.active') : t('common.inactive')}
                    size="small"
                    sx={{
                      bgcolor: customer.is_active ? '#2e7d32' : '#9e9e9e',
                      color: '#fff',
                      height: 20,
                      fontSize: '11px',
                    }}
                  />
                </TableCell>
                <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                  <IconButton size="small" onClick={() => handleOpen(customer)} title={t('common.edit')}>
                    <EditIcon sx={{ fontSize: 16 }} />
                  </IconButton>
                  <IconButton size="small" onClick={() => openStatement(customer)} title={t('customers.statement')}>
                    <StatementIcon sx={{ fontSize: 16 }} />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleDelete(customer)} color="error" title={t('common.delete')}>
                    <DeleteIcon sx={{ fontSize: 16 }} />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {filteredCustomers.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                  <Typography variant="body2" color="text.secondary">{t('customers.noCustomers')}</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editing ? t('customers.editCustomer') : t('customers.addCustomer')}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label={t('common.code')} value={form.code} size="small" sx={{ width: 140 }}
                onChange={e => setForm({ ...form, code: e.target.value })}
              />
              <TextField
                label={t('common.name')} value={form.name} size="small" fullWidth
                onChange={e => setForm({ ...form, name: e.target.value })}
              />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label={t('common.email')} value={form.email} size="small" fullWidth type="email"
                onChange={e => setForm({ ...form, email: e.target.value })}
              />
              <TextField
                label={t('common.phone')} value={form.phone} size="small" sx={{ width: 180 }}
                onChange={e => setForm({ ...form, phone: e.target.value })}
              />
            </Box>
            {formError && <Alert severity="error">{formError}</Alert>}
            <TextField
              label={t('common.address')} value={form.address} size="small" fullWidth multiline rows={2}
              onChange={e => setForm({ ...form, address: e.target.value })}
            />
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField label={t('customers.postalCode', 'Postnr.')} value={form.postal_code} size="small" sx={{ width: 120 }}
                onChange={e => setForm({ ...form, postal_code: e.target.value })} />
              <TextField label={t('customers.city', 'By')} value={form.city} size="small" fullWidth
                onChange={e => setForm({ ...form, city: e.target.value })} />
              <TextField label={t('customers.country', 'Land (ISO)')} value={form.country} size="small" sx={{ width: 110 }}
                onChange={e => setForm({ ...form, country: e.target.value.toUpperCase().slice(0, 2) })} />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField select label={t('customers.vatZoneLabel', 'Momszone')} value={form.vat_zone} size="small" sx={{ width: 220 }}
                onChange={e => setForm({ ...form, vat_zone: e.target.value })}>
                {VAT_ZONES.map(z => <MenuItem key={z.value} value={z.value}>{t(z.key, z.label)}</MenuItem>)}
              </TextField>
              <FormControlLabel control={<Switch size="small" checked={form.is_business}
                onChange={e => setForm({ ...form, is_business: e.target.checked })} />}
                label={<Typography variant="body2">{t('customers.isBusiness', 'Erhvervskunde')}</Typography>} />
              <FormControlLabel control={<Switch size="small" checked={form.is_public}
                onChange={e => setForm({ ...form, is_public: e.target.checked })} />}
                label={<Typography variant="body2">{t('customers.isPublic', 'Offentlig kunde')}</Typography>} />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label={form.vat_zone === 'dk' ? t('customers.cvr', 'CVR-/SE-nummer') : t('customers.euVat', 'Momsnummer (fx DE123456789)')}
                value={form.tax_id} size="small" fullWidth
                helperText={form.vat_zone === 'eu' && form.is_business ? t('customers.euVatHelp', 'Kræves ved EU-salg uden moms (omvendt betalingspligt)') : ''}
                onChange={e => setForm({ ...form, tax_id: e.target.value })}
              />
              <TextField label={t('customers.ean', 'EAN-/GLN-nummer')} value={form.ean} size="small" fullWidth
                required={form.is_public}
                helperText={form.is_public ? t('customers.eanHelp', '13 cifre – kræves for e-faktura til offentlige kunder') : ''}
                onChange={e => setForm({ ...form, ean: e.target.value.replace(/\D/g, '').slice(0, 13) })} />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label={t('common.currency')} value={form.currency} size="small" sx={{ width: 120 }}
                onChange={e => setForm({ ...form, currency: e.target.value })}
                select
              >
                {CURRENCY_OPTIONS.map(c => (
                  <MenuItem key={c} value={c}>{c}</MenuItem>
                ))}
              </TextField>
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField select
                label={t('customers.paymentTerms')} value={form.payment_terms_code} size="small" sx={{ width: 260 }}
                onChange={e => setForm({ ...form, payment_terms_code: e.target.value })}
              >
                {PAYMENT_TERMS.map(p => <MenuItem key={p.code} value={p.code}>{t(p.key, p.label)}</MenuItem>)}
              </TextField>
              <TextField
                label={t('customers.creditLimit')} value={form.credit_limit} size="small" fullWidth
                type="number"
                onChange={e => setForm({ ...form, credit_limit: e.target.value })}
                inputProps={{ min: 0, step: '0.01' }}
              />
            </Box>
            <TextField
              label={t('common.notes')} value={form.notes} size="small" fullWidth multiline rows={2}
              onChange={e => setForm({ ...form, notes: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleSave} sx={{ bgcolor: '#2e7d32' }}>
            {editing ? t('common.update') : t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Statement Dialog */}
      <Dialog open={statementOpen} onClose={closeStatement} maxWidth="md" fullWidth>
        <DialogTitle>
          {t('customers.statement')} — {statementCustomer?.code} {statementCustomer?.name}
        </DialogTitle>
        <DialogContent>
          <TableContainer component={Paper} variant="outlined" sx={{ mt: 1 }}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell sx={{ fontWeight: 600 }}>{t('common.date')}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{t('common.type')}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{t('common.reference')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.amount')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.balance')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {statementLines.map((line) => (
                  <TableRow key={line.id} hover>
                    <TableCell>{formatDate(line.date)}</TableCell>
                    <TableCell>
                      <Chip
                        label={line.type === 'invoice' ? t('common.invoice') : line.type === 'credit_note' ? t('customers.creditNote', 'Kreditnota') : line.type}
                        size="small"
                        sx={{
                          bgcolor: line.type === 'invoice' ? '#1976d2' : '#2e7d32',
                          color: '#fff',
                          height: 20,
                          fontSize: '11px',
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {line.reference}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {formatMoney(line.amount)}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 500 }}>
                      {formatMoney(line.balance)}
                    </TableCell>
                  </TableRow>
                ))}
                {statementLines.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                      <Typography variant="body2" color="text.secondary">{t('customers.noTransactions')}</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeStatement}>{t('common.close')}</Button>
        </DialogActions>
      </Dialog>

      {/* Import Dialog */}
      <ImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onSuccess={fetchCustomers}
        previewEndpoint="/customers/import/preview"
        confirmEndpoint="/customers/import/confirm"
        templateColumns={['code', 'name', 'email', 'phone', 'address', 'tax_id', 'currency', 'payment_terms', 'credit_limit', 'notes']}
        entityName={t('customers.title')}
      />

    </Box>
  );
};

export default Customers;
