import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Button, Card, CardActionArea, CardContent, Chip, Container, Stack, Typography,
} from '@mui/material';
import { useAuth } from '../hooks/useAuth';
import { useClient } from '../hooks/useClient';

const ROLE: Record<string, string> = { admin: 'Administrator', accountant: 'Bogholder', viewer: 'Læser' };

/** Vælg hvilken virksomheds bøger der skal åbnes. */
const SelectClient: React.FC = () => {
  const { clients, selectClient, firmStaff, firm, pendingGrants } = useClient();
  const { logout } = useAuth();
  const navigate = useNavigate();

  return (
    <Container maxWidth="sm" sx={{ py: 6 }}>
      <Typography variant="h5" gutterBottom>Vælg virksomhed</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {firm?.name || 'Ajan Partners'} – gratis bogføring til vores kunder.
      </Typography>
      {pendingGrants.length > 0 && (
        <Button variant="contained" sx={{ mb: 2 }} onClick={() => navigate('/onboarding')}>
          Godkend adgang for {firm?.name || 'revisor'} ({pendingGrants.length})
        </Button>
      )}
      <Stack spacing={1.5}>
        {clients.map((c) => (
          <Card key={c.slug} variant="outlined">
            <CardActionArea onClick={() => selectClient(c.slug)}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{c.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {c.cvr ? `CVR ${c.cvr} · ` : ''}{c.package_name}
                  </Typography>
                </Box>
                {c.status === 'archived' && <Chip size="small" label="Arkiveret" />}
                <Chip size="small" variant="outlined"
                  label={c.via === 'firm' ? `Revisor · ${ROLE[c.role]}` : ROLE[c.role]} />
              </CardContent>
            </CardActionArea>
          </Card>
        ))}
        {clients.length === 0 && (
          <Typography color="text.secondary">
            Du har ikke adgang til nogen virksomheder endnu.
          </Typography>
        )}
      </Stack>
      <Stack direction="row" spacing={1} sx={{ mt: 4 }}>
        {firmStaff && <Button onClick={() => navigate('/admin')}>Til admin-portalen</Button>}
        <Button color="inherit" onClick={() => { logout(); navigate('/login'); }}>Log ud</Button>
      </Stack>
    </Container>
  );
};

export default SelectClient;
