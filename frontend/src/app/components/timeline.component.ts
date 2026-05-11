import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { StateService } from '../services/state.service';
import { StreamService } from '../services/stream.service';
import gamesManifestData from '../../assets/data/games_manifest.json';

interface GameEntry {
  year: number;
  city: string;
  season: string;
  vibe: string;
  parity_note?: string;
}

@Component({
  selector: 'app-timeline',
  standalone: true,
  imports: [CommonModule],
  template: `
    <nav class="timeline-bar glass-card" *ngIf="eligibleGames.length > 0">
      <div class="bar-header">
        <div class="bar-label-group">
          <span class="bar-label">TIME TRAVEL</span>
          <button class="info-btn" (click)="infoOpen = !infoOpen" [class.active]="infoOpen" type="button">?</button>
        </div>
        <div class="life-stage-legend">
          <span class="legend-dot" style="background:#34d399"></span><span class="legend-text">Rising Star</span>
          <span class="legend-dot" style="background:#facc15"></span><span class="legend-text">Elite Peak</span>
          <span class="legend-dot" style="background:#60a5fa"></span><span class="legend-text">Veteran</span>
          <span class="legend-dot" style="background:#a78bfa"></span><span class="legend-text">Legacy</span>
        </div>
      </div>

      <div class="info-tooltip" *ngIf="infoOpen">
        Each year shown is a Games you would have been between 16 and 55 years old — your full competitive window. Select any year to have the Scouts re-evaluate your profile at that age. Your answers and physical data stay the same; only the age changes.
      </div>

      <div class="games-scroll">
        <button
          *ngFor="let g of eligibleGames"
          class="game-pill"
          [class.active]="g.year === activeYear"
          [class.visited]="visitedYears.has(g.year)"
          [style.borderColor]="getPhaseColor(g.year)"
          (click)="travelTo(g)">
          <span class="game-year">{{ g.year }}</span>
          <span class="visited-dot" *ngIf="visitedYears.has(g.year)" [style.background]="getPhaseColor(g.year)"></span>
        </button>
      </div>
    </nav>
  `,
  styles: [`
    .timeline-bar {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      padding: 0.85rem 1.5rem;
      margin-bottom: 1.5rem;
    }

    .bar-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }

    .bar-label-group {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .bar-label {
      font-size: 0.55rem;
      font-weight: 900;
      letter-spacing: 0.2em;
      color: rgba(255,255,255,0.25);
      white-space: nowrap;
    }

    .info-btn {
      width: 14px;
      height: 14px;
      border-radius: 50%;
      border: 1px solid rgba(255,255,255,0.15);
      background: rgba(255,255,255,0.04);
      color: rgba(255,255,255,0.3);
      font-size: 0.5rem;
      font-weight: 900;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s;
      padding: 0;
      line-height: 1;
    }
    .info-btn:hover, .info-btn.active {
      background: rgba(197,164,78,0.1);
      border-color: rgba(197,164,78,0.35);
      color: rgba(197,164,78,0.8);
    }

    .info-tooltip {
      font-size: 0.65rem;
      color: rgba(255,255,255,0.45);
      line-height: 1.6;
      background: rgba(255,255,255,0.02);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 0.5rem;
      padding: 0.75rem 1rem;
    }

    .life-stage-legend {
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }
    .legend-dot {
      width: 6px; height: 6px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .legend-text {
      font-size: 0.5rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      color: rgba(255,255,255,0.3);
      margin-right: 0.4rem;
    }

    .games-scroll {
      display: flex;
      gap: 0.5rem;
      overflow-x: auto;
      padding: 0.25rem 0 0.5rem;
      scrollbar-width: thin;
      scrollbar-color: rgba(255,255,255,0.1) transparent;
    }
    .games-scroll::-webkit-scrollbar { height: 3px; }
    .games-scroll::-webkit-scrollbar-track { background: transparent; }
    .games-scroll::-webkit-scrollbar-thumb {
      background: rgba(255,255,255,0.1);
      border-radius: 99px;
    }

    .game-pill {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 0.45rem 0.9rem;
      border-radius: 0.5rem;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.08);
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
      flex-shrink: 0;
      gap: 0.2rem;
    }
    .game-pill:hover { background: rgba(255,255,255,0.06); }
    .game-pill.active {
      background: rgba(197, 164, 78, 0.08);
      box-shadow: 0 0 12px rgba(197, 164, 78, 0.12);
    }
    .game-pill.visited {
      background: rgba(255,255,255,0.05);
    }
    .game-year { font-size: 0.75rem; font-weight: 800; color: white; }
    .visited-dot {
      width: 4px;
      height: 4px;
      border-radius: 50%;
      flex-shrink: 0;
      opacity: 0.8;
    }
  `]
})
export class TimelineComponent implements OnInit, OnDestroy {
  private state = inject(StateService);
  private stream = inject(StreamService);
  private sub?: Subscription;
  private visitedSub?: Subscription;

  eligibleGames: GameEntry[] = [];
  activeYear: number | null = null;
  infoOpen = false;
  visitedYears = new Set<number>();

  private readonly gamesManifest: GameEntry[] = gamesManifestData as GameEntry[];

  constructor() {
    const birthYear = this.state.metrics.birthYear;
    if (birthYear) {
      this.eligibleGames = this.gamesManifest.filter(g => {
        const age = g.year - birthYear;
        return age >= 16 && age <= 55;
      });
    } else {
      this.eligibleGames = this.gamesManifest;
    }
  }

  ngOnInit() {
    this.visitedSub = this.state.visitedYears$.subscribe(years => {
      this.visitedYears = years;
    });
  }

  getPhaseColor(year: number): string {
    const birthYear = this.state.metrics.birthYear || 2000;
    const age = year - birthYear;
    if (age < 20)  return '#34d399';
    if (age <= 32) return '#facc15';
    if (age <= 45) return '#60a5fa';
    return '#a78bfa';
  }

  getLifeStageLabel(year: number): string {
    const birthYear = this.state.metrics.birthYear || 2000;
    const age = year - birthYear;
    if (age < 20)  return 'Rising Star';
    if (age <= 32) return 'Elite Peak';
    if (age <= 45) return 'Veteran';
    return 'Legacy';
  }

  travelTo(game: GameEntry) {
    this.sub?.unsubscribe();
    this.activeYear = game.year;
    this.infoOpen = false;
    this.state.timelineBannerDismissed = true;

    // Restore from cache instantly — no backend call needed
    if (this.state.hasVisitedYear(game.year)) {
      this.state.addUserTrace(`Revisiting The ${game.year} Games — restoring your previous report.`);
      this.state.restoreFromCache(game.year);
      return;
    }

    this.state.setActiveEraYear(game.year);
    this.state.addUserTrace(`I'm jumping to The ${game.year} Games — I'd be ${game.year - (this.state.metrics.birthYear || 2000)} years old. ${this.getLifeStageLabel(game.year)} stage.`);

    const body = {
      story: '',
      session_id: this.state.sessionId,
      height_cm: this.state.metrics.height,
      weight_kg: this.state.metrics.weight,
      birth_year: this.state.metrics.birthYear,
      conversation_history: this.state.getHistory(),
      target_game_year: game.year,
      is_ready_to_scout: false,
      era_history: this.state.getEraHistory()
    };

    this.state.setAppState('INTERVIEW');
    this.sub = this.stream.consume(body).subscribe({
      error: () => this.state.setAppState('RESULT')
    });
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
    this.visitedSub?.unsubscribe();
  }
}
