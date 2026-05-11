import { Injectable } from '@angular/core';
import { BehaviorSubject, ReplaySubject } from 'rxjs';
import { ConversationTurn, EvalResult, Question, TraceEvent, Metrics, ScoutingResult } from '../models';

export type AppState = 'LANDING' | 'INTERVIEW' | 'SCOUTING' | 'RESULT' | 'TIME_TRAVEL_INTERVIEW';

@Injectable({
  providedIn: 'root'
})
export class StateService {
  private appStateSub = new BehaviorSubject<AppState>('LANDING');
  private historySub = new BehaviorSubject<ConversationTurn[]>([]);
  private activeQuestionSub = new BehaviorSubject<Question | null>(null);
  private tracesSub = new BehaviorSubject<TraceEvent[]>([]);
  private resultSub = new BehaviorSubject<ScoutingResult | null>(null);
  private evalResultSub = new BehaviorSubject<EvalResult | null>(null);
  private loadingSub = new BehaviorSubject<boolean>(false);
  private metricsSetSub = new BehaviorSubject<boolean>(false);
  private narrativeBridgeSub = new BehaviorSubject<string | null>(null);
  private traveledYearSub = new BehaviorSubject<number | null>(null);

  /** Unique session ID — regenerated on every new interview so ADK session state never bleeds across runs. */
  sessionId: string = crypto.randomUUID();

  /** User-entered physical metrics, populated during the interview. */
  metrics: Metrics = {
    height: null,
    weight: null,
    birthYear: null
  };

  /** The Games year the user is currently time-traveling to, or null if not in time travel mode. */
  activeEraYear: number | null = null;

  /** True once the user has dismissed or engaged with the timeline banner — never shows again. */
  timelineBannerDismissed = false;

  /** The Games year of the most recently displayed time travel result (for era banner in report). */
  traveledYear: number | null = null;

  /** Era-specific answers accumulated across time travel jumps. Maps year → user's answer summary. */
  private eraHistoryMap: Map<number, string> = new Map();

  /** Cache of completed era scout results. Maps year → {result, evalResult}. */
  private eraResultCache = new Map<number, { result: ScoutingResult; evalResult: EvalResult | null }>();

  /** Tracks the last era year that completed a scout (for linking the subsequent eval to the cache). */
  private lastCompletedEraYear: number | null = null;

  /** Structured context summary the narrator emits when the era interview is complete. */
  eraContextSummary: any = null;

  private visitedYearsSub = new BehaviorSubject<Set<number>>(new Set());
  private eraReadyToScoutSub = new ReplaySubject<void>(1);

  // ── Public Observables ──
  appState$   = this.appStateSub.asObservable();
  history$    = this.historySub.asObservable();
  activeQuestion$ = this.activeQuestionSub.asObservable();
  traces$     = this.tracesSub.asObservable();
  result$     = this.resultSub.asObservable();
  evalResult$ = this.evalResultSub.asObservable();
  loading$    = this.loadingSub.asObservable();
  metricsSet$ = this.metricsSetSub.asObservable();
  narrativeBridge$ = this.narrativeBridgeSub.asObservable();
  traveledYear$   = this.traveledYearSub.asObservable();
  visitedYears$   = this.visitedYearsSub.asObservable();
  eraReadyToScout$ = this.eraReadyToScoutSub.asObservable();

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
    const optionsText = question.options?.length
      ? `\nOptions: [${question.options.join(' | ')}]`
      : '';
    this.addTurn({ role: 'narrator', content: question.question + optionsText });
  }

  setResult(result: ScoutingResult) {
    const eraYear = this.activeEraYear; // capture before clearing
    // Atomic Clear: Remove all interview context when result arrives.
    this.activeQuestionSub.next(null);
    this.loadingSub.next(false);
    this.narrativeBridgeSub.next(null);
    this.evalResultSub.next(null);
    this.activeEraYear = null;
    this.resultSub.next(result);
    // Cache era results for instant replay on revisit
    if (eraYear !== null) {
      this.lastCompletedEraYear = eraYear;
      this.eraResultCache.set(eraYear, { result, evalResult: null });
      this.visitedYearsSub.next(new Set(this.eraResultCache.keys()));
    }
  }

  setEvalResult(eval_result: EvalResult) {
    this.evalResultSub.next(eval_result);
    if (this.lastCompletedEraYear !== null) {
      const cached = this.eraResultCache.get(this.lastCompletedEraYear);
      if (cached) cached.evalResult = eval_result;
      this.lastCompletedEraYear = null;
    }
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
    this.evalResultSub.next(null);
    this.loadingSub.next(false);
    this.metricsSetSub.next(false);
    this.narrativeBridgeSub.next(null);
    this.metrics = { height: null, weight: null, birthYear: null, gender: null };
    this.activeEraYear = null;
    this.traveledYear = null;
    this.traveledYearSub.next(null);
    this.timelineBannerDismissed = false;
    this.eraHistoryMap.clear();
    this.eraResultCache.clear();
    this.visitedYearsSub.next(new Set());
    this.lastCompletedEraYear = null;
    this.eraContextSummary = null;
    this.sessionId = crypto.randomUUID();
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

  // ── Time Travel ──

  setActiveEraYear(year: number | null) {
    this.activeEraYear = year;
    if (year !== null) {
      this.traveledYear = year;
      this.traveledYearSub.next(year);
    }
  }

  saveEraAnswer(year: number, answerSummary: string) {
    const existing = this.eraHistoryMap.get(year);
    this.eraHistoryMap.set(year, existing ? `${existing} | ${answerSummary}` : answerSummary);
  }

  /** Returns era history as a plain object for JSON serialization in the POST body. */
  getEraHistory(): Record<number, string> | null {
    if (this.eraHistoryMap.size === 0) return null;
    const obj: Record<number, string> = {};
    this.eraHistoryMap.forEach((summary, year) => { obj[year] = summary; });
    return obj;
  }

  hasVisitedYear(year: number): boolean {
    return this.eraResultCache.has(year);
  }

  /** Instantly restore a previously generated era report without a backend call. */
  restoreFromCache(year: number): boolean {
    const cached = this.eraResultCache.get(year);
    if (!cached) return false;
    this.traveledYear = year;
    this.traveledYearSub.next(year);
    this.activeQuestionSub.next(null);
    this.loadingSub.next(false);
    this.narrativeBridgeSub.next(null);
    this.evalResultSub.next(null);
    this.activeEraYear = null;
    this.resultSub.next(cached.result);
    if (cached.evalResult) this.evalResultSub.next(cached.evalResult);
    this.appStateSub.next('RESULT');
    return true;
  }

  /** Called by stream service when narrator signals the era interview is complete. */
  signalEraReadyToScout(contextSummary: any) {
    this.eraContextSummary = contextSummary;
    this.eraReadyToScoutSub.next();
  }
}
