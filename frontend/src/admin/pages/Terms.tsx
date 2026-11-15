import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Grid, Paper, Snackbar,
  Tab, Table, TableBody, TableCell, TableHead, TableRow, Tabs, TextField, Typography,
} from '@mui/material';
import { firmApi } from '../../services/api';
import MarkdownText from '../../components/MarkdownText';
import { errorText } from '../api';
import { useAdmin } from '../AdminContext';

interface Doc {
  id: number; kind: string; kind_label: string; version: string; title: string; body: string; sha256: string;
  published_at: string | null; is_current: boolean; acceptances: number;
}
interface Acceptance { client_name: string; user: string; email: string; accepted_at: string; method: string; ip: string | null }

const fmt = (s: string | null) => (s ? new Date(s).toLocaleString('da-DK') : '–');

/** Forretningsbetingelser, databehandleraftale og privatlivspolitik: versioner og accepter. */
const Terms: React.FC = () => {
  const { isPartner } = useAdmin();
  const [docs, setDocs] = useState<Doc[]>([]);
  const [kinds, setKinds] = useState<Record<string, string>>({});
  const [kind, setKind] = useState('terms');
  const [selected, setSelected] = useState<Doc | null>(null);
  const [acceptances, setAcceptances] = useState<Acceptance[]>([]);
  const [edit, setEdit] = useState<{ open: boolean; version: string; title: string; body: string }>({ open: false, version: '', title: '', body: '' });
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const load = () => firmApi.get('/terms').then((r) => {
    setDocs(r.data.data.documents);
    setKinds(r.data.data.kinds);
  }).catch((e) => setError(errorText(e)));
  useEffect(() => { load(); }, []);

  const versions = useMemo(() => docs.filter((d) => d.kind === kind), [docs, kind]);
  useEffect(() => { setSelected(versions.find((d) => d.is_current) || versions[0] || null); }, [versions]);
  useEffect(() => {
    if (!selected) { setAcceptances([]); return; }
    firmApi.get(`/terms/${selected.id}/acceptances`).then((r) => setAcceptances(r.data.data.acceptances)).catch(() => setAcceptances([]));
  }, [selected]);

  const publish = async () => {
    try {
      const r = await firmApi.post('/terms', { kind, version: edit.version, title: edit.title, body: edit.body });
      setToast(r.data.message || 'Publiceret');
      setEdit({ ...edit, open: false });
      load();
    } catch (e) { setError(errorText(e, 'Kunne ikke publicere')); }
  };

  const nextVersion = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Betingelser</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Kundernes brugere accepterer forretningsbetingelser og databehandleraftale ved første login. En publiceret
        version kan ikke ændres; en ny version skal accepteres igen ved næste login. Teksterne er udkast og bør
        gennemgås af en advokat.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      <Tabs value={kind} onChange={(_, v) => setKind(v)} sx={{ mb: 2 }}>
        {Object.entries(kinds).map(([k, v]) => <Tab key={k} value={k} label={v} />)}
      </Tabs>
      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <Paper variant="outlined">
            <Table size="small">
              <TableBody>
                {versions.map((d) => (
                  <TableRow key={d.id} hover selected={selected?.id === d.id} sx={{ cursor: 'pointer' }} onClick={() => setSelected(d)}>
                    <TableCell>
                      <b>{d.version}</b> {d.is_current && <Chip size="small" color="success" label="Gældende" sx={{ ml: 0.5 }} />}
                      <Typography variant="caption" display="block" color="text.secondary">{d.acceptances} accepter</Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
          {isPartner && (
            <Button fullWidth sx={{ mt: 1 }} variant="contained" onClick={() => setEdit({
              open: true, version: nextVersion(), title: selected?.title || kinds[kind] || '', body: selected?.body || '',
            })}>Ny version</Button>
          )}
        </Grid>
        <Grid item xs={12} md={9}>
          {selected && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Version {selected.version} · publiceret {fmt(selected.published_at)} · sha256 {selected.sha256.slice(0, 12)}…
              </Typography>
              <Box sx={{ maxHeight: 420, overflowY: 'auto', mt: 1 }}><MarkdownText text={selected.body} /></Box>
              <Typography variant="subtitle2" sx={{ mt: 2 }}>Accepteret af</Typography>
              <Table size="small">
                <TableHead><TableRow><TableCell>Virksomhed</TableCell><TableCell>Bruger</TableCell><TableCell>Tidspunkt</TableCell><TableCell>IP</TableCell><TableCell>Måde</TableCell></TableRow></TableHead>
                <TableBody>
                  {acceptances.map((a, i) => (
                    <TableRow key={i}><TableCell>{a.client_name}</TableCell><TableCell>{a.user} <Typography variant="caption" color="text.secondary">{a.email}</Typography></TableCell>
                      <TableCell>{fmt(a.accepted_at)}</TableCell><TableCell>{a.ip || '–'}</TableCell><TableCell>{a.method === 'mitid' ? 'MitID' : 'Klik'}</TableCell></TableRow>
                  ))}
                  {acceptances.length === 0 && <TableRow><TableCell colSpan={5}>Ingen endnu.</TableCell></TableRow>}
                </TableBody>
              </Table>
            </Paper>
          )}
        </Grid>
      </Grid>

      <Dialog open={edit.open} onClose={() => setEdit({ ...edit, open: false })} maxWidth="md" fullWidth>
        <DialogTitle>Ny version – {kinds[kind]}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0 }}>
            <Grid item xs={4}><TextField fullWidth size="small" label="Version" value={edit.version} onChange={(e) => setEdit({ ...edit, version: e.target.value })} /></Grid>
            <Grid item xs={8}><TextField fullWidth size="small" label="Titel" value={edit.title} onChange={(e) => setEdit({ ...edit, title: e.target.value })} /></Grid>
            <Grid item xs={12}>
              <TextField fullWidth multiline minRows={16} size="small" label="Tekst (markdown: # overskrift, ## afsnit, - punkt, **fed**)"
                value={edit.body} onChange={(e) => setEdit({ ...edit, body: e.target.value })} InputProps={{ sx: { fontFamily: 'monospace', fontSize: 12 } }} />
            </Grid>
          </Grid>
          {(kind === 'terms' || kind === 'dpa') && (
            <Alert severity="warning" sx={{ mt: 2 }}>Når du publicerer, skal alle kunders brugere acceptere den nye version ved næste login.</Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEdit({ ...edit, open: false })}>Annullér</Button>
          <Button variant="contained" onClick={publish} disabled={!edit.version.trim() || !edit.body.trim()}>Publicér</Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={!!toast} autoHideDuration={4000} onClose={() => setToast('')} message={toast} />
    </Box>
  );
};

export default Terms;
