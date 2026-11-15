import React, { useState } from 'react';
import {
  Box, Card, CardActionArea, CardContent, Chip, InputAdornment, Stack, TextField, Typography,
} from '@mui/material';
import { ChevronRight, Search } from '@mui/icons-material';
import { useClient } from '../hooks/useClient';

const ROLE: Record<string, string> = { admin: 'Administrator', accountant: 'Bogholder', viewer: 'Læser' };

/** Listen over virksomheder, brugeren kan åbne. Bruges både i admin-portalen og for kundens brugere. */
const ClientPicker: React.FC = () => {
  const { clients, selectClient } = useClient();
  const [q, setQ] = useState('');
  const needle = q.trim().toLowerCase();
  const shown = needle
    ? clients.filter((c) => c.name.toLowerCase().includes(needle) || (c.cvr || '').includes(needle))
    : clients;

  return (
    <Stack spacing={1.5}>
      {clients.length > 5 && (
        <TextField size="small" placeholder="Søg på navn eller CVR" value={q} onChange={(e) => setQ(e.target.value)}
          InputProps={{ startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> }} />
      )}
      {shown.map((c) => (
        <Card key={c.slug} variant="outlined">
          <CardActionArea onClick={() => selectClient(c.slug)}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }} noWrap>{c.name}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {c.cvr ? `CVR ${c.cvr} · ` : ''}{c.package_name}
                </Typography>
              </Box>
              {c.status === 'archived' && <Chip size="small" label="Arkiveret" />}
              <Chip size="small" variant="outlined"
                label={c.via === 'firm' ? `Revisor · ${ROLE[c.role] || c.role}` : ROLE[c.role] || c.role} />
              <ChevronRight color="action" />
            </CardContent>
          </CardActionArea>
        </Card>
      ))}
      {clients.length === 0 && (
        <Typography color="text.secondary">Du har ikke adgang til nogen virksomheder endnu.</Typography>
      )}
      {clients.length > 0 && shown.length === 0 && (
        <Typography color="text.secondary">Ingen virksomheder matcher søgningen.</Typography>
      )}
    </Stack>
  );
};

export default ClientPicker;
