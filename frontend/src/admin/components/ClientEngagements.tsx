import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, Box, Button, Paper } from '@mui/material';
import { firmApi } from '../../services/api';
import { errorText } from '../api';
import { CreateEngagementDialog, EngagementRow, EngagementTable, Meta } from '../pages/Engagements';

/** Fanen "Opdrag" på en kunde. */
const ClientEngagements: React.FC<{ slug: string; name: string }> = ({ slug, name }) => {
  const navigate = useNavigate();
  const [rows, setRows] = useState<EngagementRow[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(() => {
    firmApi.get('/engagements', { params: { client: slug } }).then((r) => setRows(r.data.data.engagements))
      .catch((e) => setError(errorText(e)));
  }, [slug]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { firmApi.get('/engagements/meta').then((r) => setMeta(r.data.data)).catch(() => undefined); }, []);
  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Box sx={{ textAlign: 'right', mb: 1 }}><Button variant="contained" size="small" onClick={() => setOpen(true)}>Nyt opdrag</Button></Box>
      <Paper><EngagementTable rows={rows} showClient={false} /></Paper>
      <CreateEngagementDialog open={open} onClose={() => setOpen(false)} meta={meta} clients={[{ slug, name }]} fixedClient={slug}
        onCreated={(id) => navigate(`/admin/engagements/${id}`)} />
    </Box>
  );
};

export default ClientEngagements;
