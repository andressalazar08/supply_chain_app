// Tipos para la autenticación
export interface User {
  username: string;
  role: 'admin' | 'estudiante';
  name: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

// Función para obtener el usuario actual
export const getCurrentUser = (): User | null => {
  if (typeof window === 'undefined') return null;
  
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;
  
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

// Función para verificar si el usuario está autenticado
export const isAuthenticated = (): boolean => {
  return getCurrentUser() !== null;
};

// Función para verificar si el usuario tiene un rol específico
export const hasRole = (role: 'admin' | 'estudiante'): boolean => {
  const user = getCurrentUser();
  return user?.role === role;
};

// Función para cerrar sesión
export const logout = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('user');
  }
};
