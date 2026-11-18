import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Paper, Table, TableBody,
  TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';
import { useAdmin } from '../AdminContext';

export interface Power {
  id: string; client: string; client_name: string; kind: string; kind_label: string; scope: string; holder_id: number | null;
  holder: string | null; given_on: string | null; expires_on: string | null; reference: string; note: string;
  revoked_on: string | null; status: string; status_label: string;
}
export const POA_COLOR: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
  active: 'success', expiring: 'warning', expired: 'error', revoked: 'default',
};
const EMPTY = { id: '', kind: 'skat', scope: '', holder_id: '', given_on: '', expires_on: '', reference: '', note: '' };

/** Fuldmagter, kunden har givet huset. Registreringen erstatter ikke selve fuldmagten hos myndigheden/banken. */
const PowersPanel: React.FC<{ slug: string }> = ({ slug }) => {
  const { staff } = useAdmin();
  const [rows, setRows] = useState<Power[]>([]);
  const [kinds, setKinds] = useState<{ value: string; label: string }[]>([]);
  const [form, setForm] = useState<typeof EMPTY | null>(null);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    firmApi.get(`/clients/${slug}/powers`).then((r) => { setRows(r.data.data.powers); setKinds(r.data.data.kinds); })
      .catch((e) => setError(errorText(e)));
  }, [slug]);
  useEffect(() => { load(); }, [load]);

  const save = async () => {
    if (!form) return;
    const { id, ...body } = form;
    const payload = { ...body, holder_id: body.holder_id || null, given_on: body.given_on || null, expires_on: body.expires_on || null };
    try {
      if (id) await firmApi.put(`/powers/${id}`, payload);
      else await firmApi.post(`/clients/${slug}/powers`, payload);
      setForm(null); setError(''); load();
    } catch (e) { setError(errorText(e)); }
  };
  const revoke = async (p: Power) => {
    try { await firmApi.put(`/powers/${p.id}`, { revoke: true }); load(); } catch (e) { setError(errorText(e)); }
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1 }}>Fuldmagter</Typography>
        <Button size="small" variant="outlined" onClick={() => setForm({ ...EMPTY })}>Registrér fuldmagt</Button>
      </Box>
      <Typography variant="caption" color="text.secondary" component="div" sx={{ mb: 1 }}>
        Her registreres, hvilke fuldmagter kunden har givet huset. Selve fuldmagten gives hos myndigheden eller banken.
        30 dage før udløb oprettes en intern opgave, og fuldmagten vises på Overblik. Fuldmagter slettes ikke – de tilbagekaldes.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 1 }} onClose={() => setError('')}>{error}</Alert>}
      <Table size="small">
        <TableHead>
          <TableRow><TableCell>Type</TableCell><TableCell>Omfang</TableCell><TableCell>Givet til</TableCell><TableCell>Givet</TableCell>
            <TableCell>Udløber</TableCell><TableCell>Status</TableCell><TableCell /></TableRow>
        </TableHead>
        <TableBody>
          {rows.length === 0 && <TableRow><TableCell colSpan={7}><Typography variant="body2" color="text.secondary">Ingen fuldmagter registreret.</Typography></TableCell></TableRow>}
          {rows.map((p) => (
            <TableRow key={p.id}>
              <TableCell>{p.kind_label}</TableCell>
              <TableCell>{p.scope}{p.reference && <Typography variant="caption" display="block" color="text.secondary">{p.reference}</Typography>}</TableCell>
              <TableCell>{p.holder || 'Huset'}</TableCell>
              <TableCell>{p.given_on ? formatDate(p.given_on) : '–'}</TableCell>
              <TableCell>{p.expires_on ? formatDate(p.expires_on) : 'Ingen udløbsdato'}</TableCell>
              <TableCell><Chip size="small" color={POA_COLOR[p.status]} label={p.revoked_on ? `${p.status_label} ${formatDate(p.revoked_on)}` : p.status_label} /></TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap' }}>
                {!p.revoked_on && (
                  <>
                    <Button size="small" onClick={() => setForm({ id: p.id, kind: p.kind, scope: p.scope, holder_id: p.holder_id ? String(p.holder_id) : '',
                      given_on: p.given_on || '', expires_on: p.expires_on || '', reference: p.reference, note: p.note })}>Ret</Button>
                    <Button size="small" color="warning" onClick={() => revoke(p)}>Tilbagekald</Button>
                  </>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {form && (
        <Dialog open onClose={() => setForm(null)} maxWidth="sm" fullWidth>
          <DialogTitle>{form.id ? 'Ret fuldmagt' : 'Registrér fuldmagt'}</DialogTitle>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
            <TextField select size="small" label="Type" value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
              {kinds.map((k) => <MenuItem key={k.value} value={k.value}>{k.label}</MenuItem>)}
            </TextField>
            <TextField size="small" label="Omfang" placeholder="fx Moms og A-skat" value={form.scope} onChange={(e) => setForm({ ...form, scope: e.target.value })} />
            <TextField select size="small" label="Givet til" value={form.holder_id} onChange={(e) => setForm({ ...form, holder_id: e.target.value })}>
              <MenuItem value="">Huset</MenuItem>
              {staff.filter((s) => s.is_active).map((s) => <MenuItem key={s.user_id} value={String(s.user_id)}>{`${s.first_name} ${s.last_name}`.trim() || s.username}</MenuItem>)}
            </TextField>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField fullWidth size="small" type="date" label="Givet den" InputLabelProps={{ shrink: true }} value={form.given_on} onChange={(e) => setForm({ ...form, given_on: e.target.value })} />
              <TextField fullWidth size="small" type="date" label="Udløber" InputLabelProps={{ shrink: true }} value={form.expires_on} onChange={(e) => setForm({ ...form, expires_on: e.target.value })} />
            </Box>
            <TextField size="small" label="Reference (valgfri)" value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} />
            <TextField size="small" multiline label="Note" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setForm(null)}>Annullér</Button>
            <Button variant="contained" disabled={!form.scope.trim()} onClick={save}>Gem</Button>
          </DialogActions>
        </Dialog>
      )}
    </Paper>
  );
};

export default PowersPanel;
