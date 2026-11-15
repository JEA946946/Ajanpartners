import React, { useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Checkbox, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  FormControlLabel, FormGroup, Grid, Switch, TextField, Typography,
} from '@mui/material';
import { firmApi } from '../../services/api';
import { errorText, Package } from '../api';
import { useAdmin } from '../AdminContext';

const LIMIT_LABELS: Record<string, string> = { users: 'Brugere', invoices_per_month: 'Fakturaer pr. måned' };

const Packages: React.FC = () => {
  const { packages, features, isPartner, reload } = useAdmin();
  const [edit, setEdit] = useState<Package | null>(null);
  const [error, setError] = useState('');

  const save = async () => {
    if (!edit) return;
    try {
      await firmApi.put(`/packages/${edit.id}`, {
        name: edit.name, description: edit.description, features: edit.features, limits: edit.limits, is_active: edit.is_active,
      });
      setEdit(null);
      reload();
    } catch (e) { setError(errorText(e, 'Pakken kunne ikke gemmes')); }
  };

  const setLimit = (k: string, v: string) =>
    edit && setEdit({ ...edit, limits: { ...edit.limits, [k]: v === '' ? null : Math.max(0, Number(v)) } });

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 0.5 }}>Pakker</Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Alle pakker er gratis for husets kunder. Pakken begrænser kun kundens egne brugere – Ajan Partners har alle funktioner med kundens samtykke.
      </Typography>
      {!isPartner && <Alert severity="info" sx={{ mb: 2 }}>Kun partnere kan ændre pakkerne.</Alert>}
      <Grid container spacing={2}>
        {[...packages].reverse().map((p) => (
          <Grid item xs={12} md={4} key={p.id}>
            <Card sx={{ height: '100%', opacity: p.is_active ? 1 : 0.6 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Typography variant="h6">{p.name}</Typography>
                  <Chip size="small" sx={{ ml: 'auto' }} color="primary" label={`${p.client_count} kunder`} />
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>{p.description}</Typography>
                {Object.entries(features).map(([k, v]) => (
                  <Typography key={k} variant="body2" sx={{ color: p.features.includes(k) ? 'text.primary' : 'text.disabled' }}>
                    {p.features.includes(k) ? '✓' : '–'} {v}
                  </Typography>
                ))}
                <Typography variant="body2" sx={{ mt: 1.5 }}>
                  {Object.entries(LIMIT_LABELS).map(([k, v]) => `${v}: ${p.limits[k] ?? 'ubegrænset'}`).join(' · ')}
                </Typography>
                {isPartner && <Button sx={{ mt: 2 }} variant="outlined" onClick={() => { setError(''); setEdit({ ...p, limits: { ...p.limits } }); }}>Redigér</Button>}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={!!edit} onClose={() => setEdit(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Redigér {edit?.name}</DialogTitle>
        {edit && (
          <DialogContent>
            <TextField fullWidth size="small" sx={{ mt: 1 }} label="Navn" value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} />
            <TextField fullWidth size="small" sx={{ mt: 2 }} multiline label="Beskrivelse" value={edit.description} onChange={(e) => setEdit({ ...edit, description: e.target.value })} />
            <Typography fontWeight={600} sx={{ mt: 2 }}>Funktioner</Typography>
            <FormGroup>
              {Object.entries(features).map(([k, v]) => (
                <FormControlLabel key={k} label={v} control={<Checkbox size="small" checked={edit.features.includes(k)}
                  onChange={(e) => setEdit({ ...edit, features: e.target.checked ? [...edit.features, k] : edit.features.filter((f) => f !== k) })} />} />
              ))}
            </FormGroup>
            <Typography fontWeight={600} sx={{ mt: 2, mb: 1 }}>Grænser (tom = ubegrænset)</Typography>
            <Grid container spacing={2}>
              {Object.entries(LIMIT_LABELS).map(([k, v]) => (
                <Grid item xs={6} key={k}>
                  <TextField fullWidth size="small" type="number" label={v} value={edit.limits[k] ?? ''} onChange={(e) => setLimit(k, e.target.value)} />
                </Grid>
              ))}
            </Grid>
            <FormControlLabel sx={{ mt: 1 }} label="Aktiv (kan vælges til nye kunder)"
              control={<Switch checked={edit.is_active} onChange={(e) => setEdit({ ...edit, is_active: e.target.checked })} />} />
            {edit.client_count > 0 && (
              <Alert severity="warning" sx={{ mt: 1 }}>Ændringen gælder straks for {edit.client_count} kunde(r) med pakken.</Alert>
            )}
            {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          </DialogContent>
        )}
        <DialogActions>
          <Button onClick={() => setEdit(null)}>Annullér</Button>
          <Button variant="contained" onClick={save}>Gem</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Packages;
