import React, { useEffect, useState } from 'react';
import {
  Box, AppBar, Toolbar, Typography, Drawer, List, ListItemButton,
  ListItemIcon, ListItemText, IconButton, Avatar, Divider, Select, MenuItem,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  AccountTree as AccountsIcon,
  Receipt as JournalIcon,
  LibraryBooks as JournalsIcon,
  Lock as ClosingIcon,
  Link as LettrageIcon,
  CloudUpload as CloudUploadIcon,
  Assessment as ReportsIcon,
  Logout as LogoutIcon,
  SwapHoriz as SwapIcon,
  AdminPanelSettings as AdminIcon,
  VerifiedUser as AccessIcon,
  People as PeopleIcon,
  ShoppingCart as ShoppingCartIcon,
  Store as StoreIcon,
  CreditCard as CreditCardIcon,
  ReceiptLong as ReceiptLongIcon,
  MoneyOff as MoneyOffIcon,
  Payment as PaymentIcon,
  AccountBalance as AccountBalanceIcon,
  Rule as RuleIcon,
  Work as WorkIcon,
  Description as DescriptionIcon,
  Gavel as GavelIcon,
  Settings as SettingsIcon,
  History as HistoryIcon,
  ManageAccounts as ManageAccountsIcon,
  RequestQuote as RequestQuoteIcon,
  MenuBook as MenuBookIcon,
  Badge as BadgeIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useClient } from '../../hooks/useClient';
import { useTranslation } from 'react-i18next';
import api from '../../services/api';

const SIDEBAR_WIDTH = 220;
const APPBAR_HEIGHT = 48;

interface LayoutProps {
  children: React.ReactNode;
}

interface MenuSection {
  label: string;
  items: { text: string; icon: React.ReactNode; path: string; feature?: string }[];
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { t, i18n } = useTranslation();
  const { current, firm, firmStaff, clients, hasFeature } = useClient();

  const [siteLogo, setSiteLogo] = useState<string>('');
  useEffect(() => {
    if (!current) return;
    api.get('/settings').then(res => {
      if (res.data.success) {
        const d = res.data.data?.settings ?? res.data.settings ?? res.data.data ?? {};
        setSiteLogo(d.logo1 || '');
      }
    }).catch(() => { /* ignore */ });
  }, [current]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path: string) =>
    location.pathname === path || location.pathname.startsWith(path + '/');

