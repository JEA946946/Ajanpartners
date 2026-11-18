import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Autocomplete, Box, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, Paper, Table,
  TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import { CLIENT_KEY, firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';
import { useAdmin } from '../AdminContext';
import { kr } from '../components/FeePanel';

interface Row { client: string; client_name: string; hours: string; time_value: string; installments: string; due_installments: number; oldest: string | null; total: string }
interface Own { slug: string; name: string; cvr: string }
interface Entry { id: string; date: string; user: string; engagement_title: string | null; activity: string; note: string; hours: string; rate: string; value: string }
interface Inst { id: string; due_on: string; amount: string; text: string; engagement_title: string; kind: string }

const openOwnInvoices = (slug: string) => {
  localStorage.setItem(CLIENT_KEY, slug);
  window.location.href = '/invoices';
};

/** Admin → Fakturering: ufaktureret tid og rater pr. kunde → fakturaudkast i husets egen bogføring. */
const Billing: React.FC = () => {
  const { isPartner, firm, reload } = useAdmin();
  const [rows, setRows] = useState<Row[]>([]);
  const [own, setOwn] = useState<Own | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [clients, setClients] = useState<{ slug: string; name: string }[]>([]);
  const [pick, setPick] = useState('');
  const [open, setOpen] = useState<string | null>(null);
  const [done, setDone] = useState<{ number: string; total: string; customer: string; warning: string | null } | null>(null);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    firmApi.get('/billing').then((r) => { setRows(r.data.data.clients); setOwn(r.data.data.own_client); setLoaded(true); })
      .catch((e) => setError(errorText(e)));
  }, []);
  useEffect(() => { if (isPartner) load(); }, [load, isPartner]);
  useEffect(() => {
    firmApi.get('/clients').then((r) => setClients((r.data.data.clients || []).map((c: any) => ({ slug: c.slug, name: c.name }))))
      .catch(() => undefined);
  }, []);

  const setOwnClient = async (body: Record<string, unknown>) => {
    try { await firmApi.post('/billing/own-client', body); setError(''); load(); reload?.(); }
    catch (e) { setError(errorText(e)); }
  };

  if (!isPartner) return <Alert severity="info">Kun partnere har adgang til fakturering.</Alert>;
  return (
    <Box sx={{ maxWidth: 1200 }}>
      <Typography variant="h5" sx={{ mb: 0.5 }}>Fakturering</Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Ufaktureret tid og rater pr. kunde. Fakturaen laves som udkast i husets egen bogføring, hvor den kontrolleres,
        udstedes og bogføres i det almindelige salgsflow. Beløb er ekskl. moms.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {done && (
        <Alert severity={done.warning ? 'warning' : 'success'} sx={{ mb: 2 }} onClose={() => setDone(null)}
          action={own && <Button color="inherit" size="small" onClick={() => openOwnInvoices(own.slug)}>Åbn i husets bogføring</Button>}>
          Fakturaudkast {done.number} til {done.customer} på {kr(done.total)} kr. inkl. moms er oprettet.{done.warning ? ` ${done.warning}` : ''}
        </Alert>
      )}

      {loaded && !own && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Husets egen bogføring</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Fakturaerne laves i revisorhusets egne bøger, som er en kunde i systemet med eget CVR, kontoplan og moms.
            Opret den ud fra husets stamdata (CVR {firm?.cvr || 'mangler'}), eller vælg en eksisterende kunde.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <Button variant="contained" disabled={!firm?.cvr} onClick={() => setOwnClient({ create: true })}>Opret husets bogføring</Button>
            <Typography variant="body2">eller</Typography>
            <Autocomplete size="small" sx={{ minWidth: 260 }} options={clients} getOptionLabel={(o) => o.name}
              value={clients.find((c) => c.slug === pick) || null} onChange={(_, v) => setPick(v?.slug || '')}
              renderInput={(p) => <TextField {...p} label="Eksisterende kunde" />} />
            <Button variant="outlined" disabled={!pick} onClick={() => setOwnClient({ slug: pick })}>Vælg</Button>
          </Box>
        </Paper>
      )}
      {own && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography variant="body2">Husets bogføring: <b>{own.name}</b>{own.cvr ? ` (CVR ${own.cvr})` : ''}</Typography>
          <Button size="small" onClick={() => openOwnInvoices(own.slug)}>Åbn fakturaer</Button>
        </Box>
      )}

      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Kunde</TableCell><TableCell align="right">Timer</TableCell><TableCell align="right">Tid</TableCell>
              <TableCell align="right">Rater</TableCell><TableCell align="right">I alt</TableCell><TableCell>Ældste</TableCell><TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {loaded && rows.length === 0 && <TableRow><TableCell colSpan={7}><Typography variant="body2" color="text.secondary">Intet ufaktureret.</Typography></TableCell></TableRow>}
            {rows.map((r) => (
              <TableRow key={r.client} hover>
                <TableCell>{r.client_name}</TableCell>
                <TableCell align="right">{r.hours}</TableCell>
                <TableCell align="right">{kr(r.time_value)}</TableCell>
                <TableCell align="right">{kr(r.installments)}{r.due_installments ? ` (${r.due_installments} forfaldne)` : ''}</TableCell>
                <TableCell align="right"><b>{kr(r.total)}</b></TableCell>
                <TableCell>{r.oldest ? formatDate(r.oldest) : '–'}</TableCell>
                <TableCell><Button size="small" disabled={!own} onClick={() => setOpen(r.client)}>Fakturér</Button></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
      {open && <DraftDialog slug={open} onClose={() => setOpen(null)}
        onDone={(inv) => { setOpen(null); setDone(inv); load(); }} />}
    </Box>
  );
};

const DraftDialog: React.FC<{ slug: string; onClose: () => void; onDone: (inv: any) => void }> = ({ slug, onClose, onDone }) => {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [insts, setInsts] = useState<Inst[]>([]);
  const [name, setName] = useState('');
  const [sel, setSel] = useState<Set<string>>(new Set());
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    firmApi.get(`/billing/clients/${slug}`).then((r) => {
      const d = r.data.data;
      setName(d.client.name); setEntries(d.entries); setInsts(d.installments);
      const today = new Date().toISOString().slice(0, 10);
      setSel(new Set([...d.entries.map((e: Entry) => e.id), ...d.installments.filter((i: Inst) => i.due_on <= today).map((i: Inst) => i.id)]));
    }).catch((e) => setError(errorText(e)));
  }, [slug]);

  const toggle = (id: string) => setSel((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  const sum = entries.filter((e) => sel.has(e.id)).reduce((s, e) => s + Number(e.value), 0)
    + insts.filter((i) => sel.has(i.id)).reduce((s, i) => s + Number(i.amount), 0);
  const create = async () => {
    setBusy(true);
    try {
      const r = await firmApi.post(`/billing/clients/${slug}/draft`, {
        entries: entries.filter((e) => sel.has(e.id)).map((e) => e.id),
        installments: insts.filter((i) => sel.has(i.id)).map((i) => i.id), date, notes,
      });
      onDone({ ...r.data.data.invoice, warning: r.data.data.warning });
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  };

  return (
    <Dialog open onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Fakturaudkast – {name}</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {entries.length > 0 && (
          <>
            <Typography variant="subtitle2">Medgået tid</Typography>
            <Table size="small" sx={{ mb: 2 }}>
              <TableHead><TableRow><TableCell padding="checkbox" /><TableCell>Dato</TableCell><TableCell>Medarbejder</TableCell><TableCell>Opdrag / aktivitet</TableCell><TableCell align="right">Timer</TableCell><TableCell align="right">Sats</TableCell><TableCell align="right">Beløb</TableCell></TableRow></TableHead>
              <TableBody>
                {entries.map((e) => (
                  <TableRow key={e.id} hover onClick={() => toggle(e.id)} sx={{ cursor: 'pointer' }}>
                    <TableCell padding="checkbox"><Checkbox size="small" checked={sel.has(e.id)} /></TableCell>
                    <TableCell>{formatDate(e.date)}</TableCell><TableCell>{e.user}</TableCell>
                    <TableCell>{e.engagement_title || 'Øvrig assistance'}{(e.activity || e.note) && <Typography variant="caption" display="block" color="text.secondary">{[e.activity, e.note].filter(Boolean).join(' – ')}</Typography>}</TableCell>
                    <TableCell align="right">{e.hours}</TableCell><TableCell align="right">{kr(e.rate)}</TableCell><TableCell align="right">{kr(e.value)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}
        {insts.length > 0 && (
          <>
            <Typography variant="subtitle2">Rater</Typography>
            <Table size="small" sx={{ mb: 2 }}>
              <TableHead><TableRow><TableCell padding="checkbox" /><TableCell>Dato</TableCell><TableCell>Opdrag</TableCell><TableCell>Tekst</TableCell><TableCell align="right">Beløb</TableCell></TableRow></TableHead>
              <TableBody>
                {insts.map((i) => (
                  <TableRow key={i.id} hover onClick={() => toggle(i.id)} sx={{ cursor: 'pointer' }}>
                    <TableCell padding="checkbox"><Checkbox size="small" checked={sel.has(i.id)} /></TableCell>
                    <TableCell>{formatDate(i.due_on)}</TableCell><TableCell>{i.engagement_title} ({i.kind === 'aconto' ? 'aconto' : 'fast pris'})</TableCell>
                    <TableCell>{i.text || '–'}</TableCell><TableCell align="right">{kr(i.amount)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <TextField size="small" type="date" label="Fakturadato" InputLabelProps={{ shrink: true }} value={date} onChange={(e) => setDate(e.target.value)} />
          <TextField size="small" label="Bemærkning på fakturaen" sx={{ flex: 1, minWidth: 220 }} value={notes} onChange={(e) => setNotes(e.target.value)} />
          <Typography>Valgt: <b>{kr(sum)} kr.</b> ekskl. moms</Typography>
        </Box>
        <Typography variant="caption" color="text.secondary" component="div" sx={{ mt: 1 }}>
          Linjerne grupperes pr. opdrag og timepris. Ved aconto modregnes allerede fakturerede rater, så længe de kan rummes i den medgåede tid.
          Momskode S01 (25 %) sættes som udgangspunkt – tjek udkastet, før det udstedes.
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Annullér</Button>
        <Button variant="contained" disabled={busy || sel.size === 0} onClick={create}>Lav fakturaudkast</Button>
      </DialogActions>
    </Dialog>
  );
};

export default Billing;
