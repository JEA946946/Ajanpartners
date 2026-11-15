import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Box, Button, Card, CardContent, Checkbox, CircularProgress, Container, FormControlLabel, Stack, Tab,
  Tabs, Typography,
} from '@mui/material';
import { Download } from '@mui/icons-material';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useClient } from '../hooks/useClient';
import MarkdownText from '../components/MarkdownText';

interface Doc { id: number; kind: string; kind_label: string; version: string; title: string; sha256: string; body: string }
interface Required { client: string; client_name: string; role: string; documents: Doc[] }

const download = (d: Doc) => {
  const url = URL.createObjectURL(new Blob([d.body], { type: 'text/markdown;charset=utf-8' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = `${d.title} ${d.version}.md`;
  a.click();
  URL.revokeObjectURL(url);
};

/** Første login: kunden accepterer forretningsbetingelser og databehandleraftale. */
const Onboarding: React.FC = () => {
  const { firm, refresh, firmStaff } = useClient();
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [required, setRequired] = useState<Required[] | null>(null);
  const [tab, setTab] = useState(0);
  const [checked, setChecked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [method, setMethod] = useState<'click' | 'mitid'>('click');
  const current = required?.[0];

  const load = () => api.get('/me/terms').then((r) => {
    setRequired(r.data.data.required);
    setMethod(r.data.data.signature_method === 'mitid' ? 'mitid' : 'click');
    setTab(0);
    setChecked(false);
  }).catch(() => setError('Betingelserne kunne ikke hentes. Prøv igen.'));
  useEffect(() => {
    // Tilbage fra MitID-underskrift: ?signed=<reference>&client=<slug>
    const q = new URLSearchParams(window.location.search);
    const ref = q.get('signed');
    if (ref) {
      api.post('/me/terms/sign/complete', { client: q.get('client'), reference: ref })
        .then(async () => { window.history.replaceState({}, '', '/onboarding'); await refresh(); load(); })
        .catch((e) => { setError(e.response?.data?.message || 'Underskriften kunne ikke registreres'); load(); });
      return;
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const signWithMitId = async () => {
    if (!current) return;
    setBusy(true);
    setError('');
    try {
      const back = `${window.location.origin}/onboarding?client=${encodeURIComponent(current.client)}`;
      const r = await api.post('/me/terms/sign', { client: current.client, return_url: back });
      window.location.href = r.data.data.url;
    } catch (e: any) {
      setError(e.response?.data?.message || 'MitID-underskrift kunne ikke startes');
      setBusy(false);
    }
  };

  const accept = async () => {
    if (!current) return;
    setBusy(true);
    setError('');
    try {
      await api.post('/me/terms/accept', {
        client: current.client, confirm: true, sha256: current.documents.map((d) => d.sha256),
      });
      if ((required?.length || 0) > 1) {
        await load();
      } else {
        await refresh();
        navigate('/');
      }
    } catch (e: any) {
      setError(e.response?.data?.message || 'Accepten kunne ikke gemmes');
      if (e.response?.status === 409) load();
    } finally {
      setBusy(false);
    }
  };

  if (required === null) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  }
  if (!current) {
    return (
      <Container maxWidth="sm" sx={{ py: 6 }}>
        <Typography variant="h5" gutterBottom>Alt er på plads</Typography>
        <Button variant="contained" onClick={() => navigate(firmStaff ? '/admin' : '/')}>Fortsæt</Button>
      </Container>
    );
  }
  const doc = current.documents[Math.min(tab, current.documents.length - 1)];

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h5" gutterBottom>Velkommen til {firm?.name || 'Ajan Partners'} Bogføring</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Før <b>{current.client_name}</b> kan bruge programmet, skal I acceptere forretningsbetingelserne og
        databehandleraftalen. De supplerer jeres aftale med {firm?.name || 'os'}, som har adgang til bøgerne for at
        levere bogføring, moms og regnskab. Når I stopper, kan I altid hente alle jeres data.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Card variant="outlined">
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ borderBottom: 1, borderColor: 'divider', px: 1 }}>
          {current.documents.map((d) => <Tab key={d.id} label={`${d.kind_label} (${d.version})`} />)}
        </Tabs>
        <CardContent sx={{ maxHeight: '50vh', overflowY: 'auto' }}>
          <MarkdownText text={doc.body} />
        </CardContent>
        <Box sx={{ px: 2, pb: 1 }}>
          <Button size="small" startIcon={<Download />} onClick={() => download(doc)}>Download {doc.kind_label.toLowerCase()}</Button>
        </Box>
      </Card>
      {method === 'click' && <FormControlLabel sx={{ mt: 2 }} control={<Checkbox checked={checked} onChange={(e) => setChecked(e.target.checked)} />}
        label={current.role === 'admin'
          ? <>Jeg har læst og accepterer {current.documents.map((d) => d.title.toLowerCase()).join(' og ')} på vegne af <b>{current.client_name}</b>.</>
          : <>Jeg har læst og accepterer {current.documents.map((d) => d.title.toLowerCase()).join(' og ')}.</>} />}
      <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
        {method === 'mitid' ? (
          <Button variant="contained" disabled={busy} onClick={signWithMitId}>
            {busy ? 'Åbner MitID …' : 'Underskriv med MitID'}
          </Button>
        ) : (
          <Button variant="contained" disabled={!checked || busy} onClick={accept}>
            {busy ? 'Gemmer …' : 'Accepter og fortsæt'}
          </Button>
        )}
        <Button color="inherit" onClick={() => { logout(); navigate('/login'); }}>Log ud</Button>
      </Stack>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
        {method === 'mitid'
          ? 'Du underskriver med MitID. Det underskrevne dokument gemmes som bevis.'
          : 'Accepten gemmes med tidspunkt, IP-adresse og en kontrolsum af præcis den tekst, du har set.'}
      </Typography>
    </Container>
  );
};

export default Onboarding;
