import React, { useEffect, useMemo, useState } from 'react';
import {
  Box, Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell, TableContainer, Checkbox, Button,
  TextField, MenuItem, ToggleButton, ToggleButtonGroup, Alert, Chip,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { formatDate, formatNumber } from '../utils/format';
import { BASE_CURRENCY, CUSTOMER_PREPAYMENTS, PAYABLE, RECEIVABLE } from '../utils/chart';

interface Tiers {
  partner_id: string;
  partner_name: string;
  currency: string;
  balance: string;
  open_balance: string;
  open_lines: number;
}

interface Line {
  id: string;
  date: string;
  journal_code: string;
  entry_number: string;
  piece_number: string;
  description: string;
  debit: string;
  credit: string;
  currency: string;
  lettrage: string;
}

const ACCOUNTS = [PAYABLE, RECEIVABLE, CUSTOMER_PREPAYMENTS];

// Udligning: linjer for samme debitor/kreditor, der udligner hinanden (en faktura
// og betalingerne af den), får samme kode. Fuldt betalte regninger og fakturaer
// udlignes automatisk; resten gøres her.
const Lettrage: React.FC = () => {
  const { t } = useTranslation();
  const ACCOUNT_NAMES: Record<string, string> = {
    [PAYABLE]: t('lettrage.payables', 'Kreditorer'),
    [RECEIVABLE]: t('lettrage.receivables', 'Debitorer'),
    [CUSTOMER_PREPAYMENTS]: t('lettrage.prepayments', 'Forudbetalinger fra kunder'),
  };
  const [account, setAccount] = useState(PAYABLE);
  const [tiers, setTiers] = useState<Tiers[]>([]);
  const [filter, setFilter] = useState('');
  const [selectedTiers, setSelectedTiers] = useState<Tiers | null>(null);
  const [state, setState] = useState<'open' | 'lettered'>('open');
  const [lines, setLines] = useState<Line[]>([]);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadTiers = () => {
    api.get(`/tiers?account=${account}`).then(res => {
      if (res.data.success) setTiers(res.data.data.tiers);
    });
  };

  const loadLines = () => {
    if (!selectedTiers) return;
    const q = new URLSearchParams({ account, partner_id: selectedTiers.partner_id, state });
    api.get(`/tiers/lines?${q.toString()}`).then(res => {
      if (res.data.success) setLines(res.data.data.lines);
    });
    setPicked(new Set());
  };

  useEffect(() => {
    setSelectedTiers(null);
    setLines([]);
    loadTiers();
  // eslint-disable-next-line react-hooks/exhaustive-deps -- reload when the account changes
  }, [account]);

  // eslint-disable-next-line react-hooks/exhaustive-deps -- reload when the tiers or the view changes
  useEffect(loadLines, [selectedTiers, state]);

  const shown = useMemo(
    () => tiers.filter(x => x.partner_name.toLowerCase().includes(filter.toLowerCase())),
    [tiers, filter],
  );

  const sum = lines.filter(l => picked.has(l.id))
    .reduce((s, l) => s + parseFloat(l.debit) - parseFloat(l.credit), 0);

  const toggle = (id: string) => {
    const next = new Set(picked);
    if (next.has(id)) next.delete(id); else next.add(id);
    setPicked(next);
  };

  const lettrer = async () => {
    try {
      const res = await api.post('/lettrage', { line_ids: Array.from(picked) });
      setMessage({ type: 'success', text: res.data.message });
      loadLines();
      loadTiers();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Error' });
    }
  };

  const delettrer = async (code: string) => {
    if (!selectedTiers) return;
    try {
      const res = await api.post('/lettrage/undo', { account, partner_id: selectedTiers.partner_id, code });
      setMessage({ type: 'success', text: res.data.message });
      loadLines();
      loadTiers();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Error' });
    }
  };

  const fmt = (v: string | number) => formatNumber(v);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>{t('lettrage.title')}</Typography>
        <TextField select size="small" label={t('common.account')} value={account} sx={{ width: 240 }}
          onChange={e => setAccount(e.target.value)}>
          {ACCOUNTS.map(a => <MenuItem key={a} value={a}>{a} — {ACCOUNT_NAMES[a]}</MenuItem>)}
        </TextField>
      </Box>
      {message && <Alert severity={message.type} sx={{ mb: 2 }} onClose={() => setMessage(null)}>{message.text}</Alert>}

      <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', md: 'row' } }}>
        <Paper sx={{ width: { xs: '100%', md: 340 }, flexShrink: 0, p: 1 }}>
          <TextField size="small" fullWidth placeholder={t('common.search')} value={filter}
            onChange={e => setFilter(e.target.value)} sx={{ mb: 1 }} />
          <Box sx={{ maxHeight: 600, overflow: 'auto' }}>
            <Table size="small">
              <TableBody>
                {shown.map(x => (
                  <TableRow key={`${x.partner_id}-${x.currency}`} hover selected={selectedTiers === x}
                    onClick={() => setSelectedTiers(x)} sx={{ cursor: 'pointer' }}>
                    <TableCell>{x.partner_name}</TableCell>
                    <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                      {fmt(x.open_balance)} {x.currency && x.currency !== BASE_CURRENCY ? x.currency : ''}
                      {x.open_lines > 0 && <Chip size="small" label={x.open_lines} sx={{ ml: 1, height: 18 }} />}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        </Paper>

        <Paper sx={{ flex: 1, p: 1, minWidth: 0 }}>
          {!selectedTiers && <Typography color="text.secondary" sx={{ p: 2 }}>{t('lettrage.pickTiers')}</Typography>}
          {selectedTiers && (
            <>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1, flexWrap: 'wrap' }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{selectedTiers.partner_name}</Typography>
                <ToggleButtonGroup size="small" exclusive value={state} onChange={(_, v) => v && setState(v)}>
                  <ToggleButton value="open">{t('lettrage.open')}</ToggleButton>
                  <ToggleButton value="lettered">{t('lettrage.lettered')}</ToggleButton>
                </ToggleButtonGroup>
                <Box sx={{ flex: 1 }} />
                {state === 'open' && (
                  <>
                    <Typography variant="body2" color={Math.abs(sum) < 0.005 && picked.size > 1 ? 'success.main' : 'text.secondary'}>
                      {t('lettrage.selected', { count: picked.size })} · {t('lettrage.difference')}: {fmt(sum)}
                    </Typography>
                    <Button variant="contained" size="small" onClick={lettrer}
                      disabled={picked.size < 2 || Math.abs(sum) >= 0.005}>
                      {t('lettrage.lettrer')}
                    </Button>
                  </>
                )}
              </Box>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                      {state === 'open' && <TableCell padding="checkbox" />}
                      <TableCell sx={{ fontWeight: 600 }}>{t('common.date')}</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>{t('journal.journal')}</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>{t('accounts.entryNumber')}</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>{t('journal.piece')}</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>{t('common.description')}</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.debit')}</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.credit')}</TableCell>
                      {state === 'lettered' && <TableCell sx={{ fontWeight: 600 }}>{t('lettrage.code')}</TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {lines.map(l => (
                      <TableRow key={l.id} hover onClick={() => state === 'open' && toggle(l.id)}
                        sx={{ cursor: state === 'open' ? 'pointer' : 'default' }}>
                        {state === 'open' && (
                          <TableCell padding="checkbox"><Checkbox size="small" checked={picked.has(l.id)} /></TableCell>
                        )}
                        <TableCell>{formatDate(l.date)}</TableCell>
                        <TableCell sx={{ fontFamily: 'monospace' }}>{l.journal_code}</TableCell>
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: 12 }}>{l.entry_number}</TableCell>
                        <TableCell>{l.piece_number}</TableCell>
                        <TableCell>{l.description}</TableCell>
                        <TableCell align="right">{parseFloat(l.debit) ? fmt(l.debit) : ''}</TableCell>
                        <TableCell align="right">{parseFloat(l.credit) ? fmt(l.credit) : ''}</TableCell>
                        {state === 'lettered' && (
                          <TableCell>
                            <Chip size="small" label={l.lettrage} onDelete={() => delettrer(l.lettrage)} />
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                    {lines.length === 0 && (
                      <TableRow><TableCell colSpan={9} align="center" sx={{ py: 3, color: 'text.secondary' }}>
                        {t('lettrage.noLines')}
                      </TableCell></TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}
        </Paper>
      </Box>
    </Box>
  );
};

export default Lettrage;
