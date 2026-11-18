import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Alert, Autocomplete, Box, Button, Checkbox, Chip, FormControlLabel, IconButton, LinearProgress, MenuItem, Paper,
  Tab, Table, TableBody, TableCell, TableHead, TableRow, Tabs, TextField, Typography,
} from '@mui/material';
import { ChevronLeft, ChevronRight, Delete, Edit } from '@mui/icons-material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';
import { useAdmin } from '../AdminContext';
import { kr } from '../components/FeePanel';

interface Entry {
  id: string; user_id: number; user: string; client: string; client_name: string; engagement: string | null;
  engagement_title: string | null; date: string; minutes: number; hours: string; activity: string; note: string;
  billable: boolean; rate: string; value: string; invoiced: boolean; fixed_price: boolean;
}
interface Report {
  from: string; to: string;
  staff: { user_id: number; name: string; hours: string; billable_hours: string; internal_minutes: number; billable_pct: string; value: string }[];
  clients: { slug: string; name: string; hours: string; value: string; invoiced: string; unbilled: string }[];
  engagements: { id: string; client_name: string; title: string; budget_hours: string | null; used_hours: string; fee_kind: string }[];
}

const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const monday = (d: Date) => { const x = new Date(d); x.setDate(x.getDate() - ((x.getDay() + 6) % 7)); return x; };
const addDays = (d: Date, n: number) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const DAYS = ['Mandag', 'Tirsdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lørdag', 'Søndag'];
/** "1,5" / "1:30" / "90m" → minutter */
const toMinutes = (v: string) => {
  const s = v.trim().toLowerCase();
  if (/^\d+:\d{1,2}$/.test(s)) { const [h, m] = s.split(':').map(Number); return h * 60 + m; }
  if (/^\d+\s*m$/.test(s)) return parseInt(s, 10);
  const n = Number(s.replace(',', '.'));
  return Number.isFinite(n) ? Math.round(n * 60) : NaN;
};
const fmtH = (min: number) => (min / 60).toLocaleString('da-DK', { maximumFractionDigits: 2 });
const EMPTY = { id: '', date: iso(new Date()), client: '', engagement: '', hours: '', activity: '', note: '', billable: true };

