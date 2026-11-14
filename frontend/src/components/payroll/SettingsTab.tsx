import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, Grid, MenuItem, Paper, Table, TableBody, TableCell, TableHead, TableRow, TextField,
  Typography,
} from '@mui/material';
import api from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { MONTHS, apiError } from './format';

interface Holiday { date: string; name: string; share: string }

const SettingsTab: React.FC = () => {
  const [se, setSe] = useState('');
  const [grundlovsdag, setGrundlovsdag] = useState('half');
  const [year, setYear] = useState(new Date().getFullYear());
  const [holidays, setHolidays] = useState<Holiday[]>([]);
  const [workingDays, setWorkingDays] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    api.get('/payroll/settings').then((res) => {
      setSe(res.data.se_number);
      setGrundlovsdag(res.data.grundlovsdag);
    }).catch((e) => setMsg({ type: 'error', text: apiError(e) }));
  }, []);

  const loadHolidays = useCallback(async () => {
    try {
      const res = await api.get(`/payroll/holidays?year=${year}&grundlovsdag=${grundlovsdag}`);
      setHolidays(res.data.results);
      setWorkingDays(res.data.working_days);
    } catch (e: any) {
      setMsg({ type: 'error', text: apiError(e) });
    }
  }, [year, grundlovsdag]);

  useEffect(() => { loadHolidays(); }, [loadHolidays]);

  const save = async () => {
    try {
      await api.put('/payroll/settings', { se_number: se, grundlovsdag });
      setMsg({ type: 'success', text: 'Indstillingerne er gemt.' });
    } catch (e: any) {
      setMsg({ type: 'error', text: apiError(e) });
    }
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={5}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Lønindstillinger</Typography>
          {msg && <Alert severity={msg.type} sx={{ mb: 2 }} onClose={() => setMsg(null)}>{msg.text}</Alert>}
          <TextField fullWidth size="small" label="SE-nummer (eIndkomst)" value={se} sx={{ mb: 2 }}
            helperText="8 cifre. Tom: CVR fra virksomhedsindstillingerne" onChange={(e) => setSe(e.target.value)} />
          <TextField select fullWidth size="small" label="Grundlovsdag" value={grundlovsdag} sx={{ mb: 2 }}
            onChange={(e) => setGrundlovsdag(e.target.value)}>
            <MenuItem value="none">Almindelig arbejdsdag</MenuItem>
            <MenuItem value="half">Halv fridag</MenuItem>
            <MenuItem value="full">Hel fridag</MenuItem>
          </TextField>
          <Button variant="contained" onClick={save}>Gem</Button>
          <Alert severity="info" sx={{ mt: 2 }}>
            Indberetning til eIndkomst og hentning af eSkattekort direkte fra systemet kræver, at Ajan Partners
            er godkendt som dataleverandør hos Skattestyrelsen. Indtil da: eksportér eIndkomst-filen og indberet
            manuelt på skat.dk, og indtast skattekortet fra eSkattekort.
          </Alert>
        </Paper>
      </Grid>
      <Grid item xs={12} md={7}>
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6">Helligdage</Typography>
            <TextField size="small" type="number" label="År" value={year} sx={{ width: 110 }}
              onChange={(e) => setYear(Number(e.target.value))} />
          </Box>
          <Table size="small">
            <TableHead>
              <TableRow><TableCell>Dato</TableCell><TableCell>Helligdag</TableCell><TableCell align="right">Fri</TableCell></TableRow>
            </TableHead>
            <TableBody>
              {holidays.map((h) => (
                <TableRow key={h.date + h.name}>
                  <TableCell>{formatDate(h.date)}</TableCell>
                  <TableCell>{h.name}</TableCell>
                  <TableCell align="right">{h.share === '1' ? 'Hel dag' : 'Halv dag'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <Typography variant="subtitle2" sx={{ mt: 2 }}>Arbejdsdage pr. måned</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 1 }}>
            {MONTHS.map((m, i) => (
              <Typography key={m} variant="body2">{m}: {parseFloat(workingDays[i + 1] || '0').toLocaleString('da-DK')}</Typography>
            ))}
          </Box>
          <Typography variant="caption" color="text.secondary">Store bededag er afskaffet som helligdag fra 2024.</Typography>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default SettingsTab;
