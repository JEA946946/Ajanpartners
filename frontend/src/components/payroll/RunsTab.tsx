import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Grid, IconButton, MenuItem,
  Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import api from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import RunDetail from './RunDetail';
import { MONTHS, PayrollRun, RUN_STATUS, apiError, kr } from './format';

const RunsTab: React.FC = () => {
  const now = new Date();
  const [runs, setRuns] = useState<PayrollRun[]>([]);
  const [selected, setSelected] = useState<PayrollRun | null>(null);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    frequency: 'month', year: now.getFullYear(), month: now.getMonth() + 1, period_start: '', pay_date: '',
  });

  const load = useCallback(async () => {
    try {
      const res = await api.get('/payroll/runs');
      setRuns(res.data.results);
    } catch (e: any) {
      setError(apiError(e, 'Lønkørslerne kunne ikke hentes.'));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openRun = async (id: string) => {
    try {
      const res = await api.get(`/payroll/runs/${id}`);
      setSelected(res.data);
    } catch (e: any) {
      setError(apiError(e));
    }
  };

  const create = async () => {
    setError('');
    try {
      const payload: Record<string, any> = { ...form };
      if (form.frequency === 'month') delete payload.period_start;
      if (!form.pay_date) delete payload.pay_date;
      const res = await api.post('/payroll/runs', payload);
      setOpen(false);
      setSelected(res.data.payroll_run);
      load();
    } catch (e: any) {
      setError(apiError(e, 'Lønkørslen kunne ikke oprettes.'));
      setOpen(false);
    }
  };

  const remove = async (run: PayrollRun) => {
    if (!window.confirm(`Slet lønkørslen ${run.label}?`)) return;
    try {
      await api.delete(`/payroll/runs/${run.id}`);
      load();
    } catch (e: any) {
      setError(apiError(e));
    }
  };

  if (selected) {
    return (
      <RunDetail run={selected} onBack={() => { setSelected(null); load(); }} onChange={setSelected} />
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Lønkørsler</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpen(true)}>Ny lønkørsel</Button>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Kladde → Beregn → Godkend (låser) → Bogfør i lønjournalen. Derefter lønsedler og eIndkomst.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Periode</TableCell>
              <TableCell>Udbetaling</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Medarbejdere</TableCell>
              <TableCell align="right">A-indkomst</TableCell>
              <TableCell align="right">A-skat</TableCell>
              <TableCell align="right">AM-bidrag</TableCell>
              <TableCell align="right">Netto</TableCell>
              <TableCell>eIndkomst</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {runs.map((r) => (
              <TableRow key={r.id} hover sx={{ cursor: 'pointer' }} onClick={() => openRun(r.id)}>
                <TableCell>{r.frequency === 'month' ? `${MONTHS[r.month - 1]} ${r.year}` : `14 dage fra ${formatDate(r.period_start)}`}</TableCell>
                <TableCell>{formatDate(r.pay_date)}</TableCell>
                <TableCell><Chip size="small" label={RUN_STATUS[r.status]?.label} color={RUN_STATUS[r.status]?.color} /></TableCell>
                <TableCell align="right">{r.line_count}</TableCell>
                <TableCell align="right">{kr(r.total_gross)}</TableCell>
                <TableCell align="right">{kr(r.total_a_tax)}</TableCell>
                <TableCell align="right">{kr(r.total_am)}</TableCell>
                <TableCell align="right">{kr(r.total_net)}</TableCell>
                <TableCell>{r.eindkomst_reference ? 'Indberettet' : '—'}</TableCell>
                <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                  {r.is_editable && <IconButton size="small" onClick={() => remove(r)}><DeleteIcon fontSize="small" /></IconButton>}
                </TableCell>
              </TableRow>
            ))}
            {runs.length === 0 && <TableRow><TableCell colSpan={10} align="center">Ingen lønkørsler endnu.</TableCell></TableRow>}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Ny lønkørsel</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0 }}>
            <Grid item xs={12}>
              <TextField select fullWidth size="small" label="Lønperiode" value={form.frequency}
                onChange={(e) => setForm({ ...form, frequency: e.target.value })}>
                <MenuItem value="month">Måned (månedsløn og timeløn)</MenuItem>
                <MenuItem value="fortnight">14 dage</MenuItem>
              </TextField>
            </Grid>
            {form.frequency === 'month' ? (
              <>
                <Grid item xs={6}>
                  <TextField select fullWidth size="small" label="Måned" value={form.month}
                    onChange={(e) => setForm({ ...form, month: Number(e.target.value) })}>
                    {MONTHS.map((m, i) => <MenuItem key={m} value={i + 1}>{m}</MenuItem>)}
                  </TextField>
                </Grid>
                <Grid item xs={6}>
                  <TextField fullWidth size="small" type="number" label="År" value={form.year}
                    onChange={(e) => setForm({ ...form, year: Number(e.target.value) })} />
                </Grid>
              </>
            ) : (
              <Grid item xs={12}>
                <TextField fullWidth size="small" type="date" label="Periodens første dag" InputLabelProps={{ shrink: true }}
                  value={form.period_start} onChange={(e) => setForm({ ...form, period_start: e.target.value })} />
              </Grid>
            )}
            <Grid item xs={12}>
              <TextField fullWidth size="small" type="date" label="Udbetalingsdato" InputLabelProps={{ shrink: true }}
                helperText="Tom: periodens sidste dag" value={form.pay_date}
                onChange={(e) => setForm({ ...form, pay_date: e.target.value })} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Annullér</Button>
          <Button variant="contained" onClick={create}
            disabled={form.frequency === 'fortnight' && !form.period_start}>Opret</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RunsTab;