/** Admin → Tid: registrér tid pr. kunde/opdrag; partnere ser rapporten. */
const TimePage: React.FC = () => {
  const { isPartner, staff, firm } = useAdmin();
  const [params] = useSearchParams();
  const [tab, setTab] = useState(0);
  const [week, setWeek] = useState(() => monday(new Date()));
  const [who, setWho] = useState('');
  const [rows, setRows] = useState<Entry[]>([]);
  const [clients, setClients] = useState<{ slug: string; name: string }[]>([]);
  const [engs, setEngs] = useState<{ id: string; title: string; year_label: string }[]>([]);
  const [form, setForm] = useState({ ...EMPTY, client: params.get('client') || '', engagement: params.get('engagement') || '' });
  const [error, setError] = useState('');

  const load = useCallback(() => {
    const p: Record<string, string> = { from: iso(week), to: iso(addDays(week, 6)) };
    if (who) p.user = who;
    firmApi.get('/time', { params: p }).then((r) => setRows(r.data.data.entries)).catch((e) => setError(errorText(e)));
  }, [week, who]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    firmApi.get('/clients').then((r) => setClients((r.data.data.clients || []).map((c: any) => ({ slug: c.slug, name: c.name }))))
      .catch(() => undefined);
  }, []);
  useEffect(() => {
    if (!form.client) { setEngs([]); return; }
    firmApi.get('/engagements', { params: { client: form.client, open: '1' } })
      .then((r) => setEngs(r.data.data.engagements)).catch(() => setEngs([]));
  }, [form.client]);
  useEffect(() => {  // husets interne tid er som udgangspunkt ikke fakturerbar
    if (!form.id) setForm((f) => ({ ...f, billable: f.client !== firm?.own_client }));
  }, [form.client, form.id, firm?.own_client]);

  const submit = async () => {
    const minutes = toMinutes(form.hours);
    if (!minutes || minutes <= 0) { setError('Angiv tid, fx 1,5 eller 1:30'); return; }
    const body = { date: form.date, client: form.client, engagement: form.engagement || null, minutes,
      activity: form.activity, note: form.note, billable: form.billable };
    try {
      if (form.id) await firmApi.put(`/time/${form.id}`, body);
      else await firmApi.post('/time', body);
      setForm({ ...EMPTY, date: form.date, client: form.client, engagement: form.engagement });
      setError('');
      load();
    } catch (e) { setError(errorText(e)); }
  };
  const edit = (e: Entry) => setForm({ id: e.id, date: e.date, client: e.client, engagement: e.engagement || '',
    hours: String(Number(e.hours)).replace('.', ','), activity: e.activity, note: e.note, billable: e.billable });
  const remove = async (e: Entry) => {
    try { await firmApi.delete(`/time/${e.id}`); load(); } catch (err) { setError(errorText(err)); }
  };

  const byDay = useMemo(() => DAYS.map((name, i) => {
    const d = iso(addDays(week, i));
    return { name, date: d, rows: rows.filter((r) => r.date === d) };
  }), [rows, week]);
  const total = rows.reduce((s, r) => s + r.minutes, 0);
  const billable = rows.filter((r) => r.billable).reduce((s, r) => s + r.minutes, 0);

  return (
    <Box sx={{ maxWidth: 1200 }}>
      <Typography variant="h5" sx={{ mb: 0.5 }}>Tid</Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Registrér tid pr. kunde og opdrag. Tid på husets egen bogføring er intern tid. Fakturerede timer er låst.
      </Typography>
      {isPartner && (
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
          <Tab label="Registrering" /><Tab label="Rapport" />
        </Tabs>
      )}
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      {tab === 0 && (
        <>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'flex-start' }}>
              <TextField size="small" type="date" label="Dato" InputLabelProps={{ shrink: true }} value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })} />
              <Autocomplete size="small" sx={{ minWidth: 220, flex: 1 }} options={clients} getOptionLabel={(o) => o.name}
                value={clients.find((c) => c.slug === form.client) || null}
                onChange={(_, v) => setForm({ ...form, client: v?.slug || '', engagement: '' })}
                renderInput={(p) => <TextField {...p} label="Kunde" />} />
              <TextField select size="small" label="Opdrag" sx={{ minWidth: 200 }} value={form.engagement}
                onChange={(e) => setForm({ ...form, engagement: e.target.value })}>
                <MenuItem value="">Intet opdrag</MenuItem>
                {engs.map((g) => <MenuItem key={g.id} value={g.id}>{g.title}{g.year_label ? ` ${g.year_label}` : ''}</MenuItem>)}
              </TextField>
              <TextField size="small" label="Timer" placeholder="1,5" sx={{ width: 90 }} value={form.hours}
                onChange={(e) => setForm({ ...form, hours: e.target.value })} />
              <TextField size="small" label="Aktivitet" sx={{ width: 160 }} value={form.activity}
                onChange={(e) => setForm({ ...form, activity: e.target.value })} />
              <TextField size="small" label="Note" sx={{ flex: 1, minWidth: 180 }} value={form.note}
                onChange={(e) => setForm({ ...form, note: e.target.value })} />
              <FormControlLabel label="Fakturerbar" control={
                <Checkbox size="small" checked={form.billable} onChange={(e) => setForm({ ...form, billable: e.target.checked })} />} />
              <Button variant="contained" disabled={!form.client || !form.hours} onClick={submit}>{form.id ? 'Gem' : 'Registrér'}</Button>
              {form.id && <Button onClick={() => setForm({ ...EMPTY })}>Annullér</Button>}
            </Box>
          </Paper>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, flexWrap: 'wrap' }}>
            <IconButton onClick={() => setWeek(addDays(week, -7))}><ChevronLeft /></IconButton>
            <Typography sx={{ minWidth: 220 }}>Uge {formatDate(iso(week))} – {formatDate(iso(addDays(week, 6)))}</Typography>
            <IconButton onClick={() => setWeek(addDays(week, 7))}><ChevronRight /></IconButton>
            <Button size="small" onClick={() => setWeek(monday(new Date()))}>Denne uge</Button>
            <Box sx={{ flex: 1 }} />
            {isPartner && (
              <TextField select size="small" label="Medarbejder" sx={{ minWidth: 200 }} value={who} onChange={(e) => setWho(e.target.value)}>
                <MenuItem value="">Mig</MenuItem>
                <MenuItem value="all">Alle</MenuItem>
                {staff.filter((s) => s.is_active).map((s) => (
                  <MenuItem key={s.user_id} value={String(s.user_id)}>{`${s.first_name} ${s.last_name}`.trim() || s.username}</MenuItem>
                ))}
              </TextField>
            )}
            <Typography variant="body2">I alt <b>{fmtH(total)} t</b> · fakturerbar {fmtH(billable)} t</Typography>
          </Box>
          <Paper>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Dag</TableCell>{who && <TableCell>Medarbejder</TableCell>}<TableCell>Kunde / opdrag</TableCell>
                  <TableCell>Aktivitet / note</TableCell><TableCell align="right">Timer</TableCell><TableCell align="right">Værdi</TableCell>
                  <TableCell /><TableCell />
                </TableRow>
              </TableHead>
              <TableBody>
                {byDay.map((d) => (
                  <React.Fragment key={d.date}>
                    <TableRow sx={{ bgcolor: 'action.hover' }}>
                      <TableCell colSpan={who ? 4 : 3}><b>{d.name}</b> {formatDate(d.date)}</TableCell>
                      <TableCell align="right"><b>{fmtH(d.rows.reduce((s, r) => s + r.minutes, 0))}</b></TableCell>
                      <TableCell colSpan={3} />
                    </TableRow>
                    {d.rows.map((r) => (
                      <TableRow key={r.id} hover>
                        <TableCell />
                        {who && <TableCell>{r.user}</TableCell>}
                        <TableCell>{r.client_name}{r.engagement_title && <Typography variant="caption" display="block" color="text.secondary">{r.engagement_title}</Typography>}</TableCell>
                        <TableCell>{r.activity}{r.note && <Typography variant="caption" display="block" color="text.secondary">{r.note}</Typography>}</TableCell>
                        <TableCell align="right">{Number(r.hours).toLocaleString('da-DK')}</TableCell>
                        <TableCell align="right">{r.billable ? kr(r.value) : '–'}</TableCell>
                        <TableCell>
                          {r.invoiced && <Chip size="small" color="success" label="Faktureret" />}
                          {!r.billable && <Chip size="small" label="Ikke fakturerbar" />}
                          {r.billable && r.fixed_price && <Chip size="small" label="Fast pris" />}
                        </TableCell>
                        <TableCell sx={{ whiteSpace: 'nowrap' }}>
                          {!r.invoiced && (
                            <>
                              <IconButton size="small" onClick={() => edit(r)}><Edit fontSize="small" /></IconButton>
                              <IconButton size="small" onClick={() => remove(r)}><Delete fontSize="small" /></IconButton>
                            </>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </>
      )}
      {tab === 1 && isPartner && <TimeReport />}
    </Box>
  );
};

const TimeReport: React.FC = () => {
  const now = new Date();
  const [from, setFrom] = useState(iso(new Date(now.getFullYear(), now.getMonth(), 1)));
  const [to, setTo] = useState(iso(now));
  const [r, setR] = useState<Report | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    firmApi.get('/time/report', { params: { from, to } }).then((x) => setR(x.data.data)).catch((e) => setError(errorText(e)));
  }, [from, to]);

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <TextField size="small" type="date" label="Fra" InputLabelProps={{ shrink: true }} value={from} onChange={(e) => setFrom(e.target.value)} />
        <TextField size="small" type="date" label="Til" InputLabelProps={{ shrink: true }} value={to} onChange={(e) => setTo(e.target.value)} />
      </Box>
      {error && <Alert severity="error">{error}</Alert>}
      {r && (
        <>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Medarbejdere</Typography>
          <Paper sx={{ mb: 3 }}>
            <Table size="small">
              <TableHead><TableRow><TableCell>Medarbejder</TableCell><TableCell align="right">Timer</TableCell><TableCell align="right">Fakturerbare</TableCell><TableCell align="right">Intern</TableCell><TableCell align="right">Faktureringsgrad</TableCell><TableCell align="right">Værdi</TableCell></TableRow></TableHead>
              <TableBody>
                {r.staff.length === 0 && <TableRow><TableCell colSpan={6}>Ingen registreringer i perioden.</TableCell></TableRow>}
                {r.staff.map((s) => (
                  <TableRow key={s.user_id}>
                    <TableCell>{s.name}</TableCell><TableCell align="right">{s.hours}</TableCell>
                    <TableCell align="right">{s.billable_hours}</TableCell><TableCell align="right">{fmtH(s.internal_minutes)}</TableCell>
                    <TableCell align="right">{s.billable_pct} %</TableCell><TableCell align="right">{kr(s.value)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Kunder</Typography>
          <Paper sx={{ mb: 3 }}>
            <Table size="small">
              <TableHead><TableRow><TableCell>Kunde</TableCell><TableCell align="right">Timer</TableCell><TableCell align="right">Værdi</TableCell><TableCell align="right">Faktureret</TableCell><TableCell align="right">Igangværende arbejde</TableCell></TableRow></TableHead>
              <TableBody>
                {r.clients.map((c) => (
                  <TableRow key={c.slug}>
                    <TableCell>{c.name}</TableCell><TableCell align="right">{c.hours}</TableCell><TableCell align="right">{kr(c.value)}</TableCell>
                    <TableCell align="right">{kr(c.invoiced)}</TableCell><TableCell align="right">{kr(c.unbilled)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Åbne opdrag: budget mod forbrug (al tid)</Typography>
          <Paper>
            <Table size="small">
              <TableHead><TableRow><TableCell>Kunde</TableCell><TableCell>Opdrag</TableCell><TableCell align="right">Budget</TableCell><TableCell align="right">Forbrug</TableCell><TableCell sx={{ width: 180 }} /></TableRow></TableHead>
              <TableBody>
                {r.engagements.map((g) => {
                  const b = Number(g.budget_hours || 0); const u = Number(g.used_hours);
                  return (
                    <TableRow key={g.id}>
                      <TableCell>{g.client_name}</TableCell><TableCell>{g.title}</TableCell>
                      <TableCell align="right">{g.budget_hours ?? '–'}</TableCell><TableCell align="right">{g.used_hours}</TableCell>
                      <TableCell>{b > 0 && <LinearProgress variant="determinate" color={u > b ? 'error' : 'primary'} value={Math.min(100, (100 * u) / b)} />}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </Paper>
        </>
      )}
    </Box>
  );
};

export default TimePage;
