import React, { useEffect, useState } from 'react';
import { formatDate } from '../utils/dateFormat';
import { formatNumber, formatMoney } from '../utils/format';
import { BASE_CURRENCY } from '../utils/chart';
import {
  Box, Typography, Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, MenuItem, Chip, Tooltip, TablePagination,
  Autocomplete, InputAdornment, Checkbox, FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon,
  RemoveRedEye as ViewIcon, CheckCircle as ApproveIcon,
  AddCircleOutline as AddLineIcon, RemoveCircleOutline as RemoveLineIcon,
  Download as DownloadIcon, Upload as UploadIcon,
  Search as SearchIcon, Clear as ClearIcon,
  ArrowUpward as ArrowUpIcon, ArrowDownward as ArrowDownIcon,
  DriveFileMove as MoveIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { downloadBlob } from '../utils/csvExport';
import BillImportDialog from '../components/BillImportDialog';
import { ReadInvoiceButton, ReadInvoiceNotice, ReadInvoiceResult } from '../components/ReadInvoice';

interface Supplier {
  id: string;
  code: string;
  name: string;
  default_account_id?: string | null;
  default_tax_code_id?: string | null;
}

interface Account {
  id: string;
  code: string;
  name: string;
}

interface TaxCode {
  id: string;
  code: string;
  name: string;
  rate: string;
  type?: string;
  is_active?: boolean;
  reverse_charge?: string;
  deduction_rate?: string;
  rubrik?: string;
  energy_tax?: boolean;
}

const CURRENCY_OPTIONS = ['DKK', 'EUR', 'SEK', 'NOK', 'USD', 'GBP'];

/** Moms, leverandøren fakturerer: 0 ved omvendt betalingspligt, energiafgift og momsfri køb. */
const supplierVat = (amount: number, tc?: TaxCode) => {
  if (!tc || tc.reverse_charge || tc.energy_tax) return 0;
  return Math.round(amount * parseFloat(tc.rate || '0')) / 100;
};

interface BillLine {
  id?: string;
  description: string;
  quantity: string;
  unit_price: string;
  account_id: string;
  tax_code_id: string;
  amount: string;
}

interface Bill {
  id: string;
  bill_number: string;
  supplier_id: string;
  supplier_name: string;
  date: string;
  due_date: string;
  reference: string;
  notes: string;
  status: string;
  subtotal: string;
  tax_amount: string;
  total: string;
  paid_amount: string;
  currency?: string;
  exchange_rate?: string;
  lines?: BillLine[];
  line_account_codes?: string[];
}

const STATUS_COLORS: Record<string, 'default' | 'primary' | 'success' | 'error'> = {
  draft: 'default',
  approved: 'primary',
  paid: 'success',
  overdue: 'error',
};

const EMPTY_LINE: BillLine = {
  description: '',
  quantity: '1',
  unit_price: '0',
  account_id: '',
  tax_code_id: '',
  amount: '0',
};

const Bills: React.FC = () => {
  const { t } = useTranslation();

  const STATUS_LABELS: Record<string, string> = {
    draft: t('bills.draft'),
    approved: t('bills.approved'),
    paid: t('bills.paid'),
    overdue: t('bills.overdue'),
  };

  const [bills, setBills] = useState<Bill[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [taxCodes, setTaxCodes] = useState<TaxCode[]>([]);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [editing, setEditing] = useState<Bill | null>(null);
  const [viewing, setViewing] = useState<Bill | null>(null);

  // New supplier inline creation
  const [newSupplierOpen, setNewSupplierOpen] = useState(false);
  const [newSupplierName, setNewSupplierName] = useState('');
  const [newSupplierAccount, setNewSupplierAccount] = useState('');

  // Filter state
  const [filterStatus, setFilterStatus] = useState('');
  const [filterSupplier, setFilterSupplier] = useState('');
  const [filterDateFrom, setFilterDateFrom] = useState('');
  const [filterDateTo, setFilterDateTo] = useState('');
  const [filterSearch, setFilterSearch] = useState('');
  const [filterAmountMin, setFilterAmountMin] = useState('');
  const [filterAmountMax, setFilterAmountMax] = useState('');
  const [filterOverdue, setFilterOverdue] = useState(false);
  const [filterNoSupplier, setFilterNoSupplier] = useState(false);
  const [filterHasSupplier, setFilterHasSupplier] = useState(false);

  // Sort state
  const [sortField, setSortField] = useState('date');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [totalCount, setTotalCount] = useState(0);

  // Form state
  const [form, setForm] = useState({
    supplier_id: '',
    date: '',
    due_date: '',
    reference: '',
    notes: '',
    currency: BASE_CURRENCY,
    exchange_rate: '1',
  });
  const [lines, setLines] = useState<BillLine[]>([{ ...EMPTY_LINE }]);
  const [readInfo, setReadInfo] = useState<ReadInvoiceResult | null>(null);

  const buildFilterParams = () => {
    const params = new URLSearchParams();
    if (filterSearch) params.set('search', filterSearch);
    if (filterStatus) params.set('status', filterStatus);
    if (filterSupplier) params.set('supplier_id', filterSupplier);
    if (filterDateFrom) params.set('date_from', filterDateFrom);
    if (filterDateTo) params.set('date_to', filterDateTo);
    if (filterAmountMin) params.set('amount_min', filterAmountMin);
    if (filterAmountMax) params.set('amount_max', filterAmountMax);
    if (filterOverdue) params.set('overdue', 'true');
    if (filterNoSupplier) params.set('no_supplier', 'true');
    if (filterHasSupplier) params.set('has_supplier', 'true');
    if (sortField) params.set('sort', sortField);
    if (sortDir) params.set('sort_dir', sortDir);
    return params;
  };

  const fetchBills = (p?: number) => {
    const params = buildFilterParams();
    const currentPage = p !== undefined ? p : page;
    params.set('page', String(currentPage + 1));
    params.set('page_size', String(rowsPerPage));
    const qs = params.toString() ? `?${params.toString()}` : '';
    api.get(`/bills${qs}`).then(res => {
      if (res.data.success) {
        setBills(res.data.data.bills);
        setTotalCount(res.data.data.total_count ?? res.data.data.count ?? 0);
      }
    });
  };

  const fetchDropdowns = () => {
    api.get('/suppliers').then(res => {
      if (res.data.success) setSuppliers(res.data.data.suppliers);
    });
    api.get('/accounts?is_active=true').then(res => {
      if (res.data.success) setAccounts(res.data.data.accounts);
    });
    api.get('/tax-codes').then(res => {
      if (res.data.success) setTaxCodes(res.data.data.tax_codes);
    });
  };

  useEffect(() => {
    fetchBills();
    fetchDropdowns();
  // eslint-disable-next-line react-hooks/exhaustive-deps -- load once on mount; filters apply when the user presses Search
  }, []);

  const handleApplyFilters = () => {
    setPage(0);
    fetchBills(0);
  };

  const handleSort = (field: string) => {
    const newDir = sortField === field && sortDir === 'desc' ? 'asc' : 'desc';
    setSortField(field);
    setSortDir(newDir);
    // Fetch immediately with new sort (state is async, so build params manually)
    const params = buildFilterParams();
    params.set('sort', field);
    params.set('sort_dir', newDir);
    params.set('page', '1');
    params.set('page_size', String(rowsPerPage));
    api.get(`/bills?${params.toString()}`).then(res => {
      if (res.data.success) {
        setBills(res.data.data.bills);
        setTotalCount(res.data.data.total_count ?? res.data.data.count ?? 0);
      }
    });
    setPage(0);
  };

  const SortHeader = ({ field, label, align }: { field: string; label: string; align?: 'right' }) => (
    <TableCell
      align={align}
      sx={{ fontWeight: 600, cursor: 'pointer', userSelect: 'none', '&:hover': { bgcolor: '#e0e0e0' } }}
      onClick={() => handleSort(field)}
    >
      <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
        {label}
        {sortField === field ? (
          sortDir === 'desc' ? <ArrowDownIcon sx={{ fontSize: 14 }} /> : <ArrowUpIcon sx={{ fontSize: 14 }} />
        ) : null}
      </Box>
    </TableCell>
  );

  const handleResetFilters = () => {
    setFilterSearch('');
    setFilterStatus('');
    setFilterSupplier('');
    setFilterDateFrom('');
    setFilterDateTo('');
    setFilterAmountMin('');
    setFilterAmountMax('');
    setFilterOverdue(false);
    setFilterNoSupplier(false);
    setFilterHasSupplier(false);
    setSortField('date');
    setSortDir('desc');
    setPage(0);
    // Fetch with empty filters directly since state updates are async
    const params = new URLSearchParams();
    params.set('page', '1');
    params.set('page_size', String(rowsPerPage));
    api.get(`/bills?${params.toString()}`).then(res => {
      if (res.data.success) {
        setBills(res.data.data.bills);
        setTotalCount(res.data.data.total_count ?? res.data.data.count ?? 0);
      }
    });
  };

  const handleExportBills = async () => {
    const params = buildFilterParams();
    const qs = params.toString() ? `?${params.toString()}` : '';
    try {
      const res = await api.get(`/bills/export${qs}`, { responseType: 'blob' });
      downloadBlob(new Blob([res.data]), 'bills.csv');
    } catch { /* ignore */ }
  };

  const handlePageChange = (_: unknown, newPage: number) => {
    setPage(newPage);
    fetchBills(newPage);
  };

  const handleRowsPerPageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newSize = parseInt(e.target.value, 10);
    setRowsPerPage(newSize);
    setPage(0);
    setTimeout(() => fetchBills(0), 0);
  };

  const recalcLineAmount = (line: BillLine): string => {
    const qty = parseFloat(line.quantity || '0');
    const price = parseFloat(line.unit_price || '0');
    return (qty * price).toFixed(2);
  };

  const handleOpen = async (bill?: Bill) => {
    if (bill) {
      const res = await api.get(`/bills/${bill.id}`);
      if (res.data.success) {
        const full = res.data.data.bill;
        setEditing(full);
        const billLines = full.lines && full.lines.length > 0
          ? full.lines.map((l: BillLine) => ({
              description: l.description,
              quantity: l.quantity,
              unit_price: l.unit_price,
              account_id: l.account_id || '',
              tax_code_id: l.tax_code_id || '',
              amount: l.amount,
            }))
          : [{ ...EMPTY_LINE }];
        // Auto-detect supplier from line accounts if not set
        let supplierId = full.supplier_id || '';
        if (!supplierId && billLines.length > 0) {
          for (const line of billLines) {
            if (line.account_id) {
              const matched = suppliers.find(s => s.default_account_id === line.account_id);
              if (matched) { supplierId = matched.id; break; }
            }
          }
        }
        setForm({
          supplier_id: supplierId,
          date: full.date,
          due_date: full.due_date,
          reference: full.reference || '',
          notes: full.notes || '',
          currency: full.currency || BASE_CURRENCY,
          exchange_rate: full.exchange_rate || '1',
        });
        setLines(billLines);
      }
    } else {
      setEditing(null);
      setReadInfo(null);
      const today = new Date();
      setForm({
        supplier_id: '',
        date: today.toISOString().split('T')[0],
        due_date: '',
        reference: '',
        notes: '',
        currency: BASE_CURRENCY,
        exchange_rate: '1',
      });
      setLines([{ ...EMPTY_LINE }]);
    }
    setDialogOpen(true);
  };

  /** Udfyld en ny regning ud fra en læst leverandørfaktura (kladde; brugeren tjekker og gemmer). */
  const applyRead = (r: ReadInvoiceResult) => {
    const p = r.proposal;
    const today = new Date().toISOString().split('T')[0];
    setEditing(null);
    setReadInfo(r);
    const supplier = suppliers.find((s) => s.id === p?.supplier_id);
    setForm({
      supplier_id: p?.supplier_id || '',
      date: p?.date || today,
      due_date: p?.due_date || '',
      reference: p?.reference || '',
      notes: p?.notes || '',
      currency: p?.currency || BASE_CURRENCY,
      exchange_rate: '1',
    });
    setLines(p?.lines?.length ? p.lines.map((l) => ({
      description: l.description, quantity: l.quantity, unit_price: l.unit_price,
      account_id: l.account_id || supplier?.default_account_id || '',
      tax_code_id: l.tax_code_id || supplier?.default_tax_code_id || '',
      amount: l.amount,
    })) : [{ ...EMPTY_LINE }]);
    setDialogOpen(true);
  };

  const createSupplierFromRead = async () => {
    const ns = readInfo?.proposal?.new_supplier;
    if (!ns) return;
    try {
      const res = await api.post('/suppliers', { name: ns.name || 'Ny leverandør', tax_id: ns.tax_id, address: ns.address });
      const created = res.data.data.supplier;
      const supRes = await api.get('/suppliers');
      if (supRes.data.success) setSuppliers(supRes.data.data.suppliers);
      setForm((prev) => ({ ...prev, supplier_id: created.id }));
      setReadInfo((prev) => (prev && prev.proposal ? { ...prev, proposal: { ...prev.proposal, new_supplier: null, supplier_id: created.id } } : prev));
    } catch (err: any) {
      alert(err.response?.data?.message || 'Leverandøren kunne ikke oprettes');
    }
  };

  const handleView = async (bill: Bill) => {
    const res = await api.get(`/bills/${bill.id}`);
    if (res.data.success) {
      setViewing(res.data.data.bill);
      setViewDialogOpen(true);
    }
  };

  const handleSave = async () => {
    const payload = {
      ...form,
      exchange_rate: form.currency === BASE_CURRENCY ? '1' : form.exchange_rate,
      lines: lines.filter(l => l.description || l.account_id),
      ...(readInfo && !editing ? { document_id: readInfo.document_id } : {}),
    };
    try {
      if (editing) {
        await api.put(`/bills/${editing.id}`, payload);
      } else {
        await api.post('/bills', payload);
      }
      setDialogOpen(false);
      setReadInfo(null);
      fetchBills();
    } catch (err: any) {
      alert(err.response?.data?.message || t('bills.errorSaving'));
    }
  };

  const handleDelete = async (id: string) => {
    const bill = bills.find(b => b.id === id);
    if (!confirm(t('bills.deleteConfirm', { number: bill?.bill_number || id }))) return;
    try {
      await api.delete(`/bills/${id}`);
      fetchBills();
    } catch (err: any) {
      alert(err.response?.data?.message || t('bills.errorDeleting'));
    }
  };

  const handleApprove = async (id: string) => {
    try {
      await api.post(`/bills/${id}/approve`);
      fetchBills();
    } catch (err: any) {
      alert(err.response?.data?.message || t('bills.errorApproving'));
    }
  };

  const handleBulkApprove = async () => {
    const draftBills = bills.filter(b => b.status === 'draft');
    if (!draftBills.length) return;
    if (!window.confirm(t('bills.bulkApproveConfirm', { count: draftBills.length }))) return;
    try {
      const res = await api.post('/bills/bulk-approve', { bill_ids: draftBills.map(b => b.id) });
      if (res.data.success) {
        alert(t('bills.bulkApproveSuccess', { count: res.data.approved_count }));
        fetchBills();
      }
    } catch (err: any) {
      alert(err.response?.data?.message || t('bills.errorApproving'));
    }
  };

  const handleMoveToExpenses = async (id: string) => {
    if (!window.confirm(t('bills.moveToExpensesConfirm'))) return;
    try {
      await api.post(`/bills/${id}/move-to-expenses`);
      setDialogOpen(false);
      setViewDialogOpen(false);
      fetchBills();
    } catch (err: any) {
      alert(err.response?.data?.message || t('bills.errorMoving'));
    }
  };

  const handleCreateSupplier = async () => {
    if (!newSupplierName.trim()) return;
    try {
      const res = await api.post('/suppliers', {
        name: newSupplierName.trim(),
        default_account_id: newSupplierAccount || undefined,
      });
      if (res.data.success) {
        const created = res.data.data.supplier;
        // Refresh suppliers list and select the new one
        const supRes = await api.get('/suppliers');
        if (supRes.data.success) setSuppliers(supRes.data.data.suppliers);
        setForm(prev => ({ ...prev, supplier_id: created.id }));
        // Auto-fill account on lines
        if (created.default_account_id) {
          setLines(prev => prev.map(l =>
            l.account_id ? l : { ...l, account_id: created.default_account_id }
          ));
        }
        setNewSupplierOpen(false);
        setNewSupplierName('');
        setNewSupplierAccount('');
      }
    } catch (err: any) {
      alert(err.response?.data?.message || t('suppliers.errorSaving'));
    }
  };

  const updateLine = (index: number, field: keyof BillLine, value: string) => {
    setLines(prev =>
      prev.map((l, i) => {
        if (i !== index) return l;
        const updated = { ...l, [field]: value };
        if (field === 'quantity' || field === 'unit_price') {
          updated.amount = recalcLineAmount(updated);
        }
        return updated;
      })
    );
    // Auto-fill supplier when account changes and no supplier is set
    if (field === 'account_id' && value && !form.supplier_id) {
      const matched = suppliers.find(s => s.default_account_id === value);
      if (matched) {
        setForm(prev => ({ ...prev, supplier_id: matched.id }));
      }
    }
  };

  const addLine = () => setLines(prev => [...prev, { ...EMPTY_LINE }]);
  const removeLine = (index: number) => {
    if (lines.length <= 1) return;
    setLines(prev => prev.filter((_, i) => i !== index));
  };

  const subtotal = lines.reduce((sum, l) => sum + parseFloat(l.amount || '0'), 0);
  const taxAmount = lines.reduce(
    (sum, l) => sum + supplierVat(parseFloat(l.amount || '0'), taxCodes.find(tc => tc.id === l.tax_code_id)), 0);
  const total = subtotal + taxAmount;
  const purchaseCodes = taxCodes.filter(tc => tc.is_active !== false && tc.type !== 'sales');
  const hasReverseCharge = lines.some(l => taxCodes.find(tc => tc.id === l.tax_code_id)?.reverse_charge);
  const taxCodeHint = (tc?: TaxCode) => {
    if (!tc) return '';
    const parts: string[] = [];
    if (tc.reverse_charge) parts.push(t('bills.reverseChargeShort', 'Omvendt betalingspligt'));
    if (tc.energy_tax) parts.push(t('bills.energyTaxShort', 'Energiafgift (godtgørelse)'));
    if (tc.deduction_rate && parseFloat(tc.deduction_rate) < 100 && parseFloat(tc.rate) > 0) {
      parts.push(t('bills.deductionShort', '{{pct}} % fradrag', { pct: formatNumber(tc.deduction_rate).replace(/,00$/, '') }));
    }
    if (tc.rubrik) parts.push(t('bills.rubrikShort', 'Rubrik {{r}}', { r: tc.rubrik.charAt(0) }));
    return parts.join(' · ');
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>{t('bills.title')}</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {filterHasSupplier && filterStatus === 'draft' && (
            <Button variant="contained" color="primary" startIcon={<ApproveIcon />} onClick={handleBulkApprove} size="small">
              {t('bills.bulkApprove')}
            </Button>
          )}
          <Button variant="outlined" startIcon={<DownloadIcon />} onClick={handleExportBills} size="small">
            {t('importExport.export')}
          </Button>
          <ReadInvoiceButton onRead={applyRead} />
          <Button variant="outlined" startIcon={<UploadIcon />} onClick={() => setImportOpen(true)} size="small">
            {t('importExport.import')}
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpen()} sx={{ bgcolor: '#2e7d32' }}>
            {t('bills.newBill')}
          </Button>
        </Box>
      </Box>

      {/* Filter Bar */}
      <Paper sx={{ p: 1.5, mb: 2, display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField
          label={t('common.search')}
          value={filterSearch}
          size="small"
          sx={{ width: 200 }}
          onChange={e => setFilterSearch(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') handleApplyFilters(); }}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <SearchIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
              </InputAdornment>
            ),
          }}
        />
        <TextField
          select label={t('common.status')} value={filterStatus} size="small"
          onChange={e => setFilterStatus(e.target.value)}
          sx={{ width: 140 }}
        >
          <MenuItem value="">{t('common.all')}</MenuItem>
          <MenuItem value="draft">{t('bills.draft')}</MenuItem>
          <MenuItem value="approved">{t('bills.approved')}</MenuItem>
          <MenuItem value="paid">{t('bills.paid')}</MenuItem>
          <MenuItem value="overdue">{t('bills.overdue')}</MenuItem>
        </TextField>
        <Autocomplete
          options={suppliers}
          getOptionLabel={(s) => `${s.code} — ${s.name}`}
          value={suppliers.find(s => s.id === filterSupplier) || null}
          onChange={(_, v) => setFilterSupplier(v?.id || '')}
          renderInput={(params) => (
            <TextField {...params} label={t('bills.supplier')} size="small" />
          )}
          sx={{ width: 250 }}
          size="small"
        />
        <TextField
          label={t('common.from')} type="date" value={filterDateFrom} size="small"
          onChange={e => setFilterDateFrom(e.target.value)}
          InputLabelProps={{ shrink: true }} sx={{ width: 140 }}
        />
        <TextField
          label={t('common.to')} type="date" value={filterDateTo} size="small"
          onChange={e => setFilterDateTo(e.target.value)}
          InputLabelProps={{ shrink: true }} sx={{ width: 140 }}
        />
        <TextField
          label={t('bills.amountMin')} type="number" value={filterAmountMin} size="small"
          onChange={e => setFilterAmountMin(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') handleApplyFilters(); }}
          sx={{ width: 120 }}
          inputProps={{ min: 0, step: '0.01' }}
        />
        <TextField
          label={t('bills.amountMax')} type="number" value={filterAmountMax} size="small"
          onChange={e => setFilterAmountMax(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') handleApplyFilters(); }}
          sx={{ width: 120 }}
          inputProps={{ min: 0, step: '0.01' }}
        />
        <FormControlLabel
          control={<Checkbox size="small" checked={filterOverdue} onChange={e => setFilterOverdue(e.target.checked)} />}
          label={<Typography variant="body2">{t('bills.overdueOnly')}</Typography>}
          sx={{ mr: 0 }}
        />
        <FormControlLabel
          control={<Checkbox size="small" checked={filterNoSupplier} onChange={e => { setFilterNoSupplier(e.target.checked); if (e.target.checked) setFilterHasSupplier(false); }} />}
          label={<Typography variant="body2">{t('bills.noSupplierOnly')}</Typography>}
          sx={{ mr: 0 }}
        />
        <FormControlLabel
          control={<Checkbox size="small" checked={filterHasSupplier} onChange={e => { setFilterHasSupplier(e.target.checked); if (e.target.checked) setFilterNoSupplier(false); }} />}
          label={<Typography variant="body2">{t('bills.hasSupplierOnly')}</Typography>}
          sx={{ mr: 0 }}
        />
        <Button variant="outlined" size="small" onClick={handleApplyFilters}>
          {t('common.apply')}
        </Button>
        <Button variant="outlined" size="small" color="secondary" startIcon={<ClearIcon />} onClick={handleResetFilters}>
          {t('bills.resetFilters')}
        </Button>
      </Paper>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <SortHeader field="bill_number" label={t('bills.billNumber')} />
              <SortHeader field="supplier_name" label={t('bills.supplier')} />
              <SortHeader field="date" label={t('common.date')} />
              <SortHeader field="due_date" label={t('bills.dueDate')} />
              <SortHeader field="subtotal" label={t('common.subtotal')} align="right" />
              <SortHeader field="tax_amount" label={t('common.tax')} align="right" />
              <SortHeader field="total" label={t('common.total')} align="right" />
              <SortHeader field="paid_amount" label={t('bills.amountPaid')} align="right" />
              <SortHeader field="status" label={t('common.status')} />
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {bills.map(bill => (
              <TableRow key={bill.id} hover sx={!bill.supplier_name ? { bgcolor: '#e3f2fd' } : undefined}>
                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 500 }}>
                    {bill.bill_number}
                  </Typography>
                </TableCell>
                <TableCell>
                  {bill.supplier_name || (
                    <Chip label={t('bills.noSupplier')} size="small" color="warning" variant="outlined" sx={{ height: 20, fontSize: '11px' }} />
                  )}
                </TableCell>
                <TableCell>{formatDate(bill.date)}</TableCell>
                <TableCell>{formatDate(bill.due_date)}</TableCell>
                <TableCell align="right">
                  {formatNumber(bill.subtotal)}
                </TableCell>
                <TableCell align="right">
                  {formatNumber(bill.tax_amount)}
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>
                  {formatMoney(bill.total, bill.currency || BASE_CURRENCY)}
                </TableCell>
                <TableCell align="right">
                  {formatNumber(bill.paid_amount)}
                </TableCell>
                <TableCell>
                  <Chip
                    label={STATUS_LABELS[bill.status] || bill.status}
                    size="small"
                    color={STATUS_COLORS[bill.status] || 'default'}
                    sx={{ height: 20, fontSize: '11px' }}
                  />
                </TableCell>
                <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                  <Tooltip title={t('common.view')}>
                    <IconButton size="small" onClick={() => handleView(bill)}>
                      <ViewIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={t('common.edit')}>
                    <IconButton size="small" onClick={() => handleOpen(bill)}>
                      <EditIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                  </Tooltip>
                  {(bill.status === 'draft' || bill.status === 'approved') && (
                    <Tooltip title={t('common.approve')}>
                      <span>
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleApprove(bill.id)}
                          disabled={bill.status !== 'draft'}
                        >
                          <ApproveIcon sx={{ fontSize: 16 }} />
                        </IconButton>
                      </span>
                    </Tooltip>
                  )}
                  {bill.status === 'draft' && (
                    <Tooltip title={t('bills.moveToExpenses')}>
                      <IconButton size="small" color="warning" onClick={() => handleMoveToExpenses(bill.id)}>
                        <MoveIcon sx={{ fontSize: 16 }} />
                      </IconButton>
                    </Tooltip>
                  )}
                  {bill.status === 'draft' && (
                    <Tooltip title={t('common.delete')}>
                      <IconButton size="small" color="error" onClick={() => handleDelete(bill.id)}>
                        <DeleteIcon sx={{ fontSize: 16 }} />
                      </IconButton>
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {bills.length === 0 && (
              <TableRow>
                <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                  <Typography variant="body2" color="text.secondary">{t('bills.noBills')}</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={totalCount}
          page={page}
          onPageChange={handlePageChange}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleRowsPerPageChange}
          rowsPerPageOptions={[25, 50, 100]}
          labelRowsPerPage={t('common.rowsPerPage')}
        />
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>{editing ? t('bills.editBill', { number: editing.bill_number }) : t('bills.newBill')}</DialogTitle>
        <DialogContent>
          {readInfo && !editing && (
            <Box sx={{ mt: 1 }}>
              <ReadInvoiceNotice info={readInfo} onCreateSupplier={createSupplierFromRead} />
            </Box>
          )}
          {editing && editing.status !== 'draft' && (
            <Box sx={{ mt: 1, mb: 1, p: 1, bgcolor: '#fff3e0', borderRadius: 1, border: '1px solid #ffe0b2' }}>
              <Typography variant="body2" sx={{ color: '#e65100' }}>
                {t('bills.editApprovedNote')}
              </Typography>
            </Box>
          )}
          <Box sx={{ display: 'flex', gap: 2, mt: 1, mb: 2, flexWrap: 'wrap' }}>
            <Autocomplete
              options={[...suppliers, { id: '__new__', code: '', name: '' } as Supplier]}
              getOptionLabel={(s) => s.id === '__new__' ? `+ ${t('bills.addNewSupplier')}` : `${s.code} — ${s.name}`}
              value={suppliers.find(s => s.id === form.supplier_id) || null}
              onChange={(_, v) => {
                if (v?.id === '__new__') {
                  setNewSupplierName('');
                  setNewSupplierAccount('');
                  setNewSupplierOpen(true);
                  return;
                }
                setForm({ ...form, supplier_id: v?.id || '' });
                if (v?.default_account_id || v?.default_tax_code_id) {
                  setLines(prev => prev.map(l => ({
                    ...l,
                    account_id: l.account_id || v.default_account_id || '',
                    tax_code_id: l.tax_code_id || v.default_tax_code_id || '',
                  })));
                }
              }}
              filterOptions={(options, state) => {
                const input = state.inputValue.toLowerCase();
                const addNew = options.find(s => s.id === '__new__')!;
                const real = options.filter(s => s.id !== '__new__');
                const filtered = input
                  ? real.filter(s =>
                      s.name.toLowerCase().includes(input) || s.code.toLowerCase().includes(input)
                    ).slice(0, 50)
                  : real.slice(0, 50);
                filtered.push(addNew);
                return filtered;
              }}
              renderOption={(props, s) => (
                <li {...props} key={s.id} style={s.id === '__new__' ? { ...props.style, borderTop: '1px solid #e0e0e0' } : props.style}>
                  {s.id === '__new__' ? (
                    <Typography variant="body2" sx={{ color: 'primary.main', fontWeight: 600 }}>
                      + {t('bills.addNewSupplier')}
                    </Typography>
                  ) : (
                    <Typography variant="body2">
                      <span style={{ fontFamily: 'monospace', marginRight: 8 }}>{s.code}</span>
                      {s.name}
                    </Typography>
                  )}
                </li>
              )}
              renderInput={(params) => (
                <TextField {...params} label={t('bills.supplier')} size="small" />
              )}
              sx={{ width: 300 }}
              size="small"
              isOptionEqualToValue={(option, value) => option.id === value.id}
            />
            <TextField
              label={t('common.date')} type="date" value={form.date} size="small"
              onChange={e => setForm(prev => ({ ...prev, date: e.target.value }))}
              InputLabelProps={{ shrink: true }} sx={{ width: 160 }}
            />
            <TextField
              label={t('bills.dueDate')} type="date" value={form.due_date} size="small"
              onChange={e => setForm({ ...form, due_date: e.target.value })}
              InputLabelProps={{ shrink: true }} sx={{ width: 160 }}
            />
            <TextField
              label={t('common.reference')} value={form.reference} size="small" sx={{ width: 180 }}
              onChange={e => setForm({ ...form, reference: e.target.value })}
            />
            <TextField
              select label={t('bills.currency', 'Valuta')} value={form.currency} size="small" sx={{ width: 100 }}
              onChange={e => setForm({ ...form, currency: e.target.value, exchange_rate: e.target.value === BASE_CURRENCY ? '1' : form.exchange_rate })}
            >
              {CURRENCY_OPTIONS.map(c => <MenuItem key={c} value={c}>{c}</MenuItem>)}
            </TextField>
            {form.currency !== BASE_CURRENCY && (
              <TextField
                label={t('bills.exchangeRate', 'Kurs')} value={form.exchange_rate} size="small" type="number" sx={{ width: 130 }}
                onChange={e => setForm({ ...form, exchange_rate: e.target.value })}
                inputProps={{ min: 0, step: '0.0001' }}
                helperText={t('bills.exchangeRateHint', 'DKK pr. 1 {{cur}}', { cur: form.currency })}
              />
            )}
          </Box>
          <TextField
            label={t('bills.remarks')} value={form.notes} size="small" fullWidth multiline rows={2} sx={{ mb: 2 }}
            onChange={e => setForm({ ...form, notes: e.target.value })}
          />

          {/* Lines */}
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>{t('bills.billLines')}</Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell sx={{ fontWeight: 600, width: '25%' }}>{t('common.description')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600, width: 80 }}>{t('bills.quantity')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600, width: 110 }}>{t('bills.unitPrice')}</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '20%' }}>{t('common.account')}</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '15%' }}>{t('bills.taxCode')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600, width: 110 }}>{t('common.amount')}</TableCell>
                  <TableCell sx={{ width: 40 }} />
                </TableRow>
              </TableHead>
              <TableBody>
                {lines.map((line, i) => (
                  <TableRow key={i}>
                    <TableCell sx={{ p: 0.5 }}>
                      <TextField
                        value={line.description} size="small" fullWidth
                        onChange={e => updateLine(i, 'description', e.target.value)}
                        placeholder={t('common.description')}
                      />
                    </TableCell>
                    <TableCell sx={{ p: 0.5 }}>
                      <TextField
                        value={line.quantity} size="small" type="number" sx={{ width: 80 }}
                        onChange={e => updateLine(i, 'quantity', e.target.value)}
                        inputProps={{ min: 0, step: '1' }}
                      />
                    </TableCell>
                    <TableCell sx={{ p: 0.5 }}>
                      <TextField
                        value={line.unit_price} size="small" type="number" sx={{ width: 110 }}
                        onChange={e => updateLine(i, 'unit_price', e.target.value)}
                        inputProps={{ min: 0, step: '0.01' }}
                      />
                    </TableCell>
                    <TableCell sx={{ p: 0.5 }}>
                      <Autocomplete
                        size="small"
                        fullWidth
                        options={accounts}
                        value={accounts.find(a => a.id === line.account_id) || null}
                        onChange={(_e, val) => updateLine(i, 'account_id', val?.id || '')}
                        getOptionLabel={(a) => `${a.code} ${a.name}`}
                        filterOptions={(options, state) => {
                          const input = state.inputValue.toLowerCase();
                          if (!input) return options.slice(0, 50);
                          return options.filter(a =>
                            a.name.toLowerCase().includes(input) || a.code.toLowerCase().includes(input)
                          ).slice(0, 50);
                        }}
                        renderOption={(props, a) => (
                          <li {...props} key={a.id}>
                            <Typography variant="body2" component="span" sx={{ fontFamily: 'monospace', mr: 1 }}>{a.code}</Typography>
                            {a.name}
                          </li>
                        )}
                        renderInput={(params) => <TextField {...params} placeholder="—" />}
                        isOptionEqualToValue={(option, value) => option.id === value.id}
                      />
                    </TableCell>
                    <TableCell sx={{ p: 0.5 }}>
                      <TextField
                        select value={line.tax_code_id} size="small" fullWidth
                        onChange={e => updateLine(i, 'tax_code_id', e.target.value)}
                      >
                        <MenuItem value="">{t('common.none')}</MenuItem>
                        {purchaseCodes.map(tc => (
                          <MenuItem key={tc.id} value={tc.id}>
                            <Box>
                              <Typography variant="body2">{tc.code} — {tc.name}</Typography>
                              {taxCodeHint(tc) && (
                                <Typography variant="caption" color="text.secondary">{taxCodeHint(tc)}</Typography>
                              )}
                            </Box>
                          </MenuItem>
                        ))}
                      </TextField>
                      {taxCodeHint(taxCodes.find(tc => tc.id === line.tax_code_id)) && (
                        <Typography variant="caption" color="text.secondary">
                          {taxCodeHint(taxCodes.find(tc => tc.id === line.tax_code_id))}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell sx={{ p: 0.5 }} align="right">
                      <Typography variant="body2" sx={{ lineHeight: '40px', fontWeight: 500 }}>
                        {formatNumber(line.amount || '0')}
                      </Typography>
                    </TableCell>
                    <TableCell sx={{ p: 0.5 }}>
                      <IconButton size="small" onClick={() => removeLine(i)} disabled={lines.length <= 1}>
                        <RemoveLineIcon sx={{ fontSize: 16 }} />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
                {/* Totals */}
                <TableRow>
                  <TableCell colSpan={5} align="right" sx={{ fontWeight: 600 }}>{t('common.subtotal')}:</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>
                    {formatNumber(subtotal)}
                  </TableCell>
                  <TableCell />
                </TableRow>
                <TableRow>
                  <TableCell colSpan={5} align="right" sx={{ fontWeight: 600 }}>{t('common.tax')}:</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>
                    {formatNumber(taxAmount)}
                  </TableCell>
                  <TableCell />
                </TableRow>
                <TableRow sx={{ bgcolor: '#e8f5e9' }}>
                  <TableCell colSpan={5} align="right" sx={{ fontWeight: 700 }}>{t('common.total')}:</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 700 }}>
                    {formatNumber(total)}
                  </TableCell>
                  <TableCell />
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
          <Button startIcon={<AddLineIcon />} onClick={addLine} size="small" sx={{ mt: 1 }}>
            {t('bills.addLine')}
          </Button>
          {hasReverseCharge && (
            <Box sx={{ mt: 1, p: 1, bgcolor: '#e3f2fd', borderRadius: 1, border: '1px solid #bbdefb' }}>
              <Typography variant="body2">
                {t('bills.reverseChargeInfo', 'Omvendt betalingspligt: leverandøren fakturerer uden moms. Du beregner selv momsen (salgsmoms af køb i udlandet) og fratrækker den som købsmoms efter fradragsretten. Regningens total er derfor uden moms.')}
              </Typography>
            </Box>
          )}
          {form.currency !== BASE_CURRENCY && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              {t('bills.currencyInfo', 'Beløbene er i {{cur}} og bogføres i DKK til kurs {{rate}}.', { cur: form.currency, rate: form.exchange_rate })}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          {editing?.status === 'draft' && (
            <Button variant="outlined" color="warning" startIcon={<MoveIcon />} onClick={() => handleMoveToExpenses(editing.id)}>
              {t('bills.moveToExpenses')}
            </Button>
          )}
          <Box sx={{ flex: 1 }} />
          <Button onClick={() => setDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleSave} sx={{ bgcolor: '#2e7d32' }}>
            {editing ? t('common.update') : t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* New Supplier Dialog */}
      <Dialog open={newSupplierOpen} onClose={() => setNewSupplierOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>{t('bills.addNewSupplier')}</DialogTitle>
        <DialogContent>
          <TextField
            label={t('suppliers.title').replace(/s$/, '')}
            value={newSupplierName}
            onChange={e => setNewSupplierName(e.target.value)}
            size="small"
            fullWidth
            autoFocus
            sx={{ mt: 1, mb: 2 }}
            onKeyDown={e => { if (e.key === 'Enter') handleCreateSupplier(); }}
          />
          <Autocomplete
            options={accounts}
            getOptionLabel={(a) => `${a.code} ${a.name}`}
            value={accounts.find(a => a.id === newSupplierAccount) || null}
            onChange={(_, v) => setNewSupplierAccount(v?.id || '')}
            filterOptions={(options, state) => {
              const input = state.inputValue.toLowerCase();
              if (!input) return options.slice(0, 50);
              return options.filter(a =>
                a.name.toLowerCase().includes(input) || a.code.toLowerCase().includes(input)
              ).slice(0, 50);
            }}
            renderOption={(props, a) => (
              <li {...props} key={a.id}>
                <Typography variant="body2" component="span" sx={{ fontFamily: 'monospace', mr: 1 }}>{a.code}</Typography>
                {a.name}
              </li>
            )}
            renderInput={(params) => <TextField {...params} label={t('suppliers.defaultAccount')} size="small" />}
            size="small"
            isOptionEqualToValue={(option, value) => option.id === value.id}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewSupplierOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleCreateSupplier} disabled={!newSupplierName.trim()} sx={{ bgcolor: '#2e7d32' }}>
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {viewing?.bill_number} — {viewing?.supplier_name}
          <Chip
            label={STATUS_LABELS[viewing?.status || ''] || viewing?.status}
            size="small"
            color={STATUS_COLORS[viewing?.status || ''] || 'default'}
            sx={{ ml: 2 }}
          />
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', gap: 3, mb: 2, mt: 1 }}>
            <Typography variant="body2"><strong>{t('common.date')}:</strong> {formatDate(viewing?.date)}</Typography>
            <Typography variant="body2"><strong>{t('bills.dueDate')}:</strong> {formatDate(viewing?.due_date)}</Typography>
            {viewing?.currency && viewing.currency !== BASE_CURRENCY && (
              <Typography variant="body2">
                <strong>{t('bills.currency', 'Valuta')}:</strong> {viewing.currency} ({t('bills.exchangeRate', 'Kurs')} {viewing.exchange_rate})
              </Typography>
            )}
            {viewing?.reference && (
              <Typography variant="body2"><strong>{t('common.reference')}:</strong> {viewing.reference}</Typography>
            )}
          </Box>
          {viewing?.notes && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {viewing.notes}
            </Typography>
          )}
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell sx={{ fontWeight: 600 }}>{t('common.description')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>{t('bills.quantity')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>{t('bills.unitPrice')}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{t('common.account')}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{t('bills.taxCode')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.amount')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {viewing?.lines?.map((line, i) => (
                  <TableRow key={i} hover>
                    <TableCell>{line.description}</TableCell>
                    <TableCell align="right">{line.quantity}</TableCell>
                    <TableCell align="right">
                      {formatNumber(line.unit_price)}
                    </TableCell>
                    <TableCell>
                      {(() => {
                        if (!line.account_id) return '—';
                        const acct = accounts.find(a => a.id === line.account_id);
                        return acct ? `${acct.code} — ${acct.name}` : line.account_id;
                      })()}
                    </TableCell>
                    <TableCell>
                      {(() => {
                        const tc = taxCodes.find(x => x.id === line.tax_code_id);
                        if (!tc) return '—';
                        const hint = taxCodeHint(tc);
                        return hint ? `${tc.code} — ${tc.name} (${hint})` : `${tc.code} — ${tc.name}`;
                      })()}
                    </TableCell>
                    <TableCell align="right">
                      {formatNumber(line.amount)}
                    </TableCell>
                  </TableRow>
                ))}
                <TableRow>
                  <TableCell colSpan={5} align="right" sx={{ fontWeight: 600 }}>{t('common.subtotal')}:</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>
                    {viewing ? formatNumber(viewing.subtotal) : ''}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell colSpan={5} align="right" sx={{ fontWeight: 600 }}>{t('common.tax')}:</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>
                    {viewing ? formatNumber(viewing.tax_amount) : ''}
                  </TableCell>
                </TableRow>
                <TableRow sx={{ bgcolor: '#e8f5e9' }}>
                  <TableCell colSpan={5} align="right" sx={{ fontWeight: 700 }}>{t('common.total')}:</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 700 }}>
                    {viewing ? formatNumber(viewing.total) : ''}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell colSpan={5} align="right" sx={{ fontWeight: 600 }}>{t('bills.amountPaid')}:</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>
                    {viewing ? formatNumber(viewing.paid_amount) : ''}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          {viewing?.status === 'draft' && (
            <Button color="warning" startIcon={<MoveIcon />} onClick={() => handleMoveToExpenses(viewing.id)}>
              {t('bills.moveToExpenses')}
            </Button>
          )}
          <Button onClick={() => setViewDialogOpen(false)}>{t('common.close')}</Button>
        </DialogActions>
      </Dialog>

      {/* Import Dialog */}
      <BillImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onSuccess={() => fetchBills()}
      />
    </Box>
  );
};

export default Bills;
