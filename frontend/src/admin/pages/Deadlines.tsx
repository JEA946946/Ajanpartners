import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert, Box, Chip, CircularProgress, IconButton, MenuItem, Paper, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, TextField, ToggleButton, ToggleButtonGroup, Tooltip, Typography,
} from '@mui/material';
import { ChevronLeft, ChevronRight } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { Deadline, DEADLINE_KINDS, errorText, isoDate, MONTHS } from '../api';
import { useAdmin } from '../AdminContext';

const KIND_COLOR: Record<string, string> = {
  moms: '#1565c0', a_skat: '#6a1b9a', aarsrapport: '#2e7d32', selvangivelse: '#c62828',
  oplysningsskema: '#c62828', acontoskat: '#ef6c00', opdrag: '#455a64',
};
const WEEKDAYS = ['man', 'tir', 'ons', 'tor', 'fre', 'lør', 'søn'];

export const KindChip: React.FC<{ kind: string }> = ({ kind }) => (
  <Chip size="small" label={DEADLINE_KINDS[kind] || kind}
    sx={{ bgcolor: KIND_COLOR[kind], color: '#fff', fontWeight: 500 }} />
);

/** Listevisning af frister (bruges også på kundens side). */
export const DeadlineTable: React.FC<{ rows: Deadline[]; showClient?: boolean }> = ({ rows, showClient = true }) => {
  const navigate = useNavigate();
  const today = isoDate(new Date());
  return (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Frist</TableCell>
            <TableCell>Type</TableCell>
            {showClient && <TableCell>Kunde</TableCell>}
            <TableCell>Hvad</TableCell>
            <TableCell>Periode</TableCell>
            {showClient && <TableCell>Ansvarlig</TableCell>}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.length === 0 && <TableRow><TableCell colSpan={6} align="center">Ingen frister i perioden.</TableCell></TableRow>}
          {rows.map((d, i) => {
            const days = Math.round((new Date(d.date).getTime() - new Date(today).getTime()) / 86400000);
            return (
              <TableRow key={`${d.client}-${d.kind}-${d.period}-${i}`} hover
                sx={{ cursor: showClient ? 'pointer' : undefined }}
                onClick={() => (d.engagement ? navigate(`/admin/engagements/${d.engagement}`) : showClient && d.client && navigate(`/admin/clients/${d.client}`))}>
                <TableCell>
                  <Typography fontSize={13} fontWeight={600} color={days >= 0 && days <= 7 ? 'error.main' : undefined}>
                    {formatDate(d.date)}
                  </Typography>
                  {d.shifted && (
                    <Tooltip title={`Reglens dato ${formatDate(d.due)} er ikke en bank-/hverdag`}>
                      <Typography variant="caption" color="text.secondary">rykket fra {formatDate(d.due)}</Typography>
                    </Tooltip>
                  )}
                </TableCell>
                <TableCell><KindChip kind={d.kind} /></TableCell>
                {showClient && <TableCell>{d.client_name}{d.cvr ? ` · ${d.cvr}` : ''}</TableCell>}
                <TableCell>
                  {d.title}
                  {d.note && <Typography variant="caption" color="text.secondary" display="block">{d.note}</Typography>}
                </TableCell>
                <TableCell>{d.period}</TableCell>
                {showClient && <TableCell>{d.responsible_name || '—'}</TableCell>}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

const MonthView: React.FC<{ year: number; month: number; rows: Deadline[] }> = ({ year, month, rows }) => {
  const navigate = useNavigate();
  const first = new Date(year, month, 1);
  const offset = (first.getDay() + 6) % 7; // mandag først
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells = Array.from({ length: Math.ceil((offset + daysInMonth) / 7) * 7 }, (_, i) => i - offset + 1);
  const byDay = useMemo(() => {
    const m: Record<number, Deadline[]> = {};
    rows.forEach((d) => {
      const [y, mo, day] = d.date.split('-').map(Number);
      if (y === year && mo - 1 === month) (m[day] ||= []).push(d);
    });
    return m;
  }, [rows, year, month]);
  const today = new Date();

  return (
    <Paper sx={{ p: 1 }}>
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 0.5 }}>
        {WEEKDAYS.map((w) => <Typography key={w} variant="caption" align="center" fontWeight={600}>{w}</Typography>)}
        {cells.map((day, i) => {
          const valid = day >= 1 && day <= daysInMonth;
          const isToday = valid && today.getFullYear() === year && today.getMonth() === month && today.getDate() === day;
          const weekend = i % 7 >= 5;
          return (
            <Box key={i} sx={{
              minHeight: 96, border: '1px solid', borderColor: isToday ? 'primary.main' : 'divider', borderRadius: 1, p: 0.5,
              bgcolor: !valid ? 'transparent' : weekend ? '#f7f7f7' : '#fff', overflow: 'hidden',
            }}>
              {valid && <Typography variant="caption" fontWeight={isToday ? 700 : 400}>{day}</Typography>}
              {valid && (byDay[day] || []).slice(0, 4).map((d, j) => (
                <Tooltip key={j} title={`${d.client_name}: ${d.title} – ${d.period}`}>
                  <Box onClick={() => d.client && navigate(`/admin/clients/${d.client}`)} sx={{
                    fontSize: 11, px: 0.5, mb: 0.3, borderRadius: 0.5, color: '#fff', bgcolor: KIND_COLOR[d.kind],
                    whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', cursor: 'pointer',
                  }}>
                    {DEADLINE_KINDS[d.kind]} · {d.client_name}
                  </Box>
                </Tooltip>
              ))}
              {valid && (byDay[day]?.length || 0) > 4 && (
                <Typography variant="caption" color="text.secondary">+{byDay[day].length - 4} flere</Typography>
              )}
            </Box>
          );
        })}
      </Box>
    </Paper>
  );
};

const Deadlines: React.FC = () => {
  const { staff } = useAdmin();
  const now = new Date();
  const [view, setView] = useState<'list' | 'month'>('list');
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());
  const [listDays, setListDays] = useState(90);
  const [staffId, setStaffId] = useState('');
  const [kind, setKind] = useState('');
  const [rows, setRows] = useState<Deadline[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let from: Date, to: Date;
    if (view === 'month') {
      from = new Date(year, month, 1);
      to = new Date(year, month + 1, 0);
    } else {
      from = new Date();
      to = new Date(Date.now() + listDays * 86400000);
    }
    const params: Record<string, string> = { from: isoDate(from), to: isoDate(to) };
    if (staffId) params.staff = staffId;
    if (kind) params.kind = kind;
    setLoading(true);
    firmApi.get('/deadlines', { params })
      .then((r) => { setRows(r.data.data.deadlines); setError(''); })
      .catch((e) => setError(errorText(e, 'Fristerne kunne ikke hentes')))
      .finally(() => setLoading(false));
  }, [view, year, month, listDays, staffId, kind]);

  const shiftMonth = (n: number) => {
    const d = new Date(year, month + n, 1);
    setYear(d.getFullYear());
    setMonth(d.getMonth());
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 0.5 }}>Fristkalender</Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Beregnet ud fra kundernes momsperiode, regnskabsår, regnskabsklasse og virksomhedsform. Frister på weekend- og helligdage er rykket til næste bank-/hverdag.
      </Typography>
      <Paper sx={{ p: 1.5, mb: 2, display: 'flex', gap: 1.5, alignItems: 'center', flexWrap: 'wrap' }}>
        <ToggleButtonGroup size="small" exclusive value={view} onChange={(_, v) => v && setView(v)}>
          <ToggleButton value="list">Liste</ToggleButton>
          <ToggleButton value="month">Måned</ToggleButton>
        </ToggleButtonGroup>
        {view === 'month' ? (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton size="small" onClick={() => shiftMonth(-1)}><ChevronLeft /></IconButton>
            <Typography sx={{ minWidth: 120, textAlign: 'center', textTransform: 'capitalize' }}>{MONTHS[month]} {year}</Typography>
            <IconButton size="small" onClick={() => shiftMonth(1)}><ChevronRight /></IconButton>
          </Box>
        ) : (
          <TextField select size="small" label="Periode" value={listDays} onChange={(e) => setListDays(Number(e.target.value))} sx={{ minWidth: 150 }}>
            <MenuItem value={30}>Næste 30 dage</MenuItem>
            <MenuItem value={90}>Næste 3 måneder</MenuItem>
            <MenuItem value={180}>Næste 6 måneder</MenuItem>
            <MenuItem value={365}>Næste 12 måneder</MenuItem>
          </TextField>
        )}
        <TextField select size="small" label="Medarbejder" value={staffId} onChange={(e) => setStaffId(e.target.value)} sx={{ minWidth: 180 }}>
          <MenuItem value="">Alle</MenuItem>
          {staff.map((s) => (
            <MenuItem key={s.user_id} value={String(s.user_id)}>{`${s.first_name} ${s.last_name}`.trim() || s.username}</MenuItem>
          ))}
        </TextField>
        <TextField select size="small" label="Type" value={kind} onChange={(e) => setKind(e.target.value)} sx={{ minWidth: 150 }}>
          <MenuItem value="">Alle</MenuItem>
          {Object.entries(DEADLINE_KINDS).map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
        </TextField>
        {loading && <CircularProgress size={18} />}
      </Paper>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {view === 'list' ? <DeadlineTable rows={rows} /> : <MonthView year={year} month={month} rows={rows} />}
      <Alert severity="info" sx={{ mt: 2 }}>
        A-skat/AM vises for kunder med lønmodulet og med fristen for små og mellemstore virksomheder (den 10. i måneden efter).
        Store virksomheder har frist den sidste bankdag i lønmåneden. Tjek altid Skats aktuelle kalender.
      </Alert>
    </Box>
  );
};

export default Deadlines;
