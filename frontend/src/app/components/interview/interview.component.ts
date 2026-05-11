import { Component, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { StateService } from '../../services/state.service';
import { StreamService } from '../../services/stream.service';
import { MultiChoiceComponent } from './multi-choice.component';
import { TextInputComponent } from './text-input.component';
import { MetricsComponent } from './metrics.component';
import { FactRotatorComponent } from '../fact-rotator.component';

@Component({
  selector: 'app-interview',
  standalone: true,
  imports: [CommonModule, MultiChoiceComponent, TextInputComponent, MetricsComponent, FactRotatorComponent],
  template: `
    <div class="interview-wrap animate-fade-in-up">

      <!-- ── TIME TRAVEL ERA BANNER ── -->
      <div class="era-banner animate-fade-in" *ngIf="activeEraYear">
        <div class="era-icon">⏳</div>
        <div class="era-text">
          <span class="era-label">TIME TRAVEL ACTIVE</span>
          <span class="era-destination">The {{ activeEraYear }} Games · Age {{ ageAtEra }}</span>
        </div>
        <span class="era-stage" [style.color]="eraStageColor">{{ eraStageLabel }}</span>
      </div>

      <!-- ── STEP 1: Physical Metrics ── -->
      <div class="interview-card glass-card-elevated" *ngIf="!(metricsSet$ | async)">
        <app-metrics (completed)="startNarrative()"></app-metrics>
      </div>

      <!-- ── LOADING STATE (both initial connect and between questions) ── -->
      <div class="narrator-loading animate-fade-in"
           *ngIf="(metricsSet$ | async) && (loading$ | async)">
        <div class="narrator-spinner"></div>
        <h2 class="narrator-loading-title">Crafting Your Story</h2>
        <p class="narrator-loading-sub">Agent Active</p>
        <app-fact-rotator></app-fact-rotator>
      </div>

      <!-- ── STEP 2: The Interview Loop ── -->
      <div class="interview-card glass-card-elevated"
           *ngIf="(metricsSet$ | async) && !(loading$ | async) && (activeQuestion$ | async) as q">

        <!-- Narrator Feedback -->
        <div class="feedback-bar" *ngIf="q.feedback">
          <span class="feedback-icon">💬</span>
          <p class="feedback-text">{{ q.feedback }}</p>
        </div>

        <!-- Question -->
        <h2 class="question-text animate-fade-in">{{ q.question }}</h2>

        <!-- Interactive Area -->
        <app-multi-choice
          *ngIf="q.options && q.options.length > 0"
          [options]="q.options"
          (selected)="onAnswer($event)">
        </app-multi-choice>

        <app-text-input
          *ngIf="!q.options || q.options.length === 0"
          (submitted)="onAnswer($event)">
        </app-text-input>

        <!-- Ready CTA — only shown when narrator has enough context -->
        <div class="ready-divider" *ngIf="q.readyToProceed">
          <span class="divider-line"></span>
          <span class="divider-label">or</span>
          <span class="divider-line"></span>
        </div>
        <button
          class="btn-ready"
          *ngIf="q.readyToProceed"
          (click)="onReadyToScout()">
          Show me my results →
        </button>

        <!-- Disclaimer -->
        <p class="card-disclaimer">
          This assessment is for entertainment and archetypal analysis only.
          Not medical or professional athletic advice.
        </p>
      </div>
    </div>
  `,
  styles: [`
    .interview-wrap {
      width: 100%;
      max-width: 700px;
      padding: 2rem;
    }
    .interview-card {
      padding: 3rem;
    }

    /* ── Narrator Loading State (mirrors scouting phase structure) ── */
    .narrator-loading {
      text-align: center;
      padding: 4rem 2rem;
      width: 100%;
    }
    .narrator-spinner {
      width: 3rem;
      height: 3rem;
      border: 4px solid rgba(197, 164, 78, 0.15);
      border-top-color: #c5a44e;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin: 0 auto 1.5rem;
    }
    .narrator-loading-title {
      font-size: 1.3rem;
      font-weight: 900;
      color: white;
      text-transform: uppercase;
      letter-spacing: -0.02em;
      margin-bottom: 0.5rem;
    }
    .narrator-loading-sub {
      font-size: 0.625rem;
      color: rgba(212, 185, 94, 0.5);
      font-weight: 700;
      letter-spacing: 0.4em;
      text-transform: uppercase;
      margin-bottom: 0;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* ── Feedback Bar ── */
    .feedback-bar {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      margin-bottom: 2rem;
      padding: 1rem 1.25rem;
      background: rgba(197, 164, 78, 0.08);
      border-left: 3px solid #c5a44e;
      border-radius: 0 0.75rem 0.75rem 0;
    }
    .feedback-icon { font-size: 1.2rem; flex-shrink: 0; margin-top: 2px; }
    .feedback-text {
      color: #e3ce6f;
      font-size: 0.95rem;
      font-weight: 500;
      line-height: 1.5;
      margin: 0;
    }

    /* ── Question Text ── */
    .question-text {
      font-size: 1.5rem;
      font-weight: 800;
      color: white;
      line-height: 1.4;
      margin-bottom: 2rem;
    }

    /* ── Ready CTA ── */
    .ready-divider {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin: 1.5rem 0 1rem;
    }
    .divider-line {
      flex: 1;
      height: 1px;
      background: rgba(255,255,255,0.07);
    }
    .divider-label {
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      color: rgba(255,255,255,0.2);
      text-transform: uppercase;
    }
    .btn-ready {
      width: 100%;
      padding: 0.9rem 1.5rem;
      background: transparent;
      border: 1px solid rgba(197, 164, 78, 0.35);
      border-radius: 0.5rem;
      color: #c5a44e;
      font-size: 0.85rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      cursor: pointer;
      transition: all 0.2s ease;
      font-family: inherit;
    }
    .btn-ready:hover {
      background: rgba(197, 164, 78, 0.08);
      border-color: #c5a44e;
      box-shadow: 0 0 16px rgba(197, 164, 78, 0.15);
    }

    /* ── Disclaimer ── */
    .card-disclaimer {
      margin-top: 3rem;
      font-size: 0.6rem;
      color: rgba(255,255,255,0.2);
      text-align: center;
      line-height: 1.4;
      border-top: 1px solid rgba(255,255,255,0.06);
      padding-top: 1.5rem;
    }

    /* ── Era Banner ── */
    .era-banner {
      display: flex;
      align-items: center;
      gap: 0.85rem;
      padding: 0.85rem 1.25rem;
      margin-bottom: 1.25rem;
      background: linear-gradient(135deg, #c5a44e 0%, #e3ce6f 60%, #c5a44e 100%);
      border: none;
      border-radius: 0.75rem;
      box-shadow: 0 4px 20px rgba(197, 164, 78, 0.35);
    }
    .era-icon { font-size: 1.1rem; flex-shrink: 0; }
    .era-text {
      display: flex;
      flex-direction: column;
      gap: 0.1rem;
      flex: 1;
    }
    .era-label {
      font-size: 0.5rem;
      font-weight: 900;
      letter-spacing: 0.2em;
      color: rgba(0, 0, 0, 0.5);
    }
    .era-destination {
      font-size: 0.85rem;
      font-weight: 800;
      color: rgba(0, 0, 0, 0.85);
    }
    .era-stage {
      font-size: 0.55rem;
      font-weight: 900;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      flex-shrink: 0;
      color: rgba(0, 0, 0, 0.6) !important;
    }
  `]
})
export class InterviewComponent implements OnDestroy {
  private state = inject(StateService);
  private stream = inject(StreamService);

  activeQuestion$ = this.state.activeQuestion$;
  metricsSet$ = this.state.metricsSet$;
  loading$ = this.state.loading$;
  private sub?: Subscription;

  get activeEraYear(): number | null { return this.state.activeEraYear; }

  get ageAtEra(): number | null {
    if (!this.state.activeEraYear || !this.state.metrics.birthYear) return null;
    return this.state.activeEraYear - this.state.metrics.birthYear;
  }

  get eraStageLabel(): string {
    const age = this.ageAtEra;
    if (age === null) return '';
    if (age < 20) return 'Rising Star';
    if (age <= 32) return 'Elite Peak';
    if (age <= 45) return 'Veteran';
    return 'Legacy';
  }

  get eraStageColor(): string {
    const age = this.ageAtEra;
    if (age === null) return '#c5a44e';
    if (age < 20) return '#34d399';
    if (age <= 32) return '#facc15';
    if (age <= 45) return '#60a5fa';
    return '#a78bfa';
  }

  startNarrative() {
    this.sub?.unsubscribe();
    this.state.setLoading(true);
    const g = this.state.metrics.gender;
    this.state.addUserTrace(
      `I'm ${this.state.metrics.height}cm, ${this.state.metrics.weight}kg, born ${this.state.metrics.birthYear}${g ? `, gender: ${g}` : ''}.`
    );
    const body = {
      story: 'Initial metrics provided.',
      session_id: this.state.sessionId,
      height_cm: this.state.metrics.height,
      weight_kg: this.state.metrics.weight,
      birth_year: this.state.metrics.birthYear,
      gender: g || null,
      conversation_history: [],
      is_ready_to_scout: false
    };

    this.sub = this.stream.consume(body).subscribe({
      complete: () => this.state.setLoading(false),
      error: () => this.state.setLoading(false)
    });
  }

  onAnswer(answer: string) {
    this.sub?.unsubscribe();
    this.state.setLoading(true);
    this.state.addTurn({ role: 'user', content: answer });

    const eraYear = this.state.activeEraYear;

    if (eraYear !== null) {
      // ── Time Travel mode: any answer triggers a full re-scout with age override ──
      const shortAnswer = answer.length > 120 ? answer.substring(0, 120) + '…' : answer;
      this.state.addUserTrace(`My answer for The ${eraYear} Games: "${shortAnswer}"`);
      this.state.saveEraAnswer(eraYear, shortAnswer);
      this.state.setActiveEraYear(null);
      this.state.setAppState('SCOUTING');

      const body = {
        story: answer,
        session_id: this.state.sessionId,
        height_cm: this.state.metrics.height,
        weight_kg: this.state.metrics.weight,
        birth_year: this.state.metrics.birthYear,
        gender: this.state.metrics.gender || null,
        conversation_history: this.state.getHistory(),
        is_ready_to_scout: true,
        target_game_year: eraYear,
        era_history: this.state.getEraHistory()
      };

      this.sub = this.stream.consume(body).subscribe({
        complete: () => this.state.setLoading(false),
        error: () => { this.state.setLoading(false); this.state.setAppState('RESULT'); }
      });
      return;
    }

    // ── Normal interview answer ──
    const label = answer.length > 80 ? answer.substring(0, 80) + '…' : answer;
    this.state.addUserTrace(`I chose: "${label}"`);

    const body = {
      story: answer,
      session_id: this.state.sessionId,
      height_cm: this.state.metrics.height,
      weight_kg: this.state.metrics.weight,
      birth_year: this.state.metrics.birthYear,
      gender: this.state.metrics.gender || null,
      conversation_history: this.state.getHistory(),
      is_ready_to_scout: false
    };

    this.sub = this.stream.consume(body).subscribe({
      complete: () => this.state.setLoading(false),
      error: () => this.state.setLoading(false)
    });
  }

  onReadyToScout() {
    this.sub?.unsubscribe();
    this.state.setLoading(true);
    this.state.addUserTrace("I'm ready — show me my results.");

    const eraYear = this.state.activeEraYear;
    if (eraYear !== null) {
      this.state.setActiveEraYear(null);
    }

    const body: any = {
      story: '',
      session_id: this.state.sessionId,
      height_cm: this.state.metrics.height,
      weight_kg: this.state.metrics.weight,
      birth_year: this.state.metrics.birthYear,
      gender: this.state.metrics.gender || null,
      conversation_history: this.state.getHistory(),
      is_ready_to_scout: true
    };

    if (eraYear !== null) {
      body['target_game_year'] = eraYear;
      body['era_history'] = this.state.getEraHistory();
    }

    this.sub = this.stream.consume(body).subscribe({
      complete: () => this.state.setLoading(false),
      error: () => this.state.setLoading(false)
    });
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }
}
