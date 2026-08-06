export interface User {
  id: number;
  username: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface DailySummary {
  date: string;
  good_posture_seconds: number;
  mild_slouch_seconds: number;
  severe_slouch_seconds: number;
  total_tracked_seconds: number;
  good_posture_count: number;
  mild_slouch_count: number;
  severe_slouch_count: number;
  good_posture_percent: number;
  bad_posture_percent: number;
  bad_posture_seconds: number;
  avg_neck_angle?: number | null;
  avg_back_angle?: number | null;
}

export interface LiveSessionSnapshot {
  timestamp: string;
  current_posture_label: string;
  neck_angle: number | null;
  back_angle: number | null;
  good_posture_percent: number;
  bad_posture_percent: number;
  bad_posture_seconds: number;
  good_posture_seconds: number;
  mild_slouch_seconds: number;
  severe_slouch_seconds: number;
  total_tracked_seconds: number;
  good_posture_count: number;
  mild_slouch_count: number;
  severe_slouch_count: number;
}

export interface CalibrationResponse {
  neck_angle: number;
  back_angle: number;
}

export interface AnalysisResponse {
  posture_label: string;
  neck_angle: number | null;
  back_angle: number | null;
  show_warning: boolean;
  warning_message: string | null;
  show_break: boolean;
  break_message: string | null;
  show_fatigue: boolean;
  fatigue_message: string | null;
  calibration_message: string | null;
}

export interface ReportResponse {
  ergonomic_score: number;
  posture_summary: string;
  recommendations: string[];
}
