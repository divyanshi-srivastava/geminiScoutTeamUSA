import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { ConversationTurn, Question, TraceEvent, Metrics, ScoutingResult } from '../models';

export type AppState = 'LANDING' | 'INTERVIEW' | 'SCOUTING' | 'RESULT';

@Injectable({
  providedIn: 'root'
})
export class StateService {
  private appStateSub = new BehaviorSubject<AppState>('LANDING');
  private historySub = new BehaviorSubject<ConversationTurn[]>([]);
  private activeQuestionSub = new BehaviorSubject<Question | null>(null);
  private tracesSub = new BehaviorSubject<TraceEvent[]>([]);
  private resultSub = new BehaviorSubject<ScoutingResult | null>(null);
  private loadingSub = new BehaviorSubject<boolean>(false);
  private metricsSetSub = new BehaviorSubject<boolean>(false);
  private narrativeBridgeSub = new BehaviorSubject<string | null>(null);

  /** User-entered physical metrics, populated during the interview. */
  metrics: Metrics = {
    height: null,
    weight: null,
    birthYear: null
  };

  // ── Public Observables ──
  appState$   = this.appStateSub.asObservable();
  history$    = this.historySub.asObservable();
  activeQuestion$ = this.activeQuestionSub.asObservable();
  traces$     = this.tracesSub.asObservable();
  result$     = this.resultSub.asObservable();
  loading$    = this.loadingSub.asObservable();
  metricsSet$ = this.metricsSetSub.asObservable();
  narrativeBridge$ = this.narrativeBridgeSub.asObservable();

  // ── Mutations ──
  setAppState(state: AppState) {
    this.appStateSub.next(state);
  }

  setLoading(val: boolean) {
    this.loadingSub.next(val);
  }

  addTurn(turn: ConversationTurn) {
    const current = this.historySub.value;
    this.historySub.next([...current, turn]);
  }

  setActiveQuestion(question: Question) {
    this.activeQuestionSub.next(question);
    // Record the narrator's question in conversation history
    this.addTurn({ role: 'narrator', content: question.question });
  }

  setResult(result: ScoutingResult) {
    // Atomic Clear: Remove all interview context when result arrives.
    this.activeQuestionSub.next(null);
    this.loadingSub.next(false);
    this.narrativeBridgeSub.next(null);
    this.resultSub.next(result);
  }

  clearTraces() {
    this.tracesSub.next([]);
  }

  addUserTrace(detail: string) {
    this.addTrace({
      type: 'trace',
      agent: 'user',
      event: 'UserAction',
      timestamp: new Date().toLocaleTimeString(),
      detail
    });
  }

  addTrace(trace: TraceEvent) {
    const current = this.tracesSub.value;
    this.tracesSub.next([...current, trace]);
  }

  reset() {
    this.appStateSub.next('LANDING');
    this.historySub.next([]);
    this.activeQuestionSub.next(null);
    this.tracesSub.next([]);
    this.resultSub.next(null);
    this.loadingSub.next(false);
    this.metricsSetSub.next(false);
    this.narrativeBridgeSub.next(null);
    this.metrics = { height: null, weight: null, birthYear: null };
  }

  setMetrics(data: Metrics) {
    this.metrics = data;
    this.metricsSetSub.next(true);
  }

  setNarrativeBridge(text: string | null) {
    this.narrativeBridgeSub.next(text);
  }

  /** Snapshot for building the next POST body. */
  getHistory(): ConversationTurn[] {
    return this.historySub.value;
  }
}
