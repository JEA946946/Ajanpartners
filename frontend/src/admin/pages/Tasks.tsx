import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, CircularProgress, FormControlLabel, MenuItem, Paper, Switch, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText, FirmClient, FirmTask, REF_TYPES, TASK_KINDS, TASK_STATUS } from '../api';
import { NewTaskDialog, TaskStatusChip, TaskThreadDialog } from '../components/TaskDialogs';

/** Opgaveliste – bruges både på opgavesiden og på kundens side. */
export const TaskTable: React.FC<{ client?: string; clients?: FirmClient[]; showFilters?: boolean }> = ({
  client, clients, showFilters = true,
}) => {
  const [tasks, setTasks] = useState<FirmTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('active');
  const [kind, setKind] = useState('');
  const [clientFilter, setClientFilter] = useState('');
  const [mine, setMine] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const load = useCallback(() => {
    const params: Record<string, string> = {};
    if (status) params.status = status;
    if (kind) params.kind = kind;
    if (client || clientFilter) params.client = client || clientFilter;
    if (mine) params.mine = '1';
    setLoading(true);
    firmApi.get('/tasks', { params })
      .then((r) => { setTasks(r.data.data.tasks); setError(''); })
      .catch((e) => setError(errorText(e, 'Opgaverne kunne ikke hentes')))
      .finally(() => setLoading(false));
  }, [status, kind, client, clientFilter, mine]);

  useEffect(() => { load(); }, [load]);

  const overdue = (t: FirmTask) => t.due_date && t.status !== 'closed' && t.due_date < new Date().toISOString().slice(0, 10);

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center', mb: 2 }}>
        {showFilters && (
          <>
            <TextField select size="small" label="Status" value={status} onChange={(e) => setStatus(e.target.value)} sx={{ minWidth: 170 }}>
              <MenuItem value="active">Alle åbne</MenuItem>
              <MenuItem value="">Alle</MenuItem>
              {Object.entries(TASK_STATUS).map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
            </TextField>
            <TextField select size="small" label="Type" value={kind} onChange={(e) => setKind(e.target.value)} sx={{ minWidth: 140 }}>
              <MenuItem value="">Alle</MenuItem>
              {Object.entries(TASK_KINDS).map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
            </TextField>
            {!client && clients && (
              <TextField select size="small" label="Kunde" value={clientFilter} onChange={(e) => setClientFilter(e.target.value)} sx={{ minWidth: 180 }}>
                <MenuItem value="">Alle</MenuItem>
                {clients.map((c) => <MenuItem key={c.slug} value={c.slug}>{c.name}</MenuItem>)}
              </TextField>
            )}
            <FormControlLabel control={<Switch checked={mine} onChange={(e) => setMine(e.target.checked)} />} label="Mine" />
          </>
        )}
        <Button sx={{ ml: 'auto' }} variant="contained" startIcon={<AddIcon />} onClick={() => setCreating(true)}>
          Ny forespørgsel
        </Button>
      </Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {!client && <TableCell>Kunde</TableCell>}
              <TableCell>Titel</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Reference</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Ansvarlig</TableCell>
              <TableCell>Frist</TableCell>
              <TableCell align="right">Beskeder</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && <TableRow><TableCell colSpan={8} align="center"><CircularProgress size={20} /></TableCell></TableRow>}
            {!loading && tasks.length === 0 && <TableRow><TableCell colSpan={8} align="center">Ingen opgaver.</TableCell></TableRow>}
            {!loading && tasks.map((t) => (
              <TableRow key={t.id} hover sx={{ cursor: 'pointer' }} onClick={() => setOpenId(t.id)}>
                {!client && <TableCell>{t.client_name}</TableCell>}
                <TableCell>
                  <Typography fontSize={13} fontWeight={t.status === 'answered' ? 700 : 400}>{t.title}</Typography>
                  {t.list_name && <Typography variant="caption" color="text.secondary" display="block">{t.list_name}</Typography>}
                  {t.visible_to_client === false && <Typography variant="caption" color="text.secondary">Intern</Typography>}
                </TableCell>
                <TableCell>{t.kind_label}</TableCell>
                <TableCell>{t.reference_type ? `${REF_TYPES[t.reference_type]} ${t.reference_label || t.reference_id}` : '—'}</TableCell>
                <TableCell><TaskStatusChip status={t.status} /></TableCell>
                <TableCell>{t.assigned_name || '—'}</TableCell>
                <TableCell sx={{ color: overdue(t) ? 'error.main' : undefined }}>{formatDate(t.due_date)}</TableCell>
                <TableCell align="right">{t.message_count ?? ''}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TaskThreadDialog taskId={openId} onClose={() => setOpenId(null)} onChanged={load} />
      <NewTaskDialog open={creating} onClose={() => setCreating(false)} onCreated={load} client={client} clients={clients} />
    </Box>
  );
};

const Tasks: React.FC = () => {
  const [clients, setClients] = useState<FirmClient[]>([]);
  useEffect(() => {
    firmApi.get('/clients').then((r) => setClients(r.data.data.clients.filter((c: FirmClient) => c.status !== 'archived'))).catch(() => undefined);
  }, []);
  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 0.5 }}>Opgaver og bilagsforespørgsler</Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Forespørgsler, der er synlige for kunden, vises i kundens indbakke &quot;Beskeder fra revisor&quot;.
      </Typography>
      <TaskTable clients={clients} />
    </Box>
  );
};

export default Tasks;
