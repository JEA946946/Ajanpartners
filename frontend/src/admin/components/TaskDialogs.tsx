import React, { useEffect, useState } from 'react';
import {
  Alert, Box, Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel,
  Grid, MenuItem, Paper, Switch, TextField, Typography,
} from '@mui/material';
import { AttachFile as AttachIcon } from '@mui/icons-material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { downloadFile, errorText, FirmClient, FirmTask, REF_TYPES, TASK_KINDS, TASK_STATUS } from '../api';
import { useAdmin } from '../AdminContext';

export const TaskStatusChip: React.FC<{ status: FirmTask['status'] }> = ({ status }) => {
  const color = status === 'answered' ? 'info' : status === 'open' ? 'warning' : status === 'closed' ? 'default' : 'primary';
  return <Chip size="small" color={color as any} label={TASK_STATUS[status]} />;
};

/** Ny opgave eller forespørgsel til en kunde. */
export const NewTaskDialog: React.FC<{
  open: boolean; onClose: () => void; onCreated: (t: FirmTask) => void; client?: string; clients?: FirmClient[];
}> = ({ open, onClose, onCreated, client, clients }) => {
  const { staff } = useAdmin();
  const empty = {
    client: client || '', kind: 'bilag_mangler', title: '', message: '', reference_type: '', reference_id: '',
    reference_label: '', due_date: '', assigned_to: '' as number | '', visible_to_client: true,
  };
  const [form, setForm] = useState(empty);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) { setForm({ ...empty, client: client || '' }); setError(''); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, client]);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) => setForm((f) => {
    const next: any = { ...f, [k]: e.target.value };
    if (k === 'kind') next.visible_to_client = e.target.value !== 'opgave';
    if (k === 'reference_type' && e.target.value === '') { next.reference_id = ''; next.reference_label = ''; }
    return next;
  });

  const save = async () => {
    setSaving(true);
    try {
      const r = await firmApi.post('/tasks', { ...form, assigned_to: form.assigned_to || undefined });
      onCreated(r.data.data.task);
      onClose();
    } catch (e) {
      setError(errorText(e, 'Opgaven kunne ikke oprettes'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Ny opgave eller forespørgsel</DialogTitle>
      <DialogContent>
        <Grid container spacing={2} sx={{ mt: 0 }}>
          {!client && (
            <Grid item xs={12}>
              <TextField select fullWidth size="small" label="Kunde" value={form.client} onChange={set('client')}>
                {(clients || []).map((c) => <MenuItem key={c.slug} value={c.slug}>{c.name}</MenuItem>)}
              </TextField>
            </Grid>
          )}
          <Grid item xs={12} sm={5}>
            <TextField select fullWidth size="small" label="Type" value={form.kind} onChange={set('kind')}>
              {Object.entries(TASK_KINDS).map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={7}>
            <TextField fullWidth size="small" label="Titel" value={form.title} onChange={set('title')}
              placeholder={form.kind === 'bilag_mangler' ? 'Mangler bilag til betaling 12-03' : ''} />
          </Grid>
          <Grid item xs={12}>
            <TextField fullWidth multiline minRows={3} size="small"
              label={form.visible_to_client ? 'Besked til kunden' : 'Beskrivelse (intern)'}
              value={form.message} onChange={set('message')} />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField select fullWidth size="small" label="Reference" value={form.reference_type} onChange={set('reference_type')}>
              {Object.entries(REF_TYPES).map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
            </TextField>
          </Grid>
          {form.reference_type && (
            <>
              <Grid item xs={12} sm={4}>
                <TextField fullWidth size="small" label="Id" value={form.reference_id} onChange={set('reference_id')} />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField fullWidth size="small" label="Tekst til kunden" value={form.reference_label}
                  onChange={set('reference_label')} placeholder="12-03, 1.250,00 kr." />
              </Grid>
            </>
          )}
          <Grid item xs={12} sm={6}>
            <TextField fullWidth size="small" type="date" label="Frist" InputLabelProps={{ shrink: true }}
              value={form.due_date} onChange={set('due_date')} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField select fullWidth size="small" label="Ansvarlig" value={form.assigned_to} onChange={set('assigned_to')}>
              <MenuItem value="">Mig selv</MenuItem>
              {staff.filter((s) => s.is_active).map((s) => (
                <MenuItem key={s.user_id} value={s.user_id}>{`${s.first_name} ${s.last_name}`.trim() || s.username}</MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12}>
            <FormControlLabel label="Vis for kunden (i kundens indbakke)" control={
              <Switch checked={form.visible_to_client} onChange={(e) => setForm({ ...form, visible_to_client: e.target.checked })} />} />
          </Grid>
        </Grid>
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Annullér</Button>
        <Button variant="contained" onClick={save} disabled={saving || !form.title.trim() || !form.client}>Opret</Button>
      </DialogActions>
    </Dialog>
  );
};

/** Tråden i en opgave: svar, statusskift og vedhæftede bilag. */
export const TaskThreadDialog: React.FC<{ taskId: string | null; onClose: () => void; onChanged: () => void }> = ({
  taskId, onClose, onChanged,
}) => {
  const [task, setTask] = useState<FirmTask | null>(null);
  const [reply, setReply] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setTask(null); setReply(''); setError('');
    if (taskId) {
      firmApi.get(`/tasks/${taskId}`).then((r) => setTask(r.data.data.task))
        .catch((e) => setError(errorText(e, 'Opgaven kunne ikke hentes')));
    }
  }, [taskId]);

  const run = async (fn: () => Promise<any>) => {
    setBusy(true);
    try {
      const r = await fn();
      setTask(r.data.data.task);
      setError('');
      onChanged();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  };

  const send = () => run(async () => {
    const r = await firmApi.post(`/tasks/${taskId}/messages`, { body: reply });
    setReply('');
    return r;
  });
  const setStatus = (status: string) => run(() => firmApi.put(`/tasks/${taskId}`, { status }));

  return (
    <Dialog open={!!taskId} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {task ? task.title : 'Opgave'}
        {task && <Box component="span" sx={{ ml: 1 }}><TaskStatusChip status={task.status} /></Box>}
      </DialogTitle>
      <DialogContent dividers>
        {!task && !error && <CircularProgress size={22} />}
        {task && (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {task.client_name} · {task.kind_label}
              {task.reference_type && ` · ${REF_TYPES[task.reference_type]} ${task.reference_label || task.reference_id}`}
              {task.due_date && ` · frist ${formatDate(task.due_date)}`}
              {task.assigned_name && ` · ${task.assigned_name}`}
              {!task.visible_to_client && ' · intern'}
            </Typography>
            {task.description && <Typography sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>{task.description}</Typography>}
            {(task.messages || []).length === 0 && <Typography color="text.secondary">Ingen beskeder endnu.</Typography>}
            {(task.messages || []).map((m) => (
              <Paper key={m.id} variant="outlined" sx={{
                p: 1.5, mb: 1, maxWidth: '80%', ml: m.from_firm ? 'auto' : 0,
                bgcolor: m.from_firm ? 'rgba(11,61,92,0.06)' : '#fff',
              }}>
                <Typography variant="caption" color="text.secondary">
                  {m.from_firm ? 'Revisor' : 'Kunden'} · {m.author} · {new Date(m.created_at).toLocaleString('da-DK')}
                </Typography>
                <Typography sx={{ whiteSpace: 'pre-wrap' }}>{m.body}</Typography>
                {m.document_id && (
                  <Button size="small" startIcon={<AttachIcon />} sx={{ mt: 0.5 }}
                    onClick={() => downloadFile(`/tasks/${task.id}/messages/${m.id}/document`, 'bilag')
                      .catch((e) => setError(errorText(e, 'Bilaget kunne ikke hentes (kræver kundens samtykke)')))}>
                    Hent vedhæftet bilag
                  </Button>
                )}
              </Paper>
            ))}
            {task.status !== 'closed' && (
              <Box sx={{ mt: 2 }}>
                <TextField fullWidth multiline minRows={2} size="small" label="Svar" value={reply} onChange={(e) => setReply(e.target.value)} />
              </Box>
            )}
          </>
        )}
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </DialogContent>
      <DialogActions>
        {task && task.status !== 'closed' && (
          <>
            {task.status !== 'in_progress' && <Button disabled={busy} onClick={() => setStatus('in_progress')}>Under behandling</Button>}
            <Button disabled={busy} color="success" onClick={() => setStatus('closed')}>Luk sagen</Button>
          </>
        )}
        {task?.status === 'closed' && <Button disabled={busy} onClick={() => setStatus('open')}>Genåbn</Button>}
        <Box sx={{ flex: 1 }} />
        <Button onClick={onClose}>Luk</Button>
        {task && task.status !== 'closed' && (
          <Button variant="contained" disabled={busy || !reply.trim()} onClick={send}>Send svar</Button>
        )}
      </DialogActions>
    </Dialog>
  );
};
