import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, Checkbox, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle,
  FormControlLabel, FormGroup, Grid, MenuItem, Paper, Snackbar, Tab, Table, TableBody, TableCell, TableHead,
  TableRow, Tabs, TextField, Typography,
} from '@mui/material';
import { ArrowBack, Login as WorkIcon } from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { firmApi } from '../../services/api';
import { useClient } from '../../hooks/useClient';
import { formatDate } from '../../utils/dateFormat';
import {
  accessState, ACCOUNTING_CLASSES, CHART_TEMPLATES, CLIENT_ROLES, CLIENT_STATUS, Deadline, errorText, FirmClient,
  Grant, GRANT_STATES, isoDate, label, LEGAL_FORMS, Member, MONTHS, SCOPES, STAFF_ROLES, VAT_PERIODS,
} from '../api';
import { useAdmin } from '../AdminContext';
import { AccessChip } from './ClientsList';
import { DeadlineTable } from './Deadlines';
import { TaskTable } from './Tasks';
import IndustryCodeField from '../components/IndustryCodeField';
import AuditorTools from '../components/AuditorTools';
import KycPanel from '../components/KycPanel';
import AcceptancePanel from '../components/AcceptancePanel';

const EDIT_FIELDS = ['name', 'cvr', 'legal_form', 'address', 'zip_code', 'city', 'industry_code', 'email', 'phone',
  'vat_period', 'fiscal_year_start_month', 'accounting_class'] as const;

