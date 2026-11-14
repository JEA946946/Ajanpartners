import React, { useCallback, useEffect, useState } from 'react';
import {
  Box, Typography, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
  TextField, Card, CardContent, Chip, Alert, MenuItem, Dialog, DialogTitle, DialogContent, DialogActions,
  List, ListItemButton, ListItemText,
} from '@mui/material';
import { Lock as LockIcon, Download as DownloadIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { exportToCSV } from '../utils/csvExport';
import { formatDate, formatMoney, formatNumber } from '../utils/format';

interface VatPeriod {
  start: string; end: string; name: string; deadline: string;
  status: 'open' | 'draft' | 'filed'; settled: boolean; momstilsvar: string | null;
}
interface VatField { key: string; name: string; amount: string; amount_kr: string }
interface ReconRow { field: string; account_code: string; account_name: string; booked: string; from_vat_codes: string; manual: string }
interface VatReturn {
  id: string; status: string; settlement_entry: string | null; filed_at: string | null; filed_by: string;
  receipt_number: string;
}
interface VatReportData {
  start: string; end: string; deadline: string; fields: VatField[]; reconciliation: ReconRow[];
  account_balances: Record<string, string>; return: VatReturn | null;
}

const MOMS_KEYS = ['salgsmoms', 'moms_varekoeb_udland', 'moms_ydelseskoeb_udland', 'koebsmoms'];
const AFGIFT_KEYS = ['olie_flaskegasafgift', 'elafgift', 'naturgas_bygasafgift', 'kulafgift', 'co2_afgift', 'vandafgift'];

const TaxReport: React.FC = () => {
  const { t } = useTranslation();
  const [year, setYear] = useState(new Date().getFullYear());
  const [vatPeriod, setVatPeriod] = useState('');
  const [periods, setPeriods] = useState<VatPeriod[]>([]);
  const [selected, setSelected] = useState<VatPeriod | null>(null);
  const [report, setReport] = useState<VatReportData | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
  const [fileOpen, setFileOpen] = useState(false);
  const [receipt, setReceipt] = useState('');
  const [busy, setBusy] = useState(false);

  const loadPeriods = useCallback(() => {
    api.get(`/vat/periods?year=${year}`).then(res => {
      if (res.data.success) {
        setVatPeriod(res.data.data.vat_period);
        setPeriods(res.data.data.periods || []);
      }
    }).catch(e => setMessage({ type: 'error', text: e?.response?.data?.message || t('vat.loadError', 'Momsperioderne kunne ikke hentes') }));
  }, [year, t]);

  const loadReport = useCallback((p: VatPeriod) => {
    api.get(`/vat/report?start=${p.start}&end=${p.end}`).then(res => {
      if (res.data.success) setReport(res.data.data);
    }).catch(e => setMessage({ type: 'error', text: e?.response?.data?.message || t('vat.reportError', 'Momsangivelsen kunne ikke beregnes') }));
  }, [t]);

  useEffect(() => { loadPeriods(); }, [loadPeriods]);
  useEffect(() => { if (selected) loadReport(selected); }, [selected, loadReport]);

  const act = async (path: string, body: Record<string, string> = {}) => {
    if (!selected) return;
    setBusy(true);
    setMessage(null);
    try {
      const res = await api.post(`/vat/${path}`, { start: selected.start, end: selected.end, ...body });
      setMessage({ type: 'success', text: res.data.message });
      loadPeriods();
      loadReport(selected);
    } catch (e: any) {
      setMessage({ type: 'error', text: e?.response?.data?.message || t('vat.actionError', 'Handlingen mislykkedes') });
    } finally {
      setBusy(false);
    }
  };

  const statusChip = (p: { status: string; settled: boolean }) => {
    if (p.status === 'filed') return <Chip size="small" color="success" icon={<LockIcon />} label={t('vat.statusFiled', 'Angivet og låst')} />;
    if (p.settled) return <Chip size="small" color="warning" label={t('vat.statusSettled', 'Afregning bogført')} />;
    return <Chip size="small" variant="outlined" label={t('vat.statusOpen', 'Åben')} />;
  };

  const fieldRows = (keys: string[]) => (report?.fields || []).filter(f => keys.includes(f.key));
  const rubrikRows = () => (report?.fields || []).filter(f => f.key.startsWith('rubrik_'));
  const tilsvar = report?.fields.find(f => f.key === 'momstilsvar');
  const filed = report?.return?.status === 'filed';
  const settled = !!report?.return?.settlement_entry;

  const exportCsv = () => {
    if (!report) return;
    exportToCSV(`moms_${report.start}_${report.end}.csv`,
      [t('vat.field', 'Felt'), t('vat.exact', 'Beløb'), t('vat.wholeKr', 'Hele kroner')],
      report.fields.map(f => [f.name, f.amount, f.amount_kr]));
  };

  const fieldTable = (title: string, rows: VatField[], hint?: string) => (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{title}</Typography>
        {hint && <Typography variant="caption" color="text.secondary">{hint}</Typography>}
        <Table size="small" sx={{ mt: 1 }}>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>{t('vat.field', 'Felt')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('vat.exact', 'Beløb')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('vat.toTastSelv', 'Til TastSelv (hele kr.)')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map(f => (
              <TableRow key={f.key}>
                <TableCell>{f.name}</TableCell>
                <TableCell align="right">{formatNumber(f.amount)}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600, fontFamily: 'monospace' }}>{formatNumber(f.amount_kr).replace(/,00$/, '')}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>{t('vat.title', 'Momsangivelse')}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('vat.intro', 'Momsangivelsen beregnes ud fra momskontiene (salgsmoms, købsmoms, moms af køb i udlandet og energiafgifter) og rubrikkerne A, B og C ud fra momskoderne på posteringerne. Bogfør momsafregningen, indberet beløbene på Skats TastSelv Erhverv i hele kroner, og markér derefter perioden som angivet. En angivet periode er låst: der kan ikke længere bogføres i den.')}
      </Typography>

      {message && <Alert severity={message.type} sx={{ mb: 2 }} onClose={() => setMessage(null)}>{message.text}</Alert>}

      {vatPeriod === 'none' && (
        <Alert severity="info">{t('vat.notRegistered', 'Kunden er ikke momsregistreret.')}</Alert>
      )}

      {vatPeriod !== 'none' && (
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <Card sx={{ width: 300, flexShrink: 0 }}>
            <CardContent>
              <TextField select size="small" fullWidth label={t('vat.year', 'År')} value={year}
                onChange={e => { setYear(Number(e.target.value)); setSelected(null); setReport(null); }}>
                {[0, 1, 2, 3].map(d => new Date().getFullYear() + 1 - d).map(y => <MenuItem key={y} value={y}>{y}</MenuItem>)}
              </TextField>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                {t('vat.periodType', 'Momsperiode: {{type}}', {
                  type: ({ month: t('vat.month', 'måned'), quarter: t('vat.quarter', 'kvartal'), half: t('vat.half', 'halvår') } as Record<string, string>)[vatPeriod] || vatPeriod,
                })}
              </Typography>
              <List dense>
                {periods.map(p => (
                  <ListItemButton key={p.start} selected={selected?.start === p.start} onClick={() => setSelected(p)}>
                    <ListItemText
                      primary={p.name}
                      secondary={t('vat.deadline', 'Frist {{date}}', { date: formatDate(p.deadline) })}
                    />
                    {statusChip(p)}
                  </ListItemButton>
                ))}
              </List>
            </CardContent>
          </Card>

          <Box sx={{ flex: 1, minWidth: 360 }}>
            {!report && <Typography color="text.secondary">{t('vat.choosePeriod', 'Vælg en momsperiode.')}</Typography>}
            {report && (
              <>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                  <Typography variant="h6">
                    {formatDate(report.start)} – {formatDate(report.end)}
                  </Typography>
                  {statusChip({ status: report.return?.status || 'open', settled })}
                  <Typography variant="body2" color="text.secondary">
                    {t('vat.deadline', 'Frist {{date}}', { date: formatDate(report.deadline) })}
                  </Typography>
                  <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
                    <Button size="small" startIcon={<DownloadIcon />} onClick={exportCsv}>{t('common.exportCsv')}</Button>
                    {!filed && !settled && (
                      <Button size="small" variant="contained" disabled={busy} onClick={() => act('settle')}>
                        {t('vat.settle', 'Bogfør momsafregning')}
                      </Button>
                    )}
                    {!filed && settled && (
                      <>
                        <Button size="small" color="inherit" disabled={busy} onClick={() => act('unsettle')}>
                          {t('vat.unsettle', 'Fjern afregning')}
                        </Button>
                        <Button size="small" variant="contained" color="success" disabled={busy} onClick={() => setFileOpen(true)}>
                          {t('vat.markFiled', 'Markér som angivet')}
                        </Button>
                      </>
                    )}
                  </Box>
                </Box>

                {filed && (
                  <Alert severity="success" icon={<LockIcon />} sx={{ mb: 2 }}>
                    {t('vat.filedInfo', 'Angivet {{date}} af {{by}}{{receipt}}. Perioden er låst; rettelser bogføres i en åben periode og angives som en ændring hos Skat.', {
                      date: report.return?.filed_at ? formatDate(report.return.filed_at) : '',
                      by: report.return?.filed_by || '',
                      receipt: report.return?.receipt_number ? ` (${t('vat.receipt', 'kvittering')} ${report.return.receipt_number})` : '',
                    })}
                  </Alert>
                )}
                {settled && !filed && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    {t('vat.settledInfo', 'Momsafregningen er bogført ({{entry}}): momskontiene er nulstillet mod momsafregningskontoen. Indtast felterne nedenfor på TastSelv Erhverv i hele kroner.', {
                      entry: report.return?.settlement_entry,
                    })}
                  </Alert>
                )}

                {tilsvar && (
                  <Card sx={{ mb: 2, bgcolor: parseFloat(tilsvar.amount) >= 0 ? '#fff3e0' : '#e8f5e9' }}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">{tilsvar.name}</Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>{formatMoney(tilsvar.amount_kr)}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {parseFloat(tilsvar.amount) >= 0 ? t('vat.toPay', 'Skal betales til Skat') : t('vat.toReceive', 'Tilgode hos Skat')}
                        {' · '}{t('vat.exactAmount', 'præcist {{amount}}', { amount: formatMoney(tilsvar.amount) })}
                      </Typography>
                    </CardContent>
                  </Card>
                )}

                {fieldTable(t('vat.vatFields', 'Moms'), fieldRows(MOMS_KEYS))}
                {fieldTable(t('vat.dutyFields', 'Energiafgifter (godtgørelse)'), fieldRows(AFGIFT_KEYS))}
                {fieldTable(t('vat.rubrikFields', 'Rubrikker (værdi uden moms)'), rubrikRows(),
                  t('vat.rubrikHint', 'Rubrik A: køb i andre EU-lande. Rubrik B: salg til andre EU-lande (B-varer, der skal indberettes, indberettes også til EU-salg uden moms). Rubrik C: andre leverancer uden moms.'))}

                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{t('vat.reconciliation', 'Afstemning mod saldobalancen')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('vat.reconHint', 'Bogført = bevægelsen på momskontoen i perioden (uden momsafregningen). "Uden momskode" er manuelle posteringer på momskontoen; de skal kunne forklares.')}
                    </Typography>
                    <TableContainer component={Paper} variant="outlined" sx={{ mt: 1 }}>
                      <Table size="small">
                        <TableHead>
                          <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                            <TableCell sx={{ fontWeight: 600 }}>{t('common.account')}</TableCell>
                            <TableCell align="right" sx={{ fontWeight: 600 }}>{t('vat.booked', 'Bogført')}</TableCell>
                            <TableCell align="right" sx={{ fontWeight: 600 }}>{t('vat.fromCodes', 'Fra momskoder')}</TableCell>
                            <TableCell align="right" sx={{ fontWeight: 600 }}>{t('vat.manual', 'Uden momskode')}</TableCell>
                            <TableCell align="right" sx={{ fontWeight: 600 }}>{t('vat.balanceAtEnd', 'Saldo pr. {{date}}', { date: formatDate(report.end) })}</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {report.reconciliation.map(r => (
                            <TableRow key={r.account_code}>
                              <TableCell><Box component="span" sx={{ fontFamily: 'monospace', mr: 1 }}>{r.account_code}</Box>{r.account_name}</TableCell>
                              <TableCell align="right">{formatNumber(r.booked)}</TableCell>
                              <TableCell align="right">{formatNumber(r.from_vat_codes)}</TableCell>
                              <TableCell align="right" sx={{ color: parseFloat(r.manual) ? 'warning.main' : 'inherit', fontWeight: parseFloat(r.manual) ? 600 : 400 }}>
                                {formatNumber(r.manual)}
                              </TableCell>
                              <TableCell align="right">{formatNumber(report.account_balances[r.account_code] || '0')}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </>
            )}
          </Box>
        </Box>
      )}

      <Dialog open={fileOpen} onClose={() => setFileOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>{t('vat.fileTitle', 'Markér perioden som angivet')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            {t('vat.fileText', 'Gør det, når angivelsen er indberettet på TastSelv Erhverv. Perioden låses derefter, så ingen posteringer kan dateres i den.')}
          </Typography>
          <TextField fullWidth size="small" label={t('vat.receiptNumber', 'Kvitteringsnummer fra Skat (valgfrit)')}
            value={receipt} onChange={e => setReceipt(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFileOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" color="success" disabled={busy}
            onClick={async () => { setFileOpen(false); await act('file', { receipt_number: receipt }); setReceipt(''); }}>
            {t('vat.confirmFile', 'Angivet – lås perioden')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TaxReport;
