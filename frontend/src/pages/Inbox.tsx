import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, Chip, CircularProgress, Divider, List, ListItemButton, ListItemText, Paper, TextField,
  ToggleButton, ToggleButtonGroup, Typography,
} from '@mui/material';
import { AttachFile as AttachIcon, Send as SendIcon } from '@mui/icons-material';
import api from '../services/api';
import { useClient } from '../hooks/useClient';
import { formatDate } from '../utils/dateFormat';

interface Message { id: string; author: string | null; from_firm: boolean; body: string; document_id: string | null; created_at: string }
interface Task {
  id: string; title: string; description: string; kind: string; kind_label: string; status: string; status_label: string;
  reference_type: string; reference_label: string; reference_id: string; due_date: string | null;
  assigned_name: string | null; created_at: string; updated_at: string; message_count?: number | null; messages?: Message[];
}

const STATUS_COLOR: Record<string, 'warning' | 'info' | 'default' | 'primary'> = {
  open: 'warning', answered: 'info', in_progress: 'primary', closed: 'default',
};
const STATUS_TEXT: Record<string, string> = {
  open: 'Venter på dit svar', answered: 'Besvaret', in_progress: 'Revisor arbejder på det', closed: 'Lukket',
};
const REF_TEXT: Record<string, string> = { entry: 'Postering', bank_line: 'Banklinje', document: 'Bilag' };

/** "Beskeder fra revisor": spørgsmål og bilagsforespørgsler fra Ajan Partners. */
const Inbox: React.FC = () => {
  const { canWrite } = useClient();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<'active' | ''>('active');
  const [selected, setSelected] = useState<Task | null>(null);
  const [reply, setReply] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    api.get('/inbox', { params: { status: filter || undefined } })
      .then((r) => { setTasks(r.data.data.tasks); setError(''); })
      .catch((e) => setError(e?.response?.data?.message || 'Beskederne kunne ikke hentes'))
      .finally(() => setLoading(false));
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const open = (id: string) => {
    setReply(''); setFile(null);
    api.get(`/inbox/${id}`).then((r) => setSelected(r.data.data.task))
      .catch((e) => setError(e?.response?.data?.message || 'Beskeden kunne ikke hentes'));
  };

  const send = async () => {
    if (!selected) return;
    setSending(true);
    try {
      let document_id: string | undefined;
      if (file) {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('description', `Svar til revisor: ${selected.title}`);
        const up = await api.post('/documents', fd, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 60000 });
        document_id = up.data.data?.document?.id || up.data.data?.id;
      }
      const r = await api.post(`/inbox/${selected.id}/reply`, { body: reply, document_id });
      setSelected(r.data.data.task);
      setReply(''); setFile(null);
      load();
    } catch (e: any) {
      setError(e?.response?.data?.message || 'Svaret kunne ikke sendes');
    } finally {
      setSending(false);
    }
  };

  const waiting = tasks.filter((t) => t.status === 'open').length;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Beskeder fra revisor</Typography>
        {waiting > 0 && <Chip sx={{ ml: 1.5 }} color="warning" size="small" label={`${waiting} venter på dig`} />}
        <ToggleButtonGroup sx={{ ml: 'auto' }} size="small" exclusive value={filter} onChange={(_, v) => v !== null && setFilter(v)}>
          <ToggleButton value="active">Åbne</ToggleButton>
          <ToggleButton value="">Alle</ToggleButton>
        </ToggleButtonGroup>
      </Box>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', flexWrap: { xs: 'wrap', md: 'nowrap' } }}>
        <Paper sx={{ width: { xs: '100%', md: 360 }, flexShrink: 0 }}>
          {loading && <Box sx={{ p: 2, textAlign: 'center' }}><CircularProgress size={22} /></Box>}
          {!loading && tasks.length === 0 && (
            <Typography sx={{ p: 2 }} color="text.secondary">Ingen beskeder fra revisor. Godt gået!</Typography>
          )}
          <List dense disablePadding>
            {tasks.map((t) => (
              <React.Fragment key={t.id}>
                <ListItemButton selected={selected?.id === t.id} onClick={() => open(t.id)}>
                  <ListItemText
                    primary={<Typography fontWeight={t.status === 'open' ? 700 : 400} fontSize={13}>{t.title}</Typography>}
                    secondary={`${t.kind_label} · ${formatDate(t.created_at)}${t.due_date ? ` · svar senest ${formatDate(t.due_date)}` : ''}`} />
                  <Chip size="small" color={STATUS_COLOR[t.status]} label={STATUS_TEXT[t.status] || t.status_label} />
                </ListItemButton>
                <Divider />
              </React.Fragment>
            ))}
          </List>
        </Paper>

        <Paper sx={{ flex: 1, p: 2, minHeight: 300, width: '100%' }}>
          {!selected ? (
            <Typography color="text.secondary">Vælg en besked til venstre.</Typography>
          ) : (
            <>
              <Typography variant="h6">{selected.title}</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {selected.kind_label}
                {selected.reference_type && ` · ${REF_TEXT[selected.reference_type] || ''} ${selected.reference_label || selected.reference_id}`}
                {selected.assigned_name && ` · ${selected.assigned_name}, Ajan Partners`}
              </Typography>
              {selected.description && <Typography sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>{selected.description}</Typography>}
              {(selected.messages || []).map((m) => (
                <Paper key={m.id} variant="outlined" sx={{
                  p: 1.5, mb: 1, maxWidth: '85%', ml: m.from_firm ? 0 : 'auto',
                  bgcolor: m.from_firm ? 'rgba(11,61,92,0.06)' : '#fff',
                }}>
                  <Typography variant="caption" color="text.secondary">
                    {m.from_firm ? 'Revisor' : 'Dig'} · {m.author} · {new Date(m.created_at).toLocaleString('da-DK')}
                  </Typography>
                  <Typography sx={{ whiteSpace: 'pre-wrap' }}>{m.body}</Typography>
                  {m.document_id && <Chip size="small" icon={<AttachIcon />} label="Bilag vedhæftet" sx={{ mt: 0.5 }} />}
                </Paper>
              ))}
              {selected.status !== 'closed' ? (
                <Box sx={{ mt: 2 }}>
                  <TextField fullWidth multiline minRows={3} size="small" label="Dit svar" value={reply} onChange={(e) => setReply(e.target.value)} />
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                    {canWrite && (
                      <Button component="label" startIcon={<AttachIcon />} variant="outlined" size="small">
                        {file ? file.name : 'Vedhæft bilag'}
                        <input hidden type="file" accept="image/*,application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                      </Button>
                    )}
                    {file && <Button size="small" onClick={() => setFile(null)}>Fjern</Button>}
                    <Button sx={{ ml: 'auto' }} variant="contained" startIcon={<SendIcon />} disabled={sending || (!reply.trim() && !file)} onClick={send}>
                      Send svar
                    </Button>
                  </Box>
                </Box>
              ) : (
                <Alert severity="info" sx={{ mt: 2 }}>Sagen er lukket af revisor.</Alert>
              )}
            </>
          )}
        </Paper>
      </Box>
    </Box>
  );
};

export default Inbox;
