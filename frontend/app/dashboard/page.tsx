'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  username: string;
  role: string;
  name: string;
}

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Verificar si el usuario está autenticado
    const userStr = localStorage.getItem('user');
    if (!userStr) {
      router.push('/login');
      return;
    }

    setUser(JSON.parse(userStr));
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('user');
    router.push('/login');
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Dashboard - Cadena de Suministro
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Bienvenido, {user.name}
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition duration-200"
          >
            Cerrar Sesión
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Información del Usuario
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Usuario</p>
              <p className="text-lg font-semibold text-gray-800">{user.username}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Nombre</p>
              <p className="text-lg font-semibold text-gray-800">{user.name}</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Rol</p>
              <p className="text-lg font-semibold text-gray-800 capitalize">{user.role}</p>
            </div>
          </div>
        </div>

        {/* Contenido según el rol */}
        {user.role === 'admin' ? (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Panel de Administrador
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition cursor-pointer">
                <div className="text-3xl mb-2">👥</div>
                <h3 className="font-semibold text-gray-800">Gestión de Usuarios</h3>
                <p className="text-sm text-gray-600 mt-2">Administrar estudiantes y permisos</p>
              </div>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition cursor-pointer">
                <div className="text-3xl mb-2">📊</div>
                <h3 className="font-semibold text-gray-800">Reportes</h3>
                <p className="text-sm text-gray-600 mt-2">Ver estadísticas y análisis</p>
              </div>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition cursor-pointer">
                <div className="text-3xl mb-2">⚙️</div>
                <h3 className="font-semibold text-gray-800">Configuración</h3>
                <p className="text-sm text-gray-600 mt-2">Ajustes del sistema</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Panel del Estudiante
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-green-500 transition cursor-pointer">
                <div className="text-3xl mb-2">🎮</div>
                <h3 className="font-semibold text-gray-800">Iniciar Lúdica</h3>
                <p className="text-sm text-gray-600 mt-2">Comienza la simulación de cadena de suministro</p>
              </div>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-green-500 transition cursor-pointer">
                <div className="text-3xl mb-2">📈</div>
                <h3 className="font-semibold text-gray-800">Mi Progreso</h3>
                <p className="text-sm text-gray-600 mt-2">Ver resultados y aprendizaje</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
