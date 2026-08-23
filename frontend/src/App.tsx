import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import { ToastProvider } from './components/ui/Toast';
import { AppLayout } from './components/layout/AppLayout';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { ResidentDashboard } from './pages/resident/Dashboard';
import { ComplaintsList } from './pages/resident/ComplaintsList';
import { ComplaintNew } from './pages/resident/ComplaintNew';
import { ComplaintDetail } from './pages/resident/ComplaintDetail';
import { NoticesList } from './pages/resident/NoticesList';
import { AdminDashboard } from './pages/admin/Dashboard';
import { AdminComplaintsList } from './pages/admin/ComplaintsList';
import { AdminComplaintDetail } from './pages/admin/ComplaintDetail';
import { AdminNoticesList } from './pages/admin/NoticesList';
import { NoticeForm } from './pages/admin/NoticeForm';
import { Settings } from './pages/admin/Settings';
import { AdminUsersList } from './pages/admin/UsersList';
import { NotFound } from './pages/NotFound';
import { Spinner } from './components/ui/Spinner';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, refetchOnWindowFocus: false },
  },
});

function ProtectedRoute({ children, adminOnly = false }: { children: React.ReactNode; adminOnly?: boolean }) {
  const { user, loading } = useAuth();

  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && user.role !== 'admin') return <Navigate to="/" replace />;

  return <>{children}</>;
}

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) return <Spinner />;

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to={user.role === 'admin' ? '/admin' : '/'} replace /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to={user.role === 'admin' ? '/admin' : '/'} replace /> : <Register />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<ResidentDashboard />} />
        <Route path="/complaints" element={<ComplaintsList />} />
        <Route path="/complaints/new" element={<ComplaintNew />} />
        <Route path="/complaints/:id" element={<ComplaintDetail />} />
        <Route path="/notices" element={<NoticesList />} />
      </Route>

      <Route
        element={
          <ProtectedRoute adminOnly>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/complaints" element={<AdminComplaintsList />} />
        <Route path="/admin/complaints/:id" element={<AdminComplaintDetail />} />
        <Route path="/admin/notices" element={<AdminNoticesList />} />
        <Route path="/admin/notices/new" element={<NoticeForm />} />
        <Route path="/admin/notices/:id" element={<NoticeForm />} />
        <Route path="/admin/settings" element={<Settings />} />
        <Route path="/admin/users" element={<AdminUsersList />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ToastProvider>
            <AppRoutes />
          </ToastProvider>
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );
}