  const menuSections: MenuSection[] = [
    {
      label: t('sidebar.overview'),
      items: [
        { text: t('sidebar.dashboard'), icon: <DashboardIcon fontSize="small" />, path: '/dashboard' },
      ],
    },
    {
      label: t('sidebar.sales'),
      items: [
        { text: t('sidebar.customers'), icon: <PeopleIcon fontSize="small" />, path: '/customers' },
        { text: t('sidebar.invoices'), icon: <ReceiptLongIcon fontSize="small" />, path: '/invoices', feature: 'invoicing' },
        { text: t('sidebar.creditNotes'), icon: <MoneyOffIcon fontSize="small" />, path: '/credit-notes', feature: 'invoicing' },
      ],
    },
    {
      label: t('sidebar.purchasing'),
      items: [
        { text: t('sidebar.suppliers'), icon: <StoreIcon fontSize="small" />, path: '/suppliers' },
        { text: t('sidebar.bills'), icon: <RequestQuoteIcon fontSize="small" />, path: '/bills', feature: 'purchases' },
        { text: t('sidebar.expenses'), icon: <ShoppingCartIcon fontSize="small" />, path: '/expenses', feature: 'purchases' },
      ],
    },
    {
      label: t('sidebar.payroll'),
      items: [
        { text: t('sidebar.payrollOverview'), icon: <BadgeIcon fontSize="small" />, path: '/payroll', feature: 'payroll' },
      ],
    },
    {
      label: t('sidebar.bank'),
      items: [
        { text: t('sidebar.bankUpload'), icon: <CloudUploadIcon fontSize="small" />, path: '/bank-statements', feature: 'bank' },
        { text: t('sidebar.bankTransactions'), icon: <ReceiptLongIcon fontSize="small" />, path: '/bank-transactions', feature: 'bank' },
        { text: t('sidebar.payments'), icon: <PaymentIcon fontSize="small" />, path: '/payments', feature: 'bank' },
        { text: t('sidebar.reconciliation'), icon: <AccountBalanceIcon fontSize="small" />, path: '/bank-reconciliation', feature: 'bank' },
        { text: t('sidebar.bankRules'), icon: <RuleIcon fontSize="small" />, path: '/bank-rules', feature: 'bank' },
      ],
    },
    {
      label: t('sidebar.bookkeeping'),
      items: [
        { text: t('sidebar.chartOfAccounts'), icon: <AccountsIcon fontSize="small" />, path: '/accounts' },
        { text: t('sidebar.journalEntries'), icon: <JournalIcon fontSize="small" />, path: '/journal-entries', feature: 'journal' },
        { text: t('sidebar.journals'), icon: <JournalsIcon fontSize="small" />, path: '/journals', feature: 'journal' },
        { text: t('sidebar.lettrage'), icon: <LettrageIcon fontSize="small" />, path: '/lettrage', feature: 'lettrage' },
        { text: t('sidebar.closing'), icon: <ClosingIcon fontSize="small" />, path: '/closing', feature: 'journal' },
        { text: t('sidebar.projects'), icon: <WorkIcon fontSize="small" />, path: '/projects', feature: 'projects' },
      ],
    },
    {
      label: t('sidebar.taxVat'),
      items: [
        { text: t('sidebar.taxReport'), icon: <GavelIcon fontSize="small" />, path: '/tax-report', feature: 'vat' },
        { text: t('sidebar.taxCodes'), icon: <CreditCardIcon fontSize="small" />, path: '/tax-codes', feature: 'vat' },
      ],
    },
    {
      label: t('sidebar.reports'),
      items: [
        { text: t('sidebar.reportsOverview'), icon: <ReportsIcon fontSize="small" />, path: '/reports', feature: 'reports' },
        { text: t('sidebar.accountingRules'), icon: <MenuBookIcon fontSize="small" />, path: '/accounting-rules' },
      ],
    },
    {
      label: t('sidebar.system'),
      items: [
        { text: t('sidebar.documents'), icon: <DescriptionIcon fontSize="small" />, path: '/documents' },
        { text: t('sidebar.auditLog'), icon: <HistoryIcon fontSize="small" />, path: '/audit-log' },
        { text: t('sidebar.settings'), icon: <SettingsIcon fontSize="small" />, path: '/settings' },
        { text: t('sidebar.users'), icon: <ManageAccountsIcon fontSize="small" />, path: '/users' },
        { text: 'Revisoradgang', icon: <AccessIcon fontSize="small" />, path: '/settings/access' },
      ],
    },
  ];

  const visibleSections = menuSections
    .map((sec) => ({ ...sec, items: sec.items.filter((i) => hasFeature(i.feature)) }))
    .filter((sec) => sec.items.length > 0);

