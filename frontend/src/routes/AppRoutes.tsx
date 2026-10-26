import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { ProtectedRoute } from '../components/common/ProtectedRoute';

// Public pages
import { HomePage } from '../pages/public/HomePage';
import { LoginPage } from '../pages/public/LoginPage';
import { RegisterPage } from '../pages/public/RegisterPage';
import { DepartmentLandingPage } from '../pages/public/DepartmentLandingPage';
import { NotFoundPage } from '../pages/public/NotFoundPage';

// Patient pages
import { PatientDashboardPage } from '../pages/patient/PatientDashboardPage';
import { JoinQueuePage } from '../pages/patient/JoinQueuePage';
import { MyQueuePage } from '../pages/patient/MyQueuePage';

// Doctor pages
import { DoctorDashboardPage } from '../pages/doctor/DoctorDashboardPage';

// Admin pages
import { AdminDashboardPage } from '../pages/admin/AdminDashboardPage';

// Staff legacy fallback page
import { StaffDashboardPage } from '../pages/staff/StaffDashboardPage';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes with MainLayout */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/department/:slug" element={<DepartmentLandingPage />} />
      </Route>

      {/* Patient Protected Routes */}
      <Route
        path="/patient"
        element={
          <ProtectedRoute allowedRoles={['patient', 'doctor', 'staff', 'admin']}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/patient/dashboard" replace />} />
        <Route path="dashboard" element={<PatientDashboardPage />} />
        <Route path="join" element={<JoinQueuePage />} />
        <Route path="queue/:id" element={<MyQueuePage />} />
      </Route>

      {/* Doctor Protected Routes */}
      <Route
        path="/doctor"
        element={
          <ProtectedRoute allowedRoles={['doctor', 'admin']}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/doctor/dashboard" replace />} />
        <Route path="dashboard" element={<DoctorDashboardPage />} />
      </Route>

      {/* Admin Protected Routes */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/admin/dashboard" replace />} />
        <Route path="dashboard" element={<AdminDashboardPage />} />
      </Route>

      {/* Staff route (redirects or serves doctor dashboard) */}
      <Route
        path="/staff"
        element={
          <ProtectedRoute allowedRoles={['doctor', 'staff', 'admin']}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/staff/dashboard" replace />} />
        <Route path="dashboard" element={<StaffDashboardPage />} />
      </Route>

      {/* Catch-all 404 Route */}
      <Route element={<MainLayout />}>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
};
