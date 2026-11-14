import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography,
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { formatDate } from '../utils/dateFormat';

interface Incoming {
  id: string; document_type: string; format: string; document_number: string;
  issue_date: string | null; due_date: string | null; currency: string; total: string; tax_amount: string;
  sender_name: string; sender: string; status: string; status_display: string; error: string;
  bill_id: string | null; received_at: string; supplier_found: boolean;
}

interface Detail extends Incoming {
  parsed: {
    lines?: { description: string; quantity: string; unit_price: string; amount: string; tax_percent: string }[];
    suggestion?: { supplier_name: string; supplier_found: boolean; lines: { account_code: string | null; tax_code: string | null }[] };
  };
}

const STATUS_COLOR: Record<string, 'info' | 'success' | 'default' | 'error'> = {
  new: 'info', converted: 'success', rejected: 'default', failed: 'error',
};

const kr = (v: string, cur = 'DKK') =>
  `${Number(v).toLocaleString('da-DK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${cur === 'DKK' ? 'kr.' : cur}`;

/** Indbakke for modtagne e-fakturaer (Peppol/NemHandel). Hver faktura kan oprettes som regning. */
const EInvoiceInbox: React.FC = () => {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [docs, setDocs] = useState<Incoming[]>([]);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => api.get('/einvoice/inbox')
    .then((r) => setDocs(r.data.data.documents))
    .catch((e) => setError(e.response?.data?.message || 'Kunne ikke hente indbakken')), []);
  useEffect(() => { load(); }, [load]);

  const open = async (id: string) => {
    setError('');
    try { setDetail((await api.get(`/einvoice/inbox/${id}`)).data.data); } catch (e: any) {
      setError(e.response?.data?.message || 'Kunne ikke åbne e-fakturaen');
    }
  };

  const toBill = async (id: string) => {
    setBusy(true); setError('');
    try {
      const r = await api.post(`/einvoice/inbox/${id}/to-bill`, {});
      setInfo(r.data.message || 'Regningen er oprettet.');
      setDetail(null);
      await load();
    } catch (e: any) { setError(e.response?.data?.message || 'Kunne ikke oprette regningen'); } finally { setBusy(false); }
  };

  const reject = async (id: string) => {
    setBusy(true);
    try { await api.patch(`/einvoice/inbox/${id}`, { status: 'rejected' }); setDetail(null); await load(); } catch (e: any) {
      setError(e.response?.data?.message || 'Kunne ikke afvise');
    } finally { setBusy(false); }
  };

  const upload = async (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    setError(''); setInfo('');
    try {
      await api.post('/einvoice/inbox', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      setInfo(`${file.name} er lagt i indbakken.`);
      await load();
    } catch (e: any) { setError(e.response?.data?.message || 'Filen kunne ikke læses som e-faktura'); }
  };

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Typography variant="h5">E-faktura – indbakke</Typography>
        <Button variant="outlined" startIcon={<UploadFileIcon />} onClick={() => fileRef.current?.click()}>
          Upload UBL-fil
        </Button>
        <input ref={fileRef} type="file" accept=".xml,application/xml,text/xml" hidden
          onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(f); e.target.value = ''; }} />
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Fakturaer modtaget via Peppol/NemHandel (OIOUBL og Peppol BIS). Leverandøren findes ud fra CVR- eller
        GLN-nummer, og hver faktura kan oprettes som en regning (kladde), I gennemser før godkendelse.
        Den modtagne XML gemmes uændret som bilag.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {info && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setInfo('')}>{info}</Alert>}
      <Card variant="outlined">
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Modtaget</TableCell><TableCell>Leverandør</TableCell><TableCell>Nummer</TableCell>
                <TableCell>Dato</TableCell><TableCell>Forfald</TableCell><TableCell align="right">Beløb</TableCell>
                <TableCell>Status</TableCell><TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              {docs.length === 0 && (
                <TableRow><TableCell colSpan={8}><Typography color="text.secondary">Ingen e-fakturaer endnu.</Typography></TableCell></TableRow>
              )}
              {docs.map((d) => (
                <TableRow key={d.id} hover sx={{ cursor: 'pointer' }} onClick={() => open(d.id)}>
                  <TableCell>{formatDate(d.received_at)}</TableCell>
                  <TableCell>
                    {d.sender_name || '–'}
                    {d.status === 'new' && !d.supplier_found && <Chip size="small" label="Ny leverandør" sx={{ ml: 1 }} />}
                  </TableCell>
                  <TableCell>{d.document_type === 'credit_note' ? `Kreditnota ${d.document_number}` : d.document_number}</TableCell>
                  <TableCell>{formatDate(d.issue_date)}</TableCell>
                  <TableCell>{formatDate(d.due_date)}</TableCell>
                  <TableCell align="right">{kr(d.total, d.currency)}</TableCell>
                  <TableCell><Chip size="small" color={STATUS_COLOR[d.status] || 'default'} label={d.status_display} /></TableCell>
                  <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                    {d.status === 'new' && d.document_type === 'invoice' && (
                      <Button size="small" disabled={busy} onClick={() => toBill(d.id)}>Opret regning</Button>
                    )}
                    {d.bill_id && <Button size="small" onClick={() => navigate('/bills')}>Se regning</Button>}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={!!detail} onClose={() => setDetail(null)} maxWidth="md" fullWidth>
        {detail && (
          <>
            <DialogTitle>{detail.sender_name} – {detail.document_number}</DialogTitle>
            <DialogContent>
              {detail.error && <Alert severity="error" sx={{ mb: 2 }}>{detail.error}</Alert>}
              <Typography variant="body2" sx={{ mb: 1 }}>
                Afsender: {detail.sender || '–'} · Format: {detail.format || 'ukendt'} · Moms: {kr(detail.tax_amount, detail.currency)}
                {' '}· I alt: {kr(detail.total, detail.currency)}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {detail.parsed.suggestion?.supplier_found
                  ? `Leverandør fundet: ${detail.parsed.suggestion.supplier_name}`
                  : 'Leverandøren findes ikke endnu og oprettes sammen med regningen.'}
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Tekst</TableCell><TableCell align="right">Antal</TableCell>
                    <TableCell align="right">Pris</TableCell><TableCell align="right">Beløb</TableCell>
                    <TableCell align="right">Moms %</TableCell><TableCell>Forslag: konto / momskode</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(detail.parsed.lines || []).map((l, i) => {
                    const s = detail.parsed.suggestion?.lines?.[i];
                    return (
                      <TableRow key={i}>
                        <TableCell>{l.description}</TableCell>
                        <TableCell align="right">{l.quantity}</TableCell>
                        <TableCell align="right">{kr(l.unit_price, detail.currency)}</TableCell>
                        <TableCell align="right">{kr(l.amount, detail.currency)}</TableCell>
                        <TableCell align="right">{l.tax_percent}</TableCell>
                        <TableCell>{s?.account_code || '–'} / {s?.tax_code || '–'}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </DialogContent>
            <DialogActions>
              {detail.status === 'new' && <Button color="inherit" disabled={busy} onClick={() => reject(detail.id)}>Afvis</Button>}
              <Button onClick={() => setDetail(null)}>Luk</Button>
              {detail.status === 'new' && detail.document_type === 'invoice' && (
                <Button variant="contained" disabled={busy} onClick={() => toBill(detail.id)}>Opret regning</Button>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default EInvoiceInbox;
