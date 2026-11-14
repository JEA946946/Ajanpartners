import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Paper, Tab, Tabs, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, TextField, Tooltip, Typography,
} from '@mui/material';
import { NotificationsActive as RemindIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { formatDate, formatMoney, parseAmount } from '../utils/format';
import { errorMessage } from './Invoices';

interface Candidate {
  invoice_id: string; invoice_number: string; customer_name: string; due_date: string; days_overdue: number;
  balance_due: string; reminders_sent: number; last_reminder: string | null; can_remind: boolean; reason: string;
}

interface Reminder {
  id: string; invoice_id: string; invoice_number: string; customer_name: string; level: number; date: string;
  due_date: string; fee: string; interest: string; text: string; balance_due: string; total_due: string;
}

const today = () => new Date().toISOString().slice(0, 10);

const Reminders: React.FC = () => {
  const { t } = useTranslation();
  const [tab, setTab] = useState(0);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [defaultFee, setDefaultFee] = useState('100');
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [creating, setCreating] = useState<Candidate | null>(null);
  const [form, setForm] = useState({ date: today(), fee: '100', text: '' });
  const [formError, setFormError] = useState('');

  const reload = useCallback(() => {
    api.get('/reminders/candidates').then(r => {
      setCandidates(r.data.candidates || []);
      setDefaultFee(r.data.default_fee || '100');
    }).catch(e => setError(errorMessage(e, t('reminders.loadError', 'Rykkerne kunne ikke hentes'))));
    api.get('/reminders').then(r => setReminders(r.data.reminders || [])).catch(() => undefined);
  }, [t]);

  useEffect(() => { reload(); }, [reload]);

  const open = (c: Candidate) => {
    setCreating(c);
    setFormError('');
    setForm({ date: today(), fee: defaultFee, text: '' });
  };

  const create = async () => {
    if (!creating) return;
    try {
      const r = await api.post('/reminders', {
        invoice_id: creating.invoice_id, date: form.date, fee: String(parseAmount(form.fee)), text: form.text || undefined,
      });
      setInfo(r.data.message);
      setCreating(null);
      reload();
    } catch (e) {
      setFormError(errorMessage(e, t('reminders.createError', 'Rykkeren kunne ikke oprettes')));
    }
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 1 }}>{t('reminders.title', 'Rykkere')}</Typography>
      <Alert severity="info" sx={{ mb: 2 }}>
        {t('reminders.law', 'Renteloven § 9 b: Der må højst opkræves 100 kr. i rykkergebyr pr. rykker, højst for 3 rykkere for samme betaling, og der skal være mindst 10 dage mellem rykkerne. Gebyret bogføres uden moms.')}
      </Alert>
      {error && <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>{error}</Alert>}
      {info && <Alert severity="success" onClose={() => setInfo('')} sx={{ mb: 2 }}>{info}</Alert>}
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('reminders.overdue', 'Forfaldne fakturaer ({{n}})', { n: candidates.length })} />
        <Tab label={t('reminders.sent', 'Sendte rykkere ({{n}})', { n: reminders.length })} />
      </Tabs>
      {tab === 0 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t('reminders.invoice', 'Faktura')}</TableCell>
                <TableCell>{t('reminders.customer', 'Kunde')}</TableCell>
                <TableCell>{t('reminders.dueDate', 'Forfaldsdato')}</TableCell>
                <TableCell align="right">{t('reminders.daysOverdue', 'Dage over forfald')}</TableCell>
                <TableCell align="right">{t('reminders.balanceDue', 'Restbeløb')}</TableCell>
                <TableCell>{t('reminders.sentCount', 'Rykkere sendt')}</TableCell>
                <TableCell align="right" />
              </TableRow>
            </TableHead>
            <TableBody>
              {candidates.map(c => (
                <TableRow key={c.invoice_id} hover>
                  <TableCell>{c.invoice_number}</TableCell>
                  <TableCell>{c.customer_name}</TableCell>
                  <TableCell>{formatDate(c.due_date)}</TableCell>
                  <TableCell align="right">{c.days_overdue}</TableCell>
                  <TableCell align="right">{formatMoney(c.balance_due)}</TableCell>
                  <TableCell>
                    {c.reminders_sent}/3
                    {c.last_reminder && <Typography variant="caption" sx={{ ml: 1 }}>{t('reminders.last', 'senest {{d}}', { d: formatDate(c.last_reminder) })}</Typography>}
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title={c.can_remind ? '' : c.reason}>
                      <span>
                        <Button size="small" startIcon={<RemindIcon />} disabled={!c.can_remind} onClick={() => open(c)}>
                          {t('reminders.create', '{{n}}. rykker', { n: c.reminders_sent + 1 })}
                        </Button>
                      </span>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
              {candidates.length === 0 && <TableRow><TableCell colSpan={7} align="center">{t('reminders.noOverdue', 'Ingen forfaldne fakturaer')}</TableCell></TableRow>}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      {tab === 1 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t('reminders.invoice', 'Faktura')}</TableCell>
                <TableCell>{t('reminders.customer', 'Kunde')}</TableCell>
                <TableCell>{t('reminders.level', 'Rykker')}</TableCell>
                <TableCell>{t('reminders.date', 'Dato')}</TableCell>
                <TableCell>{t('reminders.newDueDate', 'Ny frist')}</TableCell>
                <TableCell align="right">{t('reminders.fee', 'Gebyr')}</TableCell>
                <TableCell align="right">{t('reminders.totalDue', 'Skyldigt i alt')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {reminders.map(r => (
                <TableRow key={r.id} hover>
                  <TableCell>{r.invoice_number}</TableCell>
                  <TableCell>{r.customer_name}</TableCell>
                  <TableCell><Chip size="small" label={t('reminders.levelLabel', '{{n}}. rykker', { n: r.level })} /></TableCell>
                  <TableCell>{formatDate(r.date)}</TableCell>
                  <TableCell>{formatDate(r.due_date)}</TableCell>
                  <TableCell align="right">{formatMoney(r.fee)}</TableCell>
                  <TableCell align="right">{formatMoney(r.total_due)}</TableCell>
                </TableRow>
              ))}
              {reminders.length === 0 && <TableRow><TableCell colSpan={7} align="center">{t('reminders.none', 'Ingen rykkere')}</TableCell></TableRow>}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={!!creating} onClose={() => setCreating(null)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {creating && t('reminders.dialogTitle', '{{n}}. rykker for faktura {{inv}}', { n: creating.reminders_sent + 1, inv: creating.invoice_number })}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'grid', gap: 2, pt: 1 }}>
            {formError && <Alert severity="error">{formError}</Alert>}
            <TextField type="date" label={t('reminders.date', 'Dato')} InputLabelProps={{ shrink: true }}
              value={form.date} onChange={e => setForm({ ...form, date: e.target.value })} />
            <TextField label={t('reminders.feeLabel', 'Rykkergebyr (højst 100 kr.)')} value={form.fee}
              onChange={e => setForm({ ...form, fee: e.target.value })}
              error={parseAmount(form.fee) > 100}
              helperText={parseAmount(form.fee) > 100 ? t('reminders.feeMax', 'Renteloven tillader højst 100 kr.') : ''} />
            <TextField label={t('reminders.text', 'Tekst (valgfri)')} multiline minRows={2} value={form.text}
              onChange={e => setForm({ ...form, text: e.target.value })} />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreating(null)}>{t('common.cancel', 'Annuller')}</Button>
          <Button variant="contained" onClick={create} disabled={parseAmount(form.fee) > 100}>
            {t('reminders.createAndPost', 'Opret og bogfør')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Reminders;
