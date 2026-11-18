import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Paper, Table, TableBody,
  TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';
import { useAdmin } from '../AdminContext';

interface Entry {
  id: string; kind: string; kind_label: string; title: string; description: string; follow_up: string;
  client: string | null; client_name: string | null; created_by: string | null; created_at: string;
  closed_at: string | null; closed_by: string | null;
}

/** Admin → Kvalitetslog: konsultationer, klager, hændelser og årlig evaluering (BEK 512/2024 § 3, stk. 1, nr. 8, stk. 3-4). */
const QualityLog: React.FC = () => {
  const { isPartner } = useAdmin();
  const [rows, setRows] = useState<Entry[]>([]);
  const [kinds, setKinds] = useState<{ value: string; label: string }[]>([]);
  const [clients, setClients] = useState<{ slug: string; name: string }[]>([]);
  const [error, setError] = useState('');
  const [dlg, setDlg] = useState<{ kind: string; title: string; description: string; client: string } | null>(null);
  const [edit, setEdit] = useState<{ e: Entry; follow_up: string } | null>(null);

  const load = useCallback(() => {
    firmApi.get('/quality-log').then((r) => { setRows(r.data.data.entries); setKinds(r.data.data.kinds); })
      .catch((e) => setError(errorText(e, 'Kvalitetsloggen kunne ikke hentes')));
  }, []);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    firmApi.get('/clients').then((r) => setClients((r.data.data.clients || []).map((c: any) => ({ slug: c.slug, name: c.name })))).catch(() => undefined);
  }, []);

  const create = async () => {
    try { await firmApi.post('/quality-log', dlg); setDlg(null); load(); } catch (e) { setError(errorText(e)); }
  };
  const save = async (close: boolean) => {
    if (!edit) return;
    try { await firmApi.put(`/quality-log/${edit.e.id}`, { follow_up: edit.follow_up, close }); setEdit(null); load(); } catch (e) { setError(errorText(e)); }
  };
  const year = new Date().getFullYear();
  const evaluated = rows.some((r) => r.kind === 'evaluering' && r.created_at.startsWith(String(year)));

  return (
    <Box sx={{ maxWidth: 1100 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
        <Typography variant="h5" sx={{ flex: 1 }}>Kvalitetslog</Typography>
        <Button variant="contained" onClick={() => setDlg({ kind: 'konsultation', title: '', description: '', client: '' })}>Ny registrering</Button>
      </Box>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Konsultationer, klager og hændelser, der kan have betydning for kvaliteten eller indebære en overtrædelse – med opfølgning
        (BEK 512/2024 § 3, stk. 1, nr. 8, og stk. 4) – samt den årlige evaluering af kvalitetsstyringssystemet (§ 3, stk. 3).
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {!evaluated && <Alert severity="info" sx={{ mb: 2 }}>Der er ikke registreret en evaluering af kvalitetsstyringssystemet for {year}. Den skal foretages årligt (BEK 512/2024 § 3, stk. 3).</Alert>}
      <Paper>
        <Table size="small">
          <TableHead><TableRow><TableCell>Dato</TableCell><TableCell>Type</TableCell><TableCell>Emne</TableCell><TableCell>Kunde</TableCell><TableCell>Opfølgning</TableCell><TableCell /></TableRow></TableHead>
          <TableBody>
            {rows.length === 0 && <TableRow><TableCell colSpan={6}><Typography variant="body2" color="text.secondary">Ingen registreringer.</Typography></TableCell></TableRow>}
            {rows.map((r) => (
              <TableRow key={r.id}>
                <TableCell>{formatDate(r.created_at)}<Typography variant="caption" sx={{ display: 'block' }}>{r.created_by}</Typography></TableCell>
                <TableCell>{r.kind_label}</TableCell>
                <TableCell><Typography variant="body2" sx={{ fontWeight: 500 }}>{r.title}</Typography><Typography variant="caption" sx={{ whiteSpace: 'pre-wrap' }}>{r.description}</Typography></TableCell>
                <TableCell>{r.client_name || '–'}</TableCell>
                <TableCell sx={{ whiteSpace: 'pre-wrap' }}>
                  {r.follow_up || '–'}
                  {r.closed_at && <Chip size="small" color="success" sx={{ ml: 1 }} label={`Lukket ${formatDate(r.closed_at)}`} />}
                </TableCell>
                <TableCell>{!r.closed_at && <Button size="small" onClick={() => setEdit({ e: r, follow_up: r.follow_up })}>Opfølgning</Button>}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={!!dlg} onClose={() => setDlg(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Ny registrering</DialogTitle>
        {dlg && (
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
            <TextField select size="small" label="Type" value={dlg.kind} onChange={(e) => setDlg({ ...dlg, kind: e.target.value })}>
              {kinds.filter((k) => isPartner || k.value !== 'evaluering').map((k) => <MenuItem key={k.value} value={k.value}>{k.label}</MenuItem>)}
            </TextField>
            <TextField size="small" label="Emne" value={dlg.title} onChange={(e) => setDlg({ ...dlg, title: e.target.value })} />
            <TextField multiline minRows={3} size="small" label="Beskrivelse" value={dlg.description} onChange={(e) => setDlg({ ...dlg, description: e.target.value })} />
            <TextField select size="small" label="Kunde (valgfri)" value={dlg.client} onChange={(e) => setDlg({ ...dlg, client: e.target.value })}>
              <MenuItem value="">–</MenuItem>
              {clients.map((c) => <MenuItem key={c.slug} value={c.slug}>{c.name}</MenuItem>)}
            </TextField>
          </DialogContent>
        )}
        <DialogActions>
          <Button onClick={() => setDlg(null)}>Annullér</Button>
          <Button variant="contained" disabled={!dlg?.title.trim()} onClick={create}>Gem</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={!!edit} onClose={() => setEdit(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Opfølgning</DialogTitle>
        {edit && (
          <DialogContent sx={{ pt: '8px !important' }}>
            <Typography variant="body2" sx={{ mb: 1 }}><b>{edit.e.title}</b></Typography>
            <TextField fullWidth multiline minRows={3} size="small" label="Opfølgning / afhjælpning" value={edit.follow_up}
              onChange={(e) => setEdit({ ...edit, follow_up: e.target.value })} />
          </DialogContent>
        )}
        <DialogActions>
          <Button onClick={() => setEdit(null)}>Annullér</Button>
          <Button onClick={() => save(false)}>Gem</Button>
          {isPartner && <Button variant="contained" disabled={!edit?.follow_up.trim()} onClick={() => save(true)}>Gem og luk</Button>}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default QualityLog;
