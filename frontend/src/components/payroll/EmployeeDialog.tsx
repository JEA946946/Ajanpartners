import React, { useEffect, useState } from 'react';
import {
  Alert, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Grid,
  MenuItem, TextField, Typography,
} from '@mui/material';
import api from '../../services/api';
import {
  ALLOWANCE_MODES, ATP_CLASSES, Employee, HOLIDAY_SCHEMES, HOLIDAY_TYPES, PAY_FORMS, TAX_CARDS, apiError,
} from './format';

type Form = Record<string, any>;

const EMPTY: Form = {
  employee_number: '', first_name: '', last_name: '', cpr: '', address: '', email: '', bank_reg: '',
  bank_account: '', start_date: '', end_date: '', pay_form: 'month', monthly_salary: '0', hourly_rate: '0',
  hours_per_week: '37', tax_card: 'main', tax_rate: '0', deduction_month: '0', deduction_fortnight: '',
  free_card_amount: '0', holiday_scheme: 'own', holiday_type: 'with_pay', holiday_allowance_pct: '1',
  holiday_allowance_mode: 'monthly', pension_employee_pct: '0', pension_employer_pct: '0',
  pension_company: '', atp_class: 'A', car_benefit_month: '0', free_phone: false, is_active: true, notes: '',
};

interface Props {
  open: boolean;
  employee: Employee | null;
  onClose: () => void;
  onSaved: () => void;
}

const Section: React.FC<{ title: string }> = ({ title }) => (
  <Grid item xs={12}><Typography variant="subtitle2" sx={{ mt: 1 }}>{title}</Typography></Grid>
);

