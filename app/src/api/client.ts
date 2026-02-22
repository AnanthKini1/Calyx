import axios from 'axios'
import type { AnalysisResult, Doctor, Patient, PatientWithSummary } from '../types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
})

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (email: string, password: string) =>
  api.post<Patient | Doctor>('/api/auth/login', { email, password }).then(r => r.data)

export const registerPatient = (data: {
  email: string; password: string; name: string; age: number
  comorbidities: string[]; blood_glucose?: number; serum_albumin?: number
  mobility_score?: number; post_op_day?: number; doctor_id?: string
}) => api.post<Patient>('/api/auth/register/patient', data).then(r => r.data)

export const registerDoctor = (data: {
  email: string; password: string; name: string; specialty: string
}) => api.post<Doctor>('/api/auth/register/doctor', data).then(r => r.data)

// ── Patients ──────────────────────────────────────────────────────────────────
export const getPatient = (id: string) =>
  api.get<Patient>(`/api/patients/${id}`).then(r => r.data)

export const getAllPatients = () =>
  api.get<Patient[]>('/api/patients').then(r => r.data)

export const getPatientAnalysis = (id: string) =>
  api.get<AnalysisResult>(`/api/patients/${id}/analysis`).then(r => r.data)

export const getDoctors = () =>
  api.get<Doctor[]>('/api/doctors').then(r => r.data)

// ── Doctor ────────────────────────────────────────────────────────────────────
export const getDoctorPatients = (doctorId: string) =>
  api.get<PatientWithSummary[]>(`/api/doctors/${doctorId}/patients`).then(r => r.data)

export const addPatientToDoctor = (doctorId: string, patientId: string) =>
  api.post<Doctor>(`/api/doctors/${doctorId}/patients/${patientId}`).then(r => r.data)

export const removePatientFromDoctor = (doctorId: string, patientId: string) =>
  api.delete<Doctor>(`/api/doctors/${doctorId}/patients/${patientId}`).then(r => r.data)

// ── Vision scan ───────────────────────────────────────────────────────────────
export const runScan = async (
  patientId: string,
  file: File | null,
): Promise<AnalysisResult> => {
  const form = new FormData()
  form.append('patient_id', patientId)
  if (file) form.append('file', file)
  const r = await api.post<AnalysisResult>('/api/scan/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return r.data
}

// ── Save a scan ───────────────────────────────────────────────────────────────
export const saveScan = (
  patientId: string,
  data: { area_cm2: number; ryb_ratios: { red: number; yellow: number; black: number } },
) => api.post<AnalysisResult>(`/api/patients/${patientId}/scan`, data).then(r => r.data)
