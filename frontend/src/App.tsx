import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Box, CircularProgress } from '@mui/material';
import CssBaseline from '@mui/material/CssBaseline';

import { AuthProvider } from './hooks/useAuth';
import { SettingsProvider } from './hooks/useSettings';
import { ClientProvider } from './hooks/useClient';
import RequireFeature from './components/RequireFeature';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout/Layout';

const Login = React.lazy(() => import('./pages/Login'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const ChartOfAccounts = React.lazy(() => import('./pages/ChartOfAccounts'));
const JournalEntries = React.lazy(() => import('./pages/JournalEntries'));
const Journals = React.lazy(() => import('./pages/Journals'));
const Closing = React.lazy(() => import('./pages/Closing'));
const Lettrage = React.lazy(() => import('./pages/Lettrage'));
const BankStatements = React.lazy(() => import('./pages/BankStatements'));
const Reports = React.lazy(() => import('./pages/Reports'));
const SelectClient = React.lazy(() => import('./pages/SelectClient'));
const Onboarding = React.lazy(() => import('./pages/Onboarding'));
const Profile = React.lazy(() => import('./pages/Profile'));
const DataExport = React.lazy(() => import('./pages/DataExport'));
const AccessGrants = React.lazy(() => import('./pages/AccessGrants'));
const AdminApp = React.lazy(() => import('./admin/AdminApp'));

// New pages
const Customers = React.lazy(() => import('./pages/Customers'));
const Invoices = React.lazy(() => import('./pages/Invoices'));
const CreditNotes = React.lazy(() => import('./pages/CreditNotes'));
const Quotes = React.lazy(() => import('./pages/Quotes'));
const Reminders = React.lazy(() => import('./pages/Reminders'));
const Suppliers = React.lazy(() => import('./pages/Suppliers'));
const Bills = React.lazy(() => import('./pages/Bills'));
const EInvoiceInbox = React.lazy(() => import('./pages/EInvoiceInbox'));
const Expenses = React.lazy(() => import('./pages/Expenses'));
const Payments = React.lazy(() => import('./pages/Payments'));
const BankTransactions = React.lazy(() => import('./pages/BankTransactions'));
const BankReconciliation = React.lazy(() => import('./pages/BankReconciliation'));
const BankRules = React.lazy(() => import('./pages/BankRules'));
const BankFeeds = React.lazy(() => import('./pages/BankFeeds'));
const Projects = React.lazy(() => import('./pages/Projects'));
const Documents = React.lazy(() => import('./pages/Documents'));
const TaxCodes = React.lazy(() => import('./pages/TaxCodes'));
const TaxReport = React.lazy(() => import('./pages/TaxReport'));
const AuditLog = React.lazy(() => import('./pages/AuditLog'));
const Settings = React.lazy(() => import('./pages/Settings'));
const Users = React.lazy(() => import('./pages/Users'));
const AccountingRules = React.lazy(() => import('./pages/AccountingRules'));
const Payroll = React.lazy(() => import('./pages/Payroll'));
const Inbox = React.lazy(() => import('./pages/Inbox'));

const PageLoader = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
    <CircularProgress />
  </Box>
);

const theme = createTheme({
  palette: {
    primary: { main: '#0B3D5C', light: '#2E6A8E', dark: '#062638' },
    secondary: { main: '#C8963E' },
    background: { default: '#f5f5f5', paper: '#ffffff' },
    text: { primary: '#333333', secondary: '#666666' },
  },
  typography: {
    fontSize: 13,
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    body1: { fontSize: '0.8125rem' },
    body2: { fontSize: '0.8125rem' },
    caption: { fontSize: '0.75rem' },
    button: { fontSize: '0.8125rem', textTransform: 'none', fontWeight: 500 },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: { boxShadow: '0 2px 8px rgba(0,0,0,0.1)', borderRadius: 8 },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 6, padding: '8px 16px' },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': { fontSize: '0.8125rem' },
          '& .MuiInputLabel-root': { fontSize: '0.8125rem' },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { fontSize: '0.8125rem' },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: { fontSize: '0.8125rem' },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: { fontSize: '0.8125rem' },
      },
    },
    MuiChip: {
      styleOverrides: {
        label: { fontSize: '0.8125rem' },
        labelSmall: { fontSize: '0.75rem' },
      },
    },
  },
});

