import React, { useEffect, useState, useMemo } from 'react';
import { formatDate, formatMoney, formatNumber } from '../utils/format';
import { BASE_CURRENCY } from '../utils/chart';
import {
  Box, Typography, Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, MenuItem, Chip, Autocomplete, FormControlLabel, Switch, Checkbox, Alert,
} from '@mui/material';
import {
  Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon,
  ExpandMore, ExpandLess, RemoveRedEye as ViewIcon,
  Upload as UploadIcon, Download as DownloadIcon,
} from '@mui/icons-material';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { exportToCSV } from '../utils/csvExport';
import ImportDialog from '../components/ImportDialog';

interface AccountType {
  id: number;
  name: string;
  normal_balance: string;
}

interface Account {
  id: string;
  code: string;
  name: string;
  account_type_id: number;
  account_type_name: string;
  normal_balance: string;
  parent_id: string | null;
  currency: string;
  standard_code: string;
  arl_line: string;
  arl_line_name: string;
  is_header: boolean;
  description: string;
  is_active: boolean;
}

interface LedgerLine {
  id: string;
  date: string;
  entry_number: string;
  description: string;
  debit: string;
  credit: string;
  currency: string;
  amount_currency: string | null;
  running_balance: string;
}

const TYPE_COLORS: Record<string, string> = {
  Asset: '#1976d2',
  Liability: '#e65100',
  Equity: '#7b1fa2',
  Revenue: '#2e7d32',
  Expense: '#d32f2f',
};

