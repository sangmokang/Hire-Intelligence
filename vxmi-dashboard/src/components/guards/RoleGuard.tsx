import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { hasPermission, type UserRole } from '../../types/auth';

interface RoleGuardProps {
  children: React.ReactNode;
  requiredRole: UserRole;
}

export function RoleGuard({ children, requiredRole }: RoleGuardProps) {
  const { user } = useAuthStore();

  if (!user || !hasPermission(user.role, requiredRole)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
