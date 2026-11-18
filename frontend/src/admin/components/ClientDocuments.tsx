import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, Checkbox, Chip, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, IconButton,
  MenuItem, Paper, Switch, Table, TableBody, TableCell, TableHead, TableRow, TextField, Tooltip, Typography,
} from '@mui/material';
import { Download, Edit, UploadFile } from '@mui/icons-material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';

export interface ArchiveDoc {
  id: string; engagement: string | null; engagement_title: string | null; kind: string; kind_label: string; title: string;
  version: number; filename: string; size: number; sha256: string; source: string; visible_to_client: boolean;
  signed_on: string | null; signed_note: string; retain_until: string | null; note: string; created_by: string | null;
  created_at: string;
}

const download = async (d: ArchiveDoc) => {
  const r = await firmApi.get(`/documents/${d.id}`, { responseType: 'blob' });
  const url = URL.createObjectURL(r.data);
  const a = document.createElement('a');
  a.href = url; a.download = d.filename; a.click();
  URL.revokeObjectURL(url);
};

/** Dokumentarkiv for en kunde (evt. kun ét opdrag). Intet slettes – samme type og titel giver en ny version. */
const ClientDocuments: React.FC<{ slug: string; engagementId?: string }> = ({ slug, engagementId }) => {
  const [docs, setDocs] = useState<ArchiveDoc[]>([]);
  const [kinds, setKinds] = useState<{ value: string; label: string }[]>([]);
  const [showOld, setShowOld] = useState(false);
  const [upload, setUpload] = useState<{ file: File | null; kind: string; title: string; visible: boolean; retain_until: string; note: string } | null>(null);
  const [edit, setEdit] = useState<ArchiveDoc | null>(null);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    firmApi.get(`/clients/${slug}/documents`, { params: engagementId ? { engagement: engagementId } : {} })
      .then((r) => { setDocs(r.data.data.documents); setKinds(r.data.data.kinds); })
      .catch((e) => setError(errorText(e)));
  }, [slug, engagementId]);
  useEffect(() => { load(); }, [load]);

  const latest = new Map<string, number>();
  docs.forEach((d) => latest.set(`${d.kind}|${d.title}`, Math.max(latest.get(`${d.kind}|${d.title}`) || 0, d.version)));
  const shown = showOld ? docs : docs.filter((d) => latest.get(`${d.kind}|${d.title}`) === d.version);

  const save = async () => {
    if (!upload?.file) return;
    const fd = new FormData();
    fd.append('file', upload.file);
    fd.append('kind', upload.kind);
    fd.append('title', upload.title);
    fd.append('visible_to_client', upload.visible ? '1' : '0');
    if (upload.retain_until) fd.append('retain_until', upload.retain_until);
    if (upload.note) fd.append('note', upload.note);
    if (engagementId) fd.append('engagement', engagementId);
    try { await firmApi.post(`/clients/${slug}/documents`, fd); setUpload(null); setError(''); load(); }
    catch (e) { setError(errorText(e)); }
  };
  const update = async (id: string, patch: Record<string, unknown>) => {
    try { await firmApi.put(`/documents/${id}`, patch); setEdit(null); setError(''); load(); }
    catch (e) { setError(errorText(e)); }
  };
  const newVersion = (d: ArchiveDoc) => setUpload({ file: null, kind: d.kind, title: d.title, visible: d.visible_to_client, retain_until: d.retain_until || '', note: '' });

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, gap: 1, flexWrap: 'wrap' }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1 }}>Dokumentarkiv</Typography>
        <FormControlLabel control={<Switch size="small" checked={showOld} onChange={(e) => setShowOld(e.target.checked)} />} label="Vis tidligere versioner" />
        <Button size="small" variant="outlined" startIcon={<UploadFile />}
          onClick={() => setUpload({ file: null, kind: 'andet', title: '', visible: false, retain_until: '', note: '' })}>Upload</Button>
      </Box>
      <Typography variant="caption" color="text.secondary" component="div" sx={{ mb: 1 }}>
        Dokumenter slettes ikke; en ny fil med samme type og titel bliver en ny version. Kun dokumenter, der er delt med kunden,
        vises for kunden og indgår i kundens eksport. Skabeloner kan gemmes direkte her fra Skabeloner → "Gem i arkiv".
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 1 }} onClose={() => setError('')}>{error}</Alert>}
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Type</TableCell><TableCell>Titel</TableCell><TableCell>Version</TableCell>
            {!engagementId && <TableCell>Opdrag</TableCell>}<TableCell>Underskrevet</TableCell><TableCell>Delt</TableCell>
            <TableCell>Oprettet</TableCell><TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {shown.length === 0 && <TableRow><TableCell colSpan={8}><Typography variant="body2" color="text.secondary">Ingen dokumenter.</Typography></TableCell></TableRow>}
          {shown.map((d) => (
            <TableRow key={d.id} hover>
              <TableCell>{d.kind_label}</TableCell>
              <TableCell>{d.title}<Typography variant="caption" display="block" color="text.secondary">{d.filename}</Typography></TableCell>
              <TableCell>v{d.version}</TableCell>
              {!engagementId && <TableCell>{d.engagement_title || '–'}</TableCell>}
              <TableCell>{d.signed_on ? `${formatDate(d.signed_on)}${d.signed_note ? ` · ${d.signed_note}` : ''}` : '–'}</TableCell>
              <TableCell>{d.visible_to_client ? <Chip size="small" color="info" label="Delt med kunden" /> : <Chip size="small" label="Internt" />}</TableCell>
              <TableCell>{formatDate(d.created_at)}<Typography variant="caption" display="block" color="text.secondary">{d.created_by}</Typography></TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap' }}>
                <Tooltip title="Hent"><IconButton size="small" onClick={() => download(d).catch((e) => setError(errorText(e)))}><Download fontSize="small" /></IconButton></Tooltip>
                <Tooltip title="Oplysninger"><IconButton size="small" onClick={() => setEdit(d)}><Edit fontSize="small" /></IconButton></Tooltip>
                <Button size="small" onClick={() => newVersion(d)}>Ny version</Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {upload && (
        <Dialog open onClose={() => setUpload(null)} maxWidth="sm" fullWidth>
          <DialogTitle>Upload til arkivet</DialogTitle>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
            <Button component="label" variant="outlined" startIcon={<UploadFile />}>
              {upload.file ? upload.file.name : 'Vælg fil (højst 25 MB)'}
              <input hidden type="file" onChange={(e) => setUpload({ ...upload, file: e.target.files?.[0] || null })} />
            </Button>
            <TextField select size="small" label="Type" value={upload.kind} onChange={(e) => setUpload({ ...upload, kind: e.target.value })}>
              {kinds.map((k) => <MenuItem key={k.value} value={k.value}>{k.label}</MenuItem>)}
            </TextField>
            <TextField size="small" label="Titel" helperText="Samme type og titel som et eksisterende dokument = ny version"
              value={upload.title} onChange={(e) => setUpload({ ...upload, title: e.target.value })} />
            <TextField size="small" type="date" label="Opbevares til (husets politik, valgfri)" InputLabelProps={{ shrink: true }}
              value={upload.retain_until} onChange={(e) => setUpload({ ...upload, retain_until: e.target.value })} />
            <TextField size="small" label="Intern note" value={upload.note} onChange={(e) => setUpload({ ...upload, note: e.target.value })} />
            <FormControlLabel control={<Checkbox checked={upload.visible} onChange={(e) => setUpload({ ...upload, visible: e.target.checked })} />}
              label="Del med kunden (vises i kundens indbakke og eksport)" />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setUpload(null)}>Annullér</Button>
            <Button variant="contained" disabled={!upload.file} onClick={save}>Gem</Button>
          </DialogActions>
        </Dialog>
      )}
      {edit && (
        <Dialog open onClose={() => setEdit(null)} maxWidth="sm" fullWidth>
          <DialogTitle>{edit.title} (v{edit.version})</DialogTitle>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
            <Typography variant="caption" color="text.secondary">SHA-256: {edit.sha256}{edit.source.startsWith('skabelon:') ? ` · fra skabelonen ${edit.source.slice(9)}` : ''}</Typography>
            <TextField size="small" type="date" label="Underskrevet den" InputLabelProps={{ shrink: true }} value={edit.signed_on || ''}
              onChange={(e) => setEdit({ ...edit, signed_on: e.target.value || null })} />
            <TextField size="small" label="Underskrevet af" value={edit.signed_note} onChange={(e) => setEdit({ ...edit, signed_note: e.target.value })} />
            <TextField size="small" type="date" label="Opbevares til" InputLabelProps={{ shrink: true }} value={edit.retain_until || ''}
              onChange={(e) => setEdit({ ...edit, retain_until: e.target.value || null })} />
            <TextField size="small" multiline label="Intern note" value={edit.note} onChange={(e) => setEdit({ ...edit, note: e.target.value })} />
            <FormControlLabel control={<Checkbox checked={edit.visible_to_client} onChange={(e) => setEdit({ ...edit, visible_to_client: e.target.checked })} />}
              label="Del med kunden" />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEdit(null)}>Annullér</Button>
            <Button variant="contained" onClick={() => update(edit.id, {
              signed_on: edit.signed_on, signed_note: edit.signed_note, retain_until: edit.retain_until, note: edit.note,
              visible_to_client: edit.visible_to_client,
            })}>Gem</Button>
          </DialogActions>
        </Dialog>
      )}
    </Paper>
  );
};

export default ClientDocuments;
