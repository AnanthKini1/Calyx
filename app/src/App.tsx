import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { getSession } from './api/session'
import CreateProfile from './pages/CreateProfile'
import Login from './pages/Login'
import DoctorLayout from './pages/doctor/DoctorLayout'
import PatientLayout from './pages/patient/PatientLayout'

export default function App() {
  const user = getSession()

  if (!user) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/create-profile" element={<CreateProfile />} />
          <Route path="*" element={<Login />} />
        </Routes>
      </BrowserRouter>
    )
  }

  if (user.role === 'patient') {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/*" element={<PatientLayout patient={user} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    )
  }

  if (user.role === 'doctor') {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/*" element={<DoctorLayout doctor={user} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    )
  }

  return null
}
