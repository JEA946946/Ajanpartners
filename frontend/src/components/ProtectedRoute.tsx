import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { useAuth } from '../hooks/useAuth';
import { useClient } from '../hooks/useClient';

/** Kræver login og – medmindre `noClient` – en valgt kunde. */
const ProtectedRoute: React.FC<{ children: React.ReactNode; noClient?: boolean; firmOnly?: boolean }> = ({
  children, noClient, firmOnly,
}) => {
  const { isAuthenticated, loading } = useAuth();
  const { loading: clientLoading, current, firmStaff, termsRequired, mfa } = useClient();
  const location = useLocation();

  if (loading || (isAuthenticated && clientLoading)) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  // Medarbejdere i revisorhuset skal slå to-faktor til, før de kommer videre.
  if (mfa.required && !mfa.enabled && location.pathname !== '/profile') return <Navigate to="/profile" replace />;
  if (firmOnly && !firmStaff) return <Navigate to="/" replace />;
  if (!noClient && !firmOnly) {
    // Kundens brugere skal acceptere forretningsbetingelser og databehandleraftale først.
    if (termsRequired.length > 0 && (!firmStaff || termsRequired.some((t) => t.client === current?.client.slug))) {
      return <Navigate to="/onboarding" replace />;
    }
    if (!current) return <Navigate to={firmStaff ? '/admin' : '/select-client'} replace />;
  }
  return <>{children}</>;
};

export default ProtectedRoute;
