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
      
      <!-- ── SCOUT VERDICT SUMMARY ── -->
      <header class="verdict-summary glass-card">
        <span class="summary-label">SCOUT VERDICT</span>
        <p class="summary-text">{{ v.summaryVerdict }}</p>
      </header>

      <div class="archetypes-grid">
        <!-- ── OLYMPIC PATHWAY ── -->
        <div class="archetype-card glass-card-elevated">
          <div class="card-type-label">OLYMPIC PATHWAY</div>
          
          <div class="badge-row" *ngIf="v.olympic.life_stage">
            <span class="life-stage-badge">{{ v.olympic.life_stage }}</span>
          </div>

          <h1 class="archetype-name text-gradient-usa">
            {{ v.olympic.matched_profile_name }}
          </h1>

          <p class="pathway-discipline" *ngIf="v.olympicPathway">
            {{ v.olympicPathway }}
          </p>

          <div class="verdict-box">
            <p>{{ v.olympicVerdict }}</p>
          </div>
        </div>

        <!-- ── PARALYMPIC PATHWAY ── -->
        <div class="archetype-card glass-card-elevated">
          <div class="card-type-label">PARALYMPIC PATHWAY</div>
          
          <div class="badge-row" *ngIf="v.paralympic.life_stage">
            <span class="life-stage-badge">{{ v.paralympic.life_stage }}</span>
          </div>

          <h1 class="archetype-name text-gradient-usa">
            {{ v.paralympic.matched_profile_name }}
          </h1>

          <p class="pathway-discipline" *ngIf="v.paralympicPathway">
            {{ v.paralympicPathway }}
          </p>

          <div class="verdict-box">
            <p>{{ v.paralympicVerdict }}</p>
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

    /* ── Grid ── */
    .archetypes-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2rem;
      align-items: stretch;
    }

    @media (max-width: 900px) {
      .archetypes-grid { grid-template-columns: 1fr; }
    }

    .archetype-card {
      padding: 4rem 3rem 3rem;
      position: relative;
      display: flex;
      flex-direction: column;
      height: 100%;
    }

    .card-type-label {
      position: absolute;
      top: 1.5rem;
      left: 0;
      right: 0;
      text-align: center;
      font-size: 0.65rem;
      font-weight: 900;
      letter-spacing: 0.4em;
      color: rgba(255,255,255,0.3);
      text-transform: uppercase;
    }

    .life-stage-badge {
      display: inline-block;
      font-size: 0.6rem;
      font-weight: 800;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #c5a44e;
      background: rgba(197, 164, 78, 0.1);
      border: 1px solid rgba(197, 164, 78, 0.2);
      padding: 0.25rem 0.75rem;
      border-radius: 99px;
      margin-bottom: 1.5rem;
    }

    .archetype-name {
      font-size: clamp(1.75rem, 3.5vw, 2.5rem);
      font-weight: 900;
      letter-spacing: -0.02em;
      line-height: 1.1;
      margin-bottom: 1rem;
      text-align: center;
    }

    .pathway-discipline {
      text-align: center;
      font-size: 0.7rem;
      font-weight: 800;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: rgba(197, 164, 78, 0.6);
      margin-bottom: 2rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    .verdict-box {
      text-align: left;
      color: rgba(255,255,255,0.7);
      line-height: 1.7;
      font-size: 0.95rem;
    }

    .action-row {
      margin-top: 4rem;
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

  /**
   * Transforms the raw ScoutingResult into a deduplicated view model.
   * Detects duplicate verdicts and provides fallback text.
   */
  view$ = this.state.result$.pipe(
    map(res => {
      if (!res) return null;
      return this.buildViewModel(res);
    })
  );

  private buildViewModel(res: ScoutingResult) {
    const isDuplicateVerdict = res.olympic.scout_verdict === res.paralympic.scout_verdict;
    const isDuplicateName = res.olympic.matched_profile_name === res.paralympic.matched_profile_name;

    return {
      // Top summary — always use the olympic verdict as the primary analysis
      summaryVerdict: res.overall_narrative || res.olympic.scout_verdict,

      // Olympic card
      olympic: res.olympic,
      olympicPathway: res.olympic.pathway_standing || null,
      olympicVerdict: this.truncateForCard(res.olympic.scout_verdict),

      // Paralympic card — detect duplication and provide fallback
      paralympic: {
        ...res.paralympic,
        matched_profile_name: isDuplicateName 
          ? res.paralympic.matched_profile_name 
          : res.paralympic.matched_profile_name
      },
      paralympicPathway: res.paralympic.pathway_adaptive || null,
      paralympicVerdict: isDuplicateVerdict
        ? 'Discovering your Paralympic potential — a secondary analysis tailored to adaptive disciplines is being prepared based on your physical profile.'
        : this.truncateForCard(res.paralympic.scout_verdict),
    };
  }

  /** 
   * For the cards: keep the verdict short and technical. 
   * The full narrative was already shown in the summary.
   */
  private truncateForCard(verdict: string): string {
    if (!verdict) return '';
    // If the verdict is very long (likely a narrative), trim it
    if (verdict.length > 400) {
      return verdict.substring(0, 397) + '…';
    }
    return verdict;
  }

  restart() {
    this.state.reset();
  }
}
