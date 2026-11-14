import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Card, CardContent, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Tabs, Tab, TextField, Button, Chip, Link,
  MenuItem, Autocomplete, Alert, IconButton, Collapse,
} from '@mui/material';
import { Download as DownloadIcon, ExpandMore, ChevronRight } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { exportToCSV } from '../utils/csvExport';
import { formatDate, formatMoney, formatNumber } from '../utils/format';

interface AccountOption { id: string; code: string; name: string; is_header?: boolean }

const num = (v: string | number | null | undefined) => formatNumber(v ?? 0);
const head = { fontWeight: 600 };

const Reports: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [tab, setTab] = useState(0);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [compare, setCompare] = useState('period');
  const [accounts, setAccounts] = useState<AccountOption[]>([]);
  const [cardAccount, setCardAccount] = useState<AccountOption | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [error, setError] = useState('');

  const [trialBalance, setTrialBalance] = useState<any>(null);
  const [pnl, setPnl] = useState<any>(null);
  const [balanceSheet, setBalanceSheet] = useState<any>(null);
  const [accountCard, setAccountCard] = useState<any>(null);
  const [cashFlow, setCashFlow] = useState<any>(null);
  const [generalLedger, setGeneralLedger] = useState<any>(null);
  const [agingReceivable, setAgingReceivable] = useState<any>(null);
  const [agingPayable, setAgingPayable] = useState<any>(null);

  useEffect(() => {
    api.get('/accounts').then(res => {
      if (res.data.success) setAccounts((res.data.data.accounts || []).filter((a: AccountOption) => !a.is_header));
    });
  }, []);

  const fetchReport = () => {
    const params = new URLSearchParams();
    if (dateFrom) params.set('date_from', dateFrom);
    if (dateTo) params.set('date_to', dateTo);
    setError('');
    const onErr = (e: any) => setError(e?.response?.data?.message || t('reports.loadError', 'Rapporten kunne ikke hentes'));

    if (tab === 0) {
      params.set('compare', compare);
      api.get(`/reports/trial-balance?${params}`).then(res => res.data.success && setTrialBalance(res.data.data)).catch(onErr);
    } else if (tab === 1) {
      api.get(`/reports/profit-and-loss?${params}`).then(res => res.data.success && setPnl(res.data.data)).catch(onErr);
    } else if (tab === 2) {
      const bp = new URLSearchParams();
      if (dateTo) bp.set('date', dateTo);
      api.get(`/reports/balance-sheet?${bp}`).then(res => res.data.success && setBalanceSheet(res.data.data)).catch(onErr);
    } else if (tab === 3) {
      if (!cardAccount) { setAccountCard(null); return; }
      params.set('account_id', cardAccount.id);
      api.get(`/reports/account-card?${params}`).then(res => res.data.success && setAccountCard(res.data.data)).catch(onErr);
    } else if (tab === 4) {
      api.get(`/reports/cash-flow?${params}`).then(res => res.data.success && setCashFlow(res.data)).catch(onErr);
    } else if (tab === 5) {
      api.get(`/reports/general-ledger?${params}`).then(res => res.data.success && setGeneralLedger(res.data.data)).catch(onErr);
    } else if (tab === 6) {
      const ap = dateTo ? `?as_of=${dateTo}` : '';
      api.get(`/reports/aging-receivable${ap}`).then(res => res.data.success && setAgingReceivable(res.data.data)).catch(onErr);
      api.get(`/reports/aging-payable${ap}`).then(res => res.data.success && setAgingPayable(res.data.data)).catch(onErr);
    }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps -- hent igen ved fanebyt; datoerne gælder, når brugeren trykker Anvend
  useEffect(() => { fetchReport(); }, [tab, cardAccount]);

  const compareLabel = (c: string) => ({
    period: t('reports.comparePeriod', 'Samme periode sidste år'),
    year: t('reports.compareYear', 'År til dato'),
    last_year: t('reports.compareLastYear', 'Hele sidste regnskabsår'),
  } as Record<string, string>)[c] || c;

  const handleExportCSV = () => {
    if (tab === 0 && trialBalance) {
      exportToCSV('saldobalance.csv',
        [t('common.code'), t('common.account'), t('reports.standardCode', 'Standardkonto'), t('reports.opening', 'Primo'),
          t('common.debit'), t('common.credit'), t('reports.closing', 'Ultimo'), compareLabel(trialBalance.compare)],
        trialBalance.rows.map((r: any) => [r.account_code, r.account_name, r.standard_code, r.opening, r.debit, r.credit,
          r.closing, r.compare]));
    } else if (tab === 1 && pnl) {
      const rows: string[][] = [];
      pnl.sections.forEach((s: any) => {
        rows.push([s.type === 'subtotal' ? `= ${s.name}` : s.name, '', s.amount, s.amount_prev]);
        (s.accounts || []).forEach((a: any) => rows.push([a.account_code, a.account_name, a.amount, a.amount_prev]));
      });
      exportToCSV('resultatopgoerelse.csv', [t('common.code'), t('common.account'), t('reports.thisPeriod', 'Periode'),
        t('reports.lastYear', 'Sidste år')], rows);
    } else if (tab === 2 && balanceSheet) {
      const rows: string[][] = [];
      [[t('reports.assets'), balanceSheet.assets], [t('reports.liabilitiesAndEquity', 'Passiver'), balanceSheet.liabilities]]
        .forEach(([title, lines]: any) => {
          rows.push([`--- ${title} ---`, '', '', '']);
          lines.forEach((l: any) => {
            rows.push([l.name, '', l.amount, l.amount_prev]);
            l.accounts.forEach((a: any) => rows.push([a.account_code, a.account_name, a.amount, a.amount_prev]));
          });
        });
      exportToCSV('balance.csv', [t('common.code'), t('common.account'), balanceSheet.date, balanceSheet.compare_date], rows);
    } else if (tab === 3 && accountCard) {
      exportToCSV(`kontokort_${accountCard.account.code}.csv`,
        [t('reports.date'), t('reports.entry'), t('reports.journal', 'Journal'), t('reports.description'),
          t('common.debit'), t('common.credit'), t('common.balance')],
        [['', '', '', t('reports.opening', 'Primo'), '', '', accountCard.opening],
          ...accountCard.lines.map((l: any) => [l.date, l.entry_number, l.journal, l.description, l.debit, l.credit, l.balance]),
          ['', '', '', t('reports.closing', 'Ultimo'), accountCard.total_debit, accountCard.total_credit, accountCard.closing]]);
    } else if (tab === 4 && cashFlow) {
      const rows: string[][] = [];
      (cashFlow.sections || []).forEach((s: any) => {
        rows.push([`--- ${s.name} ---`, '', '']);
        (s.rows || []).forEach((r: any) => rows.push([r.account_code || '', r.description || r.account_name || '', r.amount]));
        rows.push([`${t('common.total')} ${s.name}`, '', s.total]);
      });
      rows.push([t('reports.netCashFlow'), '', cashFlow.net_cash_flow]);
      exportToCSV('pengestroem.csv', [t('common.code'), t('reports.description'), t('common.amount', 'Beløb')], rows);
    } else if (tab === 5 && generalLedger) {
      const rows: string[][] = [];
      (generalLedger.accounts || []).forEach((a: any) => {
        rows.push([`--- ${a.account_code} ${a.account_name} ---`, '', '', '', '']);
        (a.lines || []).forEach((e: any) => rows.push([e.date, e.entry_number, e.description, e.debit, e.credit]));
        rows.push(['', '', t('common.total'), a.total_debit, a.total_credit]);
      });
      exportToCSV('hovedbog.csv', [t('reports.date'), t('reports.entry'), t('reports.description'), t('common.debit'), t('common.credit')], rows);
    } else if (tab === 6) {
      const rows: string[][] = [];
      if (agingReceivable) {
        rows.push([`--- ${t('reports.receivableAging')} ---`, '', '', '', '', '']);
        (agingReceivable.rows || []).forEach((r: any) => rows.push([r.customer_name, r.current, r.days_1_30, r.days_31_60, r.days_61_90, r.days_over_90]));
      }
      if (agingPayable) {
        rows.push([`--- ${t('reports.payableAging')} ---`, '', '', '', '', '']);
        (agingPayable.rows || []).forEach((r: any) => rows.push([r.supplier_name, r.current, r.days_1_30, r.days_31_60, r.days_61_90, r.days_over_90]));
      }
      exportToCSV('aldersfordeling.csv', [t('reports.name', 'Navn'), t('reports.current'), t('reports.days1to30'), t('reports.days31to60'), t('reports.days61to90'), t('reports.daysOver90')], rows);
    }
  };

  const openCard = (accountId: string) => {
    const acc = accounts.find(a => a.id === accountId);
    if (acc) { setCardAccount(acc); setTab(3); } else navigate(`/accounts?ledger=${accountId}`);
  };

  const toggle = (key: string) => setExpanded(e => ({ ...e, [key]: !e[key] }));

  // ─── Saldobalance ───
  const renderTrialBalance = () => {
    if (!trialBalance) return null;
    const tot = trialBalance.totals;
    return (
      <TableContainer component={Paper}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', px: 2, pt: 1 }}>
          {t('reports.tbHint', 'Debet/kredit er periodens bevægelser i DKK. Sammenligning: {{label}} ({{from}} – {{to}}).', {
            label: compareLabel(trialBalance.compare), from: formatDate(trialBalance.compare_from), to: formatDate(trialBalance.compare_to),
          })}
        </Typography>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell sx={head}>{t('common.code')}</TableCell>
              <TableCell sx={head}>{t('common.account')}</TableCell>
              <TableCell sx={head}>{t('reports.arlLine', 'ÅRL-linje')}</TableCell>
              <TableCell align="right" sx={head}>{t('reports.opening', 'Primo')}</TableCell>
              <TableCell align="right" sx={head}>{t('common.debit')}</TableCell>
              <TableCell align="right" sx={head}>{t('common.credit')}</TableCell>
              <TableCell align="right" sx={head}>{t('reports.closing', 'Ultimo')}</TableCell>
              <TableCell align="right" sx={head}>{t('reports.compareColumn', 'Sammenligning')}</TableCell>
              <TableCell align="right" sx={head}>{t('reports.difference', 'Afvigelse')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {trialBalance.rows.map((row: any) => (
              <TableRow key={row.account_id} hover>
                <TableCell>
                  <Link component="button" variant="body2" onClick={() => openCard(row.account_id)} sx={{ fontFamily: 'monospace' }}>
                    {row.account_code}
                  </Link>
                </TableCell>
                <TableCell>{row.account_name}</TableCell>
                <TableCell><Typography variant="caption">{row.arl_line_name}</Typography></TableCell>
                <TableCell align="right">{num(row.opening)}</TableCell>
                <TableCell align="right">{num(row.debit)}</TableCell>
                <TableCell align="right">{num(row.credit)}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>{num(row.closing)}</TableCell>
                <TableCell align="right" sx={{ color: 'text.secondary' }}>{num(row.compare)}</TableCell>
                <TableCell align="right" sx={{ color: 'text.secondary' }}>{num(row.difference)}</TableCell>
              </TableRow>
            ))}
            <TableRow sx={{ bgcolor: '#e8f5e9' }}>
              <TableCell colSpan={3} sx={{ fontWeight: 700 }}>{t('common.totals')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700 }}>{num(tot.opening)}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700 }}>{num(tot.debit)}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700 }}>{num(tot.credit)}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700 }}>{num(tot.closing)}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700 }}>{num(tot.compare)}</TableCell>
              <TableCell align="right">
                <Chip label={trialBalance.is_balanced ? t('reports.balanced') : t('reports.unbalanced')} size="small"
                  color={trialBalance.is_balanced ? 'success' : 'error'} sx={{ height: 20, fontSize: '11px' }} />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  // ─── Linjer med konti (resultat og balance) ───
  const renderLine = (key: string, name: string, amount: string, prev: string, accs: any[], bold = false) => (
    <React.Fragment key={key}>
      <TableRow hover sx={{ cursor: accs.length ? 'pointer' : 'default' }} onClick={() => accs.length && toggle(key)}>
        <TableCell sx={{ width: 32, p: 0.5 }}>
          {accs.length > 0 && <IconButton size="small">{expanded[key] ? <ExpandMore fontSize="small" /> : <ChevronRight fontSize="small" />}</IconButton>}
        </TableCell>
        <TableCell sx={{ fontWeight: bold ? 700 : 500 }}>{name}</TableCell>
        <TableCell align="right" sx={{ fontWeight: bold ? 700 : 500 }}>{num(amount)}</TableCell>
        <TableCell align="right" sx={{ color: 'text.secondary', fontWeight: bold ? 700 : 400 }}>{num(prev)}</TableCell>
      </TableRow>
      {accs.length > 0 && (
        <TableRow>
          <TableCell colSpan={4} sx={{ p: 0, border: 0 }}>
            <Collapse in={!!expanded[key]} unmountOnExit>
              <Table size="small">
                <TableBody>
                  {accs.map((a: any) => (
                    <TableRow key={a.account_id}>
                      <TableCell sx={{ width: 32 }} />
                      <TableCell sx={{ pl: 4 }}>
                        <Link component="button" variant="body2" onClick={() => openCard(a.account_id)} sx={{ fontFamily: 'monospace', mr: 1 }}>
                          {a.account_code}
                        </Link>
                        {a.account_name}
                      </TableCell>
                      <TableCell align="right">{num(a.amount)}</TableCell>
                      <TableCell align="right" sx={{ color: 'text.secondary' }}>{num(a.amount_prev)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Collapse>
          </TableCell>
        </TableRow>
      )}
    </React.Fragment>
  );

  const periodHead = (cur: string, prev: string) => (
    <TableHead>
      <TableRow sx={{ bgcolor: '#f5f5f5' }}>
        <TableCell sx={{ width: 32 }} />
        <TableCell sx={head}>{t('reports.item', 'Regnskabspost')}</TableCell>
        <TableCell align="right" sx={head}>{cur}</TableCell>
        <TableCell align="right" sx={head}>{prev}</TableCell>
      </TableRow>
    </TableHead>
  );

  // ─── Resultatopgørelse ───
  const renderPnL = () => {
    if (!pnl) return null;
    return (
      <Card>
        <CardContent>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            {t('reports.pnlTitle', 'Resultatopgørelse (årsregnskabsloven, artsopdelt)')}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {t('reports.pnlHint', 'Indtægter er positive, omkostninger negative. Klik på en linje for at se kontiene.')}
          </Typography>
          <Table size="small" sx={{ mt: 1 }}>
            {periodHead(`${formatDate(pnl.date_from)} – ${formatDate(pnl.date_to)}`,
              `${formatDate(pnl.compare_from)} – ${formatDate(pnl.compare_to)}`)}
            <TableBody>
              {pnl.sections.map((s: any) => s.type === 'subtotal'
                ? (
                  <TableRow key={s.key} sx={{ bgcolor: s.key === 'aarets_resultat' ? '#e8f5e9' : '#fafafa' }}>
                    <TableCell />
                    <TableCell sx={{ fontWeight: 700 }}>{s.name}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>{num(s.amount)}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700, color: 'text.secondary' }}>{num(s.amount_prev)}</TableCell>
                  </TableRow>
                )
                : (s.accounts.length || parseFloat(s.amount) || parseFloat(s.amount_prev))
                  ? renderLine(`pnl-${s.key}`, s.name, s.amount, s.amount_prev, s.accounts)
                  : null)}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    );
  };

  // ─── Balance ───
  const renderBalanceSheet = () => {
    if (!balanceSheet) return null;
    const bs = balanceSheet;
    const side = (title: string, lines: any[], total: string, totalPrev: string, prefix: string) => (
      <Card sx={{ flex: 1, minWidth: 320 }}>
        <CardContent>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>{title}</Typography>
          <Table size="small">
            {periodHead(formatDate(bs.date), formatDate(bs.compare_date))}
            <TableBody>
              {lines.filter((l: any) => l.accounts.length || parseFloat(l.amount) || parseFloat(l.amount_prev))
                .map((l: any) => renderLine(`${prefix}-${l.key}`, l.name, l.amount, l.amount_prev, l.accounts))}
              <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                <TableCell />
                <TableCell sx={{ fontWeight: 700 }}>{t('reports.totalLabel', { title })}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>{num(total)}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700, color: 'text.secondary' }}>{num(totalPrev)}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    );
    return (
      <Box>
        {parseFloat(bs.unallocated_result) !== 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            {t('reports.unallocatedResult', 'Overført resultat indeholder årets resultat, som endnu ikke er overført ved årsafslutning: {{amount}}.', {
              amount: formatMoney(bs.unallocated_result),
            })}
          </Alert>
        )}
        <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
          {side(t('reports.assets'), bs.assets, bs.total_assets, bs.total_assets_prev, 'a')}
          {side(t('reports.liabilitiesAndEquity', 'Passiver'), bs.liabilities, bs.total_liabilities, bs.total_liabilities_prev, 'p')}
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
          <Chip label={t('reports.equityTotal', 'Egenkapital i alt: {{amount}}', { amount: formatMoney(bs.total_equity) })} variant="outlined" />
          <Chip label={bs.is_balanced ? t('reports.balanceSheetBalanced') : t('reports.balanceSheetNotBalanced')}
            color={bs.is_balanced ? 'success' : 'error'} />
        </Box>
      </Box>
    );
  };

  // ─── Kontokort ───
  const renderAccountCard = () => (
    <Box>
      <Autocomplete
        options={accounts}
        value={cardAccount}
        onChange={(_, v) => setCardAccount(v)}
        getOptionLabel={o => `${o.code} ${o.name}`}
        isOptionEqualToValue={(a, b) => a.id === b.id}
        renderInput={params => <TextField {...params} size="small" label={t('reports.chooseAccount', 'Vælg konto')} />}
        sx={{ maxWidth: 480, mb: 2 }}
      />
      {accountCard && (
        <TableContainer component={Paper}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, px: 2, pt: 1 }}>
            {accountCard.account.code} {accountCard.account.name}
            <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
              {t('reports.cardPeriod', '{{from}} – {{to}}', { from: formatDate(accountCard.date_from), to: formatDate(accountCard.date_to) })}
            </Typography>
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                <TableCell sx={head}>{t('reports.date')}</TableCell>
                <TableCell sx={head}>{t('reports.entry')}</TableCell>
                <TableCell sx={head}>{t('reports.journal', 'Journal')}</TableCell>
                <TableCell sx={head}>{t('reports.voucher', 'Bilag')}</TableCell>
                <TableCell sx={head}>{t('reports.description')}</TableCell>
                <TableCell sx={head}>{t('reports.vatCode', 'Momskode')}</TableCell>
                <TableCell align="right" sx={head}>{t('common.debit')}</TableCell>
                <TableCell align="right" sx={head}>{t('common.credit')}</TableCell>
                <TableCell align="right" sx={head}>{t('common.balance')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow sx={{ bgcolor: '#fafafa' }}>
                <TableCell colSpan={8} sx={{ fontWeight: 600 }}>{t('reports.opening', 'Primo')}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>{num(accountCard.opening)}</TableCell>
              </TableRow>
              {accountCard.lines.map((l: any) => (
                <TableRow key={l.id} hover>
                  <TableCell>{formatDate(l.date)}</TableCell>
                  <TableCell sx={{ fontFamily: 'monospace', fontSize: 12 }}>{l.entry_number}</TableCell>
                  <TableCell>{l.journal}</TableCell>
                  <TableCell>{l.piece_number}</TableCell>
                  <TableCell>
                    {l.description}{l.partner_name ? ` · ${l.partner_name}` : ''}
                    {l.amount_currency && (
                      <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                        ({formatMoney(l.amount_currency, l.currency)})
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>{l.vat_code}</TableCell>
                  <TableCell align="right">{parseFloat(l.debit) ? num(l.debit) : ''}</TableCell>
                  <TableCell align="right">{parseFloat(l.credit) ? num(l.credit) : ''}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>{num(l.balance)}</TableCell>
                </TableRow>
              ))}
              <TableRow sx={{ bgcolor: '#e8f5e9' }}>
                <TableCell colSpan={6} sx={{ fontWeight: 700 }}>{t('reports.closing', 'Ultimo')}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>{num(accountCard.total_debit)}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>{num(accountCard.total_credit)}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>{num(accountCard.closing)}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      )}
      {!cardAccount && (
        <Typography color="text.secondary">{t('reports.chooseAccountHint', 'Vælg en konto for at se kontokortet.')}</Typography>
      )}
    </Box>
  );

  // ─── Pengestrøm ───
  const renderCashFlow = () => {
    if (!cashFlow) return null;
    const sections = cashFlow.sections || [];
    return (
      <Box>
        {sections.map((section: any, idx: number) => (
          <Card key={idx} sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>{section.name}</Typography>
              <Table size="small">
                <TableBody>
                  {(section.rows || []).map((row: any, i: number) => (
                    <TableRow key={i}>
                      <TableCell sx={{ fontFamily: 'monospace', fontSize: '12px' }}>{row.account_code}</TableCell>
                      <TableCell>{row.description || row.account_name}</TableCell>
                      <TableCell align="right">{num(row.amount)}</TableCell>
                    </TableRow>
                  ))}
                  <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                    <TableCell colSpan={2} sx={{ fontWeight: 700 }}>{t('reports.totalLabel', { title: section.name })}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>{num(section.total)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        ))}
        <Card sx={{ bgcolor: '#e8f5e9' }}>
          <CardContent sx={{ textAlign: 'center', py: 2, '&:last-child': { pb: 2 } }}>
            <Typography variant="caption" color="text.secondary">{t('reports.netCashFlow')}</Typography>
            <Typography variant="h5" sx={{ fontWeight: 700, color: parseFloat(cashFlow.net_cash_flow || '0') >= 0 ? '#2e7d32' : '#d32f2f' }}>
              {formatMoney(cashFlow.net_cash_flow || 0)}
            </Typography>
          </CardContent>
        </Card>
      </Box>
    );
  };

  // ─── Hovedbog ───
  const renderGeneralLedger = () => {
    if (!generalLedger) return null;
    const accs = generalLedger.accounts || [];
    return (
      <Box>
        {accs.map((acct: any, idx: number) => (
          <Card key={idx} sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                <Link component="button" onClick={() => openCard(acct.account_id)} sx={{ fontWeight: 600 }}>
                  {acct.account_code}
                </Link>
                {' '}{acct.account_name}
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                      <TableCell sx={head}>{t('reports.date')}</TableCell>
                      <TableCell sx={head}>{t('reports.entry')}</TableCell>
                      <TableCell sx={head}>{t('reports.description')}</TableCell>
                      <TableCell align="right" sx={head}>{t('common.debit')}</TableCell>
                      <TableCell align="right" sx={head}>{t('common.credit')}</TableCell>
                      <TableCell align="right" sx={head}>{t('common.balance')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(acct.lines || []).map((e: any, i: number) => (
                      <TableRow key={i} hover>
                        <TableCell>{formatDate(e.date)}</TableCell>
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '12px' }}>{e.entry_number}</TableCell>
                        <TableCell>{e.description}</TableCell>
                        <TableCell align="right">{parseFloat(e.debit || '0') > 0 ? num(e.debit) : ''}</TableCell>
                        <TableCell align="right">{parseFloat(e.credit || '0') > 0 ? num(e.credit) : ''}</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 600 }}>{num(e.running_balance)}</TableCell>
                      </TableRow>
                    ))}
                    <TableRow sx={{ bgcolor: '#e8f5e9' }}>
                      <TableCell colSpan={3} sx={{ fontWeight: 700 }}>{t('common.total')}</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>{num(acct.total_debit)}</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>{num(acct.total_credit)}</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700 }}>{num(acct.closing_balance)}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        ))}
        {accs.length === 0 && (
          <Typography color="text.secondary" sx={{ textAlign: 'center', mt: 4 }}>{t('reports.noEntriesForPeriod')}</Typography>
        )}
      </Box>
    );
  };

  // ─── Aldersfordeling ───
  const renderAgingTable = (title: string, data: any, nameField: string, color: string) => {
    if (!data) return null;
    const rows = data.rows || [];
    const totals = data.totals || {};
    const cols = ['current', 'days_1_30', 'days_31_60', 'days_61_90', 'days_over_90', 'total'];
    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, color, mb: 1 }}>{title}</Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell sx={head}>{nameField === 'customer_name' ? t('reports.customer') : t('reports.supplier')}</TableCell>
                  <TableCell align="right" sx={head}>{t('reports.current')}</TableCell>
                  <TableCell align="right" sx={head}>{t('reports.days1to30')}</TableCell>
                  <TableCell align="right" sx={head}>{t('reports.days31to60')}</TableCell>
                  <TableCell align="right" sx={head}>{t('reports.days61to90')}</TableCell>
                  <TableCell align="right" sx={head}>{t('reports.daysOver90')}</TableCell>
                  <TableCell align="right" sx={head}>{t('common.total')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((row: any, i: number) => (
                  <TableRow key={i} hover>
                    <TableCell>{row[nameField]}</TableCell>
                    {cols.map(c => (
                      <TableCell key={c} align="right" sx={{
                        fontWeight: c === 'total' ? 600 : 400,
                        color: c === 'days_over_90' && parseFloat(row[c] || '0') > 0 ? '#d32f2f' : 'inherit',
                      }}>{num(row[c])}</TableCell>
                    ))}
                  </TableRow>
                ))}
                {rows.length > 0 && (
                  <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                    <TableCell sx={{ fontWeight: 700 }}>{t('common.total')}</TableCell>
                    {cols.map(c => <TableCell key={c} align="right" sx={{ fontWeight: 700 }}>{num(totals[c])}</TableCell>)}
                  </TableRow>
                )}
                {rows.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} sx={{ textAlign: 'center', color: 'text.secondary' }}>{t('reports.noOutstanding')}</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>{t('reports.title')}</Typography>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" scrollButtons="auto">
          <Tab label={t('reports.trialBalance')} />
          <Tab label={t('reports.profitLoss')} />
          <Tab label={t('reports.balanceSheet')} />
          <Tab label={t('reports.accountCard', 'Kontokort')} />
          <Tab label={t('reports.cashFlow')} />
          <Tab label={t('reports.generalLedger')} />
          <Tab label={t('reports.agingAnalysis')} />
        </Tabs>
        <Box sx={{ ml: 'auto', display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
          {tab === 0 && (
            <TextField select size="small" label={t('reports.compareWith', 'Sammenlign med')} value={compare}
              onChange={e => setCompare(e.target.value)} sx={{ width: 220 }}>
              {['period', 'year', 'last_year'].map(c => <MenuItem key={c} value={c}>{compareLabel(c)}</MenuItem>)}
            </TextField>
          )}
          {tab !== 2 && tab !== 6 && (
            <TextField label={t('common.from')} type="date" value={dateFrom} size="small"
              onChange={e => setDateFrom(e.target.value)} InputLabelProps={{ shrink: true }} sx={{ width: 150 }} />
          )}
          <TextField label={tab === 2 || tab === 6 ? t('reports.asOf', 'Pr. dato') : t('common.to')} type="date" value={dateTo}
            size="small" onChange={e => setDateTo(e.target.value)} InputLabelProps={{ shrink: true }} sx={{ width: 150 }} />
          <Button variant="outlined" onClick={fetchReport} size="small">{t('common.apply')}</Button>
          <Button variant="outlined" onClick={handleExportCSV} size="small" startIcon={<DownloadIcon />} color="secondary">
            {t('common.exportCsv')}
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {tab === 0 && renderTrialBalance()}
      {tab === 1 && renderPnL()}
      {tab === 2 && renderBalanceSheet()}
      {tab === 3 && renderAccountCard()}
      {tab === 4 && renderCashFlow()}
      {tab === 5 && renderGeneralLedger()}
      {tab === 6 && (
        <Box>
          {renderAgingTable(t('reports.receivableAging'), agingReceivable, 'customer_name', '#1976d2')}
          {renderAgingTable(t('reports.payableAging'), agingPayable, 'supplier_name', '#e65100')}
        </Box>
      )}
    </Box>
  );
};

export default Reports;
