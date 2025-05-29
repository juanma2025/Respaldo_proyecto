import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function PatientDashboard() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Verificar si el usuario está logueado
    const userData = localStorage.getItem('user');
    if (!userData) {
      navigate('/login');
      return;
    }
    
    const parsedUser = JSON.parse(userData);
    if (parsedUser.user_type !== 'patient') {
      navigate('/login');
      return;
    }
    
    setUser(parsedUser);
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('userType');
    navigate('/login');
  };

  if (!user) return <div>Cargando...</div>;

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold">Panel del Paciente</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span>Bienvenido, {user.full_name}</span>
              <button
                onClick={handleLogout}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              >
                Cerrar Sesión
              </button>
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 p-4">
            <h2 className="text-2xl font-bold mb-4">Mis Citas Médicas</h2>
            {/* Aquí irá el contenido para gestionar citas */}
            <p className="text-gray-600">
              Próximamente: Aquí podrás ver y agendar tus citas médicas.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}