const ChartOfAccounts: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const TYPE_LABELS: Record<string, string> = {
    Asset: t('accounts.typeAsset', 'Aktiv'),
    Liability: t('accounts.typeLiability', 'Gæld'),
    Equity: t('accounts.typeEquity', 'Egenkapital'),
    Revenue: t('accounts.typeRevenue', 'Indtægt'),
    Expense: t('accounts.typeExpense', 'Omkostning'),
  };
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountTypes, setAccountTypes] = useState<AccountType[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Account | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [showInactive, setShowInactive] = useState(false);
  const [search, setSearch] = useState('');
  const [saveError, setSaveError] = useState('');

  // Ledger dialog state
  const [ledgerOpen, setLedgerOpen] = useState(false);
  const [ledgerAccount, setLedgerAccount] = useState<Account | null>(null);
  const [ledgerLines, setLedgerLines] = useState<LedgerLine[]>([]);
  const [ledgerTotalDebit, setLedgerTotalDebit] = useState('0');
  const [ledgerTotalCredit, setLedgerTotalCredit] = useState('0');
  const [ledgerDateFrom, setLedgerDateFrom] = useState('');
  const [ledgerDateTo, setLedgerDateTo] = useState('');

  // Form state
  const [form, setForm] = useState({ code: '', name: '', account_type_id: '', parent_id: '', currency: BASE_CURRENCY, description: '', standard_code: '', is_header: false });

  const fetchData = () => {
    api.get('/accounts').then(res => {
      if (res.data.success) setAccounts(res.data.data.accounts);
    });
    api.get('/accounts/types').then(res => {
      if (res.data.success) setAccountTypes(res.data.data.account_types);
    });
  };

  useEffect(() => { fetchData(); }, []);

  // Handle URL param for drill-down
  useEffect(() => {
    const ledgerId = searchParams.get('ledger');
    if (ledgerId && accounts.length > 0) {
      const acct = accounts.find(a => a.id === ledgerId);
      if (acct) {
        openLedger(acct);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps -- open the ledger from the URL once accounts arrive; openLedger is recreated every render and would reopen it
  }, [searchParams, accounts]);

  const openLedger = (account: Account) => {
    setLedgerAccount(account);
    setLedgerDateFrom('');
    setLedgerDateTo('');
    setLedgerOpen(true);
    fetchLedger(account.id, '', '');
  };

  const fetchLedger = (accountId: string, dateFrom: string, dateTo: string) => {
    const params = new URLSearchParams();
    if (dateFrom) params.set('date_from', dateFrom);
    if (dateTo) params.set('date_to', dateTo);
    const qs = params.toString() ? `?${params.toString()}` : '';
    api.get(`/accounts/${accountId}/ledger${qs}`).then(res => {
      if (res.data.success) {
        setLedgerLines(res.data.data.lines);
        setLedgerTotalDebit(res.data.data.total_debit);
        setLedgerTotalCredit(res.data.data.total_credit);
      }
    });
  };

  const handleLedgerFilter = () => {
    if (ledgerAccount) {
      fetchLedger(ledgerAccount.id, ledgerDateFrom, ledgerDateTo);
    }
  };

  const closeLedger = () => {
    setLedgerOpen(false);
    setLedgerAccount(null);
    setLedgerLines([]);
    // Clear URL param
    if (searchParams.has('ledger')) {
      searchParams.delete('ledger');
      setSearchParams(searchParams, { replace: true });
    }
  };

  const handleOpen = (account?: Account) => {
    if (account) {
      setEditing(account);
      setForm({
        code: account.code,
        name: account.name,
        account_type_id: String(account.account_type_id),
        parent_id: account.parent_id || '',
        currency: account.currency,
        description: account.description,
        standard_code: account.standard_code,
        is_header: account.is_header,
      });
    } else {
      setEditing(null);
      setForm({ code: '', name: '', account_type_id: '', parent_id: '', currency: BASE_CURRENCY, description: '', standard_code: '', is_header: false });
    }
    setSaveError('');
    setDialogOpen(true);
  };

  const handleSave = async () => {
    const payload = {
      ...form,
      account_type_id: parseInt(form.account_type_id),
      parent_id: form.parent_id || null,
    };
    try {
      if (editing) {
        await api.put(`/accounts/${editing.id}`, payload);
      } else {
        await api.post('/accounts', payload);
      }
      setDialogOpen(false);
      fetchData();
    } catch (err: any) {
      setSaveError(err.response?.data?.message || t('accounts.errorSaving'));
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm(t('accounts.deactivateConfirm'))) return;
    await api.delete(`/accounts/${id}`);
    fetchData();
  };

  const toggleExpand = (id: string) => {
    setExpanded(prev => ({ ...prev, [id]: !prev[id] }));
  };

  // Import/Export
  const [importOpen, setImportOpen] = useState(false);

  const handleExportAccounts = () => {
    const headers = ['code', 'name', 'account_type', 'parent_code', 'currency', 'description', 'standard_code', 'arl_line'];
    const codeToAccount = Object.fromEntries(accounts.map(a => [a.id, a]));
    const rows = accounts.map(a => {
      const parent = a.parent_id ? codeToAccount[a.parent_id] : null;
      return [
        a.code, a.name, a.account_type_name, parent ? parent.code : '',
        a.currency, a.description, a.standard_code, a.arl_line,
      ];
    });
    exportToCSV('chart_of_accounts.csv', headers, rows);
  };

  // Build tree structure (memoized to avoid re-rendering table on form keystrokes)
  // Synlige konti: aktive (eller alle) og søgning; overskrifter vises, hvis de har synlige konti under sig.
  const visibleIds = useMemo(() => {
    const q = search.trim().toLowerCase();
    const byId = Object.fromEntries(accounts.map(a => [a.id, a]));
    const ids = new Set<string>();
    for (const a of accounts) {
      if (a.is_header) continue;
      if (!showInactive && !a.is_active) continue;
      if (q && !a.code.toLowerCase().includes(q) && !a.name.toLowerCase().includes(q)
          && !(a.standard_code || '').includes(q)) continue;
      let cur: Account | undefined = a;
      while (cur) {
        ids.add(cur.id);
        cur = cur.parent_id ? byId[cur.parent_id] : undefined;
      }
    }
    return ids;
  }, [accounts, showInactive, search]);

  const childrenMap = useMemo(() => {
    const map: Record<string, Account[]> = {};
    for (const a of accounts.filter(x => visibleIds.has(x.id))) {
      const pid = a.parent_id || '__root__';
      if (!map[pid]) map[pid] = [];
      map[pid].push(a);
    }
    return map;
  }, [accounts, visibleIds]);

  const topLevel = childrenMap['__root__'] || [];
  const childrenOf = (parentId: string) => childrenMap[parentId] || [];

  const renderedRows = useMemo(() => {
    const renderRow = (account: Account, depth: number = 0): React.ReactNode => {
      const children = childrenOf(account.id);
      const hasChildren = children.length > 0;
      const isExpanded = expanded[account.id] !== false;

      return (
        <React.Fragment key={account.id}>
          <TableRow hover sx={{ opacity: account.is_active ? 1 : 0.5, bgcolor: account.is_header ? '#fafafa' : undefined }}>
            <TableCell sx={{ pl: 2 + depth * 3, whiteSpace: 'nowrap' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {hasChildren && (
                  <IconButton size="small" onClick={() => toggleExpand(account.id)} sx={{ p: 0 }}>
                    {isExpanded ? <ExpandLess sx={{ fontSize: 16 }} /> : <ExpandMore sx={{ fontSize: 16 }} />}
                  </IconButton>
                )}
                <Typography variant="body2" sx={{ fontWeight: account.is_header ? 600 : 400, fontFamily: 'monospace' }}>
                  {account.code}
                </Typography>
              </Box>
            </TableCell>
            <TableCell>
              <Typography variant="body2" sx={{ fontWeight: account.is_header ? 600 : 400 }}>
                {account.name}
              </Typography>
            </TableCell>
            <TableCell>
              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{account.standard_code}</Typography>
            </TableCell>
            <TableCell>
              {!account.is_header && <Typography variant="caption">{account.arl_line_name}</Typography>}
            </TableCell>
            <TableCell>
              {account.is_header ? (
                <Typography variant="caption" color="text.secondary">{t('accounts.header', 'Overskrift')}</Typography>
              ) : (
                <Chip
                  label={TYPE_LABELS[account.account_type_name] || account.account_type_name}
                  size="small"
                  sx={{ bgcolor: TYPE_COLORS[account.account_type_name] || '#666', color: '#fff', height: 20, fontSize: '11px' }}
                />
              )}
            </TableCell>
            <TableCell>{account.is_header ? '' : account.currency}</TableCell>
            <TableCell align="right">
              {!account.is_header && (
                <IconButton size="small" onClick={() => openLedger(account)}><ViewIcon sx={{ fontSize: 16 }} /></IconButton>
              )}
              <IconButton size="small" onClick={() => handleOpen(account)}><EditIcon sx={{ fontSize: 16 }} /></IconButton>
              {!account.is_header && (
                <IconButton size="small" onClick={() => handleDelete(account.id)} color="error"><DeleteIcon sx={{ fontSize: 16 }} /></IconButton>
              )}
            </TableCell>
          </TableRow>
          {hasChildren && isExpanded && children.map(child => renderRow(child, depth + 1))}
        </React.Fragment>
      );
    };
    return topLevel.map(a => renderRow(a));
  // eslint-disable-next-line react-hooks/exhaustive-deps -- the row helpers are recreated every render and only read accounts and expanded
  }, [accounts, expanded, visibleIds]);

  // Konti lægges under en overskrift (gruppekonto) i standardkontoplanen.
  const parentOptions = useMemo(() =>
    accounts.filter(a => a.id !== editing?.id && a.is_header),
    [accounts, editing?.id]
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>{t('accounts.title')}</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField size="small" placeholder={t('common.search')} value={search} onChange={e => setSearch(e.target.value)}
            sx={{ width: 200 }} />
          <FormControlLabel
            control={<Switch size="small" checked={showInactive} onChange={e => setShowInactive(e.target.checked)} />}
            label={t('accounts.showInactive', 'Vis inaktive konti')}
          />
          <Button variant="outlined" startIcon={<DownloadIcon />} onClick={handleExportAccounts} size="small">
            {t('importExport.export')}
          </Button>
          <Button variant="outlined" startIcon={<UploadIcon />} onClick={() => setImportOpen(true)} size="small">
            {t('importExport.import')}
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpen()} sx={{ bgcolor: '#2e7d32' }}>
            {t('accounts.addAccount')}
          </Button>
        </Box>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('accounts.introDk', 'Kontoplanen følger Erhvervsstyrelsens standardkontoplan. Hver konto har standardkontoplanens nummer (bruges i SAF-T) og en linje i årsregnskabslovens skema, som rapporterne grupperer efter. Overskrifter kan ikke bogføres på. Inaktive konti kan aktiveres, når der er brug for dem.')}
      </Typography>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.code')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.name')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('accounts.standardCode', 'Standardkonto')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('accounts.arlLine', 'ÅRL-linje')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.type')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.currency')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {renderedRows}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editing ? t('accounts.editAccount') : t('accounts.addAccount')}</DialogTitle>
        <DialogContent>
          {saveError && <Alert severity="error" sx={{ mb: 1 }}>{saveError}</Alert>}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label={t('common.code')} value={form.code} size="small" sx={{ width: 120 }}
                onChange={e => setForm({ ...form, code: e.target.value })}
              />
              <TextField
                label={t('common.name')} value={form.name} size="small" fullWidth
                onChange={e => setForm({ ...form, name: e.target.value })}
              />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label={t('accounts.accountType')} value={form.account_type_id} size="small" select fullWidth
                onChange={e => setForm({ ...form, account_type_id: e.target.value })}
              >
                {accountTypes.map(at => (
                  <MenuItem key={at.id} value={String(at.id)}>{TYPE_LABELS[at.name] || at.name}</MenuItem>
                ))}
              </TextField>
              <TextField
                label={t('common.currency')} value={form.currency} size="small" sx={{ width: 100 }}
                onChange={e => setForm({ ...form, currency: e.target.value })}
              />
            </Box>
            <Autocomplete
              size="small"
              fullWidth
              options={parentOptions}
              value={accounts.find(a => a.id === form.parent_id) || null}
              onChange={(_e, val) => setForm({ ...form, parent_id: val?.id || '' })}
              getOptionLabel={(a) => `${a.code} — ${a.name}`}
              filterOptions={(options, state) => {
                const input = state.inputValue.toLowerCase();
                if (!input) return options.slice(0, 50);
                return options.filter(a =>
                  a.name.toLowerCase().includes(input) || a.code.toLowerCase().includes(input)
                ).slice(0, 50);
              }}
              renderInput={(params) => (
                <TextField {...params} label={t('accounts.parentGroup', 'Gruppe i standardkontoplanen')} placeholder={t('accounts.noParent')} />
              )}
              isOptionEqualToValue={(option, value) => option.id === value.id}
            />
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <TextField
                label={t('accounts.standardCode', 'Standardkonto')} value={form.standard_code} size="small" sx={{ width: 160 }}
                onChange={e => setForm({ ...form, standard_code: e.target.value })}
                helperText={t('accounts.standardCodeHint', 'Tomt = gruppens/eget nummer')}
              />
              <FormControlLabel
                control={<Checkbox size="small" checked={form.is_header} disabled={!!editing}
                  onChange={e => setForm({ ...form, is_header: e.target.checked })} />}
                label={t('accounts.isHeader', 'Overskrift (kan ikke bogføres på)')}
              />
            </Box>
            <TextField
              label={t('common.description')} value={form.description} size="small" multiline rows={2}
              onChange={e => setForm({ ...form, description: e.target.value })}
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

      {/* Ledger Dialog */}
      <Dialog open={ledgerOpen} onClose={closeLedger} maxWidth="lg" fullWidth>
        <DialogTitle>
          {t('accounts.accountLedger')} — {ledgerAccount?.code} {ledgerAccount?.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 2, mt: 1 }}>
            <TextField
              label={t('common.from')} type="date" value={ledgerDateFrom} size="small"
              onChange={e => setLedgerDateFrom(e.target.value)}
              InputLabelProps={{ shrink: true }} sx={{ width: 150 }}
            />
            <TextField
              label={t('common.to')} type="date" value={ledgerDateTo} size="small"
              onChange={e => setLedgerDateTo(e.target.value)}
              InputLabelProps={{ shrink: true }} sx={{ width: 150 }}
            />
            <Button variant="outlined" size="small" onClick={handleLedgerFilter}>
              {t('common.apply')}
            </Button>
          </Box>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell sx={{ fontWeight: 600 }}>{t('common.date')}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{t('accounts.entryNumber')}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{t('common.description')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.debit')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.credit')}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>{t('accounts.runningBalance')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {ledgerLines.map((line) => (
                  <TableRow key={line.id} hover>
                    <TableCell>{formatDate(line.date)}</TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{line.entry_number}</Typography>
                    </TableCell>
                    <TableCell>{line.description}</TableCell>
                    <TableCell align="right">
                      {parseFloat(line.debit) > 0 ? formatNumber(line.debit) : ''}
                    </TableCell>
                    <TableCell align="right">
                      {parseFloat(line.credit) > 0 ? formatNumber(line.credit) : ''}
                      {line.amount_currency && line.currency !== BASE_CURRENCY && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          {formatMoney(line.amount_currency, line.currency)}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 500 }}>
                      {formatNumber(line.running_balance)}
                    </TableCell>
                  </TableRow>
                ))}
                {ledgerLines.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                      <Typography variant="body2" color="text.secondary">{t('accounts.noTransactions')}</Typography>
                    </TableCell>
                  </TableRow>
                )}
                {ledgerLines.length > 0 && (
                  <TableRow sx={{ bgcolor: '#e8f5e9' }}>
                    <TableCell colSpan={3} sx={{ fontWeight: 700 }}>{t('common.totals')}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>
                      {formatNumber(ledgerTotalDebit)}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>
                      {formatNumber(ledgerTotalCredit)}
                    </TableCell>
                    <TableCell />
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeLedger}>{t('common.close')}</Button>
        </DialogActions>
      </Dialog>

      {/* Import Dialog */}
      <ImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onSuccess={fetchData}
        previewEndpoint="/accounts/import/preview"
        confirmEndpoint="/accounts/import/confirm"
        templateColumns={['code', 'name', 'account_type', 'parent_code', 'currency', 'description']}
        entityName={t('accounts.title')}
      />
    </Box>
  );
};

export default ChartOfAccounts;
