import React, { useEffect, useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  MenuItem, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import api from '../services/api';
import { useClient } from '../hooks/useClient';

interface Grant {
  id: string; scope: string; staff_scope: string; state: string; valid_until: string | null;
  request_note: string; requested_by: string | null; requested_at: string | null;
  accepted_at: string | null; revoked_at: string | null;
  staff: { id: number; name: string; role: string }[];
}

const SCOPE: Record<string, string> = { read: 'Læse', bookkeeping: 'Bogføre', full: 'Fuld adgang' };
const STATE: Record<string, { label: string; color: 'success' | 'warning' | 'default' | 'error' }> = {
  active: { label: 'Aktiv', color: 'success' },
  pending: { label: 'Afventer jer', color: 'warning' },
  expired: { label: 'Udløbet', color: 'default' },
  revoked: { label: 'Tilbagekaldt', color: 'error' },
};
const fmt = (s: string | null) => (s ? new Date(s).toLocaleDateString('da-DK') : '–');

/** Indstillinger → Revisoradgang: kunden styrer revisorhusets adgang. */
const AccessGrants: React.FC = () => {
  const { current, firm } = useClient();
  const isAdmin = current?.access.role === 'admin' && current?.access.via === 'member';
  const [grants, setGrants] = useState<Grant[]>([]);
  const [staff, setStaff] = useState<{ id: number; name: string; role: string; title: string }[]>([]);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ scope: 'bookkeeping', staff_scope: 'all', valid_until: '', staff_ids: [] as number[] });

  const load = () => api.get('/access-grants').then((r) => {
    setGrants(r.data.data.grants);
    setStaff(r.data.data.staff);
  }).catch((e) => setError(e.response?.data?.message || 'Kunne ikke hente adgange'));
  useEffect(() => { load(); }, []);

  const act = async (path: string, body: object = {}) => {
    setError('');
    try { await api.post(path, body); await load(); } catch (e: any) { setError(e.response?.data?.message || 'Fejl'); }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Revisoradgang</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Her bestemmer I, om {firm?.name || 'Ajan Partners'} må arbejde i jeres bogføring. Adgangen kan
        begrænses i omfang og tid og trækkes tilbage med det samme. Alt, revisor gør, står i audit-loggen.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {!isAdmin && <Alert severity="info" sx={{ mb: 2 }}>Kun virksomhedens administrator kan ændre adgangen.</Alert>}
      <Card variant="outlined">
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Status</TableCell><TableCell>Omfang</TableCell><TableCell>Hvem</TableCell>
                <TableCell>Anmodet</TableCell><TableCell>Godkendt</TableCell><TableCell>Gyldig til</TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              {grants.map((g) => (
                <TableRow key={g.id}>
                  <TableCell><Chip size="small" color={STATE[g.state]?.color} label={STATE[g.state]?.label || g.state} /></TableCell>
                  <TableCell>{SCOPE[g.scope]}</TableCell>
                  <TableCell>{g.staff_scope === 'all' ? 'Alle i revisorhuset' : g.staff.map((s) => s.name).join(', ')}</TableCell>
                  <TableCell>{fmt(g.requested_at)}{g.requested_by ? ` · ${g.requested_by}` : ''}</TableCell>
                  <TableCell>{fmt(g.accepted_at)}</TableCell>
                  <TableCell>{g.valid_until ? fmt(g.valid_until) : 'Indtil videre'}</TableCell>
                  <TableCell align="right">
                    {isAdmin && g.state === 'pending' && (
                      <Button size="small" onClick={() => act(`/access-grants/${g.id}/accept`)}>Godkend</Button>
                    )}
                    {isAdmin && (g.state === 'active' || g.state === 'pending') && (
                      <Button size="small" color="error" onClick={() => act(`/access-grants/${g.id}/revoke`)}>
                        {g.state === 'pending' ? 'Afvis' : 'Tilbagekald'}
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {grants.length === 0 && (
                <TableRow><TableCell colSpan={7}>Revisorhuset har ingen adgang.</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
          {isAdmin && <Button sx={{ mt: 2 }} variant="outlined" onClick={() => setOpen(true)}>Giv ny adgang</Button>}
        </CardContent>
      </Card>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Giv revisoradgang</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField select label="Omfang" value={form.scope} onChange={(e) => setForm({ ...form, scope: e.target.value })}>
              {Object.entries(SCOPE).map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
            </TextField>
            <TextField select label="Hvem" value={form.staff_scope}
              onChange={(e) => setForm({ ...form, staff_scope: e.target.value })}>
              <MenuItem value="all">Alle i revisorhuset, der arbejder for os</MenuItem>
              <MenuItem value="named">Kun navngivne medarbejdere</MenuItem>
            </TextField>
            {form.staff_scope === 'named' && (
              <TextField select SelectProps={{ multiple: true }} label="Medarbejdere" value={form.staff_ids}
                onChange={(e) => setForm({ ...form, staff_ids: e.target.value as unknown as number[] })}>
                {staff.map((s) => <MenuItem key={s.id} value={s.id}>{s.name}{s.title ? ` (${s.title})` : ''}</MenuItem>)}
              </TextField>
            )}
            <TextField type="date" label="Gyldig til (valgfri)" InputLabelProps={{ shrink: true }}
              value={form.valid_until} onChange={(e) => setForm({ ...form, valid_until: e.target.value })} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Annuller</Button>
          <Button variant="contained" onClick={async () => {
            await act('/access-grants/create', { ...form, valid_until: form.valid_until || null });
            setOpen(false);
          }}>Giv adgang</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AccessGrants;
