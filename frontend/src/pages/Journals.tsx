import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell, TableContainer, Switch, TextField,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';

interface Journal {
  id: number;
  code: string;
  name: string;
  type: string;
  account_code: string | null;
  currency: string;
  is_active: boolean;
}

// Journaux auxiliaires. Code, type and account are fixed (entries and number
// series refer to them); the name and whether it is in use can change.
const Journals: React.FC = () => {
  const { t } = useTranslation();
  const [journals, setJournals] = useState<Journal[]>([]);

  const load = () => {
    api.get('/journals').then(res => {
      if (res.data.success) setJournals(res.data.data.journals);
    });
  };
  useEffect(load, []);

  const save = (j: Journal, patch: Partial<Journal>) => {
    api.put(`/journals/${j.id}`, patch).then(load).catch(err => alert(err.response?.data?.message));
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>{t('journals.title')}</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.code')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.name')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.type')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.account')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.currency')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('journals.active')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {journals.map(j => (
              <TableRow key={j.id} hover>
                <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600 }}>{j.code}</TableCell>
                <TableCell>
                  <TextField
                    variant="standard" size="small" defaultValue={j.name} fullWidth
                    onBlur={e => e.target.value !== j.name && save(j, { name: e.target.value })}
                  />
                </TableCell>
                <TableCell>{t(`journals.types.${j.type}`)}</TableCell>
                <TableCell sx={{ fontFamily: 'monospace' }}>{j.account_code || '—'}</TableCell>
                <TableCell>{j.currency}</TableCell>
                <TableCell>
                  <Switch size="small" checked={j.is_active} onChange={e => save(j, { is_active: e.target.checked })} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default Journals;
