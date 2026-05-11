/** ═══ CORE APPLICATION MODELS ═══ **/

export interface Agent {
  id: string;
  name: string;
  role: 'supervisor' | 'scout' | 'narrator' | 'compliance' | 'logger';
  avatar?: string;
}

export interface TraceEvent {
  type: 'trace' | 'interview' | 'result' | 'error';
  agent: string;
  event: string;
  timestamp: string;
  detail?: string;
  before?: string;
  after?: string;
}

export interface Profile {
  matched_profile_id: number;
  matched_profile_name: string;
  scout_verdict: string;
  life_stage?: 'Rising Star' | 'Elite Peak' | 'Veteran' | 'Legacy Coach';
  /** Olympic discipline, e.g. "Elite Swimming" */
  pathway_standing?: string;
  /** Paralympic discipline, e.g. "Elite Adaptive Swimming" */
  pathway_adaptive?: string;
}

/** The comprehensive result of the scouting pipeline */
export interface ScoutingResult {
  olympic: Profile;
  paralympic: Profile;
  overall_narrative?: string;
}

export interface Question {
  type?: string;
  feedback?: string;
  question: string;
  options: string[];
  readyToProceed?: boolean;
}

export interface ConversationTurn {
  role: 'narrator' | 'user';
  content: string;
}

export interface Metrics {
  height: number | null;
  weight: number | null;
  birthYear: number | null;
  gender?: 'M' | 'F' | null;
}

/** Specific Chunk Types for SSE Streaming */

export interface TraceChunk extends TraceEvent {
  type: 'trace';
}

export interface InterviewChunk {
  type: 'interview';
  response: string;
}

export interface ResultChunk {
  type: 'result';
  response: string;
}

export interface ErrorChunk {
  type: 'error';
  detail: string;
}

/** Structured evaluation from the Eval Agent ("The Authenticator") */
export interface EvalDimension {
  score: number;
  reasoning: string;
}

export interface EvalResult {
  overall: number;
  summary: string;
  authenticity: EvalDimension;
  personalization: EvalDimension;
  distinctness: EvalDimension;
  life_stage_coherence?: EvalDimension;
  interview_quality?: EvalDimension;
  compliance: { passed: boolean; note: string };
}

export interface EvalChunk {
  type: 'eval';
  result: EvalResult;
}

export type ScoutChunk = TraceChunk | InterviewChunk | ResultChunk | ErrorChunk | EvalChunk;
