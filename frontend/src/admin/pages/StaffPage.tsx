import React, { useEffect, useState } from 'react';
import {
  Alert, Autocomplete, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel,
  Grid, MenuItem, Paper, Switch, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { firmApi } from '../../services/api';
import { errorText, FirmClient, Staff, STAFF_ROLES } from '../api';
import { useAdmin } from '../AdminContext';

const EMPTY = { id: 0, email: '', first_name: '', last_name: '', role: 'bogholder', title: '', hourly_rate: '', password: '', is_active: true, clients: [] as string[] };

const StaffPage: React.FC = () => {
  const { staff, isPartner, reload } = useAdmin();
  const [clients, setClients] = useState<FirmClient[]>([]);
  const [edit, setEdit] = useState<typeof EMPTY | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    firmApi.get('/clients').then((r) => setClients(r.data.data.clients)).catch(() => undefined);
  }, []);

  const open = (s?: Staff) => {
    setError('');
    setEdit(s ? { id: s.id, email: s.email, first_name: s.first_name, last_name: s.last_name, role: s.role, title: s.title, hourly_rate: s.hourly_rate || '',
      password: '', is_active: s.is_active, clients: s.clients } : { ...EMPTY });
  };

  const save = async () => {
    if (!edit) return;
    try {
      const { id, password, ...rest } = edit;
      if (id) await firmApi.put(`/staff/${id}`, { ...rest, ...(password ? { password } : {}) });
      else await firmApi.post('/staff', { ...rest, password });
      setEdit(null);
      reload();
    } catch (e) { setError(errorText(e, 'Kunne ikke gemmes')); }
  };

  const clientName = (slug: string) => clients.find((c) => c.slug === slug)?.name || slug;
  const needsAssignment = edit && (edit.role === 'bogholder' || edit.role === 'assistent');

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Medarbejdere</Typography>
        {isPartner && <Button sx={{ ml: 'auto' }} variant="contained" startIcon={<AddIcon />} onClick={() => open()}>Ny medarbejder</Button>}
      </Box>
      {!isPartner && <Alert severity="info" sx={{ mb: 2 }}>Kun partnere kan oprette og ændre medarbejdere.</Alert>}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Navn</TableCell><TableCell>E-mail</TableCell><TableCell>Rolle</TableCell><TableCell>Titel</TableCell>
              <TableCell>Kunder</TableCell><TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {staff.map((s) => (
              <TableRow key={s.id} hover={isPartner} sx={{ cursor: isPartner ? 'pointer' : undefined }} onClick={() => isPartner && open(s)}>
                <TableCell>{`${s.first_name} ${s.last_name}`.trim() || s.username}</TableCell>
                <TableCell>{s.email}</TableCell>
                <TableCell>{STAFF_ROLES[s.role]}</TableCell>
                <TableCell>{s.title}</TableCell>
                <TableCell>
                  {s.role === 'partner' || s.role === 'revisor' ? <Typography variant="caption">Alle kunder</Typography>
                    : s.clients.length ? s.clients.map((c) => <Chip key={c} size="small" label={clientName(c)} sx={{ mr: 0.5, mb: 0.3 }} />)
                      : <Typography variant="caption" color="text.secondary">Ingen tildelt</Typography>}
                </TableCell>
                <TableCell>{s.is_active ? <Chip size="small" color="success" label="Aktiv" /> : <Chip size="small" label="Deaktiveret" />}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Paper sx={{ p: 2, mt: 2 }}>
        <Typography fontWeight={600} gutterBottom>Roller</Typography>
        <Typography variant="body2">Partner: alt, også pakker, medarbejdere og arkivering.</Typography>
        <Typography variant="body2">Revisor: alle kunder, årsafslutning og låsning af regnskabsår.</Typography>
        <Typography variant="body2">Bogholder: tildelte kunder, bogføring og moms.</Typography>
        <Typography variant="body2">Assistent: tildelte kunder, bilag og forespørgsler.</Typography>
      </Paper>

      <Dialog open={!!edit} onClose={() => setEdit(null)} maxWidth="sm" fullWidth>
        <DialogTitle>{edit?.id ? 'Redigér medarbejder' : 'Ny medarbejder'}</DialogTitle>
        {edit && (
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 0 }}>
              <Grid item xs={6}><TextField fullWidth size="small" label="Fornavn" value={edit.first_name} onChange={(e) => setEdit({ ...edit, first_name: e.target.value })} /></Grid>
              <Grid item xs={6}><TextField fullWidth size="small" label="Efternavn" value={edit.last_name} onChange={(e) => setEdit({ ...edit, last_name: e.target.value })} /></Grid>
              <Grid item xs={12}><TextField fullWidth size="small" label="E-mail" disabled={!!edit.id} value={edit.email} onChange={(e) => setEdit({ ...edit, email: e.target.value })} /></Grid>
              <Grid item xs={6}>
                <TextField select fullWidth size="small" label="Rolle" value={edit.role} onChange={(e) => setEdit({ ...edit, role: e.target.value })}>
                  {Object.entries(STAFF_ROLES).map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid item xs={6}><TextField fullWidth size="small" label="Titel" value={edit.title} onChange={(e) => setEdit({ ...edit, title: e.target.value })} /></Grid>
              <Grid item xs={6}>
                <TextField fullWidth size="small" type="number" label="Timepris (kr. ekskl. moms)" value={edit.hourly_rate}
                  helperText="Tom = husets standardsats" onChange={(e) => setEdit({ ...edit, hourly_rate: e.target.value })} />
              </Grid>
              <Grid item xs={12}>
                <TextField fullWidth size="small" type="password" label={edit.id ? 'Ny adgangskode (valgfri)' : 'Adgangskode (mindst 10 tegn)'}
                  value={edit.password} onChange={(e) => setEdit({ ...edit, password: e.target.value })} />
              </Grid>
              {needsAssignment && (
                <Grid item xs={12}>
                  <Autocomplete multiple size="small" options={clients.map((c) => c.slug)} getOptionLabel={clientName}
                    value={edit.clients} onChange={(_, v) => setEdit({ ...edit, clients: v })}
                    renderInput={(p) => <TextField {...p} label="Tildelte kunder" />} />
                </Grid>
              )}
              {!!edit.id && (
                <Grid item xs={12}>
                  <FormControlLabel label="Aktiv" control={<Switch checked={edit.is_active} onChange={(e) => setEdit({ ...edit, is_active: e.target.checked })} />} />
                </Grid>
              )}
            </Grid>
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

export default StaffPage;
