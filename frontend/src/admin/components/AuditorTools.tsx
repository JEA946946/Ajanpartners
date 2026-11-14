import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Badge, Box, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, IconButton,
  MenuItem, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Tooltip, Typography,
} from '@mui/material';
import {
  ChatBubbleOutline as CommentIcon, CheckCircleOutline as ResolveIcon, Delete as DeleteIcon,
  Download as DownloadIcon, Lock as LockIcon,
} from '@mui/icons-material';
import { CLIENT_KEY, firmApi } from '../../services/api';
import { downloadFile, errorText, formatAmount } from '../api';

interface Row {
  code: string; name: string; type: string; arl_line: string;
  opening: string; debit: string; credit: string; closing: string; open_comments: number;
}
interface FiscalYear { id: string; name: string; start_date: string; end_date: string; is_closed: boolean }
interface Comment { id: string; account_code: string; fiscal_year: number | null; body: string; resolved: boolean; author: string; created_at: string }

/** Saldobalance, eksport og kommentarer pr. konto. Kræver kundens samtykke (aktiv grant). */
const AuditorTools: React.FC<{ slug: string; canWork: boolean }> = ({ slug, canWork }) => {
  const [years, setYears] = useState<FiscalYear[]>([]);
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [rows, setRows] = useState<Row[]>([]);
  const [totals, setTotals] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [account, setAccount] = useState<Row | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');

  const load = useCallback((f?: string, t?: string) => {
    setLoading(true);
    firmApi.get(`/clients/${slug}/trial-balance`, { params: { from: f || undefined, to: t || undefined } })
      .then((r) => {
        const d = r.data.data;
        setRows(d.rows); setTotals(d.totals); setYears(d.fiscal_years); setFrom(d.from); setTo(d.to); setError('');
      })
      .catch((e) => setError(errorText(e, 'Saldobalancen kunne ikke hentes')))
      .finally(() => setLoading(false));
  }, [slug]);

  useEffect(() => { if (canWork) load(); }, [canWork, load]);

  const loadComments = (code: string) =>
    firmApi.get(`/clients/${slug}/account-comments`, { params: { account: code } })
      .then((r) => setComments(r.data.data.comments));

  const openAccount = (row: Row) => { setAccount(row); setNewComment(''); loadComments(row.code); };

  const fiscalYear = to ? Number(to.slice(0, 4)) : null;
  const addComment = async () => {
    if (!account) return;
    try {
      await firmApi.post(`/clients/${slug}/account-comments`, { account_code: account.code, body: newComment, fiscal_year: fiscalYear });
      setNewComment('');
      loadComments(account.code);
      load(from, to);
    } catch (e) { setError(errorText(e)); }
  };
  const updateComment = async (c: Comment, data: Partial<Comment> | null) => {
    if (data === null) await firmApi.delete(`/clients/${slug}/account-comments/${c.id}`);
    else await firmApi.put(`/clients/${slug}/account-comments/${c.id}`, data);
    loadComments(c.account_code);
    load(from, to);
  };

  const lockYear = () => {
    // Låsning sker i kundens eget API (periodeafslutning) med revisorens grant.
    localStorage.setItem(CLIENT_KEY, slug);
    window.location.href = '/closing';
  };

  if (!canWork) {
    return <Alert severity="info">Revisorværktøjerne kræver, at kunden har givet adgang til bøgerne.</Alert>;
  }

  return (
    <Box>
      <Paper sx={{ p: 1.5, mb: 2, display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField select size="small" label="Regnskabsår" sx={{ minWidth: 180 }}
          value={years.find((y) => y.start_date === from && y.end_date === to)?.id || ''}
          onChange={(e) => { const y = years.find((x) => x.id === e.target.value); if (y) load(y.start_date, y.end_date); }}>
          {years.map((y) => <MenuItem key={y.id} value={y.id}>{y.name}{y.is_closed ? ' (lukket)' : ''}</MenuItem>)}
        </TextField>
        <TextField size="small" type="date" label="Fra" InputLabelProps={{ shrink: true }} value={from} onChange={(e) => setFrom(e.target.value)} />
        <TextField size="small" type="date" label="Til" InputLabelProps={{ shrink: true }} value={to} onChange={(e) => setTo(e.target.value)} />
        <Button variant="outlined" onClick={() => load(from, to)}>Vis</Button>
        {loading && <CircularProgress size={18} />}
        <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
          <Button variant="contained" startIcon={<DownloadIcon />}
            onClick={() => downloadFile(`/clients/${slug}/trial-balance?export=csv&from=${from}&to=${to}`, 'saldobalance.csv')
              .catch((e) => setError(errorText(e, 'Eksporten mislykkedes')))}>
            Saldobalance (CSV)
          </Button>
          <Tooltip title="Åbner kundens periodeafslutning, hvor året låses efter godkendelse">
            <Button variant="outlined" startIcon={<LockIcon />} onClick={lockYear}>Lås regnskabsår</Button>
          </Tooltip>
        </Box>
      </Paper>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
        CSV-filen er semikolonsepareret med decimalkomma (UTF-8) og kolonnerne Kontonr, Kontonavn, Kontotype, ÅRL-linje, Primo, Debet, Kredit og Ultimo – til import i årsrapport-software.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <TableContainer component={Paper} sx={{ maxHeight: 560 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>Konto</TableCell>
              <TableCell>Navn</TableCell>
              <TableCell align="right">Primo</TableCell>
              <TableCell align="right">Debet</TableCell>
              <TableCell align="right">Kredit</TableCell>
              <TableCell align="right">Ultimo</TableCell>
              <TableCell align="center">Noter</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.length === 0 && !loading && <TableRow><TableCell colSpan={7} align="center">Ingen bogførte posteringer i perioden.</TableCell></TableRow>}
            {rows.map((r) => (
              <TableRow key={r.code} hover>
                <TableCell>{r.code}</TableCell>
                <TableCell>{r.name}</TableCell>
                <TableCell align="right">{formatAmount(r.opening)}</TableCell>
                <TableCell align="right">{formatAmount(r.debit)}</TableCell>
                <TableCell align="right">{formatAmount(r.credit)}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>{formatAmount(r.closing)}</TableCell>
                <TableCell align="center">
                  <IconButton size="small" onClick={() => openAccount(r)}>
                    <Badge color="warning" badgeContent={r.open_comments}><CommentIcon fontSize="small" /></Badge>
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {rows.length > 0 && (
              <TableRow>
                <TableCell colSpan={2}><b>I alt</b></TableCell>
                {['opening', 'debit', 'credit', 'closing'].map((k) => (
                  <TableCell key={k} align="right"><b>{formatAmount(totals[k] || 0)}</b></TableCell>
                ))}
                <TableCell />
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={!!account} onClose={() => setAccount(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Noter til konto {account?.code} {account?.name}</DialogTitle>
        <DialogContent dividers>
          {comments.length === 0 && <Typography color="text.secondary">Ingen noter endnu.</Typography>}
          {comments.map((c) => (
            <Paper key={c.id} variant="outlined" sx={{ p: 1.2, mb: 1, opacity: c.resolved ? 0.6 : 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="caption" color="text.secondary">
                  {c.author} · {new Date(c.created_at).toLocaleDateString('da-DK')}{c.fiscal_year ? ` · ${c.fiscal_year}` : ''}
                  {c.resolved ? ' · løst' : ''}
                </Typography>
                <Box sx={{ ml: 'auto' }}>
                  <Tooltip title={c.resolved ? 'Genåbn' : 'Markér som løst'}>
                    <IconButton size="small" onClick={() => updateComment(c, { resolved: !c.resolved })}><ResolveIcon fontSize="small" /></IconButton>
                  </Tooltip>
                  <IconButton size="small" onClick={() => updateComment(c, null)}><DeleteIcon fontSize="small" /></IconButton>
                </Box>
              </Box>
              <Typography sx={{ whiteSpace: 'pre-wrap' }}>{c.body}</Typography>
            </Paper>
          ))}
          <TextField fullWidth multiline minRows={2} size="small" sx={{ mt: 1 }} label="Ny note"
            value={newComment} onChange={(e) => setNewComment(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAccount(null)}>Luk</Button>
          <Button variant="contained" disabled={!newComment.trim()} onClick={addComment}>Tilføj note</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AuditorTools;
