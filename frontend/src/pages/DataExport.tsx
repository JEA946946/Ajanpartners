import React, { useState } from 'react';
import { Alert, Box, Button, Card, CardContent, Typography } from '@mui/material';
import api from '../services/api';
import { useClient } from '../hooks/useClient';

/** Eksportér alt regnskabsmateriale (ved ophør, skift af system eller til myndigheder). */
const DataExport: React.FC = () => {
  const { current } = useClient();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const isAdmin = current?.access.role === 'admin';

  const download = async () => {
    setBusy(true);
    setError('');
    try {
      const r = await api.get('/export-all', { responseType: 'blob', timeout: 600000 });
      const name = /filename="?([^";]+)"?/.exec(r.headers['content-disposition'] || '')?.[1] || 'regnskabsmateriale.zip';
      const url = URL.createObjectURL(r.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError('Eksporten kunne ikke laves. Prøv igen, eller kontakt Ajan Partners.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 720 }}>
      <Typography variant="h5" gutterBottom>Eksport af regnskabsmateriale</Typography>
      <Card variant="outlined">
        <CardContent>
          <Typography variant="body2" sx={{ mb: 1 }}>
            Hent alt jeres regnskabsmateriale i én fil: SAF-T (Erhvervsstyrelsens standardformat, kan læses af
            andre bogføringssystemer) for hvert regnskabsår, saldobalancer, alle bilag med kontrolsum og
            audit-loggen.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Materialet skal opbevares i 5 år fra udgangen af det regnskabsår, det vedrører. Stopper I hos os,
            gemmer vi bøgerne read-only i hele perioden, og I kan altid hente eksporten her.
          </Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          {!isAdmin && <Alert severity="info" sx={{ mb: 2 }}>Kun virksomhedens administrator kan hente eksporten.</Alert>}
          <Button variant="contained" disabled={!isAdmin || busy} onClick={download}>
            {busy ? 'Laver eksport …' : 'Hent eksport (zip)'}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
};

export default DataExport;
