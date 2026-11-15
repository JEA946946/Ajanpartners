import React from 'react';
import { Box, Typography } from '@mui/material';
import ClientPicker from '../../components/ClientPicker';

/** Kundevalg i admin-portalen: åbn en kundes bøger. */
const AdminSelectClient: React.FC = () => (
  <Box sx={{ maxWidth: 720 }}>
    <Typography variant="h5" gutterBottom>Arbejd i en kunde</Typography>
    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
      Vælg den virksomhed, hvis bøger du vil åbne. Alt, du læser og ændrer, logges.
    </Typography>
    <ClientPicker />
  </Box>
);

export default AdminSelectClient;
