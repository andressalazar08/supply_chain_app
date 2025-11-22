# Sistema de Autenticación - Frontend

## 🔐 Sistema de Login

Este proyecto incluye un sistema de autenticación básico con dos tipos de usuarios: **Admin** y **Estudiante**.

### Credenciales de Acceso

#### Usuario Administrador
- **Usuario:** `admin`
- **Contraseña:** `admin123`
- **Rol:** Administrador

#### Usuario Estudiante
- **Usuario:** `estudiante`
- **Contraseña:** `estudiante123`
- **Rol:** Estudiante

## 🚀 Cómo usar

1. **Iniciar el servidor de desarrollo:**
   ```bash
   npm run dev
   ```

2. **Acceder a la aplicación:**
   - Abre tu navegador en `http://localhost:3000`
   - Serás redirigido automáticamente a `/login`

3. **Iniciar sesión:**
   - Usa cualquiera de las credenciales mencionadas arriba
   - Serás redirigido al dashboard según tu rol

## 📁 Estructura del Proyecto

```
frontend/
├── app/
│   ├── login/
│   │   └── page.tsx          # Página de login
│   ├── dashboard/
│   │   └── page.tsx          # Dashboard (protegido)
│   ├── page.tsx              # Página principal (redirección)
│   ├── layout.tsx
│   └── globals.css
├── lib/
│   └── auth.ts               # Utilidades de autenticación
└── middleware.ts             # Middleware para rutas
```

## 🔧 Funcionalidades Implementadas

### Autenticación
- ✅ Login con credenciales básicas
- ✅ Almacenamiento de sesión en localStorage
- ✅ Protección de rutas
- ✅ Redirección automática según estado de autenticación

### Roles y Permisos
- ✅ **Admin:** Acceso a panel de administración
  - Gestión de usuarios
  - Reportes y estadísticas
  - Configuración del sistema

- ✅ **Estudiante:** Acceso a panel de estudiante
  - Iniciar lúdica/simulación
  - Ver progreso personal

### Componentes
- ✅ Formulario de login con validación
- ✅ Dashboard diferenciado por rol
- ✅ Botón de cerrar sesión
- ✅ Información del usuario actual

## 🎨 Tecnologías Utilizadas

- **Next.js 16** - Framework de React
- **React 19** - Biblioteca de UI
- **TypeScript** - Tipado estático
- **Tailwind CSS 4** - Estilos
- **Axios** - Cliente HTTP (preparado para backend futuro)

## 🔜 Próximos Pasos

Para conectar con el backend:

1. **Crear endpoint de autenticación en el backend:**
   ```typescript
   POST /api/auth/login
   Body: { username, password }
   Response: { user, token }
   ```

2. **Modificar la función de login en `/app/login/page.tsx`:**
   ```typescript
   const response = await axios.post('http://tu-backend/api/auth/login', {
     username,
     password
   });
   ```

3. **Implementar gestión de tokens:**
   - Guardar JWT en localStorage
   - Agregar interceptor de axios para incluir token en headers
   - Implementar refresh token

4. **Agregar más rutas protegidas según necesidades de la lúdica**

## 📝 Notas

- La autenticación actual es solo del lado del cliente (localStorage)
- Las credenciales están hardcodeadas en el código
- **No usar en producción sin implementar autenticación real con backend**
- El middleware está preparado pero la validación real se hace en el cliente

## 🛠️ Desarrollo

Para agregar más usuarios temporales, edita el array `MOCK_USERS` en `/app/login/page.tsx`:

```typescript
const MOCK_USERS = [
  {
    username: 'nuevo_usuario',
    password: 'contraseña',
    role: 'estudiante', // o 'admin'
    name: 'Nombre Completo'
  }
];
```
