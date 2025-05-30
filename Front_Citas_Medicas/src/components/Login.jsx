import axios from "axios";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [mensaje, setMensaje] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMensaje("");
    setLoading(true);
    
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}auth/login/`,
        form
      );
      
      console.log('Respuesta del login:', response.data); // Para debug
      
      // Manejo flexible de diferentes formatos de token
      let token = null;
      if (response.data.access_token) {
        token = response.data.access_token;
      } else if (response.data.access) {
        token = response.data.access;
      } else if (response.data.token) {
        token = response.data.token;
      } else if (response.data.user?.token) {
        token = response.data.user.token;
      }

      if (!token) {
        throw new Error('No se recibió token de autenticación');
      }

      // Guardar token con nombre consistente
      localStorage.setItem('auth_token', token);
      localStorage.setItem('token', token); // Compatibilidad con código existente
      
      // Configurar axios para usar el token en futuras peticiones
      axios.defaults.headers.common['Authorization'] = `Token ${token}`;
      
      // Manejo mejorado de datos de usuario
      const userData = response.data.user || response.data;
      
      if (userData) {
        // Guardar datos completos del usuario
        localStorage.setItem('user', JSON.stringify(userData));
        
        // Guardar nombre de usuario de forma flexible
        const fullName = userData.full_name || 
                        `${userData.first_name || ''} ${userData.last_name || ''}`.trim() ||
                        userData.email ||
                        'Usuario';
        localStorage.setItem('user_full_name', fullName);
        
        // Guardar tipo de usuario
        if (userData.user_type) {
          localStorage.setItem('userType', userData.user_type);
        }
        
        // Guardar avatar si existe
        if (userData.avatar) {
          localStorage.setItem('user_avatar', userData.avatar);
        }
        
        // Guardar información adicional del usuario
        if (userData.id) {
          localStorage.setItem('user_id', userData.id.toString());
        }
        
        if (userData.email) {
          localStorage.setItem('user_email', userData.email);
        }
      }
      
      console.log('Token guardado:', localStorage.getItem('auth_token')); // Para debug
      
      // Disparar evento de storage para sincronización con otros componentes
      window.dispatchEvent(new Event('storage'));
      
      setMensaje("Login exitoso. Redirigiendo...");
      
      // Redirección inteligente según el tipo de usuario
      setTimeout(() => {
        const userType = userData?.user_type;
        
        switch(userType) {
          case 'patient':
            navigate('/appointments/create/');
            break;
          case 'doctor':
            navigate('/appointments/doctor/');
            break;
          case 'admin':
            navigate('/dashboard/admin');
            break;
          case 'secretary':
            navigate('/dashboard/secretary');
            break;
          default:
            // Si no hay tipo definido o es desconocido, ir al dashboard general
            navigate('/dashboard');
        }
      }, 1000);
      
    } catch (error) {
      console.error('Error en login:', error);
      
      // Manejo mejorado de errores
      let errorMessage = 'Error al iniciar sesión';
      
      if (error.response?.data) {
        errorMessage = error.response.data.detail ||
                      error.response.data.message ||
                      error.response.data.non_field_errors?.[0] ||
                      error.response.data.error ||
                      'Credenciales incorrectas';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setMensaje(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Función de debug para verificar estructura de respuesta (solo en desarrollo)
  const debugLogin = async () => {
    if (import.meta.env.MODE === 'development') {
      try {
        const response = await axios.post(`${import.meta.env.VITE_API_URL}auth/login/`, {
          email: 'test@example.com',
          password: 'testpassword'
        });
        
        console.log('ESTRUCTURA DE RESPUESTA DEL LOGIN:');
        console.log(JSON.stringify(response.data, null, 2));
        
      } catch (err) {
        console.log('Error en debug:', err.response?.data);
      }
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-500 via-gray-950 to-gray-500">
      <div className="w-full max-w-md p-8 rounded-2xl shadow-2xl bg-white/95 backdrop-blur-sm">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-gray-800 mb-2">
            Iniciar Sesión
          </h2>
          <p className="text-gray-600">
            Accede a tu sistema de gestión de citas
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Email Input */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
              </svg>
            </div>
            <input
              type="email"
              name="email"
              placeholder="Correo electrónico"
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              value={form.email}
              onChange={handleChange}
              required
            />
          </div>

          {/* Password Input */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <input
              type={showPassword ? "text" : "password"}
              name="password"
              placeholder="Contraseña"
              className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              value={form.password}
              onChange={handleChange}
              required
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={togglePasswordVisibility}
            >
              {showPassword ? (
                <svg className="h-5 w-5 text-gray-400 hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                </svg>
              ) : (
                <svg className="h-5 w-5 text-gray-400 hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              )}
            </button>
          </div>

          {/* Forgot Password Link */}
          <div className="flex justify-end">
            <button
              type="button"
              className="text-sm text-indigo-600 hover:text-indigo-800 font-medium transition-colors"
              onClick={() => console.log('Implementar recuperación de contraseña')}
            >
              ¿Olvidaste tu contraseña?
            </button>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-4 rounded-lg font-semibold text-lg hover:from-indigo-700 hover:to-purple-700 transition-all transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Iniciando sesión...
              </div>
            ) : (
              "Iniciar Sesión"
            )}
          </button>
        </form>

        {/* Register Link */}
        <div className="mt-6 text-center">
          <p className="text-gray-600 text-sm">
            ¿No tienes una cuenta?{" "}
            <button 
              onClick={() => navigate("/auth/register/patient/")}
              className="text-indigo-600 hover:text-indigo-800 font-medium transition-colors"
            >
              Regístrate aquí
            </button>
          </p>
        </div>

        {/* Message Display */}
        {mensaje && (
          <div className={`mt-4 p-3 rounded-lg text-center text-sm font-medium ${
            mensaje.includes("exitoso") 
              ? "bg-green-100 text-green-800 border border-green-200" 
              : "bg-red-100 text-red-800 border border-red-200"
          }`}>
            {mensaje}
          </div>
        )}

        {/* Debug Button (solo en desarrollo) */}
        {import.meta.env.MODE === 'development' && (
          <button
            type="button"
            onClick={debugLogin}
            className="mt-4 w-full text-xs text-gray-500 hover:text-gray-700 transition-colors"
          >
            🔧 Debug Login Structure
          </button>
        )}
      </div>
    </div>
  );
}