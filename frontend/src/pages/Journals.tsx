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

// Journaler (BANK pr. bankkonto, KAS, KØB, SALG, LØN, DIV, PRIMO, ÅA). Kode, type og
// konto ligger fast (posteringer og nummerserier henviser til dem); navnet og om
// journalen er i brug kan ændres.
const Journals: React.FC = () => {
  const { t } = useTranslation();
  const TYPE_LABELS: Record<string, string> = {
    bank: t('journals.types.bank', 'Bank'),
    cash: t('journals.types.cash', 'Kasse'),
    purchases: t('journals.types.purchases', 'Køb'),
    sales: t('journals.types.sales', 'Salg'),
    payroll: t('journals.types.payroll', 'Løn'),
    misc: t('journals.types.misc', 'Diverse'),
    opening: t('journals.types.opening', 'Primo'),
    closing: t('journals.types.closing', 'Årsafslutning'),
  };
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
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>{t('journals.title')}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('journals.intro', 'Hver postering ligger i én journal og får et fortløbende nummer pr. journal og år, når måneden lukkes. En ny bankkonto får automatisk sin egen bankjournal.')}
      </Typography>
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
                <TableCell>{TYPE_LABELS[j.type] || j.type}</TableCell>
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
