import React, { useEffect, useState } from 'react';
import {
  Alert, Box, Button, Chip, CircularProgress, FormControlLabel, MenuItem, Paper, Switch, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, TextField, Tooltip, Typography,
} from '@mui/material';
import { Add as AddIcon, Login as WorkIcon, Search as SearchIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { firmApi } from '../../services/api';
import { useClient } from '../../hooks/useClient';
import { formatDate } from '../../utils/dateFormat';
import { accessState, CLIENT_STATUS, DEADLINE_KINDS, errorText, FirmClient, SCOPES, VAT_PERIODS } from '../api';
import { useAdmin } from '../AdminContext';

interface ClientStatus {
  drafts: number;
  unvalidated: number;
  documents_unlinked: number;
  open_reconciliations: number | null;
  suspense_balance: string;
  last_entry_date: string | null;
  last_closed_period: string | null;
}

/** Nøgletal fra kundens bøger – hentes først, når rækken vises, og kun med aktiv adgang. */
const StatusCell: React.FC<{ slug: string }> = ({ slug }) => {
  const [status, setStatus] = useState<ClientStatus | null>(null);
  const [error, setError] = useState('');
  const ref = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver((entries) => {
      if (!entries[0].isIntersecting) return;
      obs.disconnect();
      firmApi.get(`/clients/${slug}/status`)
        .then((r) => { if (!cancelled) setStatus(r.data.data.status); })
        .catch((e) => { if (!cancelled) setError(errorText(e, 'Kunne ikke hentes')); });
    });
    obs.observe(el);
    return () => { cancelled = true; obs.disconnect(); };
  }, [slug]);

  const chip = (n: number | null | undefined, text: string, color: 'warning' | 'error' | 'info' = 'warning') =>
    n ? <Chip size="small" color={color} variant="outlined" label={`${n} ${text}`} sx={{ mr: 0.5, mb: 0.3 }} /> : null;

  return (
    <Box ref={ref} sx={{ minWidth: 200 }}>
      {error && <Typography variant="caption" color="error">{error}</Typography>}
      {!status && !error && <CircularProgress size={14} />}
      {status && (
        <>
          {chip(status.drafts, 'kladder', 'info')}
          {chip(status.unvalidated, 'ikke validerede')}
          {chip(status.documents_unlinked, 'bilag uden postering', 'error')}
          {chip(status.open_reconciliations, 'uafstemt')}
          {!status.drafts && !status.unvalidated && !status.documents_unlinked && !status.open_reconciliations && (
            <Chip size="small" color="success" variant="outlined" label="Ajour" sx={{ mr: 0.5 }} />
          )}
          <Typography variant="caption" color="text.secondary" display="block">
            Lukket t.o.m.: {status.last_closed_period || '—'}
          </Typography>
        </>
      )}
    </Box>
  );
};

export const AccessChip: React.FC<{ access: FirmClient['access'] }> = ({ access }) => {
  const s = accessState(access);
  if (s === 'active') return <Chip size="small" color="success" label={`Aktiv · ${SCOPES[access as string]}`} />;
  if (s === 'ended') return <Chip size="small" label="Afsluttet" />;
  return <Chip size="small" variant="outlined" label="Ikke tildelt" />;
};

