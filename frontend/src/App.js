import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import DashboardLayout from './components/dashboard/DashboardLayout';
import Dashboard from './components/dashboard/Dashboard';
import SiteList from './components/sites/SiteList';
import SiteForm from './components/sites/SiteForm';
import DemoPage from './components/DemoPage';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<DemoPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Protected Dashboard Routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <DashboardLayout>
                <Dashboard />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/dashboard/sites" element={
            <ProtectedRoute>
              <DashboardLayout>
                <SiteList />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/dashboard/sites/new" element={
            <ProtectedRoute>
              <DashboardLayout>
                <SiteForm />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          
          <Route path="/dashboard/sites/:id/edit" element={
            <ProtectedRoute>
              <DashboardLayout>
                <SiteForm />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          
          {/* Redirect unknown routes to dashboard for authenticated users, otherwise to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;