import { RouterProvider } from 'react-router-dom';
import { useEffect } from 'react';
import { router } from './router';
import { useAuthStore } from './stores/authStore';

function App() {
  const initializeAuth = useAuthStore((s) => s.initializeAuth);
  const isLoading = useAuthStore((s) => s.isLoading);

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  return <RouterProvider router={router} />;
}

export default App;
