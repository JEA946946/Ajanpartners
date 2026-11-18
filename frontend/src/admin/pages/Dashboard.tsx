import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Box, Card, CardActionArea, CardContent, Chip, Grid, List, ListItemButton, ListItemText, Paper,
  ToggleButton, ToggleButtonGroup, Typography,
} from '@mui/material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';
import { useAdmin } from '../AdminContext';
import { kr } from '../components/FeePanel';
import { POA_COLOR, Power } from '../components/PowersPanel';

interface Data {
  today: string; clients: number;
  deadlines: { date: string; kind: string; title: string; client: string; client_name: string; engagement?: string; responsible_name: string | null }[];
  deadlines_total: number;
  engagements: { open: number; by_status: { value: string; label: string; count: number }[]; overdue: { id: string; title: string; client_name: string; deadline: string; status_label: string }[] };
  kyc: { ok: number; due: number; missing: number; draft: number; clients: { client: string; client_name: string; status: string }[] };
  independence: { year: number; mine_signed: boolean; conflicts: number; missing?: string[] };
  tasks: { answered_by_client: number; mine_open: number };
  powers: Power[];
  terms_pending: { client: string; client_name: string; users: number }[];
  evaluation_missing: boolean;
  unbilled?: { time_value: string; oldest: string | null; due_installments: number; due_installments_value: string };
}

const Stat: React.FC<{ label: string; value: React.ReactNode; hint?: string; tone?: 'warning' | 'error' | 'success'; to?: string }> = ({ label, value, hint, tone, to }) => {
  const navigate = useNavigate();
  const body = (
    <CardContent>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
      <Typography variant="h5" sx={{ fontWeight: 600, color: tone ? `${tone}.main` : undefined }}>{value}</Typography>
      {hint && <Typography variant="caption" color="text.secondary">{hint}</Typography>}
    </CardContent>
  );
  return <Card variant="outlined" sx={{ height: '100%' }}>{to ? <CardActionArea sx={{ height: '100%' }} onClick={() => navigate(to)}>{body}</CardActionArea> : body}</Card>;
};

