import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  MenuItem, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import LinkIcon from '@mui/icons-material/Link';
import api from '../services/api';
import { formatDate } from '../utils/dateFormat';

interface Connection {
  id: string; provider: string; institution_id: string; institution_name: string; bank_account_id: string;
  iban: string; status: string; status_display: string; authorization_url: string | null;
  consent_expires_at: string | null; renewal_due: boolean; last_fetched_at: string | null;
  last_booked_date: string | null; last_error: string;
  last_result: { created?: number; skipped?: number; fetched?: number; error?: string };
}
interface Institution { id: string; name: string; country: string }
interface BankAccount { id: string; code: string; name: string; journal: string; currency: string }

const STATUS_COLOR: Record<string, 'success' | 'warning' | 'error' | 'default' | 'info'> = {
  active: 'success', pending: 'info', expired: 'warning', revoked: 'default', error: 'error',
};

const daysLeft = (iso: string | null) =>
  iso ? Math.ceil((new Date(iso).getTime() - Date.now()) / 86400000) : null;

/** Bank → Bankkobling: automatisk hentning af banktransaktioner (PSD2/open banking). */
const BankFeeds: React.FC = () => {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [provider, setProvider] = useState('');
  const [warnDays, setWarnDays] = useState(14);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [busy, setBusy] = useState('');
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ institution_id: '', bank_account_id: '' });

  const load = useCallback(async () => {
    try {
      const [c, i] = await Promise.all([api.get('/bank-feeds'), api.get('/bank-feeds/institutions')]);
      setConnections(c.data.data.connections);
      setWarnDays(c.data.data.renew_warning_days || 14);
      setInstitutions(i.data.data.institutions);
      setAccounts(i.data.data.bank_accounts || []);
      setProvider(i.data.data.provider);
    } catch (e: any) { setError(e.response?.data?.message || 'Kunne ikke hente bankkoblinger'); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const act = async (key: string, fn: () => Promise<any>, ok?: (r: any) => string) => {
    setBusy(key); setError(''); setInfo('');
    try {
      const r = await fn();
      if (r?.data?.data?.authorization_url) {
        // Rigtig udbyder: kunden godkender i banken og sendes tilbage.
        window.location.href = r.data.data.authorization_url;
        return;
      }
      if (ok) setInfo(ok(r));
      await load();
    } catch (e: any) { setError(e.response?.data?.message || 'Handlingen fejlede'); } finally { setBusy(''); }
  };

  const connect = () => act('connect', async () => {
    const r = await api.post('/bank-feeds', { ...form, redirect_url: `${window.location.origin}/bank-feeds` });
    setOpen(false);
    return r;
  }, () => 'Banken er koblet på. Transaktionerne hentes hver morgen.');

  const sync = (c: Connection) => act(`sync-${c.id}`, () => api.post(`/bank-feeds/${c.id}/sync`), (r) => {
    const res = r.data.data.result || {};
    if (res.skipped_reason) return `Ikke hentet (${res.skipped_reason}).`;
    return `${res.created ?? 0} nye banklinjer, ${res.skipped ?? 0} fandtes allerede.`;
  });
  const renew = (c: Connection) => act(`renew-${c.id}`, () => api.post(`/bank-feeds/${c.id}/renew`),
    () => 'Samtykket er fornyet i 180 dage.');
  const revoke = (c: Connection) => {
    if (!window.confirm(`Afbryd bankkoblingen til ${c.institution_name}? Der hentes ikke flere transaktioner.`)) return;
    act(`revoke-${c.id}`, () => api.delete(`/bank-feeds/${c.id}`), () => 'Bankkoblingen er afbrudt.');
  };

  const accountLabel = (id: string) => {
    const a = accounts.find((x) => x.id === id);
    return a ? `${a.code} ${a.name}` : '–';
  };
  const expiring = connections.filter((c) => c.status !== 'revoked' && (c.renewal_due || c.status === 'expired'));

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Typography variant="h5">Bankkobling</Typography>
        <Button variant="contained" startIcon={<LinkIcon />} onClick={() => setOpen(true)}
          disabled={!institutions.length || !accounts.length}>
          Kobl bank på
        </Button>
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Med jeres samtykke henter systemet banktransaktionerne automatisk hver morgen og lægger dem til
        afstemning, ligesom ved import af et kontoudtog. Samtykket gives i banken og skal fornyes hver 180. dag (PSD2).
        {provider === 'mock' && ' Lige nu bruges en testbank, så der hentes ingen rigtige transaktioner.'}
      </Typography>
      {expiring.map((c) => {
        const d = daysLeft(c.consent_expires_at);
        return (
          <Alert key={`warn-${c.id}`} severity={c.status === 'expired' || (d !== null && d <= 0) ? 'error' : 'warning'}
            sx={{ mb: 2 }}
            action={<Button color="inherit" size="small" disabled={!!busy} onClick={() => renew(c)}>Forny samtykke</Button>}>
            {c.status === 'expired' || (d !== null && d <= 0)
              ? `Samtykket til ${c.institution_name} er udløbet. Der hentes ikke transaktioner, før det er fornyet.`
              : `Samtykket til ${c.institution_name} udløber om ${d} ${d === 1 ? 'dag' : 'dage'} (${formatDate(c.consent_expires_at)}). Forny det inden for ${warnDays} dage.`}
          </Alert>
        );
      })}
      {!accounts.length && (
        <Alert severity="info" sx={{ mb: 2 }}>Opret først en bankkonto med en bankjournal i kontoplanen.</Alert>
      )}
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {info && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setInfo('')}>{info}</Alert>}
      <Card variant="outlined">
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Bank</TableCell><TableCell>Konto i bogføringen</TableCell><TableCell>IBAN</TableCell>
                <TableCell>Status</TableCell><TableCell>Samtykke til</TableCell><TableCell>Senest hentet</TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              {connections.length === 0 && (
                <TableRow><TableCell colSpan={7}><Typography color="text.secondary">Ingen bankkoblinger endnu.</Typography></TableCell></TableRow>
              )}
              {connections.map((c) => (
                <TableRow key={c.id}>
                  <TableCell>{c.institution_name || c.provider}</TableCell>
                  <TableCell>{accountLabel(c.bank_account_id)}</TableCell>
                  <TableCell>{c.iban || '–'}</TableCell>
                  <TableCell>
                    <Chip size="small" color={STATUS_COLOR[c.status] || 'default'} label={c.status_display} />
                    {c.last_error && <Typography variant="caption" color="error" display="block">{c.last_error}</Typography>}
                  </TableCell>
                  <TableCell>{formatDate(c.consent_expires_at)}</TableCell>
                  <TableCell>
                    {c.last_fetched_at ? formatDate(c.last_fetched_at) : '–'}
                    {c.last_result?.created !== undefined && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {c.last_result.created} nye, {c.last_result.skipped ?? 0} dubletter
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                    {c.status === 'active' && (
                      <Button size="small" disabled={!!busy} onClick={() => sync(c)}>Hent nu</Button>
                    )}
                    {c.status !== 'revoked' && (
                      <Button size="small" disabled={!!busy} onClick={() => renew(c)}>Forny samtykke</Button>
                    )}
                    {c.status === 'pending' && c.authorization_url && (
                      <Button size="small" href={c.authorization_url}>Godkend i banken</Button>
                    )}
                    {c.status !== 'revoked' && (
                      <Button size="small" color="error" disabled={!!busy} onClick={() => revoke(c)}>Afbryd</Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Kobl bank på</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField select size="small" label="Bank" value={form.institution_id}
              onChange={(e) => setForm({ ...form, institution_id: e.target.value })}>
              {institutions.map((i) => <MenuItem key={i.id} value={i.id}>{i.name}</MenuItem>)}
            </TextField>
            <TextField select size="small" label="Bogfør på bankkonto" value={form.bank_account_id}
              onChange={(e) => setForm({ ...form, bank_account_id: e.target.value })}>
              {accounts.map((a) => <MenuItem key={a.id} value={a.id}>{a.code} {a.name} ({a.currency})</MenuItem>)}
            </TextField>
            <Typography variant="body2" color="text.secondary">
              I godkender adgangen i jeres bank (MitID). Samtykket giver kun læseadgang til kontoen og kan
              trækkes tilbage her eller i banken.
            </Typography>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Annullér</Button>
          <Button variant="contained" disabled={!form.institution_id || !form.bank_account_id || busy === 'connect'}
            onClick={connect}>
            Fortsæt
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BankFeeds;
