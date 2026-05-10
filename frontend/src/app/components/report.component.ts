import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StateService } from '../services/state.service';
import { ScoutingResult } from '../models';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-report',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="report-container animate-fade-in-up" *ngIf="view$ | async as v">

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
            <span class="life-stage-badge" *ngIf="v.olympic.life_stage">
              {{ v.olympic.life_stage }}
            </span>
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
            <span class="life-stage-badge adaptive-badge" *ngIf="v.paralympic.life_stage">
              {{ v.paralympic.life_stage }}
            </span>
            <h2 class="archetype-name text-gradient-usa">
              {{ v.paralympic.matched_profile_name }}
            </h2>
            <p class="pathway-discipline" *ngIf="v.paralympicPathway">
              {{ v.paralympicPathway }}
            </p>
          </div>
        </div>

      </div>

      <!-- ── JUDGE'S VAULT ── -->
      <div class="vault-section">
        <button class="vault-toggle" (click)="toggleVault()">
          <span class="vault-chevron">{{ vaultOpen ? '▲' : '▼' }}</span>
          <span class="vault-title">VIEW TECHNICAL ORCHESTRATION &amp; REASONING</span>
          <span class="vault-hint">{{ vaultOpen ? 'COLLAPSE' : 'EXPAND' }}</span>
        </button>

        <div class="vault-body" [class.open]="vaultOpen">
          <div class="vault-content">
            <div class="vault-header">// STANDING PATHWAY — FULL ANALYSIS</div>
            <pre class="vault-text">{{ v.standingAnalysis }}</pre>

            <div class="vault-header vault-sep">// ADAPTIVE PATHWAY — FULL ANALYSIS</div>
            <pre class="vault-text">{{ v.adaptiveAnalysis }}</pre>

            <div class="vault-footer">
              // Agent trace &amp; SSE events logged in Mission Control sidebar.<br>
              // Physical profile matched via Euclidean distance across 12 archetype centroids.<br>
              // Pipeline: supervisor_agent → scout_agent → narrator_agent → compliance_agent
            </div>
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

    .life-stage-badge {
      display: inline-block;
      font-size: 0.6rem;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #c5a44e;
      background: rgba(197, 164, 78, 0.1);
      border: 1px solid rgba(197, 164, 78, 0.25);
      padding: 0.25rem 0.85rem;
      border-radius: 99px;
    }
    .adaptive-badge {
      color: #60a5fa;
      background: rgba(96, 165, 250, 0.08);
      border-color: rgba(96, 165, 250, 0.2);
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

    /* ── Judge's Vault ── */
    .vault-section {
      margin-bottom: 2.5rem;
      border-radius: 0.75rem;
      border: 1px solid rgba(74, 222, 128, 0.1);
      overflow: hidden;
    }

    .vault-toggle {
      width: 100%;
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 1rem 1.5rem;
      background: rgba(0, 8, 0, 0.5);
      border: none;
      cursor: pointer;
      transition: background 0.2s;
    }
    .vault-toggle:hover { background: rgba(0, 16, 0, 0.6); }

    .vault-chevron {
      font-size: 0.55rem;
      color: rgba(74, 222, 128, 0.5);
    }
    .vault-title {
      flex: 1;
      text-align: left;
      font-size: 0.6rem;
      font-weight: 700;
      letter-spacing: 0.25em;
      color: rgba(74, 222, 128, 0.6);
      font-family: 'Courier New', Courier, monospace;
    }
    .vault-hint {
      font-size: 0.55rem;
      letter-spacing: 0.1em;
      color: rgba(74, 222, 128, 0.25);
      font-family: 'Courier New', Courier, monospace;
    }

    .vault-body {
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.55s ease;
    }
    .vault-body.open { max-height: 3000px; }

    .vault-content {
      padding: 1.5rem;
      background: rgba(0, 8, 0, 0.7);
      border-top: 1px solid rgba(74, 222, 128, 0.08);
    }

    .vault-header {
      font-family: 'Courier New', Courier, monospace;
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      color: rgba(74, 222, 128, 0.7);
      margin-bottom: 0.75rem;
    }
    .vault-sep { margin-top: 2rem; }

    .vault-text {
      font-family: 'Courier New', Courier, monospace;
      font-size: 0.78rem;
      line-height: 1.75;
      color: rgba(74, 222, 128, 0.5);
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
    }

    .vault-footer {
      margin-top: 1.75rem;
      padding-top: 1rem;
      border-top: 1px solid rgba(74, 222, 128, 0.07);
      font-family: 'Courier New', Courier, monospace;
      font-size: 0.58rem;
      line-height: 1.9;
      color: rgba(74, 222, 128, 0.22);
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

  toggleVault() { this.vaultOpen = !this.vaultOpen; }
  restart() { this.state.reset(); }
}
