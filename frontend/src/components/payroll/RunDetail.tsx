import React, { useState } from 'react';
import {
  Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Grid, IconButton, Paper,
  Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Tooltip, Typography,
  FormControlLabel, Checkbox,
} from '@mui/material';
import {
  ArrowBack as BackIcon, Calculate as CalcIcon, CheckCircle as ApproveIcon, Edit as EditIcon,
  LockOpen as ReopenIcon, MenuBook as PostIcon, PictureAsPdf as PdfIcon, Send as SendIcon,
  FileDownload as ExportIcon,
} from '@mui/icons-material';
import api from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { PayrollLine, PayrollRun, RUN_STATUS, TAX_CARDS, apiError, kr, openBlob } from './format';

interface Props {
  run: PayrollRun;
  onBack: () => void;
  onChange: (run: PayrollRun) => void;
}

const INPUTS: [keyof PayrollLine, string][] = [
  ['hours', 'Timer (ATP)'],
  ['base_salary', 'Løn'],
  ['supplements', 'Tillæg og overtid'],
  ['holiday_payout', 'Udbetalte hensatte feriepenge'],
  ['a_income_no_am', 'A-indkomst uden AM-bidrag'],
  ['car_benefit', 'Fri bil'],
  ['phone_benefit', 'Fri telefon'],
  ['other_benefits', 'Andre personalegoder'],
  ['b_income', 'B-indkomst'],
  ['sick_pay_refund', 'Sygedagpengerefusion'],
];