const ClientsList: React.FC = () => {
  const navigate = useNavigate();
  const { selectClient } = useClient();
  const { packages, role } = useAdmin();
  const [clients, setClients] = useState<FirmClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [q, setQ] = useState('');
  const [pkg, setPkg] = useState('');
  const [status, setStatus] = useState('');
  const [vat, setVat] = useState('');
  const [access, setAccess] = useState('');
  const [mine, setMine] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => {
      setLoading(true);
      const params: Record<string, string> = {};
      if (q) params.q = q;
      if (pkg) params.package = pkg;
      if (status) params.status = status;
      if (vat) params.vat_period = vat;
      if (mine) params.mine = '1';
      firmApi.get('/clients', { params })
        .then((r) => { setClients(r.data.data.clients); setError(''); })
        .catch((e) => setError(errorText(e, 'Kunne ikke hente kunderne')))
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(t);
  }, [q, pkg, status, vat, mine]);

  const shown = access ? clients.filter((c) => accessState(c.access) === access) : clients;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Kunder</Typography>
        <Typography sx={{ ml: 1.5 }} color="text.secondary">{shown.length} kunder</Typography>
        {role !== 'assistent' && (
          <Button sx={{ ml: 'auto' }} variant="contained" startIcon={<AddIcon />} onClick={() => navigate('/admin/clients/new')}>
            Opret kunde
          </Button>
        )}
      </Box>

      <Paper sx={{ p: 1.5, mb: 2, display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField size="small" placeholder="Søg navn eller CVR" value={q} onChange={(e) => setQ(e.target.value)}
          InputProps={{ startAdornment: <SearchIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} /> }}
          sx={{ minWidth: 240 }} />
        <TextField select size="small" label="Pakke" value={pkg} onChange={(e) => setPkg(e.target.value)} sx={{ minWidth: 120 }}>
          <MenuItem value="">Alle</MenuItem>
          {packages.map((p) => <MenuItem key={p.code} value={p.code}>{p.name}</MenuItem>)}
        </TextField>
        <TextField select size="small" label="Status" value={status} onChange={(e) => setStatus(e.target.value)} sx={{ minWidth: 140 }}>
          <MenuItem value="">Alle</MenuItem>
          {Object.entries(CLIENT_STATUS).map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
        </TextField>
        <TextField select size="small" label="Momsperiode" value={vat} onChange={(e) => setVat(e.target.value)} sx={{ minWidth: 150 }}>
          <MenuItem value="">Alle</MenuItem>
          {VAT_PERIODS.map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
        </TextField>
        <TextField select size="small" label="Adgang" value={access} onChange={(e) => setAccess(e.target.value)} sx={{ minWidth: 130 }}>
          <MenuItem value="">Alle</MenuItem>
          <MenuItem value="active">Aktiv</MenuItem>
          <MenuItem value="ended">Afsluttet</MenuItem>
          <MenuItem value="none">Ingen</MenuItem>
        </TextField>
        <FormControlLabel control={<Switch checked={mine} onChange={(e) => setMine(e.target.checked)} />} label="Mine kunder" />
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Kunde</TableCell>
              <TableCell>CVR</TableCell>
              <TableCell>Pakke</TableCell>
              <TableCell>Ansvarlig</TableCell>
              <TableCell>Adgang</TableCell>
              <TableCell>Næste frist</TableCell>
              <TableCell>Status i bøgerne</TableCell>
              <TableCell align="right" />
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && (
              <TableRow><TableCell colSpan={8} align="center"><CircularProgress size={22} /></TableCell></TableRow>
            )}
            {!loading && shown.length === 0 && (
              <TableRow><TableCell colSpan={8} align="center">Ingen kunder matcher filtrene.</TableCell></TableRow>
            )}
            {!loading && shown.map((c) => {
              const active = accessState(c.access) === 'active';
              return (
                <TableRow key={c.slug} hover sx={{ cursor: 'pointer' }} onClick={() => navigate(`/admin/clients/${c.slug}`)}>
                  <TableCell>
                    <Typography fontWeight={600} fontSize={13}>{c.name}</Typography>
                    <Box sx={{ display: 'flex', gap: 0.5, mt: 0.3 }}>
                      {c.status !== 'active' && <Chip size="small" label={CLIENT_STATUS[c.status]} />}
                      {c.answered_tasks > 0 && <Chip size="small" color="info" label={`${c.answered_tasks} nye svar`} />}
                      {c.open_tasks > 0 && <Chip size="small" variant="outlined" label={`${c.open_tasks} åbne opgaver`} />}
                    </Box>
                  </TableCell>
                  <TableCell>{c.cvr || '—'}</TableCell>
                  <TableCell>{c.package_name}</TableCell>
                  <TableCell>{c.responsible_name || '—'}</TableCell>
                  <TableCell><AccessChip access={c.access} /></TableCell>
                  <TableCell>
                    {c.next_deadline ? (
                      <Tooltip title={`${c.next_deadline.title} · ${c.next_deadline.period}`}>
                        <Box>
                          <Typography fontSize={13}>{formatDate(c.next_deadline.date)}</Typography>
                          <Typography variant="caption" color="text.secondary">{DEADLINE_KINDS[c.next_deadline.kind]}</Typography>
                        </Box>
                      </Tooltip>
                    ) : '—'}
                  </TableCell>
                  <TableCell>
                    {active ? <StatusCell slug={c.slug} /> : (
                      <Typography variant="caption" color="text.secondary">Kræver kundens samtykke</Typography>
                    )}
                  </TableCell>
                  <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                    <Tooltip title={active ? 'Åbn kundens bøger' : 'Kunden har ikke givet adgang'}>
                      <span>
                        <Button size="small" variant="outlined" startIcon={<WorkIcon />} disabled={!active}
                          onClick={() => selectClient(c.slug)}>
                          Arbejd i kunden
                        </Button>
                      </span>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default ClientsList;