  const sidebarItemSx = (active: boolean) => ({
    py: 0.3,
    px: 2,
    borderRadius: 1,
    mx: 1,
    mb: 0.15,
    backgroundColor: active ? 'primary.main' : 'transparent',
    color: active ? '#fff' : 'text.primary',
    '&:hover': { backgroundColor: active ? 'primary.dark' : 'action.hover' },
    '& .MuiListItemIcon-root': { color: active ? '#fff' : 'text.secondary', minWidth: 28 },
    '& .MuiListItemText-primary': { fontSize: '11.5px' },
  });

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{ zIndex: (theme) => theme.zIndex.drawer + 1, height: APPBAR_HEIGHT, bgcolor: firm?.primary_color || '#0B3D5C' }}
      >
        <Toolbar variant="dense" sx={{ minHeight: APPBAR_HEIGHT, height: APPBAR_HEIGHT }}>
          {siteLogo && (
            <Box component="img" src={siteLogo} alt=""
              sx={{ height: 30, maxWidth: 140, objectFit: 'contain', mr: 1.5 }}
              onError={(e: any) => { e.target.style.display = 'none'; }} />
          )}
          <Typography variant="h6" noWrap sx={{ fontWeight: 'bold', fontSize: '16px', mr: 2 }}>
            {firm?.name || 'Ajan Partners'}
          </Typography>
          <Typography variant="body2" noWrap sx={{ fontSize: '13px', opacity: 0.9, mr: 1 }}>
            {current?.client.name}{current?.client.cvr ? ` · CVR ${current.client.cvr}` : ''}
            {current ? ` · ${current.package.name}` : ''}
          </Typography>
          {(clients.length > 1 || firmStaff) && (
            <IconButton color="inherit" size="small" title="Skift virksomhed" onClick={() => navigate('/select-client')}>
              <SwapIcon fontSize="small" />
            </IconButton>
          )}
          {firmStaff && (
            <IconButton color="inherit" size="small" title="Admin-portal" onClick={() => navigate('/admin')}>
              <AdminIcon fontSize="small" />
            </IconButton>
          )}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, ml: 'auto' }}>
            <Typography variant="body2" sx={{ fontSize: '12px', color: '#fff' }}>
              {user?.first_name} {user?.last_name}
            </Typography>
            <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 28, height: 28, fontSize: '12px' }}>
              {user?.first_name?.charAt(0)}{user?.last_name?.charAt(0)}
            </Avatar>
            <Select
              value={(i18n.resolvedLanguage || i18n.language || 'en').substring(0, 2)}
              onChange={(e) => i18n.changeLanguage(e.target.value as string)}
              size="small"
              variant="standard"
              disableUnderline
              sx={{
                color: '#fff',
                fontSize: '12px',
                fontWeight: 600,
                '& .MuiSelect-icon': { color: '#fff' },
                '& .MuiSelect-select': { py: 0, pr: '20px !important' },
                minWidth: 40,
              }}
            >
              <MenuItem value="da">DA</MenuItem>
              <MenuItem value="en">EN</MenuItem>
            </Select>
            <IconButton color="inherit" onClick={handleLogout} size="small">
              <LogoutIcon fontSize="small" />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: SIDEBAR_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: SIDEBAR_WIDTH,
            boxSizing: 'border-box',
            backgroundColor: '#fafafa',
            borderRight: '1px solid',
            borderColor: 'divider',
            mt: `${APPBAR_HEIGHT}px`,
            height: `calc(100% - ${APPBAR_HEIGHT}px)`,
            overflowX: 'hidden',
          },
        }}
      >
        <List dense sx={{ pt: 0.5 }}>
          {visibleSections.map((section, sIdx) => (
            <React.Fragment key={sIdx}>
              {sIdx > 0 && <Divider sx={{ my: 0.3 }} />}
              <Typography
                variant="caption"
                sx={{
                  px: 2,
                  pt: sIdx === 0 ? 0.5 : 0.5,
                  pb: 0.2,
                  display: 'block',
                  fontSize: '9.5px',
                  fontWeight: 700,
                  color: 'text.secondary',
                  letterSpacing: '0.5px',
                }}
              >
                {section.label}
              </Typography>
              {section.items.map((item) => (
                <ListItemButton
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  sx={sidebarItemSx(isActive(item.path))}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              ))}
            </React.Fragment>
          ))}
        </List>
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          mt: `${APPBAR_HEIGHT}px`,
          minHeight: `calc(100vh - ${APPBAR_HEIGHT}px)`,
        }}
      >
        {current?.access.via === 'firm' && (
          <Box sx={{ mb: 2, px: 2, py: 0.75, borderRadius: 1, bgcolor: '#FFF4E0', border: '1px solid #E8C98A',
            fontSize: '12.5px' }}>
            Du arbejder i <b>{current.client.name}</b> som {firm?.name || 'revisor'} med adgangen
            {' '}<b>{({ read: 'læse', bookkeeping: 'bogføre', full: 'fuld' } as Record<string, string>)[current.access.grant_scope || ''] || current.access.grant_scope}</b>.
            {' '}Alt, du gør, logges hos kunden.
          </Box>
        )}
        {current?.client.status === 'archived' && (
          <Box sx={{ mb: 2, px: 2, py: 0.75, borderRadius: 1, bgcolor: '#EEE', fontSize: '12.5px' }}>
            Virksomheden er arkiveret. Bøgerne kan kun læses.
          </Box>
        )}
        {children}
      </Box>
    </Box>
  );
};

export default Layout;