const RunDetail: React.FC<Props> = ({ run, onBack, onChange }) => {
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [busy, setBusy] = useState(false);
  const [editLine, setEditLine] = useState<PayrollLine | null>(null);
  const [form, setForm] = useState<Record<string, any>>({});
  const [showLine, setShowLine] = useState<PayrollLine | null>(null);

  const status = RUN_STATUS[run.status];
  const lines = run.lines || [];

  const act = async (path: string, ok: string) => {
    setBusy(true);
    setError('');
    setInfo('');
    try {
      const res = await api.post(`/payroll/runs/${run.id}/${path}`);
      onChange(res.data.payroll_run);
      setInfo(ok);
    } catch (e: any) {
      setError(apiError(e));
    } finally {
      setBusy(false);
    }
  };

  const pdf = async (path: string, name: string) => {
    try {
      const res = await api.get(`/payroll/runs/${run.id}/${path}`, { responseType: 'blob' });
      openBlob(res.data, 'application/pdf', name);
    } catch (e: any) {
      setError(apiError(e, 'PDF kunne ikke dannes.'));
    }
  };

  const exportEIndkomst = async () => {
    try {
      const res = await api.get(`/payroll/runs/${run.id}/eindkomst`, { responseType: 'blob' });
      openBlob(res.data, 'application/json', `eindkomst-${run.label}.json`, true);
    } catch (e: any) {
      setError(apiError(e, 'Eksporten kunne ikke dannes (kræver godkendt lønkørsel og skriveadgang).'));
    }
  };

  const submitEIndkomst = async () => {
    setError('');
    setInfo('');
    try {
      const res = await api.post(`/payroll/runs/${run.id}/eindkomst/submit`);
      onChange({ ...run, ...res.data.payroll_run, lines: run.lines });
      if (res.data.success) setInfo(`${res.data.message} Kvittering: ${res.data.reference}`);
      else setError(res.data.message);
    } catch (e: any) {
      setError(apiError(e));
    }
  };

  const openEdit = (l: PayrollLine) => {
    const f: Record<string, any> = { note: l.note, b_income_am: l.b_income_am };
    INPUTS.forEach(([k]) => { f[k] = l[k]; });
    setForm(f);
    setEditLine(l);
  };

  const saveLine = async () => {
    if (!editLine) return;
    try {
      const res = await api.put(`/payroll/runs/${run.id}/lines/${editLine.id}`, form);
      onChange(res.data.payroll_run);
      setEditLine(null);
    } catch (e: any) {
      setError(apiError(e));
    }
  };

  const totals: [string, string][] = [
    ['A-indkomst (kontant)', run.total_gross],
    ['Personalegoder', run.total_benefits],
    ['AM-bidrag', run.total_am],
    ['A-skat', run.total_a_tax],
    ['ATP (lønmodtager + arbejdsgiver)', String(parseFloat(run.total_atp_employee) + parseFloat(run.total_atp_employer))],
    ['Pension (eget + arbejdsgiver)', String(parseFloat(run.total_pension_employee) + parseFloat(run.total_pension_employer))],
    ['Feriepenge/ferietillæg hensat', run.total_holiday],
    ['B-indkomst', run.total_b_income],
    ['Nettoløn til udbetaling', run.total_net],
  ];

  return (
    <Box>
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
        <IconButton onClick={onBack}><BackIcon /></IconButton>
        <Typography variant="h6">Lønkørsel {run.label}</Typography>
        <Chip label={status?.label} color={status?.color} size="small" />
        <Typography variant="body2" color="text.secondary">
          {formatDate(run.period_start)} – {formatDate(run.period_end)}, udbetales {formatDate(run.pay_date)}
        </Typography>
      </Stack>

      <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap', rowGap: 1 }}>
        <Button variant="outlined" startIcon={<CalcIcon />} disabled={busy || !run.is_editable}
          onClick={() => act('calculate', 'Lønnen er beregnet.')}>Beregn</Button>
        <Button variant="outlined" startIcon={<ApproveIcon />} disabled={busy || run.status !== 'calculated'}
          onClick={() => act('approve', 'Lønkørslen er godkendt og låst.')}>Godkend</Button>
        {run.status === 'approved' && (
          <Button startIcon={<ReopenIcon />} disabled={busy} onClick={() => act('reopen', 'Lønkørslen er genåbnet.')}>Genåbn</Button>
        )}
        <Button variant="contained" startIcon={<PostIcon />} disabled={busy || run.status !== 'approved'}
          onClick={() => { if (window.confirm('Bogfør lønkørslen i lønjournalen?')) act('post', 'Lønkørslen er bogført.'); }}>
          Bogfør
        </Button>
        <Box sx={{ flexGrow: 1 }} />
        <Button startIcon={<PdfIcon />} disabled={run.status === 'draft'} onClick={() => pdf('payslips.pdf', 'loensedler.pdf')}>Lønsedler</Button>
        <Button startIcon={<PdfIcon />} onClick={() => pdf('payroll-list.pdf', 'loenliste.pdf')}>Lønliste</Button>
        <Button startIcon={<ExportIcon />} disabled={!['approved', 'posted'].includes(run.status)} onClick={exportEIndkomst}>eIndkomst-fil</Button>
        <Button startIcon={<SendIcon />} disabled={!['approved', 'posted'].includes(run.status)} onClick={submitEIndkomst}>Indberet</Button>
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {info && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setInfo('')}>{info}</Alert>}
      {run.eindkomst_reference && (
        <Alert severity="info" sx={{ mb: 2 }}>
          eIndkomst: {run.eindkomst_status}, kvittering {run.eindkomst_reference}
          {run.eindkomst_submitted_at ? ` (${formatDate(run.eindkomst_submitted_at)})` : ''}
        </Alert>
      )}

      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Medarbejder</TableCell>
              <TableCell align="right">Timer</TableCell>
              <TableCell align="right">Løn</TableCell>
              <TableCell align="right">Goder</TableCell>
              <TableCell align="right">ATP</TableCell>
              <TableCell align="right">Pension</TableCell>
              <TableCell align="right">AM-bidrag</TableCell>
              <TableCell align="right">A-skat</TableCell>
              <TableCell align="right">Netto</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {lines.map((l) => (
              <TableRow key={l.id} hover sx={{ cursor: 'pointer' }} onClick={() => setShowLine(l)}>
                <TableCell>
                  {l.employee_name}
                  {!l.calculated && <Chip size="small" label="Ikke beregnet" sx={{ ml: 1 }} />}
                  {l.warnings?.length > 0 && <Tooltip title={l.warnings.join(' ')}><Chip size="small" color="warning" label="!" sx={{ ml: 1 }} /></Tooltip>}
                </TableCell>
                <TableCell align="right">{parseFloat(l.hours).toLocaleString('da-DK')}</TableCell>
                <TableCell align="right">{kr(l.calculated ? l.gross_cash : l.base_salary)}</TableCell>
                <TableCell align="right">{kr(l.calculated ? l.benefits : '0')}</TableCell>
                <TableCell align="right">{kr(l.atp_employee)}</TableCell>
                <TableCell align="right">{kr(l.pension_employee)}</TableCell>
                <TableCell align="right">{kr(l.am_contribution)}</TableCell>
                <TableCell align="right">{kr(l.a_tax)}</TableCell>
                <TableCell align="right"><strong>{kr(l.net_pay)}</strong></TableCell>
                <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                  {run.is_editable && <IconButton size="small" onClick={() => openEdit(l)}><EditIcon fontSize="small" /></IconButton>}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Paper sx={{ p: 2, maxWidth: 520 }}>
        <Typography variant="subtitle1" gutterBottom>Totaler</Typography>
        {totals.map(([label, v]) => (
          <Box key={label} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.25 }}>
            <Typography variant="body2">{label}</Typography>
            <Typography variant="body2">{kr(v)}</Typography>
          </Box>
        ))}
      </Paper>

      <Dialog open={!!editLine} onClose={() => setEditLine(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Ret lønlinje – {editLine?.employee_name}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0 }}>
            {INPUTS.map(([k, label]) => (
              <Grid item xs={6} key={k}>
                <TextField fullWidth size="small" type="number" label={label} value={form[k] ?? ''}
                  onChange={(e) => setForm((f) => ({ ...f, [k]: e.target.value }))} />
              </Grid>
            ))}
            <Grid item xs={6}>
              <FormControlLabel label="B-indkomst er AM-pligtig" control={
                <Checkbox checked={!!form.b_income_am} onChange={(e) => setForm((f) => ({ ...f, b_income_am: e.target.checked }))} />} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth size="small" label="Note" value={form.note ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))} />
            </Grid>
          </Grid>
          <Typography variant="caption" color="text.secondary">
            Efter en rettelse skal lønkørslen beregnes igen.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditLine(null)}>Annullér</Button>
          <Button variant="contained" onClick={saveLine}>Gem</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={!!showLine} onClose={() => setShowLine(null)} maxWidth="xs" fullWidth>
        <DialogTitle>{showLine?.employee_name}</DialogTitle>
        <DialogContent>
          {showLine && ([
            ['Kontant løn', showLine.gross_cash],
            ['heraf ferietillæg', showLine.holiday_allowance_paid],
            ['Personalegoder', showLine.benefits],
            ['ATP', `-${showLine.atp_employee}`],
            ['Pension, eget bidrag', `-${showLine.pension_employee}`],
            ['AM-grundlag', showLine.am_base],
            ['AM-bidrag 8 %', `-${showLine.am_contribution}`],
            ['Skattegrundlag', showLine.tax_base],
            [`Fradrag brugt (${TAX_CARDS[showLine.tax_card] || ''} ${parseFloat(showLine.tax_rate)} %)`, showLine.deduction_used],
            ['Frikort brugt', showLine.frikort_used],
            ['A-skat', `-${showLine.a_tax}`],
            ['B-indkomst', showLine.b_income],
            ['Nettoløn', showLine.net_pay],
            ['ATP, arbejdsgiver', showLine.atp_employer],
            ['Pension, arbejdsgiver', showLine.pension_employer],
            ['Ferietillæg hensat', showLine.holiday_allowance_accrued],
            ['Feriepenge hensat', showLine.holiday_pay_accrued],
            ['Lønomkostning i alt', showLine.employer_cost],
          ] as [string, string][]).map(([label, v]) => (
            <Box key={label} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.25 }}>
              <Typography variant="body2">{label}</Typography>
              <Typography variant="body2">{kr(v)}</Typography>
            </Box>
          ))}
        </DialogContent>
        <DialogActions>
          {showLine && run.status !== 'draft' && (
            <Button startIcon={<PdfIcon />} onClick={() => pdf(`payslips.pdf?line=${showLine.id}`, 'loenseddel.pdf')}>Lønseddel</Button>
          )}
          <Button onClick={() => setShowLine(null)}>Luk</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RunDetail;
