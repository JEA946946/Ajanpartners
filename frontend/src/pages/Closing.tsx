import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell, TableContainer, Button, Chip,
  TextField, Dialog, DialogTitle, DialogContent, DialogActions, Alert, List, ListItem,
} from '@mui/material';
import { Lock as LockIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';

interface Month {
  year: number;
  month: number;
  closed: boolean;
  closed_at: string | null;
  closed_by: string;
  entries: number;
  brouillard: number;
  drafts: number;
  validated: number;
}

interface Check {
  blockers: string[];
  warnings: string[];
  entries?: number;
}

// Month closing (clôture mensuelle): validates and numbers every entry of the
// month for good. Months close in order and cannot be reopened.
const Closing: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [year, setYear] = useState(new Date().getFullYear());
  const [months, setMonths] = useState<Month[]>([]);
  const [next, setNext] = useState<{ year: number; month: number } | null>(null);
  const [checking, setChecking] = useState<Month | null>(null);
  const [check, setCheck] = useState<Check | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  const load = () => {
    api.get(`/periods?year=${year}`).then(res => {
      if (res.data.success) {
        setMonths(res.data.data.months);
        setNext(res.data.data.next_to_close);
      }
    });
  };

  useEffect(load, [year]);

  const monthName = (m: number) =>
    new Date(2000, m - 1, 1).toLocaleString(i18n.language, { month: 'long' });

  const openCheck = (m: Month) => {
    setChecking(m);
    setCheck(null);
    setMessage('');
    api.get(`/periods/check?year=${m.year}&month=${m.month}`).then(res => {
      if (res.data.success) setCheck(res.data.data);
    });
  };

  const close = async () => {
    if (!checking) return;
    setBusy(true);
    try {
      const res = await api.post('/periods/close', {
        year: checking.year, month: checking.month, confirm_warnings: true,
      });
      setMessage(res.data.message);
      setChecking(null);
      load();
    } catch (err: any) {
      setCheck(err.response?.data?.data || check);
      setMessage(err.response?.data?.message || t('closing.error'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>{t('closing.title')}</Typography>
        <TextField
          label={t('closing.year')} type="number" size="small" value={year} sx={{ width: 110 }}
          onChange={e => setYear(parseInt(e.target.value, 10) || year)}
        />
      </Box>
      <Alert severity="info" sx={{ mb: 2 }}>{t('closing.intro')}</Alert>
      {message && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMessage('')}>{message}</Alert>}

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell sx={{ fontWeight: 600 }}>{t('closing.month')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('closing.entries')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('journal.status.brouillard')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('journal.status.draft')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('journal.status.validated')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.status')}</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {months.map(m => {
              const isNext = next && next.year === m.year && next.month === m.month;
              return (
                <TableRow key={m.month} hover>
                  <TableCell sx={{ textTransform: 'capitalize' }}>{monthName(m.month)} {m.year}</TableCell>
                  <TableCell align="right">{m.entries}</TableCell>
                  <TableCell align="right">{m.brouillard}</TableCell>
                  <TableCell align="right">{m.drafts}</TableCell>
                  <TableCell align="right">{m.validated}</TableCell>
                  <TableCell>
                    {m.closed ? (
                      <Chip size="small" icon={<LockIcon />} color="success"
                        label={t('closing.closedBy', { who: m.closed_by, date: (m.closed_at || '').slice(0, 10) })} />
                    ) : (
                      <Chip size="small" variant="outlined" label={t('closing.open')} />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {!m.closed && (
                      <Button size="small" variant={isNext ? 'contained' : 'outlined'} onClick={() => openCheck(m)}>
                        {t('closing.closeMonth')}
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={!!checking} onClose={() => setChecking(null)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ textTransform: 'capitalize' }}>
          {t('closing.closeMonth')} — {checking && `${monthName(checking.month)} ${checking.year}`}
        </DialogTitle>
        <DialogContent>
          {!check && <Typography variant="body2">{t('common.loading')}</Typography>}
          {check && check.blockers.length === 0 && check.warnings.length === 0 && (
            <Alert severity="success">{t('closing.ready', { count: check.entries ?? 0 })}</Alert>
          )}
          {check && check.blockers.length > 0 && (
            <Alert severity="error" sx={{ mb: 1 }}>
              {t('closing.blocked')}
              <List dense>{check.blockers.map(b => <ListItem key={b}>• {b}</ListItem>)}</List>
            </Alert>
          )}
          {check && check.warnings.length > 0 && (
            <Alert severity="warning">
              {t('closing.warnings')}
              <List dense>{check.warnings.map(w => <ListItem key={w}>• {w}</ListItem>)}</List>
            </Alert>
          )}
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            {t('closing.final')}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChecking(null)}>{t('common.cancel')}</Button>
          <Button variant="contained" color="success" startIcon={<LockIcon />} onClick={close}
            disabled={busy || !check || check.blockers.length > 0}>
            {check && check.warnings.length > 0 ? t('closing.confirmAndClose') : t('closing.closeMonth')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Closing;
