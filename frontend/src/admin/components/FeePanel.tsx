import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, Chip, Grid, IconButton, LinearProgress, MenuItem, Paper, Table, TableBody, TableCell, TableHead,
  TableRow, TextField, Typography,
} from '@mui/material';
import { Delete } from '@mui/icons-material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';
import { useAdmin } from '../AdminContext';

interface Installment { id: string; due_on: string; amount: string; text: string; invoiced: boolean; offset: boolean }
interface FeeData {
  fee: { kind: string; kind_label: string; hourly_rate: string | null; fixed_amount: string | null; note: string };
  kinds: { value: string; label: string }[];
  installments: Installment[];
  time: { hours: string; billable_value: string; invoiced_value: string; budget_hours: string | null };
}

export const kr = (v: string | number | null | undefined) =>
  v == null || v === '' ? '–' : Number(v).toLocaleString('da-DK', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** Honoraraftale, rater og tidsforbrug på et opdrag. */
const FeePanel: React.FC<{ engagementId: string }> = ({ engagementId }) => {
  const { isPartner } = useAdmin();
  const [d, setD] = useState<FeeData | null>(null);
  const [inst, setInst] = useState({ due_on: '', amount: '', text: '' });
  const [error, setError] = useState('');

  const load = useCallback(() => {
    firmApi.get(`/engagements/${engagementId}/fee`).then((r) => setD(r.data.data)).catch((e) => setError(errorText(e)));
  }, [engagementId]);
  useEffect(() => { load(); }, [load]);

  const save = async (patch: Record<string, unknown>) => {
    try { setD((await firmApi.put(`/engagements/${engagementId}/fee`, patch)).data.data); setError(''); }
    catch (e) { setError(errorText(e)); }
  };
  const addInst = async () => {
    try {
      setD((await firmApi.post(`/engagements/${engagementId}/installments`, inst)).data.data);
      setInst({ due_on: '', amount: '', text: '' });
      setError('');
    } catch (e) { setError(errorText(e)); }
  };
  const delInst = async (id: string) => {
    try { setD((await firmApi.delete(`/installments/${id}`)).data.data); } catch (e) { setError(errorText(e)); }
  };
  if (!d) return null;

  const used = Number(d.time.hours);
  const budget = d.time.budget_hours ? Number(d.time.budget_hours) : 0;
  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Honorar og tid</Typography>
      {error && <Alert severity="error" sx={{ mb: 1 }}>{error}</Alert>}
      <Grid container spacing={2} sx={{ mb: 1 }}>
        <Grid item xs={12} sm={4}>
          <TextField select fullWidth size="small" label="Honoraraftale" value={d.fee.kind} disabled={!isPartner}
            onChange={(e) => save({ kind: e.target.value })}>
            {d.kinds.map((k) => <MenuItem key={k.value} value={k.value}>{k.label}</MenuItem>)}
          </TextField>
        </Grid>
        <Grid item xs={6} sm={4}>
          <TextField fullWidth size="small" type="number" label="Timepris på opdraget" disabled={!isPartner}
            helperText="Tom = medarbejderens/husets sats" defaultValue={d.fee.hourly_rate ?? ''} key={`r${d.fee.hourly_rate}`}
            onBlur={(e) => e.target.value !== (d.fee.hourly_rate ?? '') && save({ hourly_rate: e.target.value })} />
        </Grid>
        {d.fee.kind === 'fast' && (
          <Grid item xs={6} sm={4}>
            <TextField fullWidth size="small" type="number" label="Fast pris i alt" disabled={!isPartner}
              defaultValue={d.fee.fixed_amount ?? ''} key={`f${d.fee.fixed_amount}`}
              onBlur={(e) => e.target.value !== (d.fee.fixed_amount ?? '') && save({ fixed_amount: e.target.value })} />
          </Grid>
        )}
      </Grid>
      <Typography variant="caption" color="text.secondary" component="div" sx={{ mb: 1 }}>
        {d.fee.kind === 'fast' && 'Fast pris: tiden registreres til styring, men faktureres via raterne nedenfor.'}
        {d.fee.kind === 'aconto' && 'Aconto: raterne faktureres løbende og modregnes, når den medgåede tid faktureres.'}
        {d.fee.kind === 'timepris' && 'Medgået tid faktureres til den timepris, der stod på registreringen.'}
        {' '}Beløb er ekskl. moms.
      </Typography>

      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 1 }}>
        <Typography variant="body2">Registreret: <b>{d.time.hours} t</b>{budget ? ` af ${d.time.budget_hours} t budget` : ''}</Typography>
        <Typography variant="body2">Værdi af fakturerbar tid: <b>{kr(d.time.billable_value)} kr.</b></Typography>
        <Typography variant="body2">Heraf faktureret: <b>{kr(d.time.invoiced_value)} kr.</b></Typography>
      </Box>
      {budget > 0 && (
        <LinearProgress variant="determinate" color={used > budget ? 'error' : 'primary'}
          value={Math.min(100, (100 * used) / budget)} sx={{ mb: 2 }} />
      )}

      {d.fee.kind !== 'timepris' && (
        <>
          <Typography variant="subtitle2" sx={{ mt: 1 }}>Rater</Typography>
          <Table size="small">
            <TableHead><TableRow><TableCell>Dato</TableCell><TableCell>Tekst</TableCell><TableCell align="right">Beløb</TableCell><TableCell>Status</TableCell><TableCell /></TableRow></TableHead>
            <TableBody>
              {d.installments.length === 0 && <TableRow><TableCell colSpan={5}><Typography variant="body2" color="text.secondary">Ingen rater.</Typography></TableCell></TableRow>}
              {d.installments.map((i) => (
                <TableRow key={i.id}>
                  <TableCell>{formatDate(i.due_on)}</TableCell>
                  <TableCell>{i.text || '–'}</TableCell>
                  <TableCell align="right">{kr(i.amount)}</TableCell>
                  <TableCell>
                    {i.invoiced ? <Chip size="small" color="success" label="Faktureret" /> : <Chip size="small" label="Ikke faktureret" />}
                    {i.offset && <Chip size="small" sx={{ ml: 0.5 }} label="Modregnet" />}
                  </TableCell>
                  <TableCell>{isPartner && !i.invoiced && <IconButton size="small" onClick={() => delInst(i.id)}><Delete fontSize="small" /></IconButton>}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {isPartner && (
            <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
              <TextField size="small" type="date" label="Dato" InputLabelProps={{ shrink: true }} value={inst.due_on}
                onChange={(e) => setInst({ ...inst, due_on: e.target.value })} />
              <TextField size="small" type="number" label="Beløb" value={inst.amount} onChange={(e) => setInst({ ...inst, amount: e.target.value })} />
              <TextField size="small" label="Tekst på fakturaen (valgfri)" sx={{ flex: 1, minWidth: 200 }} value={inst.text}
                onChange={(e) => setInst({ ...inst, text: e.target.value })} />
              <Button variant="outlined" disabled={!inst.due_on || !inst.amount} onClick={addInst}>Tilføj rate</Button>
            </Box>
          )}
        </>
      )}
    </Paper>
  );
};

export default FeePanel;