const ClientDetail: React.FC = () => {
  const { slug = '' } = useParams();
  const navigate = useNavigate();
  const { selectClient } = useClient();
  const { packages, features, staff, isPartner, role } = useAdmin();
  const [client, setClient] = useState<FirmClient | null>(null);
  const [grants, setGrants] = useState<Grant[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [form, setForm] = useState<Record<string, any>>({});
  const [tab, setTab] = useState(() => Number(new URLSearchParams(window.location.search).get('tab')) || 0);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');
  const [saving, setSaving] = useState(false);
  const [deadlines, setDeadlines] = useState<Deadline[]>([]);
  const [invite, setInvite] = useState({ open: false, email: '', name: '', role: 'admin' });
  const [invited, setInvited] = useState<{ username: string; temporary_password: string | null } | null>(null);
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [archiveConfirm, setArchiveConfirm] = useState('');

  const load = useCallback(() => {
    firmApi.get(`/clients/${slug}`).then((r) => {
      const d = r.data.data;
      setClient(d.client);
      setGrants(d.grants);
      setMembers(d.members);
      setForm(Object.fromEntries(EDIT_FIELDS.map((f) => [f, d.client[f]])));
      setError('');
    }).catch((e) => setError(errorText(e, 'Kunden kunne ikke hentes')));
  }, [slug]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const from = new Date();
    firmApi.get('/deadlines', { params: { client: slug, from: isoDate(from), to: isoDate(new Date(Date.now() + 365 * 86400000)) } })
      .then((r) => setDeadlines(r.data.data.deadlines)).catch(() => setDeadlines([]));
  }, [slug, client?.vat_period, client?.fiscal_year_start_month, client?.accounting_class, client?.legal_form]);

  const save = async (data: Record<string, any>, message = 'Gemt') => {
    setSaving(true);
    try {
      const r = await firmApi.put(`/clients/${slug}`, data);
      setClient(r.data.data.client);
      setToast(message);
      setError('');
    } catch (e) {
      setError(errorText(e, 'Kunne ikke gemmes'));
    } finally {
      setSaving(false);
    }
  };

  if (!client) {
    return error ? <Alert severity="error">{error}</Alert> : <CircularProgress />;
  }

  const active = accessState(client.access) === 'active';
  const archived = client.status === 'archived';
  const canEdit = role !== 'assistent' && !archived;
  const pkg = packages.find((p) => p.code === client.package);
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  const doInvite = async () => {
    try {
      const r = await firmApi.post(`/clients/${slug}/invite`, invite);
      setInvited(r.data.data);
      setInvite({ open: false, email: '', name: '', role: 'admin' });
      load();
    } catch (e) { setError(errorText(e, 'Invitationen mislykkedes')); }
  };
  const changeAccess = async (action: 'end' | 'open') => {
    try {
      const r = await firmApi.post(`/clients/${slug}/access`, { action });
      setToast(r.data.message || (action === 'end' ? 'Adgangen er afsluttet' : 'Adgangen er genåbnet'));
      load();
    } catch (e) { setError(errorText(e, 'Adgangen kunne ikke ændres')); }
  };
  const doArchive = async () => {
    try {
      await firmApi.post(`/clients/${slug}/archive`);
      setArchiveOpen(false);
      setToast('Kunden er arkiveret');
      load();
    } catch (e) { setError(errorText(e, 'Arkiveringen mislykkedes')); }
  };

  const canExport = (role === 'partner' || role === 'revisor') && (active || (isPartner && archived));
  const doExport = async () => {
    try {
      setToast('Eksporten laves – det kan tage lidt tid');
      const r = await firmApi.get(`/clients/${slug}/export-all`, { responseType: 'blob', timeout: 600000 });
      const name = /filename="?([^";]+)"?/.exec(r.headers['content-disposition'] || '')?.[1] || `${slug}.zip`;
      const url = URL.createObjectURL(r.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) { setError(errorText(e, 'Eksporten mislykkedes')); }
  };

  const tf = (k: string, lbl: string, props: any = {}) => (
    <TextField fullWidth size="small" label={lbl} value={form[k] ?? ''} onChange={set(k)} disabled={!canEdit} {...props} />
  );

  return (
    <Box>
      <Button startIcon={<ArrowBack />} onClick={() => navigate('/admin/clients')} sx={{ mb: 1 }}>Kunder</Button>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1, flexWrap: 'wrap' }}>
        <Typography variant="h5">{client.name}</Typography>
        <Typography color="text.secondary">{client.cvr ? `CVR ${client.cvr}` : 'Uden CVR'} · {client.package_name}</Typography>
        <Chip size="small" label={CLIENT_STATUS[client.status]} color={archived ? 'default' : client.status === 'active' ? 'success' : 'warning'} />
        <AccessChip access={client.access} />
        <Button sx={{ ml: 'auto' }} variant="outlined" onClick={() => navigate(`/admin/templates?client=${slug}`)}>
          Dokumenter
        </Button>
        <Button variant="outlined" disabled={!canExport} onClick={doExport}
          title="SAF-T pr. regnskabsår, saldobalancer, alle bilag og audit-log (ved ophør eller udlevering)">
          Eksportér alt
        </Button>
        <Button variant="contained" startIcon={<WorkIcon />} disabled={!active} onClick={() => selectClient(slug)}>
          Arbejd i kunden
        </Button>
      </Box>
      {archived && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Kunden er arkiveret. Bøgerne er read-only og opbevares til {formatDate(client.retain_until)} (Bogføringsloven, 5 år).
        </Alert>
      )}
      {client.next_deadline && (
        <Typography variant="body2" sx={{ mb: 1 }}>
          Næste frist: <b>{formatDate(client.next_deadline.date)}</b> – {client.next_deadline.title} ({client.next_deadline.period})
        </Typography>
      )}
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Tab label="Stamdata" />
        <Tab label="Pakke" />
        <Tab label="Medarbejdere" />
        <Tab label={`Brugere (${members.length})`} />
        <Tab label="Adgang" />
        <Tab label={`Opgaver${client.open_tasks ? ` (${client.open_tasks})` : ''}`} />
        <Tab label="Frister" />
        <Tab label="Revisorværktøjer" />
        <Tab label="Hvidvask" />
        <Tab label="Kundeaccept" />
      </Tabs>

      {tab === 0 && (
        <Paper sx={{ p: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>{tf('name', 'Navn')}</Grid>
            <Grid item xs={12} sm={3}>{tf('cvr', 'CVR', { inputProps: { maxLength: 8 } })}</Grid>
            <Grid item xs={12} sm={3}>
              {tf('legal_form', 'Virksomhedsform', { select: true, children: LEGAL_FORMS.map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>) })}
            </Grid>
            <Grid item xs={12} sm={6}>{tf('address', 'Adresse')}</Grid>
            <Grid item xs={4} sm={2}>{tf('zip_code', 'Postnr.')}</Grid>
            <Grid item xs={8} sm={4}>{tf('city', 'By')}</Grid>
            <Grid item xs={12} sm={6}><IndustryCodeField value={form.industry_code ?? ''} disabled={!canEdit} onChange={(code) => setForm({ ...form, industry_code: code })} /></Grid>
            <Grid item xs={12} sm={4}>{tf('email', 'E-mail')}</Grid>
            <Grid item xs={12} sm={4}>{tf('phone', 'Telefon')}</Grid>
            <Grid item xs={12} sm={4}>
              {tf('vat_period', 'Momsperiode', { select: true, children: VAT_PERIODS.map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>) })}
            </Grid>
            <Grid item xs={12} sm={4}>
              {tf('fiscal_year_start_month', 'Regnskabsåret starter', { select: true, children: MONTHS.map((m, i) => <MenuItem key={m} value={i + 1}>1. {m}</MenuItem>) })}
            </Grid>
            <Grid item xs={12} sm={4}>
              {tf('accounting_class', 'Regnskabsklasse', { select: true, children: ACCOUNTING_CLASSES.map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>) })}
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body2" color="text.secondary">
                Kontoplan: {label(CHART_TEMPLATES, client.chart_template)} · Oprettet {formatDate(client.created_at)}
              </Typography>
            </Grid>
          </Grid>
          {canEdit && (
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="contained" disabled={saving} onClick={() => save(form, 'Stamdata er gemt')}>Gem stamdata</Button>
            </Box>
          )}
          {isPartner && !archived && (
            <Paper variant="outlined" sx={{ mt: 4, p: 2, borderColor: 'error.light' }}>
              <Typography fontWeight={600} color="error">Arkivér kunden</Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Bruges når kunden ophører. Bøgerne bliver read-only og slettes ikke: Bogføringsloven kræver, at regnskabsmaterialet opbevares i 5 år fra udgangen af det regnskabsår, det vedrører.
              </Typography>
              <Button color="error" variant="outlined" onClick={() => { setArchiveConfirm(''); setArchiveOpen(true); }}>Arkivér …</Button>
            </Paper>
          )}
        </Paper>
      )}

      {tab === 1 && (
        <Paper sx={{ p: 3 }}>
          <TextField select size="small" label="Pakke" value={client.package} disabled={!canEdit} sx={{ minWidth: 240, mb: 2 }}
            onChange={(e) => save({ package: e.target.value }, 'Pakken er ændret')}>
            {packages.map((p) => <MenuItem key={p.code} value={p.code}>{p.name}</MenuItem>)}
          </TextField>
          {pkg && <Typography color="text.secondary" sx={{ mb: 2 }}>{pkg.description}</Typography>}
          <Typography fontWeight={600} sx={{ mb: 1 }}>Funktioner for kundens egne brugere</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Ekstra funktioner lægges oven i pakken. Ajan Partners har altid alle funktioner, når kunden har givet adgang.
          </Typography>
          <FormGroup>
            {Object.entries(features).map(([key, text]) => {
              const inPackage = !!pkg?.features.includes(key);
              const extra = client.extra_features.includes(key);
              return (
                <FormControlLabel key={key} label={`${text}${inPackage ? ' (i pakken)' : ''}`} control={
                  <Checkbox size="small" checked={inPackage || extra} disabled={inPackage || !canEdit}
                    onChange={(e) => save({
                      extra_features: e.target.checked ? [...client.extra_features, key] : client.extra_features.filter((f) => f !== key),
                    }, 'Funktionerne er gemt')} />
                } />
              );
            })}
          </FormGroup>
          {pkg && (
            <Typography variant="body2" sx={{ mt: 2 }}>
              Grænser: {Object.entries(pkg.limits).map(([k, v]) => `${k === 'users' ? 'brugere' : k === 'invoices_per_month' ? 'fakturaer pr. måned' : k}: ${v ?? 'ubegrænset'}`).join(' · ') || 'ingen'}
            </Typography>
          )}
        </Paper>
      )}

      {tab === 2 && (
        <Paper sx={{ p: 3 }}>
          <TextField select size="small" label="Ansvarlig" sx={{ minWidth: 260, mb: 2 }} disabled={!canEdit}
            value={client.responsible_id ?? ''} onChange={(e) => save({ responsible_id: e.target.value || null }, 'Ansvarlig er ændret')}>
            <MenuItem value="">Ingen</MenuItem>
            {staff.map((s) => <MenuItem key={s.user_id} value={s.user_id}>{`${s.first_name} ${s.last_name}`.trim() || s.username}</MenuItem>)}
          </TextField>
          <Typography fontWeight={600}>Tildelte medarbejdere</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Partnere og revisorer ser alle kunder. Bogholdere og assistenter ser kun de kunder, de er tildelt.
          </Typography>
          <FormGroup>
            {staff.filter((s) => s.is_active).map((s) => (
              <FormControlLabel key={s.id} label={`${`${s.first_name} ${s.last_name}`.trim() || s.username} – ${STAFF_ROLES[s.role]}`}
                control={<Checkbox size="small" checked={client.assigned_staff.includes(s.id)}
                  disabled={!(role === 'partner' || role === 'revisor') || archived}
                  onChange={(e) => save({
                    assigned_staff: e.target.checked ? [...client.assigned_staff, s.id] : client.assigned_staff.filter((x) => x !== s.id),
                  }, 'Tildelingen er gemt')} />} />
            ))}
          </FormGroup>
        </Paper>
      )}

      {tab === 3 && (
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', mb: 1 }}>
            <Typography fontWeight={600}>Kundens brugere</Typography>
            {!archived && <Button sx={{ ml: 'auto' }} variant="outlined" onClick={() => setInvite({ ...invite, open: true })}>Invitér bruger</Button>}
          </Box>
          <Table size="small">
            <TableHead><TableRow><TableCell>Navn</TableCell><TableCell>E-mail</TableCell><TableCell>Rolle</TableCell><TableCell>Aktiv</TableCell></TableRow></TableHead>
            <TableBody>
              {members.length === 0 && <TableRow><TableCell colSpan={4}>Ingen brugere endnu.</TableCell></TableRow>}
              {members.map((m) => (
                <TableRow key={m.id}>
                  <TableCell>{m.name}</TableCell><TableCell>{m.email}</TableCell>
                  <TableCell>{CLIENT_ROLES[m.role] || m.role}</TableCell><TableCell>{m.is_active ? 'Ja' : 'Nej'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {pkg?.limits.users != null && (
            <Typography variant="caption" color="text.secondary">Pakken {pkg.name} har plads til {pkg.limits.users} bruger(e).</Typography>
          )}
        </Paper>
      )}

      {tab === 4 && (
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', mb: 1 }}>
            <Typography fontWeight={600}>Adgangshistorik</Typography>
            {isPartner && (accessState(client.access) === 'ended'
              ? <Button sx={{ ml: 'auto' }} variant="outlined" onClick={() => changeAccess('open')}>Genåbn adgang</Button>
              : <Button sx={{ ml: 'auto' }} color="error" variant="outlined" onClick={() => changeAccess('end')}>Afslut adgang</Button>)}
          </Box>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Omfang</TableCell><TableCell>Status</TableCell><TableCell>Medarbejdere</TableCell>
                <TableCell>Oprettet</TableCell><TableCell>Gælder fra</TableCell><TableCell>Gyldig til</TableCell><TableCell>Afsluttet</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {grants.map((g) => (
                <TableRow key={g.id}>
                  <TableCell>{SCOPES[g.scope]}</TableCell>
                  <TableCell><Chip size="small" label={GRANT_STATES[g.state]} color={g.state === 'active' ? 'success' : g.state === 'revoked' ? 'default' : 'warning'} /></TableCell>
                  <TableCell>{g.staff_scope === 'all' ? 'Alle' : g.staff.map((s) => s.name).join(', ')}</TableCell>
                  <TableCell>{formatDate(g.requested_at)}{g.requested_by ? ` · ${g.requested_by}` : ''}
                    {g.request_note && <Typography variant="caption" display="block" color="text.secondary">{g.request_note}</Typography>}
                  </TableCell>
                  <TableCell>{formatDate(g.accepted_at)}</TableCell>
                  <TableCell>{formatDate(g.valid_until)}</TableCell>
                  <TableCell>{formatDate(g.revoked_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <Typography variant="caption" color="text.secondary" component="div" sx={{ mt: 1 }}>
            Adgangen følger kundeaftalen og gælder fra oprettelsen{client.agreement_reference ? ` (${client.agreement_reference})` : ''}.
            {' '}Kunden accepterede forretningsbetingelser og databehandleraftale{' '}
            {client.agreement_accepted_on ? formatDate(client.agreement_accepted_on) : '– endnu ikke (ved første login)'}.
            {' '}Afslut kun adgangen, når aftalen er ophørt; ved arkivering kan bøgerne stadig læses i opbevaringsperioden.
          </Typography>
        </Paper>
      )}

      {tab === 5 && <TaskTable client={slug} />}
      {tab === 6 && <DeadlineTable rows={deadlines} showClient={false} />}
      {tab === 7 && <AuditorTools slug={slug} canWork={active} />}
      {tab === 8 && <KycPanel slug={slug} templateClient={slug} />}
      {tab === 9 && <AcceptancePanel slug={slug} />}

      <Dialog open={invite.open} onClose={() => setInvite({ ...invite, open: false })} maxWidth="xs" fullWidth>
        <DialogTitle>Invitér bruger hos {client.name}</DialogTitle>
        <DialogContent>
          <TextField fullWidth size="small" sx={{ mt: 1 }} label="E-mail" value={invite.email} onChange={(e) => setInvite({ ...invite, email: e.target.value })} />
          <TextField fullWidth size="small" sx={{ mt: 2 }} label="Navn" value={invite.name} onChange={(e) => setInvite({ ...invite, name: e.target.value })} />
          <TextField select fullWidth size="small" sx={{ mt: 2 }} label="Rolle" value={invite.role} onChange={(e) => setInvite({ ...invite, role: e.target.value })}>
            {Object.entries(CLIENT_ROLES).map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInvite({ ...invite, open: false })}>Annullér</Button>
          <Button variant="contained" disabled={!invite.email.includes('@')} onClick={doInvite}>Invitér</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={!!invited} maxWidth="xs" fullWidth>
        <DialogTitle>Brugeren er inviteret</DialogTitle>
        <DialogContent>
          <Typography>Brugernavn: <b>{invited?.username}</b></Typography>
          {invited?.temporary_password ? (
            <>
              <Typography>Midlertidig adgangskode: <b style={{ fontFamily: 'monospace' }}>{invited.temporary_password}</b></Typography>
              <Alert severity="warning" sx={{ mt: 2 }}>Adgangskoden vises kun nu.</Alert>
            </>
          ) : <Typography>Brugeren havde allerede et login.</Typography>}
        </DialogContent>
        <DialogActions><Button variant="contained" onClick={() => setInvited(null)}>Færdig</Button></DialogActions>
      </Dialog>


      <Dialog open={archiveOpen} onClose={() => setArchiveOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Arkivér {client.name}?</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Kunden kan ikke længere bogføre, og ingen kan ændre i bøgerne. Data slettes ikke: regnskabsmaterialet opbevares read-only i mindst 5 år (Bogføringsloven). Kunden kan fortsat eksportere sine data.
          </Alert>
          <TextField fullWidth size="small" label={`Skriv "${client.name}" for at bekræfte`} value={archiveConfirm} onChange={(e) => setArchiveConfirm(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setArchiveOpen(false)}>Annullér</Button>
          <Button color="error" variant="contained" disabled={archiveConfirm.trim() !== client.name} onClick={doArchive}>Arkivér</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!toast} autoHideDuration={2500} onClose={() => setToast('')} message={toast} />
    </Box>
  );
};

export default ClientDetail;
