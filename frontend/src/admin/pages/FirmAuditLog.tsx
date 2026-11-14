import React, { useEffect, useState } from 'react';
import {
  Alert, Box, CircularProgress, MenuItem, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  TextField, Typography,
} from '@mui/material';
import { firmApi } from '../../services/api';
import { errorText, FirmClient } from '../api';
import { useAdmin } from '../AdminContext';

interface Entry {
  id: number; timestamp: string; user: string | null; client: string | null; client_name: string | null;
  action: string; detail: Record<string, any>; ip: string | null;
}

const ACTIONS: Record<string, string> = {
  write: 'Ændring i kundens bøger', client_created: 'Kunde oprettet', client_updated: 'Kunde ændret',
  client_archived: 'Kunde arkiveret', access_requested: 'Adgang anmodet', user_invited: 'Bruger inviteret',
  package_created: 'Pakke oprettet', package_updated: 'Pakke ændret', staff_created: 'Medarbejder oprettet',
  staff_updated: 'Medarbejder ændret', firm_updated: 'Firmaoplysninger ændret', task_created: 'Opgave oprettet',
  task_updated: 'Opgave ændret', task_deleted: 'Opgave slettet', task_message: 'Besked til kunden',
  document_viewed: 'Bilag hentet', trial_balance_view: 'Saldobalance vist', trial_balance_export: 'Saldobalance eksporteret',
  account_comment: 'Kontokommentar',
};

const describe = (e: Entry) => {
  const d = e.detail || {};
  if (e.action === 'write') return `${d.method} ${String(d.path || '').replace('/api/v1/', '')} → ${d.status}`;
  if (d.changes) return Object.keys(d.changes).join(', ');
  return Object.entries(d).map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`).join(' · ');
};

const FirmAuditLog: React.FC = () => {
  const { staff, role } = useAdmin();
  const [entries, setEntries] = useState<Entry[]>([]);
  const [clients, setClients] = useState<FirmClient[]>([]);
  const [client, setClient] = useState('');
  const [user, setUser] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    firmApi.get('/clients').then((r) => setClients(r.data.data.clients)).catch(() => undefined);
  }, []);
  useEffect(() => {
    setLoading(true);
    firmApi.get('/audit-log', { params: { client: client || undefined, user: user || undefined, limit: 500 } })
      .then((r) => { setEntries(r.data.data.entries); setError(''); })
      .catch((e) => setError(errorText(e, 'Loggen kunne ikke hentes')))
      .finally(() => setLoading(false));
  }, [client, user]);

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 0.5 }}>Audit-log</Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Hvem i Ajan Partners var inde hos hvilken kunde, hvornår og hvad der blev ændret. Detaljerne står i kundens egen hash-kædede log.
        {role !== 'partner' && role !== 'revisor' && ' Du ser kun dine egne handlinger.'}
      </Typography>
      <Paper sx={{ p: 1.5, mb: 2, display: 'flex', gap: 1.5 }}>
        <TextField select size="small" label="Kunde" value={client} onChange={(e) => setClient(e.target.value)} sx={{ minWidth: 220 }}>
          <MenuItem value="">Alle</MenuItem>
          {clients.map((c) => <MenuItem key={c.slug} value={c.slug}>{c.name}</MenuItem>)}
        </TextField>
        {(role === 'partner' || role === 'revisor') && (
          <TextField select size="small" label="Medarbejder" value={user} onChange={(e) => setUser(e.target.value)} sx={{ minWidth: 200 }}>
            <MenuItem value="">Alle</MenuItem>
            {staff.map((s) => <MenuItem key={s.user_id} value={String(s.user_id)}>{`${s.first_name} ${s.last_name}`.trim() || s.username}</MenuItem>)}
          </TextField>
        )}
        {loading && <CircularProgress size={18} />}
      </Paper>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow><TableCell>Tidspunkt</TableCell><TableCell>Medarbejder</TableCell><TableCell>Kunde</TableCell>
              <TableCell>Handling</TableCell><TableCell>Detaljer</TableCell><TableCell>IP</TableCell></TableRow>
          </TableHead>
          <TableBody>
            {!loading && entries.length === 0 && <TableRow><TableCell colSpan={6} align="center">Ingen hændelser.</TableCell></TableRow>}
            {entries.map((e) => (
              <TableRow key={e.id}>
                <TableCell sx={{ whiteSpace: 'nowrap' }}>{new Date(e.timestamp).toLocaleString('da-DK')}</TableCell>
                <TableCell>{e.user || '—'}</TableCell>
                <TableCell>{e.client_name || '—'}</TableCell>
                <TableCell>{ACTIONS[e.action] || e.action}</TableCell>
                <TableCell sx={{ maxWidth: 380, wordBreak: 'break-word' }}>{describe(e)}</TableCell>
                <TableCell>{e.ip || ''}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default FirmAuditLog;
