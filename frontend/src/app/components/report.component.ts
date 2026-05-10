import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StateService } from '../services/state.service';
import { EvalResult, ScoutingResult } from '../models';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-report',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="report-container animate-fade-in-up" *ngIf="view$ | async as v">

      <!-- ── ERA BANNER (Time Travel only) ── -->
      <div class="era-result-banner animate-fade-in" *ngIf="traveledYear">
        <span class="era-pill" [style.borderColor]="eraColor" [style.color]="eraColor">
          ⏳ THE {{ traveledYear }} GAMES · AGE {{ ageAtTraveledYear }} · {{ eraStageLabel }}
        </span>
      </div>

      <!-- ── SCOUT VERDICT (Human Narrative Only) ── -->
      <header class="verdict-summary glass-card">
        <span class="summary-label">SCOUT VERDICT</span>
        <p class="summary-text">{{ v.summaryVerdict }}</p>
      </header>

      <!-- ── PATHWAY CARDS (Visual / No Prose) ── -->
      <div class="archetypes-grid">

        <div class="archetype-card glass-card-elevated">
          <div class="card-type-label">ELITE SPORT PATHWAY</div>
          <div class="card-body">
            <h2 class="archetype-name text-gradient-usa">
              {{ v.olympic.matched_profile_name }}
            </h2>
            <p class="pathway-discipline" *ngIf="v.olympicPathway">
              {{ v.olympicPathway }}
            </p>
          </div>
        </div>

        <div class="archetype-card glass-card-elevated">
          <div class="card-type-label">ADAPTIVE SPORT PATHWAY</div>
          <div class="card-body">
            <h2 class="archetype-name text-gradient-usa">
              {{ v.paralympic.matched_profile_name }}
            </h2>
            <p class="pathway-discipline" *ngIf="v.paralympicPathway">
              {{ v.paralympicPathway }}
            </p>
          </div>
        </div>

      </div>

      <!-- ── ANALYSIS VAULT ── -->
      <div class="vault-section">
        <button class="vault-toggle" (click)="toggleVault()">
          <div class="vault-toggle-left">
            <span class="vault-icon">{{ vaultOpen ? '▲' : '▼' }}</span>
            <div class="vault-toggle-text">
              <span class="vault-title">PIPELINE ANALYSIS</span>
              <span class="vault-subtitle">Technical orchestration · Agent reasoning · Evaluation scores</span>
            </div>
          </div>
          <span class="vault-badge" *ngIf="evalResult$ | async as ev">
            <span class="vault-badge-score" [style.color]="scoreColor(ev.overall)">{{ ev.overall }}</span>
            <span class="vault-badge-label">/ 10</span>
          </span>
          <span class="vault-badge vault-badge-pending" *ngIf="!(evalResult$ | async)">
            SCORING…
          </span>
        </button>

        <div class="vault-body" [class.open]="vaultOpen">
          <div class="vault-card">

            <!-- ── STANDING PATHWAY ── -->
            <div class="section-label">STANDING PATHWAY — FULL ANALYSIS</div>
            <p class="analysis-text">{{ v.standingAnalysis }}</p>

            <div class="section-divider"></div>

            <!-- ── ADAPTIVE PATHWAY ── -->
            <div class="section-label">ADAPTIVE PATHWAY — FULL ANALYSIS</div>
            <p class="analysis-text">{{ v.adaptiveAnalysis }}</p>

            <div class="section-divider"></div>

            <!-- ── AUTHENTICATOR SCORE (below analysis) ── -->
            <ng-container *ngIf="evalResult$ | async as ev; else evalPending">
              <div class="eval-header-row">
                <span class="section-label">AUTHENTICATOR SCORE</span>
                <div class="overall-score-block">
                  <span class="overall-number" [style.color]="scoreColor(ev.overall)">{{ ev.overall }}</span>
                  <span class="overall-denom">/10</span>
                </div>
              </div>
              <p class="eval-summary">{{ ev.summary }}</p>

              <div class="score-grid">
                <div class="score-row" *ngFor="let dim of evalDimensions(ev)">
                  <div class="score-row-top">
                    <span class="score-dim-label">{{ dim.label }}</span>
                    <span class="score-value" [style.color]="scoreColor(dim.score)">{{ dim.score }}<span class="score-denom">/10</span></span>
                  </div>
                  <div class="score-bar-track">
                    <div class="score-bar-fill" [style.width.%]="dim.score * 10" [style.background]="scoreColor(dim.score)"></div>
                  </div>
                  <p class="score-reasoning">{{ dim.reasoning }}</p>
                </div>

                <div class="score-row">
                  <div class="score-row-top">
                    <span class="score-dim-label">COMPLIANCE</span>
                    <span class="compliance-badge" [class.pass]="ev.compliance.passed" [class.fail]="!ev.compliance.passed">
                      {{ ev.compliance.passed ? 'PASSED' : 'FAILED' }}
                    </span>
                  </div>
                  <p class="score-reasoning">{{ ev.compliance.note }}</p>
                </div>
              </div>
            </ng-container>

            <ng-template #evalPending>
              <div class="eval-header-row">
                <span class="section-label">AUTHENTICATOR SCORE</span>
              </div>
              <div class="eval-pending-body">
                <div class="dot-pulse"></div>
                <span>The Authenticator is evaluating archetype quality…</span>
              </div>
            </ng-template>

            <div class="section-divider"></div>

            <!-- ── PIPELINE FOOTER ── -->
            <div class="footer-row">
              <span class="footer-chip">supervisor_agent</span>
              <span class="footer-arrow">→</span>
              <span class="footer-chip">scout_agent</span>
              <span class="footer-arrow">→</span>
              <span class="footer-chip">narrator_agent</span>
              <span class="footer-arrow">→</span>
              <span class="footer-chip">compliance_agent</span>
              <span class="footer-arrow">→</span>
              <span class="footer-chip footer-chip-gold">eval_agent</span>
            </div>
            <p class="footer-note">Physical profile matched via Euclidean distance across 12 archetype centroids. Agent trace &amp; SSE events logged in Mission Control sidebar.</p>

          </div>
        </div>
      </div>

      <div class="action-row">
        <button class="btn-gold restart-btn" (click)="restart()">
          START A NEW JOURNEY
        </button>
      </div>

    </div>
  `,
  styles: [`
    .report-container {
      max-width: 1100px;
      margin: 0 auto;
      padding: 2rem 0;
    }

    /* ── Era Result Banner ── */
    .era-result-banner {
      text-align: center;
      margin-bottom: 1.25rem;
    }
    .era-pill {
      display: inline-block;
      font-size: 0.6rem;
      font-weight: 900;
      letter-spacing: 0.2em;
      padding: 0.4rem 1.25rem;
      border-radius: 99px;
      border: 1px solid;
      background: rgba(255,255,255,0.03);
    }

    /* ── Scout Verdict Summary ── */
    .verdict-summary {
      text-align: center;
      padding: 2.5rem 3rem;
      margin-bottom: 2.5rem;
    }
    .summary-label {
      display: block;
      font-size: 0.6rem;
      font-weight: 900;
      letter-spacing: 0.4em;
      color: rgba(197, 164, 78, 0.5);
      text-transform: uppercase;
      margin-bottom: 1rem;
    }
    .summary-text {
      font-size: 1.05rem;
      color: rgba(255,255,255,0.75);
      line-height: 1.7;
      max-width: 720px;
      margin: 0 auto;
    }

    /* ── Pathway Cards ── */
    .archetypes-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2rem;
      margin-bottom: 2rem;
    }
    @media (max-width: 900px) {
      .archetypes-grid { grid-template-columns: 1fr; }
    }

    .archetype-card {
      padding: 3.5rem 2.5rem 2.5rem;
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .card-type-label {
      position: absolute;
      top: 1.25rem;
      left: 0;
      right: 0;
      text-align: center;
      font-size: 0.6rem;
      font-weight: 900;
      letter-spacing: 0.4em;
      color: rgba(255,255,255,0.25);
      text-transform: uppercase;
    }

    .card-body {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 0.85rem;
      width: 100%;
      padding-top: 0.5rem;
    }

    .archetype-name {
      font-size: clamp(1.5rem, 3vw, 2.25rem);
      font-weight: 900;
      letter-spacing: -0.02em;
      line-height: 1.1;
      margin: 0;
    }

    .pathway-discipline {
      font-size: 0.7rem;
      font-weight: 800;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: rgba(197, 164, 78, 0.6);
      margin: 0;
    }

    /* ── Analysis Vault ── */
    .vault-section {
      margin-bottom: 2.5rem;
    }

    .vault-toggle {
      width: 100%;
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1.25rem 1.75rem;
      background: rgba(255,255,255,0.02);
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 0.75rem;
      cursor: pointer;
      transition: background 0.2s;
      text-align: left;
      margin-bottom: 0.5rem;
    }
    .vault-toggle:hover { background: rgba(255,255,255,0.04); }

    .vault-toggle-left {
      display: flex;
      align-items: center;
      gap: 0.85rem;
      flex: 1;
    }
    .vault-icon {
      font-size: 0.6rem;
      color: rgba(255,255,255,0.3);
      flex-shrink: 0;
    }
    .vault-toggle-text {
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
    }
    .vault-title {
      font-size: 0.65rem;
      font-weight: 900;
      letter-spacing: 0.3em;
      color: rgba(255,255,255,0.7);
      text-transform: uppercase;
    }
    .vault-subtitle {
      font-size: 0.55rem;
      font-weight: 500;
      letter-spacing: 0.06em;
      color: rgba(255,255,255,0.3);
    }
    .vault-badge {
      display: flex;
      align-items: baseline;
      gap: 0.2rem;
      flex-shrink: 0;
    }
    .vault-badge-score {
      font-size: 1.5rem;
      font-weight: 900;
      line-height: 1;
    }
    .vault-badge-label {
      font-size: 0.65rem;
      font-weight: 700;
      color: rgba(255,255,255,0.3);
    }
    .vault-badge-pending {
      font-size: 0.5rem;
      font-weight: 900;
      letter-spacing: 0.2em;
      color: rgba(255,255,255,0.2);
    }

    /* ── Vault Body — single unified card ── */
    .vault-body {
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.6s ease;
    }
    .vault-body.open { max-height: 5000px; }

    .vault-card {
      background: rgba(255,255,255,0.02);
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 0.75rem;
      padding: 2rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }

    .section-label {
      font-size: 0.55rem;
      font-weight: 900;
      letter-spacing: 0.3em;
      text-transform: uppercase;
      color: rgba(197, 164, 78, 0.55);
      margin-bottom: 0.5rem;
      display: block;
    }

    .section-divider {
      border: none;
      border-top: 1px solid rgba(255,255,255,0.06);
    }

    .analysis-text {
      font-size: 0.85rem;
      line-height: 1.75;
      color: rgba(255,255,255,0.5);
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
    }

    /* ── Authenticator Score ── */
    .eval-header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .overall-score-block {
      display: flex;
      align-items: baseline;
      gap: 0.2rem;
    }
    .overall-number {
      font-size: 2.25rem;
      font-weight: 900;
      line-height: 1;
    }
    .overall-denom {
      font-size: 0.75rem;
      font-weight: 700;
      color: rgba(255,255,255,0.3);
    }
    .eval-summary {
      font-size: 0.9rem;
      color: rgba(255,255,255,0.65);
      line-height: 1.65;
      margin: 0;
    }

    /* ── Score rows (flat, no card borders) ── */
    .score-grid {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    .score-row {}
    .score-row-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 0.4rem;
    }
    .score-dim-label {
      font-size: 0.52rem;
      font-weight: 900;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: rgba(255,255,255,0.35);
    }
    .score-value {
      font-size: 1rem;
      font-weight: 900;
      line-height: 1;
    }
    .score-denom {
      font-size: 0.52rem;
      font-weight: 700;
      color: rgba(255,255,255,0.3);
      margin-left: 1px;
    }
    .score-bar-track {
      height: 2px;
      background: rgba(255,255,255,0.07);
      border-radius: 99px;
      margin-bottom: 0.5rem;
      overflow: hidden;
    }
    .score-bar-fill {
      height: 100%;
      border-radius: 99px;
      transition: width 0.8s ease;
      opacity: 0.65;
    }
    .score-reasoning {
      font-size: 0.78rem;
      color: rgba(255,255,255,0.45);
      line-height: 1.55;
      margin: 0;
    }

    .compliance-badge {
      font-size: 0.52rem;
      font-weight: 900;
      letter-spacing: 0.15em;
      padding: 0.2rem 0.65rem;
      border-radius: 99px;
    }
    .compliance-badge.pass {
      color: #4ade80;
      background: rgba(74, 222, 128, 0.08);
      border: 1px solid rgba(74, 222, 128, 0.2);
    }
    .compliance-badge.fail {
      color: #f87171;
      background: rgba(248, 113, 113, 0.08);
      border: 1px solid rgba(248, 113, 113, 0.2);
    }

    /* ── Eval Pending ── */
    .eval-pending-body {
      display: flex;
      align-items: center;
      gap: 1rem;
      color: rgba(255,255,255,0.35);
      font-size: 0.8rem;
    }

    /* ── Pipeline Footer ── */
    .footer-row {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .footer-chip {
      font-size: 0.55rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      padding: 0.2rem 0.6rem;
      border-radius: 0.3rem;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
      color: rgba(255,255,255,0.35);
    }
    .footer-chip-gold {
      background: rgba(197, 164, 78, 0.06);
      border-color: rgba(197, 164, 78, 0.2);
      color: rgba(197, 164, 78, 0.6);
    }
    .footer-arrow {
      font-size: 0.55rem;
      color: rgba(255,255,255,0.15);
    }
    .footer-note {
      font-size: 0.58rem;
      color: rgba(255,255,255,0.2);
      line-height: 1.7;
      margin: 0;
    }

    /* ── Dot Pulse (shared) ── */
    .dot-pulse {
      width: 8px;
      height: 8px;
      background: #c5a44e;
      border-radius: 50%;
      animation: pulse 1.2s ease-in-out infinite;
      flex-shrink: 0;
    }
    @keyframes pulse {
      0%, 100% { opacity: 0.3; transform: scale(1); }
      50%       { opacity: 1;   transform: scale(1.5); }
    }

    /* ── Action Row ── */
    .action-row {
      margin-top: 2.5rem;
      text-align: center;
    }
    .restart-btn {
      padding: 1.25rem 3rem;
      font-size: 0.85rem;
      font-weight: 900;
    }
  `]
})
export class ReportComponent {
  private state = inject(StateService);
  vaultOpen = false;

  evalResult$ = this.state.evalResult$;

  get traveledYear(): number | null { return this.state.traveledYear; }

  get ageAtTraveledYear(): number | null {
    if (!this.state.traveledYear || !this.state.metrics.birthYear) return null;
    return this.state.traveledYear - this.state.metrics.birthYear;
  }

  get eraStageLabel(): string {
    const age = this.ageAtTraveledYear;
    if (age === null) return '';
    if (age < 20) return 'RISING STAR';
    if (age <= 32) return 'ELITE PEAK';
    if (age <= 45) return 'VETERAN';
    return 'LEGACY';
  }

  get eraColor(): string {
    const age = this.ageAtTraveledYear;
    if (age === null) return '#c5a44e';
    if (age < 20) return '#34d399';
    if (age <= 32) return '#facc15';
    if (age <= 45) return '#60a5fa';
    return '#a78bfa';
  }

  view$ = this.state.result$.pipe(
    map(res => {
      if (!res) return null;
      return this.buildViewModel(res);
    })
  );

  private buildViewModel(res: ScoutingResult) {
    const isDuplicateName =
      res.olympic.matched_profile_name === res.paralympic.matched_profile_name;

    return {
      summaryVerdict: res.overall_narrative || res.olympic.scout_verdict,

      olympic: res.olympic,
      olympicPathway: res.olympic.pathway_standing || null,

      paralympic: {
        ...res.paralympic,
        matched_profile_name: isDuplicateName
          ? `${res.paralympic.matched_profile_name} — Adaptive`
          : res.paralympic.matched_profile_name,
      },
      paralympicPathway: res.paralympic.pathway_adaptive || null,

      standingAnalysis: res.olympic.scout_verdict,
      adaptiveAnalysis: res.paralympic.scout_verdict,
    };
  }

  scoreColor(score: number): string {
    if (score >= 8) return '#4ade80';
    if (score >= 6) return '#facc15';
    if (score >= 4) return '#fb923c';
    return '#f87171';
  }

  evalDimensions(ev: EvalResult) {
    const dims = [
      { label: 'AUTHENTICITY',        score: ev.authenticity.score,    reasoning: ev.authenticity.reasoning },
      { label: 'PERSONALIZATION',     score: ev.personalization.score,  reasoning: ev.personalization.reasoning },
      { label: 'PATHWAY DISTINCTNESS', score: ev.distinctness.score,   reasoning: ev.distinctness.reasoning },
    ];
    if (ev.life_stage_coherence) {
      dims.push({ label: 'LIFE STAGE COHERENCE ⏳', score: ev.life_stage_coherence.score, reasoning: ev.life_stage_coherence.reasoning });
    }
    return dims;
  }

  toggleVault() { this.vaultOpen = !this.vaultOpen; }
  restart() { this.state.reset(); }
}
