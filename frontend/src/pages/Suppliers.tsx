import React, { useEffect, useMemo, useState } from 'react';
import { formatDate } from '../utils/dateFormat';
import { formatNumber } from '../utils/format';
import { BASE_CURRENCY } from '../utils/chart';
import {
  Autocomplete, Box, Typography, Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, MenuItem, Chip, Tooltip,
  InputAdornment, TablePagination,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Receipt as StatementIcon,
  Upload as UploadIcon,
  Download as DownloadIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { exportToCSV } from '../utils/csvExport';
import ImportDialog from '../components/ImportDialog';
import PlacesAutocomplete, { PlaceResult } from '../components/PlacesAutocomplete';

interface Account {
  id: string;
  code: string;
  name: string;
}

interface Supplier {
  id: string;
  code: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  tax_id: string;
  currency: string;
  payment_terms: string;
  notes: string;
  default_account_id: string | null;
  default_tax_code_id?: string | null;
  country?: string;
  is_active: boolean;
}

interface StatementLine {
  id: string;
  date: string;
  type: string;
  number: string;
  description: string;
  amount: string;
  balance: string;
}

interface StatementData {
  supplier: Supplier;
  lines: StatementLine[];
  total_bills: string;
  total_payments: string;
  balance: string;
}

const CURRENCY_OPTIONS = ['DKK', 'EUR', 'SEK', 'NOK', 'USD', 'GBP'];

interface TaxCode {
  id: string;
  code: string;
  name: string;
  type?: string;
  is_active?: boolean;
}

const emptyForm = {
  code: '',
  name: '',
  email: '',
  phone: '',
  address: '',
  country: 'DK',
  tax_id: '',
  currency: BASE_CURRENCY,
  payment_terms: '',
  notes: '',
  default_account_id: '',
  default_tax_code_id: '',
};

const Suppliers: React.FC = () => {
  const { t } = useTranslation();

  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [taxCodes, setTaxCodes] = useState<TaxCode[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Supplier | null>(null);

  // Search & pagination
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  const filteredSuppliers = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return suppliers;
    return suppliers.filter(s =>
      s.name.toLowerCase().includes(q) ||
      s.code.toLowerCase().includes(q) ||
      (s.email && s.email.toLowerCase().includes(q)) ||
      (s.phone && s.phone.includes(q))
    );
  }, [suppliers, search]);

  const paginatedSuppliers = useMemo(
    () => filteredSuppliers.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage),
    [filteredSuppliers, page, rowsPerPage],
  );

  // Statement dialog state
  const [statementOpen, setStatementOpen] = useState(false);
  const [statementData, setStatementData] = useState<StatementData | null>(null);
  const [statementDateFrom, setStatementDateFrom] = useState('');
  const [statementDateTo, setStatementDateTo] = useState('');
  const [statementSupplierId, setStatementSupplierId] = useState('');

  // Form state
  const [form, setForm] = useState({ ...emptyForm });

  const fetchSuppliers = () => {
    api.get('/suppliers').then(res => {
      if (res.data.success) setSuppliers(res.data.data.suppliers);
    });
  };

  const fetchAccounts = () => {
    api.get('/accounts?is_active=true').then(res => {
      if (res.data.success) setAccounts(res.data.data.accounts);
    });
    api.get('/tax-codes').then(res => {
      if (res.data.success) {
        setTaxCodes(res.data.data.tax_codes.filter((tc: TaxCode) => tc.is_active !== false && tc.type !== 'sales'));
      }
    }).catch(() => { /* momskoder kræver momsfunktionen */ });
  };

  useEffect(() => { fetchSuppliers(); fetchAccounts(); }, []);

  const handleOpen = (supplier?: Supplier) => {
    if (supplier) {
      setEditing(supplier);
      setForm({
        code: supplier.code,
        name: supplier.name,
        email: supplier.email || '',
        phone: supplier.phone || '',
        address: supplier.address || '',
        country: supplier.country || 'DK',
        tax_id: supplier.tax_id || '',
        currency: supplier.currency || BASE_CURRENCY,
        payment_terms: supplier.payment_terms || '',
        notes: supplier.notes || '',
        default_account_id: supplier.default_account_id || '',
        default_tax_code_id: supplier.default_tax_code_id || '',
      });
    } else {
      setEditing(null);
      setForm({ ...emptyForm });
    }
    setDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      if (editing) {
        await api.put(`/suppliers/${editing.id}`, form);
      } else {
        await api.post('/suppliers', form);
      }
      setDialogOpen(false);
      fetchSuppliers();
    } catch (err: any) {
      alert(err.response?.data?.message || t('suppliers.errorSaving'));
    }
  };

  const handleDelete = async (id: string) => {
    const supplier = suppliers.find(s => s.id === id);
    if (!confirm(t('suppliers.deactivateConfirm', { name: supplier?.name }))) return;
    try {
      await api.delete(`/suppliers/${id}`);
      fetchSuppliers();
    } catch (err: any) {
      alert(err.response?.data?.message || t('suppliers.errorDeleting'));
    }
  };

  const openStatement = (supplier: Supplier) => {
    setStatementSupplierId(supplier.id);
    setStatementDateFrom('');
    setStatementDateTo('');
    setStatementOpen(true);
    fetchStatement(supplier.id, '', '');
  };

  const fetchStatement = (supplierId: string, dateFrom: string, dateTo: string) => {
    const params = new URLSearchParams();
    if (dateFrom) params.set('date_from', dateFrom);
    if (dateTo) params.set('date_to', dateTo);
    const qs = params.toString() ? `?${params.toString()}` : '';
    api.get(`/suppliers/${supplierId}/statement${qs}`).then(res => {
      if (res.data.success) {
        setStatementData(res.data.data);
      }
    });
  };

  const handleStatementFilter = () => {
    if (statementSupplierId) {
      fetchStatement(statementSupplierId, statementDateFrom, statementDateTo);
    }
  };

  const closeStatement = () => {
    setStatementOpen(false);
    setStatementData(null);
    setStatementSupplierId('');
  };

  // Import/Export
  const [importOpen, setImportOpen] = useState(false);

  const handleExportSuppliers = () => {
    const headers = ['code', 'name', 'email', 'phone', 'address', 'tax_id', 'currency', 'payment_terms', 'notes'];
    const rows = suppliers.map(s => [
      s.code, s.name, s.email, s.phone, s.address, s.tax_id,
      s.currency, String(s.payment_terms), s.notes,
    ]);
    exportToCSV('suppliers.csv', headers, rows);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>{t('suppliers.title')}</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<DownloadIcon />} onClick={handleExportSuppliers} size="small">
            {t('importExport.export')}
          </Button>
          <Button variant="outlined" startIcon={<UploadIcon />} onClick={() => setImportOpen(true)} size="small">
            {t('importExport.import')}
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpen()} sx={{ bgcolor: '#2e7d32' }}>
            {t('suppliers.addSupplier')}
          </Button>
        </Box>
      </Box>

      <TextField
        label={t('common.search')}
        value={search}
        size="small"
        sx={{ mb: 1, width: 300 }}
        onChange={e => { setSearch(e.target.value); setPage(0); }}
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <SearchIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
            </InputAdornment>
          ),
        }}
      />

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.code')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.name')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.email')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.phone')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.currency')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('suppliers.paymentTerms')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.status')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedSuppliers.map(supplier => (
              <TableRow key={supplier.id} hover sx={{ opacity: supplier.is_active ? 1 : 0.5 }}>
                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 500 }}>
                    {supplier.code}
                  </Typography>
                </TableCell>
                <TableCell>{supplier.name}</TableCell>
                <TableCell>{supplier.email}</TableCell>
                <TableCell>{supplier.phone}</TableCell>
                <TableCell>{supplier.currency}</TableCell>
                <TableCell>{supplier.payment_terms}</TableCell>
                <TableCell>
                  <Chip
                    label={supplier.is_active ? t('common.active') : t('common.inactive')}
                    size="small"
                    sx={{
                      bgcolor: supplier.is_active ? '#2e7d32' : '#9e9e9e',
                      color: '#fff',
                      height: 20,
                      fontSize: '11px',
                    }}
                  />
                </TableCell>
                <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                  <Tooltip title={t('suppliers.statement')}>
                    <IconButton size="small" onClick={() => openStatement(supplier)}>
                      <StatementIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={t('common.edit')}>
                    <IconButton size="small" onClick={() => handleOpen(supplier)}>
                      <EditIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={t('common.delete')}>
                    <IconButton size="small" color="error" onClick={() => handleDelete(supplier.id)}>
                      <DeleteIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
            {paginatedSuppliers.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                  <Typography variant="body2" color="text.secondary">{t('suppliers.noSuppliers')}</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={filteredSuppliers.length}
          page={page}
          onPageChange={(_, p) => setPage(p)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={e => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
          rowsPerPageOptions={[25, 50, 100]}
        />
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editing ? t('suppliers.editSupplier') : t('suppliers.addSupplier')}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label={t('common.code')} value={form.code} size="small" sx={{ width: 120 }}
                onChange={e => setForm({ ...form, code: e.target.value })}
              />
              <PlacesAutocomplete
                value={form.name}
                onChange={(val) => setForm({ ...form, name: val })}
                onPlaceSelect={(place: PlaceResult) => {
                  setForm(prev => ({
                    ...prev,
                    name: place.name || prev.name,
                    address: place.address || prev.address,
                    phone: place.phone || prev.phone,
                  }));
                }}
                label={t('common.name')}
                sx={{ flex: 1 }}
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
            <TextField
              label={t('common.address')} value={form.address} size="small" fullWidth multiline rows={2}
              onChange={e => setForm({ ...form, address: e.target.value })}
            />
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label={t('suppliers.vatNumber', 'CVR-/momsnummer')} value={form.tax_id} size="small" fullWidth
                onChange={e => setForm({ ...form, tax_id: e.target.value })}
                helperText={t('suppliers.vatNumberHint', 'CVR for danske, momsnummer (fx DE123456789) for EU-leverandører')}
              />
              <TextField
                label={t('suppliers.country', 'Land')} value={form.country} size="small" sx={{ width: 90 }}
                onChange={e => setForm({ ...form, country: e.target.value.toUpperCase().slice(0, 2) })}
                helperText={t('suppliers.countryHint', 'ISO-kode')}
              />
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
            <TextField
              label={t('suppliers.paymentTerms')} value={form.payment_terms} size="small" fullWidth
              onChange={e => setForm({ ...form, payment_terms: e.target.value })}
              placeholder={t('suppliers.paymentTermsPlaceholder')}
            />
            <Autocomplete
              options={accounts}
              getOptionLabel={(a) => `${a.code} — ${a.name}`}
              value={accounts.find(a => a.id === form.default_account_id) || null}
              onChange={(_, v) => setForm({ ...form, default_account_id: v?.id || '' })}
              renderInput={(params) => (
                <TextField {...params} label={t('suppliers.defaultAccount')} size="small" />
              )}
              size="small"
            />
            <TextField
              select label={t('suppliers.defaultTaxCode', 'Standardmomskode')} value={form.default_tax_code_id}
              size="small" fullWidth
              onChange={e => setForm({ ...form, default_tax_code_id: e.target.value })}
              helperText={t('suppliers.defaultTaxCodeHint', 'Foreslås på nye regninger, fx K260 for en EU-leverandør af ydelser')}
            >
              <MenuItem value="">{t('common.none')}</MenuItem>
              {taxCodes.map(tc => <MenuItem key={tc.id} value={tc.id}>{tc.code} — {tc.name}</MenuItem>)}
            </TextField>
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
      <Dialog open={statementOpen} onClose={closeStatement} maxWidth="lg" fullWidth>
        <DialogTitle>
          {t('suppliers.statement')} — {statementData?.supplier?.code} {statementData?.supplier?.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 2, mt: 1 }}>
            <TextField
              label={t('common.from')} type="date" value={statementDateFrom} size="small"
              onChange={e => setStatementDateFrom(e.target.value)}
              InputLabelProps={{ shrink: true }} sx={{ width: 150 }}
            />
            <TextField
              label={t('common.to')} type="date" value={statementDateTo} size="small"
              onChange={e => setStatementDateTo(e.target.value)}
              InputLabelProps={{ shrink: true }} sx={{ width: 150 }}
            />
            <Button variant="outlined" size="small" onClick={handleStatementFilter}>
              {t('common.apply')}
            </Button>
          </Box>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell sx={{ fontWeight: 600 }}>{t('common.date')}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{t('common.type')}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{t('common.number')}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{t('common.description')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.amount')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.balance')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {statementData?.lines?.map((line) => (
                  <TableRow key={line.id} hover>
                    <TableCell>{formatDate(line.date)}</TableCell>
                    <TableCell>
                      <Chip
                        label={line.type === 'bill' ? t('common.bill') : t('common.payment')}
                        size="small"
                        sx={{
                          bgcolor: line.type === 'bill' ? '#e65100' : '#2e7d32',
                          color: '#fff',
                          height: 20,
                          fontSize: '11px',
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{line.number}</Typography>
                    </TableCell>
                    <TableCell>{line.description}</TableCell>
                    <TableCell align="right">
                      {formatNumber(line.amount)}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 500 }}>
                      {formatNumber(line.balance)}
                    </TableCell>
                  </TableRow>
                ))}
                {(!statementData?.lines || statementData.lines.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                      <Typography variant="body2" color="text.secondary">{t('suppliers.noTransactions')}</Typography>
                    </TableCell>
                  </TableRow>
                )}
                {statementData?.lines && statementData.lines.length > 0 && (
                  <TableRow sx={{ bgcolor: '#e8f5e9' }}>
                    <TableCell colSpan={3} sx={{ fontWeight: 700 }}>{t('suppliers.totalsLabel')}</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>
                      {t('suppliers.billsLabel')} {formatNumber(statementData.total_bills)}
                      {' | '}
                      {t('suppliers.paymentsLabel')} {formatNumber(statementData.total_payments)}
                    </TableCell>
                    <TableCell />
                    <TableCell align="right" sx={{ fontWeight: 700 }}>
                      {formatNumber(statementData.balance)}
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
        onSuccess={fetchSuppliers}
        previewEndpoint="/suppliers/import/preview"
        confirmEndpoint="/suppliers/import/confirm"
        templateColumns={['code', 'name', 'email', 'phone', 'address', 'tax_id', 'currency', 'payment_terms', 'notes']}
        entityName={t('suppliers.title')}
      />

    </Box>
  );
};

export default Suppliers;
