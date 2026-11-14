import React, { useCallback, useEffect, useState } from 'react';
import {
  Box, Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell, TableContainer, Button, Chip,
  TextField, Dialog, DialogTitle, DialogContent, DialogActions, Alert, List, ListItem, Tabs, Tab,
} from '@mui/material';
import { Lock as LockIcon, Add as AddIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { formatDate, formatMoney } from '../utils/format';

interface Month {
  year: number;
  month: number;
  closed: boolean;
  closed_at: string | null;
  closed_by: string;
  entries: number;
  posted: number;
  drafts: number;
  validated: number;
}

interface Check {
  blockers: string[];
  warnings: string[];
  entries?: number;
  result?: string;
  result_account?: string;
}

interface FiscalYearRow {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_closed: boolean;
  closed_at: string | null;
  closed_by: string;
  result: string;
}

const CheckView: React.FC<{ check: Check | null }> = ({ check }) => {
  const { t } = useTranslation();
  if (!check) return <Typography variant="body2">{t('common.loading')}</Typography>;
  return (
    <>
      {check.blockers.length === 0 && check.warnings.length === 0 && (
        <Alert severity="success" sx={{ mb: 1 }}>{t('closing.noIssues', 'Ingen hindringer.')}</Alert>
      )}
      {check.blockers.length > 0 && (
        <Alert severity="error" sx={{ mb: 1 }}>
          {t('closing.blocked')}
          <List dense>{check.blockers.map(b => <ListItem key={b}>• {b}</ListItem>)}</List>
        </Alert>
      )}
      {check.warnings.length > 0 && (
        <Alert severity="warning" sx={{ mb: 1 }}>
          {t('closing.warnings')}
          <List dense>{check.warnings.map(w => <ListItem key={w}>• {w}</ListItem>)}</List>
        </Alert>
      )}
    </>
  );
};

// Månedslukning: validerer og nummererer månedens posteringer endeligt (Bogføringsloven § 7).
const MonthClosing: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [year, setYear] = useState(new Date().getFullYear());
  const [months, setMonths] = useState<Month[]>([]);
  const [next, setNext] = useState<{ year: number; month: number } | null>(null);
  const [checking, setChecking] = useState<Month | null>(null);
  const [check, setCheck] = useState<Check | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  const load = useCallback(() => {
    api.get(`/periods?year=${year}`).then(res => {
      if (res.data.success) {
        setMonths(res.data.data.months);
        setNext(res.data.data.next_to_close);
      }
    });
  }, [year]);

  useEffect(load, [load]);

  const monthName = (m: number) => new Date(2000, m - 1, 1).toLocaleString(i18n.language, { month: 'long' });

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
      const res = await api.post('/periods/close', { year: checking.year, month: checking.month, confirm_warnings: true });
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
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <TextField label={t('closing.year')} type="number" size="small" value={year} sx={{ width: 110 }}
          onChange={e => setYear(parseInt(e.target.value, 10) || year)} />
      </Box>
      <Alert severity="info" sx={{ mb: 2 }}>
        {t('closing.introDk', 'Når en måned lukkes, får alle dens posteringer et fortløbende nummer pr. journal og år og kan derefter aldrig ændres (Bogføringsloven). Rettelser sker med en tilbageføring i en åben måned. Månederne lukkes i rækkefølge, og bankkontiene skal være afstemt pr. månedens sidste dag.')}
      </Alert>
      {message && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMessage('')}>{message}</Alert>}

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell sx={{ fontWeight: 600 }}>{t('closing.month')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('closing.entries')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('journal.status.posted', 'Bogført')}</TableCell>
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
                  <TableCell align="right">{m.posted}</TableCell>
                  <TableCell align="right">{m.drafts}</TableCell>
                  <TableCell align="right">{m.validated}</TableCell>
                  <TableCell>
                    {m.closed ? (
                      <Chip size="small" icon={<LockIcon />} color="success"
                        label={t('closing.closedBy', { who: m.closed_by, date: formatDate(m.closed_at) })} />
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
          {check && check.blockers.length === 0 && check.warnings.length === 0 ? (
            <Alert severity="success">{t('closing.ready', { count: check.entries ?? 0 })}</Alert>
          ) : <CheckView check={check} />}
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

// Årsafslutning: resultat til egenkapitalen (ÅA), primo (PRIMO) og lås af året.
const YearEnd: React.FC = () => {
  const { t } = useTranslation();
  const [years, setYears] = useState<FiscalYearRow[]>([]);
  const [selected, setSelected] = useState<FiscalYearRow | null>(null);
  const [check, setCheck] = useState<Check | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const thisYear = new Date().getFullYear();
  const [newYear, setNewYear] = useState({ name: String(thisYear), start_date: `${thisYear}-01-01`, end_date: `${thisYear}-12-31` });

  const load = useCallback(() => {
    api.get('/year-end/status').then(res => {
      if (res.data.success) setYears(res.data.data.fiscal_years);
    });
  }, []);

  useEffect(load, [load]);

  const openCheck = (fy: FiscalYearRow) => {
    setSelected(fy);
    setCheck(null);
    api.get(`/year-end/check?fiscal_year_id=${fy.id}`).then(res => {
      if (res.data.success) setCheck(res.data.data);
    });
  };

  const closeYear = async () => {
    if (!selected) return;
    setBusy(true);
    try {
      const res = await api.post('/year-end/close', { fiscal_year_id: selected.id, confirm_warnings: true });
      const d = res.data.data;
      setMessage({
        type: 'success',
        text: t('yearEnd.done', '{{name}} er afsluttet. Resultat {{result}} er overført til konto {{account}} (postering {{closing}}), og primo er bogført i {{next}} ({{opening}}).', {
          name: selected.name, result: formatMoney(d.result), account: d.result_account, closing: d.closing_entry || '—',
          next: d.next_year, opening: d.opening_entry || '—',
        }),
      });
      setSelected(null);
      load();
    } catch (err: any) {
      setCheck(err.response?.data?.data || check);
      setMessage({ type: 'error', text: err.response?.data?.message || t('closing.error') });
    } finally {
      setBusy(false);
    }
  };

  const createYear = async () => {
    try {
      await api.post('/fiscal-years', newYear);
      setCreateOpen(false);
      load();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || t('closing.error') });
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button size="small" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
          {t('yearEnd.newYear', 'Nyt regnskabsår')}
        </Button>
      </Box>
      <Alert severity="info" sx={{ mb: 2 }}>
        {t('yearEnd.intro', 'Årsafslutningen kan laves, når alle årets måneder er lukket. Resultatkontiene nulstilles, og årets resultat overføres til egenkapitalen (overført resultat for selskaber, årets resultat for enkeltmandsvirksomheder) i journalen ÅA. Balancens saldi overføres som primoposteringer til næste år (journalen PRIMO, pr. debitor og kreditor). Derefter er året låst og kan ikke ændres.')}
      </Alert>
      {message && <Alert severity={message.type} sx={{ mb: 2 }} onClose={() => setMessage(null)}>{message.text}</Alert>}

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell sx={{ fontWeight: 600 }}>{t('yearEnd.fiscalYear', 'Regnskabsår')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('yearEnd.period', 'Periode')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('yearEnd.result', 'Resultat')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.status')}</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {years.map(fy => (
              <TableRow key={fy.id} hover>
                <TableCell>{fy.name}</TableCell>
                <TableCell>{formatDate(fy.start_date)} – {formatDate(fy.end_date)}</TableCell>
                <TableCell align="right">{formatMoney(fy.result)}</TableCell>
                <TableCell>
                  {fy.is_closed ? (
                    <Chip size="small" icon={<LockIcon />} color="success"
                      label={t('yearEnd.closedBy', 'Afsluttet {{date}} af {{who}}', { date: formatDate(fy.closed_at), who: fy.closed_by })} />
                  ) : <Chip size="small" variant="outlined" label={t('closing.open')} />}
                </TableCell>
                <TableCell align="right">
                  {!fy.is_closed && (
                    <Button size="small" variant="outlined" onClick={() => openCheck(fy)}>
                      {t('yearEnd.close', 'Årsafslut')}
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {years.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 3, color: 'text.secondary' }}>
                  {t('yearEnd.noYears', 'Der er ingen regnskabsår. Opret det første.')}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={!!selected} onClose={() => setSelected(null)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('yearEnd.closeTitle', 'Årsafslutning {{name}}', { name: selected?.name })}</DialogTitle>
        <DialogContent>
          <CheckView check={check} />
          {check?.result !== undefined && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              {t('yearEnd.willTransfer', 'Årets resultat {{result}} overføres til konto {{account}}.', {
                result: formatMoney(check.result), account: check.result_account,
              })}
            </Typography>
          )}
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            {t('yearEnd.final', 'Årsafslutningen kan ikke fortrydes. Året låses for alle ændringer.')}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelected(null)}>{t('common.cancel')}</Button>
          <Button variant="contained" color="success" startIcon={<LockIcon />} onClick={closeYear}
            disabled={busy || !check || check.blockers.length > 0}>
            {check && check.warnings.length > 0 ? t('yearEnd.confirmClose', 'Bekræft og afslut året') : t('yearEnd.close', 'Årsafslut')}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>{t('yearEnd.newYear', 'Nyt regnskabsår')}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField size="small" label={t('common.name')} value={newYear.name}
              onChange={e => setNewYear({ ...newYear, name: e.target.value })} />
            <TextField size="small" type="date" label={t('common.from')} InputLabelProps={{ shrink: true }}
              value={newYear.start_date} onChange={e => setNewYear({ ...newYear, start_date: e.target.value })} />
            <TextField size="small" type="date" label={t('common.to')} InputLabelProps={{ shrink: true }}
              value={newYear.end_date} onChange={e => setNewYear({ ...newYear, end_date: e.target.value })} />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={createYear}>{t('common.create')}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

const Closing: React.FC = () => {
  const { t } = useTranslation();
  const [tab, setTab] = useState(0);
  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>{t('closing.title')}</Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('closing.monthTab', 'Månedslukning')} />
        <Tab label={t('closing.yearTab', 'Årsafslutning')} />
      </Tabs>
      {tab === 0 ? <MonthClosing /> : <YearEnd />}
    </Box>
  );
};

export default Closing;
