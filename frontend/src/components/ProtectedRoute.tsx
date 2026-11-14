import React from 'react';
import { Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { useAuth } from '../hooks/useAuth';
import { useClient } from '../hooks/useClient';

/** Kræver login og – medmindre `noClient` – en valgt kunde. */
const ProtectedRoute: React.FC<{ children: React.ReactNode; noClient?: boolean; firmOnly?: boolean }> = ({
  children, noClient, firmOnly,
}) => {
  const { isAuthenticated, loading } = useAuth();
  const { loading: clientLoading, current, firmStaff, pendingGrants } = useClient();

  if (loading || (isAuthenticated && clientLoading)) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (firmOnly && !firmStaff) return <Navigate to="/" replace />;
  if (!noClient && !firmOnly) {
    if (!firmStaff && pendingGrants.length > 0) return <Navigate to="/onboarding" replace />;
    if (!current) return <Navigate to={firmStaff ? '/admin' : '/select-client'} replace />;
  }
  return <>{children}</>;
};

export default ProtectedRoute;
