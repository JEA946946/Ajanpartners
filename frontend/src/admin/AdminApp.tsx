import React, { Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { AdminProvider } from './AdminContext';
import Terms from './pages/Terms';
import AdminLayout from './AdminLayout';

const ClientsList = React.lazy(() => import('./pages/ClientsList'));
const CreateClient = React.lazy(() => import('./pages/CreateClient'));
const ClientDetail = React.lazy(() => import('./pages/ClientDetail'));
const Deadlines = React.lazy(() => import('./pages/Deadlines'));
const Tasks = React.lazy(() => import('./pages/Tasks'));
const StaffPage = React.lazy(() => import('./pages/StaffPage'));
const Packages = React.lazy(() => import('./pages/Packages'));
const FirmAuditLog = React.lazy(() => import('./pages/FirmAuditLog'));
const FirmSettings = React.lazy(() => import('./pages/FirmSettings'));
const Templates = React.lazy(() => import('./pages/Templates'));
const IndustryRisk = React.lazy(() => import('./pages/IndustryRisk'));
const Aml = React.lazy(() => import('./pages/Aml'));
const Independence = React.lazy(() => import('./pages/Independence'));
const Engagements = React.lazy(() => import('./pages/Engagements'));
const EngagementDetail = React.lazy(() => import('./pages/EngagementDetail'));
const QualityLog = React.lazy(() => import('./pages/QualityLog'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const TimePage = React.lazy(() => import('./pages/TimePage'));
const Billing = React.lazy(() => import('./pages/Billing'));
const AdminSelectClient = React.lazy(() => import('./pages/SelectClient'));

const Loader = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}><CircularProgress /></Box>
);

/** Admin-portalen for Ajan Partners (/admin/*). */
const AdminApp: React.FC = () => (
  <AdminProvider>
    <AdminLayout>
      <Suspense fallback={<Loader />}>
        <Routes>
          <Route index element={<Navigate to="overview" replace />} />
          <Route path="overview" element={<Dashboard />} />
          <Route path="clients" element={<ClientsList />} />
          <Route path="clients/new" element={<CreateClient />} />
          <Route path="clients/:slug" element={<ClientDetail />} />
          <Route path="deadlines" element={<Deadlines />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="staff" element={<StaffPage />} />
          <Route path="packages" element={<Packages />} />
          <Route path="terms" element={<Terms />} />
          <Route path="templates" element={<Templates />} />
          <Route path="industry-risk" element={<IndustryRisk />} />
          <Route path="aml" element={<Aml />} />
          <Route path="independence" element={<Independence />} />
          <Route path="engagements" element={<Engagements />} />
          <Route path="engagements/:id" element={<EngagementDetail />} />
          <Route path="quality-log" element={<QualityLog />} />
          <Route path="time" element={<TimePage />} />
          <Route path="billing" element={<Billing />} />
          <Route path="audit-log" element={<FirmAuditLog />} />
          <Route path="settings" element={<FirmSettings />} />
          <Route path="select-client" element={<AdminSelectClient />} />
          <Route path="*" element={<Navigate to="clients" replace />} />
        </Routes>
      </Suspense>
    </AdminLayout>
  </AdminProvider>
);

export default AdminApp;
