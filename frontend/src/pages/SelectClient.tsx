import React from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import {
  AppBar, Avatar, Box, Container, IconButton, Toolbar, Tooltip, Typography,
} from '@mui/material';
import { Logout as LogoutIcon } from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { useClient } from '../hooks/useClient';
import ClientPicker from '../components/ClientPicker';

const BAR = 52;

/** Vælg hvilken virksomheds bøger der skal åbnes. Medarbejdere i revisorhuset vælger inde i admin-portalen. */
const SelectClient: React.FC = () => {
  const { firmStaff, firm } = useClient();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  if (firmStaff) return <Navigate to="/admin/select-client" replace />;
  const color = firm?.primary_color || '#0B3D5C';

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="fixed" sx={{ bgcolor: color }}>
        <Toolbar variant="dense" sx={{ minHeight: BAR, height: BAR }}>
          {firm?.logo && (
            <Box component="img" src={firm.logo} alt="" sx={{ height: 30, maxWidth: 140, objectFit: 'contain', mr: 1.5 }} />
          )}
          <Typography variant="h6" noWrap sx={{ fontSize: 16, fontWeight: 700 }}>
            {firm?.name || 'Ajan Partners'}
          </Typography>
          <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Typography sx={{ fontSize: 12 }}>{user?.first_name} {user?.last_name}</Typography>
            <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 28, height: 28, fontSize: 12 }}>
              {user?.first_name?.charAt(0)}{user?.last_name?.charAt(0)}
            </Avatar>
            <Tooltip title="Log ud">
              <IconButton color="inherit" size="small" onClick={() => { logout(); navigate('/login'); }}>
                <LogoutIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>
      <Container maxWidth="sm" sx={{ pt: `${BAR + 40}px`, pb: 6 }}>
        <Typography variant="h5" gutterBottom>Vælg virksomhed</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {firm?.name || 'Ajan Partners'} – gratis bogføring til vores kunder.
        </Typography>
        <ClientPicker />
      </Container>
    </Box>
  );
};

export default SelectClient;
