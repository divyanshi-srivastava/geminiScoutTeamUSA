import { Component, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { StateService } from '../../services/state.service';
import { StreamService } from '../../services/stream.service';
import { MultiChoiceComponent } from './multi-choice.component';
import { TextInputComponent } from './text-input.component';
import { MetricsComponent } from './metrics.component';

@Component({
  selector: 'app-interview',
  standalone: true,
  imports: [CommonModule, MultiChoiceComponent, TextInputComponent, MetricsComponent],
  template: `
    <div class="interview-wrap animate-fade-in-up">
      
      <!-- ── STEP 1: Physical Metrics ── -->
      <div class="interview-card glass-card-elevated" *ngIf="!(metricsSet$ | async)">
        <app-metrics (completed)="startNarrative()"></app-metrics>
      </div>

      <!-- ── NARRATIVE BRIDGE (Transition State) ── -->
      <div class="interview-card glass-card-elevated narrative-bridge animate-fade-in"
           *ngIf="(narrativeBridge$ | async) as bridge">
        <div class="bridge-icon">🏟️</div>
        <h2 class="bridge-title text-gradient-gold">The Narrator is crafting your legacy…</h2>
        <p class="bridge-text">{{ bridge }}</p>
        <div class="bridge-pulse">
          <div class="dot-pulse"></div>
        </div>
      </div>

      <!-- ── STEP 2: The Interview Loop ── -->
      <div class="interview-card glass-card-elevated"
           *ngIf="!(narrativeBridge$ | async) && (metricsSet$ | async) && (activeQuestion$ | async) as q">
        
        <!-- Narrator Feedback -->
        <div class="feedback-bar" *ngIf="q.feedback">
          <span class="feedback-icon">💬</span>
          <p class="feedback-text">{{ q.feedback }}</p>
        </div>

        <!-- Question -->
        <h2 class="question-text animate-fade-in">{{ q.question }}</h2>

        <!-- Interactive Area -->
        <div *ngIf="!(loading$ | async)">
          <app-multi-choice
            *ngIf="q.options && q.options.length > 0"
            [options]="q.options"
            (selected)="onAnswer($event)">
          </app-multi-choice>

          <app-text-input
            *ngIf="!q.options || q.options.length === 0"
            (submitted)="onAnswer($event)">
          </app-text-input>
        </div>

        <!-- Loading Indicator -->
        <div *ngIf="loading$ | async" class="loading-block">
          <div class="dot-pulse"></div>
          <span>The Narrator is thinking…</span>
        </div>

        <!-- Disclaimer -->
        <p class="card-disclaimer">
          This assessment is for entertainment and archetypal analysis only.
          Not medical or professional athletic advice.
        </p>
      </div>

      <!-- Initial Loading State (after metrics, before first question) -->
      <div class="interview-card glass-card-elevated"
           *ngIf="!(narrativeBridge$ | async) && (metricsSet$ | async) && !(activeQuestion$ | async) && (loading$ | async)">
        <div class="loading-block">
          <div class="dot-pulse"></div>
          <span>Connecting to the Narrator Agent…</span>
        </div>
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

    /* ── Narrative Bridge (Transition) ── */
    .narrative-bridge {
      text-align: center;
      padding: 4rem 3rem;
    }
    .bridge-icon {
      font-size: 3rem;
      margin-bottom: 1.5rem;
    }
    .bridge-title {
      font-size: 1.4rem;
      font-weight: 900;
      margin-bottom: 2rem;
    }
    .bridge-text {
      color: rgba(255,255,255,0.65);
      font-size: 0.95rem;
      line-height: 1.7;
      max-width: 500px;
      margin: 0 auto 2rem;
    }
    .bridge-pulse {
      display: flex;
      justify-content: center;
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

    /* ── Loading ── */
    .loading-block {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1.25rem;
      padding: 3rem 0;
      color: rgba(255,255,255,0.4);
      font-size: 0.85rem;
    }
    .dot-pulse {
      width: 10px; height: 10px;
      background: #c5a44e;
      border-radius: 50%;
      animation: pulse 1.2s ease-in-out infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 0.3; transform: scale(1); }
      50% { opacity: 1; transform: scale(1.5); }
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
  `]
})
export class InterviewComponent implements OnDestroy {
  private state = inject(StateService);
  private stream = inject(StreamService);

  activeQuestion$ = this.state.activeQuestion$;
  metricsSet$ = this.state.metricsSet$;
  loading$ = this.state.loading$;
  narrativeBridge$ = this.state.narrativeBridge$;
  private sub?: Subscription;

  startNarrative() {
    this.sub?.unsubscribe();
    this.state.setLoading(true);
    this.state.addUserTrace(
      `Submitted physical stats — Height: ${this.state.metrics.height}cm, Weight: ${this.state.metrics.weight}kg, Born: ${this.state.metrics.birthYear}`
    );
    const body = {
      story: 'Initial metrics provided.',
      height_cm: this.state.metrics.height,
      weight_kg: this.state.metrics.weight,
      birth_year: this.state.metrics.birthYear,
      conversation_history: [],
      is_ready_to_scout: false
    };

    this.sub = this.stream.consume(body).subscribe({
      complete: () => this.state.setLoading(false),
      error: ()   => this.state.setLoading(false)
    });
  }

  onAnswer(answer: string) {
    this.sub?.unsubscribe();
    this.state.setLoading(true);
    this.state.addTurn({ role: 'user', content: answer });

    const isReady = answer.trim().startsWith('[READY]');
    const traceLabel = isReady
      ? 'Ready to see results — triggering full scouting pipeline'
      : `Selected: "${answer.length > 80 ? answer.substring(0, 80) + '…' : answer}"`;
    this.state.addUserTrace(traceLabel);

    const body = {
      story: answer,
      height_cm: this.state.metrics.height,
      weight_kg: this.state.metrics.weight,
      birth_year: this.state.metrics.birthYear,
      conversation_history: this.state.getHistory(),
      is_ready_to_scout: isReady
    };

    this.sub = this.stream.consume(body).subscribe({
      complete: () => this.state.setLoading(false),
      error: ()   => this.state.setLoading(false)
    });
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }
}
