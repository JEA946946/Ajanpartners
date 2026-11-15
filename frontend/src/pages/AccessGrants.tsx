import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Box, Button, Card, CardContent, Chip, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography,
} from '@mui/material';
import api from '../services/api';
import { useClient } from '../hooks/useClient';

interface Info {
  firm: { name: string; email: string; phone: string };
  agreement_reference: string;
  agreement_accepted_on: string | null;
  access_active: boolean;
  access_since: string | null;
  staff: { id: number; name: string; role: string; title: string }[];
  acceptances: { user: string; document: string; kind: string; version: string; method: string; accepted_at: string }[];
}

const ROLE: Record<string, string> = { partner: 'Partner', revisor: 'Revisor', bogholder: 'Bogholder', assistent: 'Assistent' };
const fmt = (s: string | null) => (s ? new Date(s).toLocaleDateString('da-DK') : '–');

/** Indstillinger → Aftale og betingelser: hvad aftalen siger, hvem i revisorhuset der har adgang. */
const AccessGrants: React.FC = () => {
  const { firm } = useClient();
  const navigate = useNavigate();
  const [info, setInfo] = useState<Info | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/access-grants').then((r) => setInfo(r.data.data))
      .catch((e) => setError(e.response?.data?.message || 'Oplysningerne kunne ikke hentes'));
  }, []);

  const firmName = info?.firm.name || firm?.name || 'Ajan Partners';

  return (
    <Box sx={{ maxWidth: 900 }}>
      <Typography variant="h5" gutterBottom>Aftale og betingelser</Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {info && (
        <Stack spacing={2}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Jeres aftale med {firmName}</Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                I bruger programmet gratis, så længe I er kunde hos {firmName}. {firmName} har adgang til jeres bøger
                for at levere de ydelser, der står i jeres aftale – fx bogføring, moms og årsregnskab. Al deres
                læsning og ændring logges i audit-loggen.
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Stopper I, kan I altid hente alle jeres data under{' '}
                <Button size="small" onClick={() => navigate('/settings/export')}>Eksport af data</Button>.
              </Typography>
              <Box sx={{ mt: 1.5, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip size="small" color={info.access_active ? 'success' : 'default'}
                  label={info.access_active ? `Revisoradgang siden ${fmt(info.access_since)}` : 'Revisoradgang afsluttet'} />
                {info.agreement_accepted_on && <Chip size="small" variant="outlined" label={`Betingelser accepteret ${fmt(info.agreement_accepted_on)}`} />}
                {info.agreement_reference && <Chip size="small" variant="outlined" label={`Aftale: ${info.agreement_reference}`} />}
              </Box>
            </CardContent>
          </Card>

          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Medarbejdere hos {firmName} med adgang</Typography>
              <Table size="small">
                <TableBody>
                  {info.staff.map((s) => (
                    <TableRow key={s.id}><TableCell>{s.name}</TableCell><TableCell>{s.title || ROLE[s.role] || s.role}</TableCell></TableRow>
                  ))}
                  {info.staff.length === 0 && <TableRow><TableCell>Ingen.</TableCell></TableRow>}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Accepterede betingelser</Typography>
              <Table size="small">
                <TableHead><TableRow><TableCell>Dokument</TableCell><TableCell>Version</TableCell><TableCell>Accepteret af</TableCell><TableCell>Dato</TableCell><TableCell>Måde</TableCell></TableRow></TableHead>
                <TableBody>
                  {info.acceptances.map((a, i) => (
                    <TableRow key={i}>
                      <TableCell>{a.document}</TableCell><TableCell>{a.version}</TableCell><TableCell>{a.user}</TableCell>
                      <TableCell>{fmt(a.accepted_at)}</TableCell><TableCell>{a.method === 'mitid' ? 'MitID' : 'I programmet'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                {[['terms', 'Forretningsbetingelser'], ['dpa', 'Databehandleraftale'], ['privacy', 'Privatlivspolitik']].map(([k, label]) => (
                  <Button key={k} size="small" onClick={async () => {
                    const r = await api.get(`/public/terms/${k}`);
                    const d = r.data.data.document;
                    const url = URL.createObjectURL(new Blob([d.body], { type: 'text/markdown;charset=utf-8' }));
                    const a = document.createElement('a'); a.href = url; a.download = `${d.title} ${d.version}.md`; a.click();
                    URL.revokeObjectURL(url);
                  }}>{label}</Button>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Stack>
      )}
    </Box>
  );
};

export default AccessGrants;
