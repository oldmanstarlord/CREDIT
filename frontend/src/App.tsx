import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import PortalSelectionPage from './pages/PortalSelectionPage';
import AdminLoginPage from './pages/AdminLoginPage';
import LandingPage from './pages/user/LandingPage';
import ApplicationPage from './pages/user/ApplicationPage';
import ResultPage from './pages/user/ResultPage';
import AdminLayout from './pages/admin/AdminLayout';
import DashboardPage from './pages/admin/DashboardPage';
import PipelinePage from './pages/admin/PipelinePage';
import FairnessPage from './pages/admin/FairnessPage';
import AuditLogPage from './pages/admin/AuditLogPage';
import ModelRegistryPage from './pages/admin/ModelRegistryPage';
import PortfolioPage from './pages/admin/PortfolioPage';
import ChatbotWidget from './components/ChatbotWidget';
import ProtectedRoute from './components/ProtectedRoute';

const App: React.FC = () => {
  return (
    <div className="min-h-screen">
      <Routes>
        {/* Portal Selection - Landing */}
        <Route path="/" element={<PortalSelectionPage />} />
        
        {/* User Portal Routes */}
        <Route path="/user/login" element={<LandingPage />} />
        <Route path="/apply" element={<ApplicationPage />} />
        <Route path="/result/:applicationId" element={<ResultPage />} />

        {/* Admin Portal Routes */}
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route 
          path="/admin" 
          element={
            <ProtectedRoute 
              requiredRoles={['ADMIN', 'ANALYST', 'RISK_MANAGER', 'SENIOR_ANALYST']}
              redirectTo="/admin/login"
            >
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="pipeline" element={<PipelinePage />} />
          <Route path="fairness" element={<FairnessPage />} />
          <Route path="audit" element={<AuditLogPage />} />
          <Route path="models" element={<ModelRegistryPage />} />
          <Route path="portfolio" element={<PortfolioPage />} />
        </Route>

        {/* Catch all - redirect to portal selection */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <ChatbotWidget />
    </div>
  );
};

export default App;
