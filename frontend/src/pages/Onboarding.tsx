import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Box, Button, Card, CardContent, Container, FormControl, FormControlLabel, Radio, RadioGroup,
  Stack, TextField, Typography,
} from '@mui/material';
import api from '../services/api';
import { useClient } from '../hooks/useClient';

const SCOPES = [
  { value: 'read', label: 'Læse', help: 'Revisor kan se bøgerne, men ikke ændre noget.' },
  { value: 'bookkeeping', label: 'Bogføre', help: 'Revisor kan bogføre, afstemme og lave moms. Ikke brugere eller adgang.' },
  { value: 'full', label: 'Fuld adgang', help: 'Som jeres egen administrator.' },
];

/** Kunden giver (eller afviser) revisorhuset adgang til bøgerne. */
const Onboarding: React.FC = () => {
  const { pendingGrants, firm, clients, refresh } = useClient();
  const navigate = useNavigate();
  const [scope, setScope] = useState<Record<string, string>>({});
  const [until, setUntil] = useState<Record<string, string>>({});
  const [error, setError] = useState('');

  const decide = async (grantId: string, client: string, accept: boolean) => {
    setError('');
    try {
      const path = accept ? `/access-grants/${grantId}/accept` : `/access-grants/${grantId}/revoke`;
      const body = accept ? { scope: scope[grantId], valid_until: until[grantId] || null } : {};
      await api.post(path, body, { headers: { 'X-Client': client } });
      await refresh();
      if (pendingGrants.length <= 1) navigate('/select-client');
    } catch (e: any) {
      setError(e.response?.data?.message || 'Noget gik galt');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 6 }}>
      <Typography variant="h5" gutterBottom>Velkommen</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {firm?.name || 'Ajan Partners'} beder om adgang til jeres bogføring, så vi kan levere bogføring,
        moms og årsregnskab. I bestemmer selv omfanget og kan altid trække adgangen tilbage under
        Indstillinger → Revisoradgang. Alt, revisor gør, logges.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Stack spacing={2}>
        {pendingGrants.map((g) => {
          const name = clients.find((c) => c.slug === g.client)?.name || g.client;
          return (
            <Card key={g.id} variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{name}</Typography>
                {g.request_note && <Typography variant="body2" sx={{ mb: 1 }}>{g.request_note}</Typography>}
                <FormControl>
                  <RadioGroup value={scope[g.id] ?? g.scope}
                    onChange={(e) => setScope({ ...scope, [g.id]: e.target.value })}>
                    {SCOPES.map((s) => (
                      <FormControlLabel key={s.value} value={s.value} control={<Radio size="small" />}
                        label={<Box><b>{s.label}</b> – <Typography component="span" variant="body2"
                          color="text.secondary">{s.help}</Typography></Box>} />
                    ))}
                  </RadioGroup>
                </FormControl>
                <TextField type="date" size="small" label="Gyldig til (valgfri)" InputLabelProps={{ shrink: true }}
                  sx={{ mt: 1, display: 'block' }} value={until[g.id] || ''}
                  onChange={(e) => setUntil({ ...until, [g.id]: e.target.value })} />
                <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                  <Button variant="contained" onClick={() => decide(g.id, g.client, true)}>Giv adgang</Button>
                  <Button color="inherit" onClick={() => decide(g.id, g.client, false)}>Afvis</Button>
                </Stack>
              </CardContent>
            </Card>
          );
        })}
      </Stack>
      {pendingGrants.length === 0 && <Button onClick={() => navigate('/select-client')}>Fortsæt</Button>}
    </Container>
  );
};

export default Onboarding;
