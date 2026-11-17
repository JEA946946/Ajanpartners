import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Paper,
  Table, TableBody, TableCell, TableHead, TableRow, TextField, ToggleButton, ToggleButtonGroup, Typography,
} from '@mui/material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';
import { useAdmin } from '../AdminContext';
import { KYC_STATUS, RISK_LEVELS } from '../components/KycPanel';

interface Row {
  slug: string; name: string; industry_code: string; status: string; risk_level: string | null;
  approved_at: string | null; next_review_on: string | null;
}
interface Report {
  id: string; client: string; client_name: string; summary: string; reported_on: string | null; reference: string;
  created_by: string | null; created_at: string;
}
const HVIDVASK_TAB = 8;

/** Admin → Hvidvask: status for kundekendskab pr. kunde og (kun partnere) interne underretninger. */
const Aml: React.FC = () => {
  const navigate = useNavigate();
  const { isPartner } = useAdmin();
  const [rows, setRows] = useState<Row[]>([]);
  const [filter, setFilter] = useState('attention');
  const [reports, setReports] = useState<Report[]>([]);
  const [error, setError] = useState('');
  const [dlg, setDlg] = useState<{ client: string; summary: string; reported_on: string; reference: string } | null>(null);

  const load = () => {
    firmApi.get('/kyc/overview').then((r) => setRows(r.data.data.clients))
      .catch((e) => setError(errorText(e, 'Oversigten kunne ikke hentes')));
    if (isPartner) firmApi.get('/aml-reports').then((r) => setReports(r.data.data.reports)).catch(() => setReports([]));
  };
  useEffect(load, [isPartner]);

  const shown = filter === 'attention' ? rows.filter((r) => r.status !== 'ok') : rows;
  const count = (s: string) => rows.filter((r) => r.status === s).length;
  const saveReport = async () => {
    if (!dlg) return;
    try { await firmApi.post('/aml-reports', dlg); setDlg(null); load(); } catch (e) { setError(errorText(e)); }
  };

  return (
    <Box sx={{ maxWidth: 1100 }}>
      <Typography variant="h5" sx={{ mb: 0.5 }}>Hvidvask – kundekendskab</Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Status for kundekendskab og risikovurdering pr. kunde. Vurderingen laves under kunden → fanen Hvidvask og
        godkendes af en partner. Oplysningerne vises aldrig for kunden.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
        {(['due', 'missing', 'draft', 'ok'] as const).map((s) => (
          <Chip key={s} color={KYC_STATUS[s].color} variant={count(s) ? 'filled' : 'outlined'} label={`${KYC_STATUS[s].text}: ${count(s)}`} />
        ))}
        <Box sx={{ flex: 1 }} />
        <ToggleButtonGroup size="small" exclusive value={filter} onChange={(_, v) => v && setFilter(v)}>
          <ToggleButton value="attention">Kræver handling</ToggleButton>
          <ToggleButton value="all">Alle</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Paper sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Kunde</TableCell><TableCell>Status</TableCell><TableCell>Risiko</TableCell>
              <TableCell>Godkendt</TableCell><TableCell>Næste opdatering</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {shown.map((r) => (
              <TableRow key={r.slug} hover sx={{ cursor: 'pointer' }} onClick={() => navigate(`/admin/clients/${r.slug}?tab=${HVIDVASK_TAB}`)}>
                <TableCell>{r.name}</TableCell>
                <TableCell><Chip size="small" color={KYC_STATUS[r.status].color} label={KYC_STATUS[r.status].text} /></TableCell>
                <TableCell>{r.risk_level ? RISK_LEVELS.find(([k]) => k === r.risk_level)?.[1] : '–'}</TableCell>
                <TableCell>{r.approved_at ? formatDate(r.approved_at) : '–'}</TableCell>
                <TableCell>{r.next_review_on ? formatDate(r.next_review_on) : '–'}</TableCell>
              </TableRow>
            ))}
            {shown.length === 0 && (
              <TableRow><TableCell colSpan={5}><Typography variant="body2" color="text.secondary">Ingen kunder kræver handling.</Typography></TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </Paper>

      {isPartner && (
        <Card variant="outlined" sx={{ borderColor: 'error.light' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1 }}>Underretninger til Hvidvasksekretariatet (kun partnere)</Typography>
              <Button size="small" variant="outlined" color="error"
                onClick={() => setDlg({ client: rows[0]?.slug || '', summary: '', reported_on: '', reference: '' })}>Registrér</Button>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Intern registrering. Selve underretningen foretages til Hvidvasksekretariatet, og kunden må ikke orienteres (HVL § 38, stk. 1).
            </Typography>
            {reports.length > 0 && (
              <Table size="small">
                <TableHead><TableRow><TableCell>Kunde</TableCell><TableCell>Forhold</TableCell><TableCell>Underrettet</TableCell><TableCell>Reference</TableCell></TableRow></TableHead>
                <TableBody>
                  {reports.map((r) => (
                    <TableRow key={r.id}>
                      <TableCell>{r.client_name}</TableCell>
                      <TableCell sx={{ whiteSpace: 'pre-wrap' }}>{r.summary}</TableCell>
                      <TableCell>{r.reported_on ? formatDate(r.reported_on) : <Chip size="small" color="warning" label="Under overvejelse" />}</TableCell>
                      <TableCell>{r.reference || '–'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      <Dialog open={!!dlg} onClose={() => setDlg(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Registrér underretning</DialogTitle>
        {dlg && (
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
            <TextField select size="small" label="Kunde" value={dlg.client} onChange={(e) => setDlg({ ...dlg, client: e.target.value })}>
              {rows.map((r) => <MenuItem key={r.slug} value={r.slug}>{r.name}</MenuItem>)}
            </TextField>
            <TextField multiline minRows={3} size="small" label="Forholdet (kort)" value={dlg.summary} onChange={(e) => setDlg({ ...dlg, summary: e.target.value })} />
            <TextField size="small" type="date" label="Underrettet den (tom = under overvejelse)" InputLabelProps={{ shrink: true }}
              value={dlg.reported_on} onChange={(e) => setDlg({ ...dlg, reported_on: e.target.value })} />
            <TextField size="small" label="Sekretariatets reference" value={dlg.reference} onChange={(e) => setDlg({ ...dlg, reference: e.target.value })} />
          </DialogContent>
        )}
        <DialogActions>
          <Button onClick={() => setDlg(null)}>Annullér</Button>
          <Button variant="contained" color="error" disabled={!dlg?.summary.trim() || !dlg?.client} onClick={saveReport}>Gem</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Aml;
