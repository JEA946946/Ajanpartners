import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, MenuItem, Chip, Checkbox, FormControlLabel,
  Autocomplete, Alert,
} from '@mui/material';
import {
  Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { formatNumber } from '../utils/format';

type TaxType = 'sales' | 'purchase' | 'both';

interface TaxCode {
  id: string;
  code: string;
  name: string;
  rate: string;
  type: TaxType;
  account_id: string | null;
  account_code?: string;
  account_name?: string;
  input_account_id: string | null;
  input_account_code?: string | null;
  deduction_rate: string;
  reverse_charge: string;
  rubrik: string;
  energy_tax: boolean;
  invoice_text: string;
  standard_code: string;
  is_active: boolean;
}

interface AccountOption { id: string; code: string; name: string }

const TYPE_COLORS: Record<string, 'success' | 'primary' | 'secondary'> = {
  sales: 'success', purchase: 'primary', both: 'secondary',
};

const EMPTY_FORM = {
  code: '', name: '', rate: '', type: 'sales' as TaxType, is_active: true,
  deduction_rate: '100', reverse_charge: '', rubrik: '', energy_tax: false, invoice_text: '', standard_code: '',
};

const TaxCodes: React.FC = () => {
  const { t } = useTranslation();

  const TYPE_LABELS: Record<string, string> = {
    sales: t('taxCodes.sales'), purchase: t('taxCodes.purchase'), both: t('taxCodes.both'),
  };
  const REVERSE_LABELS: Record<string, string> = {
    '': t('taxCodes.reverseNone', 'Nej'),
    eu_goods: t('taxCodes.reverseEuGoods', 'Varekøb fra udlandet (erhvervelses-/importmoms)'),
    eu_services: t('taxCodes.reverseEuServices', 'Ydelseskøb fra udlandet'),
    domestic: t('taxCodes.reverseDomestic', 'Indenlandsk omvendt betalingspligt (fx byggeydelser)'),
  };
  const RUBRIK_LABELS: Record<string, string> = {
    '': t('taxCodes.rubrikNone', 'Ingen'),
    A_goods: t('taxCodes.rubrikAGoods', 'Rubrik A – varer (køb i EU)'),
    A_services: t('taxCodes.rubrikAServices', 'Rubrik A – ydelser (køb i EU)'),
    B_goods: t('taxCodes.rubrikBGoods', 'Rubrik B – varer (EU-salg, indberettes)'),
    B_goods_other: t('taxCodes.rubrikBGoodsOther', 'Rubrik B – varer (indberettes ikke til EU-salg uden moms)'),
    B_services: t('taxCodes.rubrikBServices', 'Rubrik B – ydelser (EU-salg)'),
    C: t('taxCodes.rubrikC', 'Rubrik C – andre leverancer uden moms'),
  };

  const [taxCodes, setTaxCodes] = useState<TaxCode[]>([]);
  const [accounts, setAccounts] = useState<AccountOption[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<TaxCode | null>(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [account, setAccount] = useState<AccountOption | null>(null);
  const [inputAccount, setInputAccount] = useState<AccountOption | null>(null);
  const [error, setError] = useState('');

  const fetchTaxCodes = () => {
    api.get('/tax-codes').then(res => {
      if (res.data.success) setTaxCodes(res.data.data?.tax_codes || []);
    });
  };

  useEffect(() => {
    fetchTaxCodes();
    api.get('/accounts').then(res => {
      if (res.data.success) {
        setAccounts((res.data.data?.accounts || []).filter((a: any) => !a.is_header)
          .map((a: any) => ({ id: a.id, code: a.code, name: a.name })));
      }
    });
  }, []);

  const handleOpen = (tc?: TaxCode) => {
    setError('');
    if (tc) {
      setEditing(tc);
      setForm({
        code: tc.code, name: tc.name, rate: tc.rate, type: tc.type, is_active: tc.is_active,
        deduction_rate: tc.deduction_rate, reverse_charge: tc.reverse_charge, rubrik: tc.rubrik,
        energy_tax: tc.energy_tax, invoice_text: tc.invoice_text, standard_code: tc.standard_code,
      });
      setAccount(accounts.find(a => a.id === tc.account_id) || null);
      setInputAccount(accounts.find(a => a.id === tc.input_account_id) || null);
    } else {
      setEditing(null);
      setForm({ ...EMPTY_FORM });
      setAccount(null);
      setInputAccount(null);
    }
    setDialogOpen(true);
  };

  const handleSave = async () => {
    const payload = {
      ...form,
      rate: parseFloat(form.rate) || 0,
      deduction_rate: parseFloat(form.deduction_rate) || 0,
      account_id: account?.id || null,
      input_account_id: inputAccount?.id || null,
    };
    try {
      if (editing) await api.put(`/tax-codes/${editing.id}`, payload);
      else await api.post('/tax-codes', payload);
      setDialogOpen(false);
      fetchTaxCodes();
    } catch (err: any) {
      setError(err.response?.data?.message || t('taxCodes.errorSave'));
    }
  };

  const handleDelete = async (tc: TaxCode) => {
    if (!confirm(t('taxCodes.deleteConfirm', { code: tc.code, name: tc.name }))) return;
    try {
      await api.delete(`/tax-codes/${tc.id}`);
      fetchTaxCodes();
    } catch (err: any) {
      alert(err.response?.data?.message || t('taxCodes.errorDelete'));
    }
  };

  const accountPicker = (label: string, value: AccountOption | null, onChange: (v: AccountOption | null) => void) => (
    <Autocomplete
      options={accounts} value={value} onChange={(_, v) => onChange(v)}
      getOptionLabel={o => `${o.code} — ${o.name}`} isOptionEqualToValue={(o, v) => o.id === v.id}
      renderInput={params => <TextField {...params} label={label} size="small" />} size="small"
    />
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>{t('taxCodes.title')}</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpen()} sx={{ bgcolor: '#2e7d32' }}>
          {t('taxCodes.addTaxCode')}
        </Button>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('taxCodes.intro', 'Momskoderne følger Erhvervsstyrelsens momskodeliste (S01, K010 …), som også bruges i SAF-T-eksporten. Koden bestemmer, hvordan en linje bogføres: momskonto, fradragsprocent (fx 25 % for restaurant og repræsentation), omvendt betalingspligt og rubrik på momsangivelsen. E-koderne er energiafgifter, der godtgøres.')}
      </Typography>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.code')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.name')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('taxCodes.rate')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('taxCodes.deduction', 'Fradrag')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.type')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.account')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('taxCodes.special', 'Særligt')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.active')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {taxCodes.map(tc => (
              <TableRow key={tc.id} hover sx={{ opacity: tc.is_active ? 1 : 0.5 }}>
                <TableCell><Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 500 }}>{tc.code}</Typography></TableCell>
                <TableCell>{tc.name}</TableCell>
                <TableCell>{formatNumber(tc.rate)} %</TableCell>
                <TableCell>{tc.type === 'sales' ? '—' : `${formatNumber(tc.deduction_rate)} %`}</TableCell>
                <TableCell>
                  <Chip label={TYPE_LABELS[tc.type] || tc.type} size="small" color={TYPE_COLORS[tc.type] || 'default'}
                    sx={{ height: 20, fontSize: '11px' }} />
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {tc.account_code}{tc.input_account_code ? ` / ${tc.input_account_code}` : ''}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {tc.reverse_charge && <Chip size="small" label={t('taxCodes.reverseShort', 'Omvendt betalingspligt')} sx={{ height: 20, fontSize: '11px' }} />}
                    {tc.rubrik && <Chip size="small" variant="outlined" label={RUBRIK_LABELS[tc.rubrik]?.split(' (')[0] || tc.rubrik} sx={{ height: 20, fontSize: '11px' }} />}
                    {tc.energy_tax && <Chip size="small" color="warning" label={t('taxCodes.energyShort', 'Energiafgift')} sx={{ height: 20, fontSize: '11px' }} />}
                  </Box>
                </TableCell>
                <TableCell>{tc.is_active ? t('common.yes') : t('common.no')}</TableCell>
                <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                  <IconButton size="small" onClick={() => handleOpen(tc)} title={t('common.edit')}><EditIcon sx={{ fontSize: 16 }} /></IconButton>
                  <IconButton size="small" onClick={() => handleDelete(tc)} color="error" title={t('common.delete')}><DeleteIcon sx={{ fontSize: 16 }} /></IconButton>
                </TableCell>
              </TableRow>
            ))}
            {taxCodes.length === 0 && (
              <TableRow>
                <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                  <Typography variant="body2" color="text.secondary">{t('taxCodes.noTaxCodes')}</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editing ? t('taxCodes.editTaxCode') : t('taxCodes.addTaxCode')}</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 1 }}>{error}</Alert>}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField label={t('common.code')} value={form.code} size="small" sx={{ width: 140 }}
                onChange={e => setForm({ ...form, code: e.target.value })} />
              <TextField label={t('common.name')} value={form.name} size="small" fullWidth
                onChange={e => setForm({ ...form, name: e.target.value })} />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField label={`${t('taxCodes.rate')} (%)`} value={form.rate} size="small" type="number" sx={{ width: 140 }}
                onChange={e => setForm({ ...form, rate: e.target.value })} inputProps={{ min: 0, step: '0.01' }} />
              <TextField label={t('taxCodes.deductionRate', 'Fradrag (%)')} value={form.deduction_rate} size="small" type="number"
                sx={{ width: 140 }} onChange={e => setForm({ ...form, deduction_rate: e.target.value })}
                inputProps={{ min: 0, max: 100, step: '0.01' }}
                helperText={t('taxCodes.deductionHint', '100 = fuldt fradrag')} />
              <TextField label={t('common.type')} value={form.type} size="small" select fullWidth
                onChange={e => setForm({ ...form, type: e.target.value as TaxType })}>
                <MenuItem value="sales">{t('taxCodes.sales')}</MenuItem>
                <MenuItem value="purchase">{t('taxCodes.purchase')}</MenuItem>
                <MenuItem value="both">{t('taxCodes.both')}</MenuItem>
              </TextField>
            </Box>
            {accountPicker(t('taxCodes.vatAccount', 'Momskonto (salgsmoms, købsmoms eller moms af køb i udlandet)'), account, setAccount)}
            <TextField label={t('taxCodes.reverseCharge', 'Omvendt betalingspligt')} value={form.reverse_charge} size="small" select
              onChange={e => setForm({ ...form, reverse_charge: e.target.value })}>
              {Object.entries(REVERSE_LABELS).map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
            </TextField>
            {form.reverse_charge &&
              accountPicker(t('taxCodes.inputAccount', 'Fradragskonto (købsmoms)'), inputAccount, setInputAccount)}
            <TextField label={t('taxCodes.rubrik', 'Rubrik på momsangivelsen')} value={form.rubrik} size="small" select
              onChange={e => setForm({ ...form, rubrik: e.target.value })}>
              {Object.entries(RUBRIK_LABELS).map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
            </TextField>
            <TextField label={t('taxCodes.invoiceText', 'Tekst på fakturaen')} value={form.invoice_text} size="small"
              onChange={e => setForm({ ...form, invoice_text: e.target.value })}
              helperText={t('taxCodes.invoiceTextHint', 'Fx "Omvendt betalingspligt" eller henvisning til momslovens fritagelse')} />
            <TextField label={t('taxCodes.standardCode', 'Standardmomskode (SAF-T)')} value={form.standard_code} size="small"
              onChange={e => setForm({ ...form, standard_code: e.target.value })} />
            <Box sx={{ display: 'flex', gap: 2 }}>
              <FormControlLabel label={t('taxCodes.energyTax', 'Energiafgift (hele beløbet bogføres på afgiftskontoen)')}
                control={<Checkbox size="small" checked={form.energy_tax} onChange={e => setForm({ ...form, energy_tax: e.target.checked })} />} />
              <FormControlLabel label={t('common.active')}
                control={<Checkbox size="small" checked={form.is_active} onChange={e => setForm({ ...form, is_active: e.target.checked })} />} />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleSave} sx={{ bgcolor: '#2e7d32' }}>
            {editing ? t('common.update') : t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TaxCodes;
