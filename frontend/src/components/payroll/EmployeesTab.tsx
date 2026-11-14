import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, Chip, IconButton, Paper, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Tooltip, Typography,
} from '@mui/material';
import { Add as AddIcon, CloudDownload as FetchIcon, Delete as DeleteIcon, Edit as EditIcon } from '@mui/icons-material';
import api from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import EmployeeDialog from './EmployeeDialog';
import { Employee, PAY_FORMS, TAX_CARDS, apiError, kr } from './format';

const EmployeesTab: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [editing, setEditing] = useState<Employee | null>(null);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  const load = useCallback(async () => {
    try {
      const res = await api.get('/payroll/employees');
      setEmployees(res.data.results);
    } catch (e: any) {
      setError(apiError(e, 'Medarbejderne kunne ikke hentes.'));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const remove = async (emp: Employee) => {
    if (!window.confirm(`Slet ${emp.name}?`)) return;
    try {
      await api.delete(`/payroll/employees/${emp.id}`);
      load();
    } catch (e: any) {
      setError(apiError(e));
    }
  };

  const fetchCard = async (emp: Employee) => {
    setError('');
    setInfo('');
    try {
      await api.post(`/payroll/employees/${emp.id}/fetch-tax-card`, {});
      setInfo(`eSkattekort hentet for ${emp.name} (testdata, indtil adgangen hos Skattestyrelsen er på plads).`);
      load();
    } catch (e: any) {
      setError(apiError(e, 'eSkattekortet kunne ikke hentes.'));
    }
  };

  const salary = (e: Employee) =>
    e.pay_form === 'hourly' || (e.pay_form === 'fortnight' && parseFloat(e.monthly_salary) === 0)
      ? `${kr(e.hourly_rate)}/time` : kr(e.monthly_salary);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Medarbejdere</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setEditing(null); setOpen(true); }}>
          Ny medarbejder
        </Button>
      </Box>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {info && <Alert severity="info" sx={{ mb: 2 }} onClose={() => setInfo('')}>{info}</Alert>}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Nr.</TableCell>
              <TableCell>Navn</TableCell>
              <TableCell>CPR</TableCell>
              <TableCell>Lønform</TableCell>
              <TableCell align="right">Løn</TableCell>
              <TableCell>Skattekort</TableCell>
              <TableCell>Ferie</TableCell>
              <TableCell>Ansat</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {employees.map((e) => (
              <TableRow key={e.id} sx={{ opacity: e.is_active ? 1 : 0.5 }}>
                <TableCell>{e.employee_number}</TableCell>
                <TableCell>{e.name}</TableCell>
                <TableCell>{e.cpr_masked || <Chip size="small" color="warning" label="Mangler" />}</TableCell>
                <TableCell>{PAY_FORMS[e.pay_form]}</TableCell>
                <TableCell align="right">{salary(e)}</TableCell>
                <TableCell>
                  {TAX_CARDS[e.tax_card]}
                  {e.tax_card !== 'none' && e.tax_card !== 'free' && ` ${parseFloat(e.tax_rate)} %`}
                </TableCell>
                <TableCell>{e.holiday_scheme === 'feriekonto' ? 'FerieKonto' : e.holiday_type === 'with_pay' ? 'Med løn' : 'Egen ordning, 12,5 %'}</TableCell>
                <TableCell>{formatDate(e.start_date)}{e.end_date ? ` – ${formatDate(e.end_date)}` : ''}</TableCell>
                <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                  <Tooltip title="Hent eSkattekort">
                    <span>
                      <IconButton size="small" disabled={!e.has_cpr} onClick={() => fetchCard(e)}><FetchIcon fontSize="small" /></IconButton>
                    </span>
                  </Tooltip>
                  <IconButton size="small" onClick={() => { setEditing(e); setOpen(true); }}><EditIcon fontSize="small" /></IconButton>
                  <IconButton size="small" onClick={() => remove(e)}><DeleteIcon fontSize="small" /></IconButton>
                </TableCell>
              </TableRow>
            ))}
            {employees.length === 0 && (
              <TableRow><TableCell colSpan={9} align="center">Ingen medarbejdere endnu.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      <EmployeeDialog open={open} employee={editing} onClose={() => setOpen(false)}
        onSaved={() => { setOpen(false); load(); }} />
    </Box>
  );
};

export default EmployeesTab;
