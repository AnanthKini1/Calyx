export type Priority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'OK'

export interface WoundScan {
  date: string
  area_cm2: number
  ryb_ratios: { red: number; yellow: number; black: number }
}

export interface Patient {
  patient_id: string
  role: 'patient'
  name: string
  email: string
  age: number
  comorbidities: string[]
  blood_glucose: number
  serum_albumin: number
  mobility_score: number
  post_op_day: number
  doctor_id?: string
  wound_history: WoundScan[]
}

export interface Doctor {
  doctor_id: string
  role: 'doctor'
  name: string
  email: string
  specialty: string
  patient_ids: string[]
}

export type User = Patient | Doctor

export interface AnalysisResult {
  priority: Priority
  alerts: string[]
  reasoning: string
  active_risk_factors: string[]
  recommended_action: string
  area_cm2: number
  area_delta: number
  ryb_ratios: { red: number; yellow: number; black: number }
  scan_date: string
  annotated_image_b64?: string
  coin_found?: boolean
}

export interface PatientWithSummary extends Patient {
  latest_summary: {
    priority: Priority
    area_cm2: number
    area_delta: number
    ryb_ratios: { red: number; yellow: number; black: number }
    scan_date: string
    alerts: string[]
  } | null
}
