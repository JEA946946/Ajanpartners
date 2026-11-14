import React, { useEffect, useState } from 'react';
import { formatDate } from '../utils/dateFormat';
import {
  Box, Typography, Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, MenuItem, Chip, Tooltip, TablePagination,
} from '@mui/material';
import {
  Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon,
  CheckCircle as PostIcon, Cancel as UnpostIcon, RemoveRedEye as ViewIcon,
  AddCircleOutline as AddLineIcon, RemoveCircleOutline as RemoveLineIcon,
  Search as SearchIcon, Download as DownloadIcon, Undo as ReverseIcon, AttachFile as AttachIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { downloadBlob } from '../utils/csvExport';
import TiersPicker from '../components/TiersPicker';

interface Account {
  id: string;
  code: string;
  name: string;
}

interface JournalLine {
  id?: string;
  account_id: string;
  account_code?: string;
  account_name?: string;
  debit: string;
  credit: string;
  description: string;
  partner_id?: string;
  partner_name?: string;
}

// Lines on these accounts need their customer or supplier (compte auxiliaire).
const TIERS_KIND: Record<string, 'customer' | 'supplier'> = { '3421': 'customer', '4421': 'customer', '4411': 'supplier' };

interface Journal {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
}

// draft: not in the books yet; brouillard: in the books, still editable;
// validated: its month is closed — numbered for good and never changed.
type EntryStatus = 'draft' | 'brouillard' | 'validated';

const STATUS_COLOR: Record<EntryStatus, string> = { draft: '#ed6c02', brouillard: '#1976d2', validated: '#2e7d32' };

interface JournalEntry {
  id: string;
  entry_number: string;
  journal_id: number;
  journal_code: string;
  piece_number: string;
  status: EntryStatus;
  reversal_of: string | null;
  reversed_by: string | null;
  date: string;
  description: string;
  reference: string;
  source: string;
  is_posted: boolean;
  documents: number;
  document_list?: { id: string; filename: string; piece_number: string }[];
  total_debit: string;
  total_credit: string;
  is_balanced: boolean;
  lines?: JournalLine[];
}

const EMPTY_LINE: JournalLine = { account_id: '', debit: '0', credit: '0', description: '' };

const JournalEntries: React.FC = () => {
  const { t, i18n } = useTranslation();

  const SOURCE_OPTIONS = [
    { value: '', label: t('journal.allSources') },
    { value: 'manual', label: t('journal.manual') },
    { value: 'bank', label: t('journal.bankSource') },
    { value: 'cmr_invoice', label: t('journal.cmrInvoice') },
    { value: 'cmr_payment', label: t('journal.cmrPayment') },
    { value: 'margin_recognition', label: t('journal.marginRecognition') },
    { value: 'tva_margin', label: t('journal.tvaMargin') },
  ];

  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [journals, setJournals] = useState<Journal[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [editing, setEditing] = useState<JournalEntry | null>(null);
  const [viewing, setViewing] = useState<JournalEntry | null>(null);
  const [autoRepost, setAutoRepost] = useState(false);
  const [fontSize, setFontSize] = useState(() => {
    const saved = localStorage.getItem('journalFontSize');
    return saved ? parseFloat(saved) : 0.7;
  });

  // Filter state
  const [filterDateFrom, setFilterDateFrom] = useState('');
  const [filterDateTo, setFilterDateTo] = useState('');
  const [filterSource, setFilterSource] = useState('');
  const [filterPosted, setFilterPosted] = useState('');
  const [filterJournal, setFilterJournal] = useState('');
  const [filterSearch, setFilterSearch] = useState('');

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [totalCount, setTotalCount] = useState(0);

  // Form state
  const [form, setForm] = useState({ date: '', description: '', reference: '', piece_number: '', journal_code: 'OD' });
  const [lines, setLines] = useState<JournalLine[]>([{ ...EMPTY_LINE }, { ...EMPTY_LINE }]);

  useEffect(() => {
    localStorage.setItem('journalFontSize', fontSize.toString());
  }, [fontSize]);

  const fetchEntries = (p?: number) => {
    const params = new URLSearchParams();
    if (filterDateFrom) params.set('date_from', filterDateFrom);
    if (filterDateTo) params.set('date_to', filterDateTo);
    if (filterSource) params.set('source', filterSource);
    if (filterPosted) params.set('status', filterPosted);
    if (filterJournal) params.set('journal', filterJournal);
    if (filterSearch) params.set('search', filterSearch);
    const currentPage = p !== undefined ? p : page;
    params.set('page', String(currentPage + 1));
    params.set('page_size', String(rowsPerPage));
    const qs = params.toString() ? `?${params.toString()}` : '';
    api.get(`/journal-entries${qs}`).then(res => {
      if (res.data.success) {
        setEntries(res.data.data.journal_entries);
        setTotalCount(res.data.data.total_count ?? res.data.data.count ?? 0);
      }
    });
  };

  useEffect(() => {
    fetchEntries();
    api.get('/accounts?is_active=true').then(res => {
      if (res.data.success) setAccounts(res.data.data.accounts);
    });
    api.get('/journals').then(res => {
      if (res.data.success) setJournals(res.data.data.journals);
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps -- load once on mount; filters apply when the user presses Search
  }, []);

  const handleApplyFilters = () => {
    setPage(0);
    fetchEntries(0);
  };

  const handleExportJournalEntries = async () => {
    const params = new URLSearchParams();
    if (filterDateFrom) params.set('date_from', filterDateFrom);
    if (filterDateTo) params.set('date_to', filterDateTo);
    if (filterSource) params.set('source', filterSource);
    if (filterPosted) params.set('status', filterPosted);
    if (filterJournal) params.set('journal', filterJournal);
    if (filterSearch) params.set('search', filterSearch);
    const qs = params.toString() ? `?${params.toString()}` : '';
    try {
      const res = await api.get(`/journal-entries/export${qs}`, { responseType: 'blob' });
      downloadBlob(new Blob([res.data]), 'journal_entries.csv');
    } catch { /* ignore */ }
  };

  const handlePageChange = (_: unknown, newPage: number) => {
    setPage(newPage);
    fetchEntries(newPage);
  };

  const handleRowsPerPageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newSize = parseInt(e.target.value, 10);
    setRowsPerPage(newSize);
    setPage(0);
    setTimeout(() => fetchEntries(0), 0);
  };

  const handleOpen = async (entry?: JournalEntry) => {
    if (entry) {
      const res = await api.get(`/journal-entries/${entry.id}`);
      if (res.data.success) {
        const full = res.data.data.journal_entry;
        setEditing(full);
        setForm({ date: full.date, description: full.description, reference: full.reference,
                  piece_number: full.piece_number || '', journal_code: full.journal_code });
        setLines(full.lines.map((l: JournalLine) => ({
          account_id: l.account_id,
          debit: l.debit,
          credit: l.credit,
          description: l.description,
          partner_id: l.partner_id,
          partner_name: l.partner_name,
        })));
      }
    } else {
      setEditing(null);
      setForm({ date: new Date().toISOString().split('T')[0], description: '', reference: '', piece_number: '',
                journal_code: 'OD' });
      setLines([{ ...EMPTY_LINE }, { ...EMPTY_LINE }]);
    }
    setDialogOpen(true);
  };

  const handleEditPosted = async (entry: JournalEntry) => {
    try {
      await api.post(`/journal-entries/${entry.id}/unpost`);
      setAutoRepost(true);
      await handleOpen({ ...entry, is_posted: false });
    } catch (err: any) {
      alert(err.response?.data?.message || t('journal.errorUnposting'));
    }
  };

  const handleView = async (entry: JournalEntry) => {
    const res = await api.get(`/journal-entries/${entry.id}`);
    if (res.data.success) {
      setViewing(res.data.data.journal_entry);
      setViewDialogOpen(true);
    }
  };

  const handleSave = async () => {
    const payload = {
      ...form,
      lines: lines.filter(l => l.account_id),
    };
    try {
      if (editing) {
        await api.put(`/journal-entries/${editing.id}`, payload);
        if (autoRepost) {
          await api.post(`/journal-entries/${editing.id}/post`);
        }
      } else {
        await api.post('/journal-entries', payload);
      }
      setDialogOpen(false);
      setAutoRepost(false);
      fetchEntries();
    } catch (err: any) {
      alert(err.response?.data?.message || t('journal.errorSaving'));
    }
  };

  const handleDialogClose = () => {
    if (autoRepost && editing) {
      // Re-post if user cancels editing a posted entry
      api.post(`/journal-entries/${editing.id}/post`).catch(() => {});
    }
    setDialogOpen(false);
    setAutoRepost(false);
    fetchEntries();
  };

  const handleDelete = async (id: string) => {
    if (!confirm(t('journal.deleteConfirm'))) return;
    try {
      await api.delete(`/journal-entries/${id}`);
      fetchEntries();
    } catch (err: any) {
      alert(err.response?.data?.message || t('journal.errorDeleting'));
    }
  };

  const handlePost = async (id: string) => {
    try {
      await api.post(`/journal-entries/${id}/post`);
      fetchEntries();
    } catch (err: any) {
      alert(err.response?.data?.message || t('journal.errorPosting'));
    }
  };

  const handleUnpost = async (id: string) => {
    try {
      await api.post(`/journal-entries/${id}/unpost`);
      fetchEntries();
    } catch (err: any) {
      alert(err.response?.data?.message || t('journal.errorUnpostingEntry'));
    }
  };

  // Pièce justificative attached to the entry being viewed.
  const handleAttach = async (file: File | undefined) => {
    if (!file || !viewing) return;
    const body = new FormData();
    body.append('file', file);
    body.append('journal_entry_id', viewing.id);
    body.append('piece_number', viewing.piece_number || '');
    try {
      await api.post('/documents', body, { headers: { 'Content-Type': 'multipart/form-data' } });
      await handleView(viewing);
      fetchEntries();
    } catch (err: any) {
      alert(err.response?.data?.message || t('journal.errorSaving'));
    }
  };

  const openDocument = async (id: string) => {
    const res = await api.get(`/documents/${id}/download`, { responseType: 'blob' });
    window.open(URL.createObjectURL(res.data), '_blank');
  };

  const handleReverse = async (entry: JournalEntry) => {
    if (!confirm(t('journal.reverseConfirm', { number: entry.entry_number }))) return;
    try {
      const res = await api.post(`/journal-entries/${entry.id}/reverse`, { date: new Date().toISOString().split('T')[0] });
      alert(res.data.message);
      fetchEntries();
    } catch (err: any) {
      alert(err.response?.data?.message || t('journal.errorSaving'));
    }
  };

  const tiersKind = (accountId: string) => TIERS_KIND[accounts.find(a => a.id === accountId)?.code || ''];

  const setLineTiers = (index: number, v: { id: string; name: string } | null) => {
    setLines(prev => prev.map((l, i) => i === index ? { ...l, partner_id: v?.id || '', partner_name: v?.name || '' } : l));
  };

  const updateLine = (index: number, field: keyof JournalLine, value: string) => {
    setLines(prev => prev.map((l, i) => i === index ? { ...l, [field]: value } : l));
  };

  const addLine = () => setLines(prev => [...prev, { ...EMPTY_LINE }]);
  const removeLine = (index: number) => {
    if (lines.length <= 2) return;
    setLines(prev => prev.filter((_, i) => i !== index));
  };

  const totalDebit = lines.reduce((sum, l) => sum + parseFloat(l.debit || '0'), 0);
  const totalCredit = lines.reduce((sum, l) => sum + parseFloat(l.credit || '0'), 0);
  const isBalanced = Math.abs(totalDebit - totalCredit) < 0.01;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>{t('journal.title')}</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', border: '1px solid #ddd', borderRadius: 1, px: 0.5 }}>
            <IconButton size="small" onClick={() => setFontSize(prev => Math.max(0.5, prev - 0.05))} sx={{ p: 0.3 }}>
              <RemoveLineIcon sx={{ fontSize: 16 }} />
            </IconButton>
            <Typography sx={{ fontSize: '0.7rem', mx: 0.5, minWidth: 20, textAlign: 'center' }}>
              {Math.round(fontSize * 100)}%
            </Typography>
            <IconButton size="small" onClick={() => setFontSize(prev => Math.min(1, prev + 0.05))} sx={{ p: 0.3 }}>
              <AddLineIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Box>
          <Button variant="outlined" startIcon={<DownloadIcon />} onClick={handleExportJournalEntries} size="small">
            {t('importExport.export')}
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpen()} sx={{ bgcolor: '#2e7d32' }}>
            {t('journal.newEntry')}
          </Button>
        </Box>
      </Box>

      {/* Filter Bar */}
      <Paper sx={{ p: 1.5, mb: 2, display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
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
          select label={t('journal.source')} value={filterSource} size="small"
          onChange={e => setFilterSource(e.target.value)}
          sx={{ width: 150 }}
        >
          {SOURCE_OPTIONS.map(o => (
            <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
          ))}
        </TextField>
        <TextField
          select label={t('journal.journal')} value={filterJournal} size="small"
          onChange={e => setFilterJournal(e.target.value)}
          sx={{ width: 170 }}
        >
          <MenuItem value="">{t('common.all')}</MenuItem>
          {journals.map(j => <MenuItem key={j.code} value={j.code}>{j.code} — {j.name}</MenuItem>)}
        </TextField>
        <TextField
          select label={t('common.status')} value={filterPosted} size="small"
          onChange={e => setFilterPosted(e.target.value)}
          sx={{ width: 140 }}
        >
          <MenuItem value="">{t('common.all')}</MenuItem>
          <MenuItem value="draft">{t('journal.status.draft')}</MenuItem>
          <MenuItem value="brouillard">{t('journal.status.brouillard')}</MenuItem>
          <MenuItem value="validated">{t('journal.status.validated')}</MenuItem>
        </TextField>
        <TextField
          label={t('common.search')} value={filterSearch} size="small"
          onChange={e => setFilterSearch(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleApplyFilters()}
          sx={{ width: 180 }}
          InputProps={{ endAdornment: <SearchIcon sx={{ fontSize: 18, color: 'text.secondary' }} /> }}
        />
        <Button variant="outlined" size="small" onClick={handleApplyFilters}>
          {t('common.apply')}
        </Button>
      </Paper>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell sx={{ fontWeight: 600, fontSize: `${fontSize}rem`, py: 0.5, whiteSpace: 'nowrap' }}>{t('journal.journal')}</TableCell>
              <TableCell sx={{ fontWeight: 600, fontSize: `${fontSize}rem`, py: 0.5, whiteSpace: 'nowrap' }}>{t('accounts.entryNumber')}</TableCell>
              <TableCell sx={{ fontWeight: 600, fontSize: `${fontSize}rem`, py: 0.5, whiteSpace: 'nowrap' }}>{t('common.date')}</TableCell>
              <TableCell sx={{ fontWeight: 600, fontSize: `${fontSize}rem`, py: 0.5, whiteSpace: 'nowrap' }}>{t('journal.piece')}</TableCell>
              <TableCell sx={{ fontWeight: 600, fontSize: `${fontSize}rem`, py: 0.5, whiteSpace: 'nowrap' }}>{t('common.description')}</TableCell>
              <TableCell sx={{ fontWeight: 600, fontSize: `${fontSize}rem`, py: 0.5, whiteSpace: 'nowrap' }}>{t('common.reference')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600, fontSize: `${fontSize}rem`, py: 0.5, whiteSpace: 'nowrap' }}>{t('common.debit')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600, fontSize: `${fontSize}rem`, py: 0.5, whiteSpace: 'nowrap' }}>{t('common.credit')}</TableCell>
              <TableCell sx={{ fontWeight: 600, fontSize: `${fontSize}rem`, py: 0.5, whiteSpace: 'nowrap' }}>{t('common.status')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600, fontSize: `${fontSize}rem`, py: 0.5, whiteSpace: 'nowrap' }}>{t('common.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {entries.map(entry => (
              <TableRow key={entry.id} hover sx={{ '& td': { fontSize: `${fontSize}rem`, py: 0.3, whiteSpace: 'nowrap' } }}>
                <TableCell sx={{ fontFamily: 'monospace' }}>{entry.journal_code}</TableCell>
                <TableCell>
                  <Typography sx={{ fontFamily: 'monospace', fontWeight: 500, fontSize: `${fontSize}rem` }}>
                    {entry.entry_number}
                  </Typography>
                </TableCell>
                <TableCell>{formatDate(entry.date)}</TableCell>
                <TableCell>
                  {entry.piece_number}
                  {entry.documents > 0 && <AttachIcon sx={{ fontSize: 12, ml: 0.5, verticalAlign: 'middle' }} />}
                </TableCell>
                <TableCell>{entry.description}</TableCell>
                <TableCell>{entry.reference}</TableCell>
                <TableCell align="right">{parseFloat(entry.total_debit).toLocaleString(i18n.language)}</TableCell>
                <TableCell align="right">{parseFloat(entry.total_credit).toLocaleString(i18n.language)}</TableCell>
                <TableCell>
                  <Chip
                    label={t(`journal.status.${entry.status}`) + (entry.reversed_by ? ` · ${t('journal.reversedBy', { number: entry.reversed_by })}` : '')}
                    size="small"
                    sx={{
                      bgcolor: STATUS_COLOR[entry.status],
                      color: '#fff', height: `${fontSize * 1.4}rem`, fontSize: `${fontSize - 0.05}rem`,
                      '& .MuiChip-label': { px: 0.8, fontSize: `${fontSize - 0.05}rem` },
                    }}
                  />
                </TableCell>
                <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                  <Tooltip title={t('common.view')}><IconButton size="small" sx={{ p: 0.3 }} onClick={() => handleView(entry)}><ViewIcon sx={{ fontSize: 14 }} /></IconButton></Tooltip>
                  {!entry.is_posted && (
                    <>
                      <Tooltip title={t('common.edit')}><IconButton size="small" sx={{ p: 0.3 }} onClick={() => handleOpen(entry)}><EditIcon sx={{ fontSize: 14 }} /></IconButton></Tooltip>
                      <Tooltip title={t('journal.post')}><IconButton size="small" sx={{ p: 0.3 }} color="success" onClick={() => handlePost(entry.id)}><PostIcon sx={{ fontSize: 14 }} /></IconButton></Tooltip>
                      <Tooltip title={t('common.delete')}><IconButton size="small" sx={{ p: 0.3 }} color="error" onClick={() => handleDelete(entry.id)}><DeleteIcon sx={{ fontSize: 14 }} /></IconButton></Tooltip>
                    </>
                  )}
                  {entry.status === 'brouillard' && entry.source === 'manual' && (
                    <>
                      <Tooltip title={t('journal.editUnpostRepost')}><IconButton size="small" sx={{ p: 0.3 }} onClick={() => handleEditPosted(entry)}><EditIcon sx={{ fontSize: 14 }} /></IconButton></Tooltip>
                      <Tooltip title={t('journal.unpost')}><IconButton size="small" sx={{ p: 0.3 }} color="warning" onClick={() => handleUnpost(entry.id)}><UnpostIcon sx={{ fontSize: 14 }} /></IconButton></Tooltip>
                    </>
                  )}
                  {entry.status === 'validated' && !entry.reversed_by && entry.source !== 'reversal' && (
                    <Tooltip title={t('journal.reverse')}><IconButton size="small" sx={{ p: 0.3 }} color="warning" onClick={() => handleReverse(entry)}><ReverseIcon sx={{ fontSize: 14 }} /></IconButton></Tooltip>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {entries.length === 0 && (
              <TableRow>
                <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                  <Typography variant="body2" color="text.secondary">{t('journal.noEntries')}</Typography>
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
        />
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleDialogClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {editing ? t('journal.editEntry', { number: editing.entry_number }) : t('journal.newJournalEntry')}
          {autoRepost && (
            <Chip label={t('journal.willAutoRepost')} size="small" color="info" sx={{ ml: 2, height: 20, fontSize: '11px' }} />
          )}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', gap: 2, mt: 1, mb: 2 }}>
            <TextField
              select label={t('journal.journal')} value={form.journal_code} size="small" sx={{ width: 200 }}
              onChange={e => setForm({ ...form, journal_code: e.target.value })}
            >
              {journals.filter(j => j.is_active).map(j => <MenuItem key={j.code} value={j.code}>{j.code} — {j.name}</MenuItem>)}
            </TextField>
            <TextField
              label={t('common.date')} type="date" value={form.date} size="small"
              onChange={e => setForm({ ...form, date: e.target.value })}
              InputLabelProps={{ shrink: true }} sx={{ width: 160 }}
            />
            <TextField
              label={t('common.description')} value={form.description} size="small" fullWidth
              onChange={e => setForm({ ...form, description: e.target.value })}
            />
            <TextField
              label={t('journal.piece')} value={form.piece_number} size="small" sx={{ width: 160 }}
              onChange={e => setForm({ ...form, piece_number: e.target.value })}
            />
            <TextField
              label={t('common.reference')} value={form.reference} size="small" sx={{ width: 160 }}
              onChange={e => setForm({ ...form, reference: e.target.value })}
            />
          </Box>

          {/* Lines */}
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>{t('journal.entryLines')}</Typography>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                <TableCell sx={{ fontWeight: 600, width: '40%' }}>{t('common.account')}</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>{t('common.description')}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.debit')}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.credit')}</TableCell>
                <TableCell sx={{ width: 40 }} />
              </TableRow>
            </TableHead>
            <TableBody>
              {lines.map((line, i) => (
                <TableRow key={i}>
                  <TableCell sx={{ p: 0.5 }}>
                    <TextField
                      select value={line.account_id} size="small" fullWidth
                      onChange={e => updateLine(i, 'account_id', e.target.value)}
                    >
                      {accounts.map(a => (
                        <MenuItem key={a.id} value={a.id}>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', mr: 1 }}>{a.code}</Typography>
                          {a.name}
                        </MenuItem>
                      ))}
                    </TextField>
                    {tiersKind(line.account_id) && (
                      <Box sx={{ mt: 0.5 }}>
                        <TiersPicker
                          kind={tiersKind(line.account_id)}
                          value={line.partner_id ? { id: line.partner_id, name: line.partner_name || '' } : null}
                          onChange={v => setLineTiers(i, v)}
                        />
                      </Box>
                    )}
                  </TableCell>
                  <TableCell sx={{ p: 0.5 }}>
                    <TextField
                      value={line.description} size="small" fullWidth
                      onChange={e => updateLine(i, 'description', e.target.value)}
                    />
                  </TableCell>
                  <TableCell sx={{ p: 0.5 }}>
                    <TextField
                      value={line.debit} size="small" type="number" sx={{ width: 100 }}
                      onChange={e => updateLine(i, 'debit', e.target.value)}
                      inputProps={{ min: 0, step: '0.01' }}
                    />
                  </TableCell>
                  <TableCell sx={{ p: 0.5 }}>
                    <TextField
                      value={line.credit} size="small" type="number" sx={{ width: 100 }}
                      onChange={e => updateLine(i, 'credit', e.target.value)}
                      inputProps={{ min: 0, step: '0.01' }}
                    />
                  </TableCell>
                  <TableCell sx={{ p: 0.5 }}>
                    <IconButton size="small" onClick={() => removeLine(i)} disabled={lines.length <= 2}>
                      <RemoveLineIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {/* Totals row */}
              <TableRow>
                <TableCell colSpan={2} align="right" sx={{ fontWeight: 600 }}>{t('common.totals') + ':'}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>{totalDebit.toFixed(2)}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>{totalCredit.toFixed(2)}</TableCell>
                <TableCell />
              </TableRow>
              {!isBalanced && (
                <TableRow>
                  <TableCell colSpan={5}>
                    <Typography variant="caption" color="error">
                      {t('journal.notBalanced', { diff: Math.abs(totalDebit - totalCredit).toFixed(2) })}
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          <Button startIcon={<AddLineIcon />} onClick={addLine} size="small" sx={{ mt: 1 }}>
            {t('journal.addLine')}
          </Button>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleSave} disabled={!isBalanced} sx={{ bgcolor: '#2e7d32' }}>
            {editing ? (autoRepost ? t('journal.updateAndRepost') : t('common.update')) : t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {viewing?.journal_code} · {viewing?.entry_number} — {viewing?.date}
          {viewing && (
            <Chip
              label={t(`journal.status.${viewing.status}`)}
              size="small"
              sx={{ ml: 2, bgcolor: STATUS_COLOR[viewing.status], color: '#fff' }}
            />
          )}
        </DialogTitle>
        <DialogContent>
          {viewing?.description && (
            <Typography variant="body2" sx={{ mb: 1 }}>{viewing.description}</Typography>
          )}
          {(viewing?.reference || viewing?.piece_number) && (
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              {viewing.piece_number && <>{t('journal.piece')}: {viewing.piece_number} · </>}Ref: {viewing.reference}
            </Typography>
          )}
          {viewing?.reversal_of && (
            <Typography variant="caption" color="warning.main" sx={{ mb: 1, display: 'block' }}>
              {t('journal.reversalOf', { number: viewing.reversal_of })}
            </Typography>
          )}
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                <TableCell sx={{ fontWeight: 600 }}>{t('common.account')}</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>{t('common.description')}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.debit')}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.credit')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {viewing?.lines?.map((line, i) => (
                <TableRow key={i}>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {line.account_code} — {line.account_name}
                    </Typography>
                    {line.partner_name && (
                      <Typography variant="caption" color="text.secondary">{line.partner_name}</Typography>
                    )}
                  </TableCell>
                  <TableCell>{line.description}</TableCell>
                  <TableCell align="right">{parseFloat(line.debit) > 0 ? parseFloat(line.debit).toLocaleString(i18n.language) : ''}</TableCell>
                  <TableCell align="right">{parseFloat(line.credit) > 0 ? parseFloat(line.credit).toLocaleString(i18n.language) : ''}</TableCell>
                </TableRow>
              ))}
              <TableRow>
                <TableCell colSpan={2} align="right" sx={{ fontWeight: 600 }}>{t('common.totals') + ':'}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>
                  {viewing ? parseFloat(viewing.total_debit).toLocaleString(i18n.language) : ''}
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>
                  {viewing ? parseFloat(viewing.total_credit).toLocaleString(i18n.language) : ''}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <Typography variant="subtitle2">{t('journal.documents')}:</Typography>
            {(viewing?.document_list || []).map(d => (
              <Chip key={d.id} size="small" icon={<AttachIcon />} label={d.filename} onClick={() => openDocument(d.id)} />
            ))}
            {(viewing?.document_list || []).length === 0 && (
              <Typography variant="caption" color="text.secondary">{t('journal.noDocuments')}</Typography>
            )}
            <Button size="small" component="label" startIcon={<AttachIcon />}>
              {t('journal.attachDocument')}
              <input hidden type="file" onChange={e => handleAttach(e.target.files?.[0])} />
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>{t('common.close')}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default JournalEntries;
