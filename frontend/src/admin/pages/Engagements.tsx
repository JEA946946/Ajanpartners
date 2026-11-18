import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Autocomplete, Box, Button, Checkbox, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  FormControlLabel, LinearProgress, MenuItem, Paper, Table, TableBody, TableCell, TableHead, TableRow, TextField,
  ToggleButton, ToggleButtonGroup, Typography,
} from '@mui/material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';
import { useAdmin } from '../AdminContext';

export interface EngagementRow {
  id: string; client: string; client_name: string; kind: string; kind_label: string; title: string;
  year_label: string; partner: string | null; manager: string | null; status: string; status_label: string;
  deadline: string | null; budget_hours: string | null; progress: { done: number; total: number };
  signoffs: { step: string; user: string; at: string }[];
}
export interface Meta {
  kinds: { value: string; label: string; suggested: string[]; letter: string | null; assurance: boolean }[];
  statuses: { value: string; label: string }[];
  checklist_templates: { id: string; title: string; category: string }[];
}
export const STATUS_COLOR: Record<string, 'default' | 'info' | 'warning' | 'success' | 'primary'> = {
  planlagt: 'default', i_gang: 'info', review: 'warning', afsluttet: 'success', leveret: 'primary',
};

/** Tabel over opdrag – bruges på Opdrag-siden og under kunden. */
export const EngagementTable: React.FC<{ rows: EngagementRow[]; showClient?: boolean }> = ({ rows, showClient = true }) => {
  const navigate = useNavigate();
  const today = new Date().toISOString().slice(0, 10);
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          {showClient && <TableCell>Kunde</TableCell>}<TableCell>Opdrag</TableCell><TableCell>År</TableCell>
          <TableCell>Partner</TableCell><TableCell>Status</TableCell><TableCell>Tjeklister</TableCell><TableCell>Frist</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.length === 0 && <TableRow><TableCell colSpan={7}><Typography variant="body2" color="text.secondary">Ingen opdrag.</Typography></TableCell></TableRow>}
        {rows.map((e) => (
          <TableRow key={e.id} hover sx={{ cursor: 'pointer' }} onClick={() => navigate(`/admin/engagements/${e.id}`)}>
            {showClient && <TableCell>{e.client_name}</TableCell>}
            <TableCell>{e.title}</TableCell>
            <TableCell>{e.year_label || '–'}</TableCell>
            <TableCell>{e.partner || '–'}</TableCell>
            <TableCell><Chip size="small" color={STATUS_COLOR[e.status]} label={e.status_label} /></TableCell>
            <TableCell sx={{ minWidth: 110 }}>
              {e.progress.total ? (
                <Box>
                  <LinearProgress variant="determinate" value={(100 * e.progress.done) / e.progress.total} />
                  <Typography variant="caption">{e.progress.done}/{e.progress.total}</Typography>
                </Box>
              ) : '–'}
            </TableCell>
            <TableCell sx={{ color: e.deadline && e.deadline < today && e.status !== 'leveret' ? 'error.main' : undefined }}>
              {e.deadline ? formatDate(e.deadline) : '–'}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

/** Dialog: opret opdrag (med foreslåede tjeklister fra de verificerede skabeloner). */
export const CreateEngagementDialog: React.FC<{
  open: boolean; onClose: () => void; meta: Meta | null; clients: { slug: string; name: string }[]; fixedClient?: string;
  onCreated: (id: string) => void;
}> = ({ open, onClose, meta, clients, fixedClient, onCreated }) => {
  const { staff } = useAdmin();
  const [form, setForm] = useState({ client: fixedClient || '', kind: 'opstilling', year: '', title: '', partner_id: '', budget_hours: '' });
  const [years, setYears] = useState<{ id: string; label: string }[]>([]);
  const [lists, setLists] = useState<string[]>([]);
  const [error, setError] = useState('');

  useEffect(() => { if (fixedClient) setForm((f) => ({ ...f, client: fixedClient })); }, [fixedClient]);
  useEffect(() => {
    if (!form.client) { setYears([]); return; }
    firmApi.post('/templates/afstemning-moms/render', { client: form.client }).then((r) => {
      const ys = (r.data.data.years || []).map((y: any) => ({ id: y.id, label: y.label || `${y.start} – ${y.end}` }));
      setYears(ys);
      setForm((f) => ({ ...f, year: r.data.data.year || ys[0]?.id || '' }));
    }).catch(() => setYears([]));
  }, [form.client]);
  useEffect(() => { setLists(meta?.kinds.find((k) => k.value === form.kind)?.suggested || []); }, [form.kind, meta]);

  const partners = staff.filter((s) => s.role === 'partner' && s.is_active);
  const create = async () => {
    try {
      const r = await firmApi.post('/engagements', { ...form, checklists: lists });
      onCreated(r.data.data.engagement.id);
    } catch (e) { setError(errorText(e)); }
  };
  const tplTitle = (id: string) => meta?.checklist_templates.find((t) => t.id === id)?.title || id;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Nyt opdrag</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
        {error && <Alert severity="error">{error}</Alert>}
        {!fixedClient && (
          <Autocomplete size="small" options={clients} getOptionLabel={(o) => o.name}
            value={clients.find((c) => c.slug === form.client) || null}
            onChange={(_, v) => setForm({ ...form, client: v?.slug || '' })}
            renderInput={(p) => <TextField {...p} label="Kunde" />} />
        )}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField select fullWidth size="small" label="Opdragstype" value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
            {meta?.kinds.map((k) => <MenuItem key={k.value} value={k.value}>{k.label}</MenuItem>)}
          </TextField>
          <TextField select fullWidth size="small" label="Regnskabsår" value={form.year} onChange={(e) => setForm({ ...form, year: e.target.value })}>
            <MenuItem value="">Ingen</MenuItem>
            {years.map((y) => <MenuItem key={y.id} value={y.id}>{y.label}</MenuItem>)}
          </TextField>
        </Box>
        <TextField size="small" label="Titel (valgfri)" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField select fullWidth size="small" label="Partner" value={form.partner_id} onChange={(e) => setForm({ ...form, partner_id: e.target.value })}>
            <MenuItem value="">–</MenuItem>
            {partners.map((s) => <MenuItem key={s.user_id} value={s.user_id}>{`${s.first_name} ${s.last_name}`.trim() || s.username}</MenuItem>)}
          </TextField>
          <TextField fullWidth size="small" type="number" label="Timebudget" value={form.budget_hours} onChange={(e) => setForm({ ...form, budget_hours: e.target.value })} />
        </Box>
        <Box>
          <Typography variant="subtitle2">Tjeklister</Typography>
          <Typography variant="caption" color="text.secondary">Punkterne hentes fra de verificerede skabeloner og flettes for kunden og året. Fristen sættes automatisk for årsrapportopdrag.</Typography>
          {(meta?.kinds.find((k) => k.value === form.kind)?.suggested || []).map((id) => (
            <FormControlLabel key={id} sx={{ display: 'block' }} label={tplTitle(id)} control={
              <Checkbox size="small" checked={lists.includes(id)} onChange={(e) => setLists(e.target.checked ? [...lists, id] : lists.filter((x) => x !== id))} />} />
          ))}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Annullér</Button>
        <Button variant="contained" disabled={!form.client} onClick={create}>Opret</Button>
      </DialogActions>
    </Dialog>
  );
};

/** Admin → Opdrag: alle opdrag med status, tjeklistefremdrift og frist. */
const Engagements: React.FC = () => {
  const navigate = useNavigate();
  const [rows, setRows] = useState<EngagementRow[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [clients, setClients] = useState<{ slug: string; name: string }[]>([]);
  const [filter, setFilter] = useState('open');
  const [status, setStatus] = useState('');
  const [open, setOpen] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    const params: Record<string, string> = {};
    if (filter === 'open') params.open = '1';
    if (filter === 'mine') { params.mine = '1'; params.open = '1'; }
    if (status) params.status = status;
    firmApi.get('/engagements', { params }).then((r) => setRows(r.data.data.engagements))
      .catch((e) => setError(errorText(e, 'Opdrag kunne ikke hentes')));
  }, [filter, status]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    firmApi.get('/engagements/meta').then((r) => setMeta(r.data.data)).catch(() => undefined);
    firmApi.get('/clients').then((r) => setClients((r.data.data.clients || []).map((c: any) => ({ slug: c.slug, name: c.name })))).catch(() => undefined);
  }, []);

  return (
    <Box sx={{ maxWidth: 1200 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
        <Typography variant="h5" sx={{ flex: 1 }}>Opdrag</Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>Nyt opdrag</Button>
      </Box>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Opdrag pr. kunde og regnskabsår med tjeklister, og udført af / gennemgået af / godkendt af (BEK 512/2024 § 3, stk. 1, nr. 5).
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <ToggleButtonGroup size="small" exclusive value={filter} onChange={(_, v) => v && setFilter(v)}>
          <ToggleButton value="open">Åbne</ToggleButton>
          <ToggleButton value="mine">Mine</ToggleButton>
          <ToggleButton value="all">Alle</ToggleButton>
        </ToggleButtonGroup>
        <TextField select size="small" label="Status" value={status} sx={{ minWidth: 180 }} onChange={(e) => setStatus(e.target.value)}>
          <MenuItem value="">Alle</MenuItem>
          {meta?.statuses.map((s) => <MenuItem key={s.value} value={s.value}>{s.label}</MenuItem>)}
        </TextField>
      </Box>
      <Paper><EngagementTable rows={rows} /></Paper>
      <CreateEngagementDialog open={open} onClose={() => setOpen(false)} meta={meta} clients={clients}
        onCreated={(id) => navigate(`/admin/engagements/${id}`)} />
    </Box>
  );
};

export default Engagements;
