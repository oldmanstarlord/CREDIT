import React from 'react';
import { Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  redirectTo?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRoles = [], 
  redirectTo = '/' 
}) => {
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);

  // Not authenticated - redirect to home
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  // No role requirements - just need to be authenticated
  if (requiredRoles.length === 0) {
    return <>{children}</>;
  }

  // Check if user has required role
  const userRole = user?.role?.toUpperCase();
  const hasRequiredRole = requiredRoles.some(
    role => role.toUpperCase() === userRole
  );

  if (!hasRequiredRole) {
    // User doesn't have required role - redirect
    return <Navigate to={redirectTo} replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