/** Admin → Overblik: det, der kræver handling nu (samler data fra de andre sider). */
const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { isPartner } = useAdmin();
  const [mine, setMine] = useState(false);
  const [d, setD] = useState<Data | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    firmApi.get('/dashboard', { params: mine ? { mine: '1' } : {} }).then((r) => setD(r.data.data)).catch((e) => setError(errorText(e)));
  }, [mine]);

  if (error) return <Alert severity="error">{error}</Alert>;
  if (!d) return null;
  const kycAttention = d.kyc.due + d.kyc.missing;

  return (
    <Box sx={{ maxWidth: 1300 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 2, flexWrap: 'wrap' }}>
        <Typography variant="h5" sx={{ flex: 1 }}>Overblik</Typography>
        <ToggleButtonGroup size="small" exclusive value={mine ? 'mine' : 'all'} onChange={(_, v) => v && setMine(v === 'mine')}>
          <ToggleButton value="all">Alle mine kunder</ToggleButton>
          <ToggleButton value="mine">Kun ansvarlig/tildelt</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
        {!d.independence.mine_signed && <Alert severity="warning" action={<Chip clickable label="Underskriv" onClick={() => navigate('/admin/independence')} />}>Du har ikke underskrevet din uafhængighedserklæring for {d.independence.year}.</Alert>}
        {d.evaluation_missing && isPartner && <Alert severity="info" action={<Chip clickable label="Kvalitetslog" onClick={() => navigate('/admin/quality-log')} />}>Årets evaluering af kvalitetsstyringssystemet er ikke registreret (BEK 512/2024 § 3, stk. 3).</Alert>}
        {d.independence.conflicts > 0 && <Alert severity="error" action={<Chip clickable label="Se forhold" onClick={() => navigate('/admin/independence')} />}>{d.independence.conflicts} uafklarede uafhængighedsforhold.</Alert>}
      </Box>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={6} md={2}><Stat label="Kunder" value={d.clients} to="/admin/clients" /></Grid>
        <Grid item xs={6} md={2}><Stat label="Frister, 14 dage" value={d.deadlines_total} tone={d.deadlines_total ? 'warning' : undefined} to="/admin/deadlines" /></Grid>
        <Grid item xs={6} md={2}><Stat label="Åbne opdrag" value={d.engagements.open} hint={d.engagements.overdue.length ? `${d.engagements.overdue.length} over frist` : undefined} tone={d.engagements.overdue.length ? 'error' : undefined} to="/admin/engagements" /></Grid>
        <Grid item xs={6} md={2}><Stat label="Kundekendskab" value={kycAttention} hint={`${d.kyc.due} forfaldne · ${d.kyc.missing} mangler`} tone={kycAttention ? 'warning' : 'success'} to="/admin/aml" /></Grid>
        <Grid item xs={6} md={2}><Stat label="Svar fra kunder" value={d.tasks.answered_by_client} hint={`${d.tasks.mine_open} åbne opgaver til dig`} to="/admin/tasks" /></Grid>
        {d.unbilled
          ? <Grid item xs={6} md={2}><Stat label="Ufaktureret tid" value={`${kr(d.unbilled.time_value)} kr.`} hint={d.unbilled.due_installments ? `+ ${d.unbilled.due_installments} forfaldne rater` : d.unbilled.oldest ? `ældste ${formatDate(d.unbilled.oldest)}` : undefined} to="/admin/billing" /></Grid>
          : <Grid item xs={6} md={2}><Stat label="Fuldmagter" value={d.powers.length} hint="udløber inden for 30 dage" tone={d.powers.length ? 'warning' : undefined} /></Grid>}
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Frister de næste 14 dage</Typography>
            {d.deadlines.length === 0 && <Typography variant="body2" color="text.secondary">Ingen frister.</Typography>}
            <List dense disablePadding>
              {d.deadlines.map((x, i) => (
                <ListItemButton key={i} onClick={() => navigate(x.engagement ? `/admin/engagements/${x.engagement}` : `/admin/clients/${x.client}`)}>
                  <ListItemText primary={`${formatDate(x.date)} · ${x.client_name}`} secondary={`${x.title}${x.responsible_name ? ` · ${x.responsible_name}` : ''}`} />
                  {x.kind === 'opdrag' && <Chip size="small" label="Opdrag" />}
                </ListItemButton>
              ))}
            </List>
            {d.deadlines_total > d.deadlines.length && <Typography variant="caption">… og {d.deadlines_total - d.deadlines.length} flere i fristkalenderen.</Typography>}
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Opdrag</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
              {d.engagements.by_status.map((s) => <Chip key={s.value} label={`${s.label}: ${s.count}`} onClick={() => navigate('/admin/engagements')} />)}
            </Box>
            {d.engagements.overdue.length > 0 && (
              <>
                <Typography variant="body2" color="error.main" sx={{ mt: 1 }}>Over frist</Typography>
                <List dense disablePadding>
                  {d.engagements.overdue.map((e) => (
                    <ListItemButton key={e.id} onClick={() => navigate(`/admin/engagements/${e.id}`)}>
                      <ListItemText primary={`${e.client_name}: ${e.title}`} secondary={`Frist ${formatDate(e.deadline)} · ${e.status_label}`} />
                    </ListItemButton>
                  ))}
                </List>
              </>
            )}
          </Paper>
          {kycAttention > 0 && (
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Kundekendskab, der skal opdateres</Typography>
              <List dense disablePadding>
                {d.kyc.clients.map((c) => (
                  <ListItemButton key={c.client} onClick={() => navigate(`/admin/clients/${c.client}?tab=8`)}>
                    <ListItemText primary={c.client_name} />
                    <Chip size="small" color={c.status === 'due' ? 'warning' : 'error'} label={c.status === 'due' ? 'Forfalden' : 'Mangler'} />
                  </ListItemButton>
                ))}
              </List>
            </Paper>
          )}
          {d.powers.length > 0 && (
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Fuldmagter, der udløber</Typography>
              <List dense disablePadding>
                {d.powers.map((p) => (
                  <ListItemButton key={p.id} onClick={() => navigate(`/admin/clients/${p.client}?tab=12`)}>
                    <ListItemText primary={`${p.client_name}: ${p.kind_label}`} secondary={`${p.scope} · udløber ${p.expires_on ? formatDate(p.expires_on) : ''}`} />
                    <Chip size="small" color={POA_COLOR[p.status]} label={p.status_label} />
                  </ListItemButton>
                ))}
              </List>
            </Paper>
          )}
          {isPartner && d.independence.missing && d.independence.missing.length > 0 && (
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Mangler uafhængighedserklæring {d.independence.year}</Typography>
              <Typography variant="body2">{d.independence.missing.join(', ')}</Typography>
            </Paper>
          )}
          {d.terms_pending.length > 0 && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Kunder, der mangler at acceptere betingelserne</Typography>
              <List dense disablePadding>
                {d.terms_pending.map((t) => (
                  <ListItemButton key={t.client} onClick={() => navigate(`/admin/clients/${t.client}`)}>
                    <ListItemText primary={t.client_name} secondary={`${t.users} bruger(e)`} />
                  </ListItemButton>
                ))}
              </List>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
