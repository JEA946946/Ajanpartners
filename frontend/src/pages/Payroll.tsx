import React, { useState } from 'react';
import { Box, Paper, Tab, Tabs, Typography } from '@mui/material';
import EmployeesTab from '../components/payroll/EmployeesTab';
import RunsTab from '../components/payroll/RunsTab';
import SettingsTab from '../components/payroll/SettingsTab';

// Dansk løn: medarbejdere, lønkørsler (kladde → beregn → godkend → bogfør),
// lønsedler, eIndkomst-eksport og helligdage.
const Payroll: React.FC = () => {
  const [tab, setTab] = useState(0);
  return (
    <Box>
      <Typography variant="h4" gutterBottom>Løn</Typography>
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable">
          <Tab label="Lønkørsler" />
          <Tab label="Medarbejdere" />
          <Tab label="Indstillinger og helligdage" />
        </Tabs>
      </Paper>
      {tab === 0 && <RunsTab />}
      {tab === 1 && <EmployeesTab />}
      {tab === 2 && <SettingsTab />}
    </Box>
  );
};

export default Payroll;