const P = ({ children, feature }: { children: React.ReactNode; feature?: string }) => (
  <ProtectedRoute><Layout><RequireFeature feature={feature}>{children}</RequireFeature></Layout></ProtectedRoute>
);

function App() {
  return (
    <AuthProvider>
      <ClientProvider>
      <SettingsProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/select-client" element={<ProtectedRoute noClient><SelectClient /></ProtectedRoute>} />
              <Route path="/onboarding" element={<ProtectedRoute noClient><Onboarding /></ProtectedRoute>} />
              <Route path="/profile" element={<ProtectedRoute noClient><Profile /></ProtectedRoute>} />
              <Route path="/admin/*" element={<ProtectedRoute firmOnly><AdminApp /></ProtectedRoute>} />

              <Route path="/" element={<P><Dashboard /></P>} />
              <Route path="/dashboard" element={<P><Dashboard /></P>} />

              <Route path="/accounts" element={<P><ChartOfAccounts /></P>} />
              <Route path="/journal-entries" element={<P feature="journal"><JournalEntries /></P>} />
              <Route path="/journals" element={<P feature="journal"><Journals /></P>} />
              <Route path="/closing" element={<P feature="journal"><Closing /></P>} />
              <Route path="/lettrage" element={<P feature="lettrage"><Lettrage /></P>} />

              <Route path="/customers" element={<P><Customers /></P>} />
              <Route path="/invoices" element={<P feature="invoicing"><Invoices /></P>} />
              <Route path="/credit-notes" element={<P feature="invoicing"><CreditNotes /></P>} />
              <Route path="/quotes" element={<P feature="invoicing"><Quotes /></P>} />
              <Route path="/reminders" element={<P feature="invoicing"><Reminders /></P>} />

              <Route path="/suppliers" element={<P><Suppliers /></P>} />
              <Route path="/bills" element={<P feature="purchases"><Bills /></P>} />
              <Route path="/einvoice/inbox" element={<P feature="einvoice_receive"><EInvoiceInbox /></P>} />
              <Route path="/expenses" element={<P feature="purchases"><Expenses /></P>} />

              <Route path="/payroll" element={<P feature="payroll"><Payroll /></P>} />

              <Route path="/bank-statements" element={<P feature="bank"><BankStatements /></P>} />
              <Route path="/bank-transactions" element={<P feature="bank"><BankTransactions /></P>} />
              <Route path="/payments" element={<P feature="bank"><Payments /></P>} />
              <Route path="/bank-reconciliation" element={<P feature="bank"><BankReconciliation /></P>} />
              <Route path="/bank-rules" element={<P feature="bank"><BankRules /></P>} />
              <Route path="/bank-feeds" element={<P feature="bank_feed"><BankFeeds /></P>} />

              <Route path="/projects" element={<P feature="projects"><Projects /></P>} />

              <Route path="/tax-codes" element={<P feature="vat"><TaxCodes /></P>} />
              <Route path="/tax-report" element={<P feature="vat"><TaxReport /></P>} />

              <Route path="/reports" element={<P feature="reports"><Reports /></P>} />

              <Route path="/documents" element={<P><Documents /></P>} />
              <Route path="/inbox" element={<P><Inbox /></P>} />
              <Route path="/audit-log" element={<P><AuditLog /></P>} />
              <Route path="/settings" element={<P><Settings /></P>} />
              <Route path="/settings/access" element={<P><AccessGrants /></P>} />
              <Route path="/settings/export" element={<P><DataExport /></P>} />
              <Route path="/users" element={<P><Users /></P>} />
              <Route path="/accounting-rules" element={<P><AccountingRules /></P>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </Router>
      </ThemeProvider>
      </SettingsProvider>
      </ClientProvider>
    </AuthProvider>
  );
}

export default App;