const EmployeeDialog: React.FC<Props> = ({ open, employee, onClose, onSaved }) => {
  const [form, setForm] = useState<Form>(EMPTY);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setError('');
    if (employee) {
      const f: Form = { ...EMPTY };
      Object.keys(EMPTY).forEach((k) => {
        const v = (employee as any)[k];
        if (v !== undefined && v !== null) f[k] = v;
      });
      f.cpr = '';
      setForm(f);
    } else {
      setForm(EMPTY);
    }
  }, [open, employee]);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));

  const field = (k: string, label: string, props: Record<string, any> = {}) => (
    <TextField fullWidth size="small" label={label} value={form[k] ?? ''} onChange={set(k)} {...props} />
  );
  const select = (k: string, label: string, options: Record<string, string>, props: Record<string, any> = {}) => (
    <TextField select fullWidth size="small" label={label} value={form[k]} onChange={set(k)} {...props}>
      {Object.entries(options).map(([v, l]) => <MenuItem key={v} value={v}>{l}</MenuItem>)}
    </TextField>
  );

  const save = async () => {
    setSaving(true);
    setError('');
    const payload: Form = { ...form };
    if (!payload.cpr) delete payload.cpr;
    try {
      if (employee) await api.put(`/payroll/employees/${employee.id}`, payload);
      else await api.post('/payroll/employees', payload);
      onSaved();
    } catch (e: any) {
      setError(apiError(e, 'Medarbejderen kunne ikke gemmes.'));
    } finally {
      setSaving(false);
    }
  };

  const feriekonto = form.holiday_scheme === 'feriekonto';

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{employee ? `Ret ${employee.name}` : 'Ny medarbejder'}</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Grid container spacing={2} sx={{ mt: 0 }}>
          <Section title="Stamdata" />
          <Grid item xs={12} sm={2}>{field('employee_number', 'Nr.', { placeholder: 'auto' })}</Grid>
          <Grid item xs={12} sm={5}>{field('first_name', 'Fornavn', { required: true })}</Grid>
          <Grid item xs={12} sm={5}>{field('last_name', 'Efternavn', { required: true })}</Grid>
          <Grid item xs={12} sm={4}>
            {field('cpr', 'CPR-nummer', {
              placeholder: employee?.has_cpr ? employee.cpr_masked : 'DDMMÅÅ-XXXX',
              helperText: employee?.has_cpr ? 'Gemt krypteret. Udfyld kun for at ændre.' : 'Gemmes krypteret',
            })}
          </Grid>
          <Grid item xs={12} sm={8}>{field('email', 'E-mail')}</Grid>
          <Grid item xs={12}>{field('address', 'Adresse', { multiline: true, minRows: 2 })}</Grid>
          <Grid item xs={6} sm={3}>{field('bank_reg', 'Reg.nr.')}</Grid>
          <Grid item xs={6} sm={3}>{field('bank_account', 'Kontonr.')}</Grid>
          <Grid item xs={6} sm={3}>{field('start_date', 'Startdato', { type: 'date', InputLabelProps: { shrink: true } })}</Grid>
          <Grid item xs={6} sm={3}>{field('end_date', 'Fratrædelsesdato', { type: 'date', InputLabelProps: { shrink: true } })}</Grid>

          <Section title="Løn" />
          <Grid item xs={12} sm={3}>{select('pay_form', 'Lønform', PAY_FORMS)}</Grid>
          <Grid item xs={12} sm={3}>{field('monthly_salary', form.pay_form === 'fortnight' ? 'Fast løn pr. 14 dage' : 'Månedsløn', { type: 'number' })}</Grid>
          <Grid item xs={12} sm={3}>{field('hourly_rate', 'Timeløn', { type: 'number' })}</Grid>
          <Grid item xs={12} sm={3}>{field('hours_per_week', 'Timer pr. uge', { type: 'number' })}</Grid>

          <Section title="Skattekort" />
          <Grid item xs={12} sm={3}>{select('tax_card', 'Skattekort', TAX_CARDS)}</Grid>
          <Grid item xs={6} sm={2}>{field('tax_rate', 'Trækprocent', { type: 'number', disabled: form.tax_card === 'none' || form.tax_card === 'free' })}</Grid>
          <Grid item xs={6} sm={2}>{field('deduction_month', 'Månedsfradrag', { type: 'number', disabled: form.tax_card !== 'main' })}</Grid>
          <Grid item xs={6} sm={2}>{field('deduction_fortnight', '14-dagesfradrag', { type: 'number', disabled: form.tax_card !== 'main', helperText: 'Tom: × 12/26' })}</Grid>
          <Grid item xs={6} sm={3}>{field('free_card_amount', 'Frikortbeløb (år)', { type: 'number', disabled: form.tax_card !== 'free' })}</Grid>

          <Section title="Ferie" />
          <Grid item xs={12} sm={3}>{select('holiday_scheme', 'Ferieordning', HOLIDAY_SCHEMES)}</Grid>
          <Grid item xs={12} sm={4}>{select('holiday_type', 'Ferietype', HOLIDAY_TYPES, { disabled: feriekonto, value: feriekonto ? 'without_pay' : form.holiday_type })}</Grid>
          <Grid item xs={6} sm={2}>{field('holiday_allowance_pct', 'Ferietillæg %', { type: 'number', disabled: feriekonto || form.holiday_type !== 'with_pay' })}</Grid>
          <Grid item xs={6} sm={3}>{select('holiday_allowance_mode', 'Ferietillæg', ALLOWANCE_MODES, { disabled: feriekonto || form.holiday_type !== 'with_pay' })}</Grid>

          <Section title="Pension, ATP og personalegoder" />
          <Grid item xs={6} sm={2}>{field('pension_employee_pct', 'Eget bidrag %', { type: 'number' })}</Grid>
          <Grid item xs={6} sm={2}>{field('pension_employer_pct', 'Arbejdsgiver %', { type: 'number' })}</Grid>
          <Grid item xs={12} sm={4}>{field('pension_company', 'Pensionsselskab')}</Grid>
          <Grid item xs={12} sm={4}>{select('atp_class', 'ATP-sats', ATP_CLASSES)}</Grid>
          <Grid item xs={12} sm={4}>{field('car_benefit_month', 'Fri bil, værdi pr. måned', { type: 'number' })}</Grid>
          <Grid item xs={12} sm={4}>
            <FormControlLabel control={<Checkbox checked={!!form.free_phone} onChange={set('free_phone')} />} label="Fri telefon/multimedier" />
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControlLabel control={<Checkbox checked={!!form.is_active} onChange={set('is_active')} />} label="Aktiv" />
          </Grid>
          <Grid item xs={12}>{field('notes', 'Noter', { multiline: true, minRows: 2 })}</Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Annullér</Button>
        <Button variant="contained" onClick={save} disabled={saving || !form.first_name || !form.last_name}>Gem</Button>
      </DialogActions>
    </Dialog>
  );
};

export default EmployeeDialog;
