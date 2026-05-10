import { Component, inject, OnDestroy } from '@angular/core';
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
        <span class="bar-label">TIME TRAVEL</span>
        <div class="life-stage-legend">
          <span class="legend-dot" style="background:#34d399"></span><span class="legend-text">Rising Star</span>
          <span class="legend-dot" style="background:#facc15"></span><span class="legend-text">Elite Peak</span>
          <span class="legend-dot" style="background:#60a5fa"></span><span class="legend-text">Veteran</span>
          <span class="legend-dot" style="background:#a78bfa"></span><span class="legend-text">Legacy</span>
        </div>
      </div>
      <div class="games-scroll">
        <button
          *ngFor="let g of eligibleGames"
          class="game-pill"
          [class.active]="g.year === activeYear"
          [style.borderColor]="getPhaseColor(g.year)"
          [style.--stage-color]="getPhaseColor(g.year)"
          (click)="travelTo(g)">
          <span class="game-year">{{ g.year }}</span>
          <span class="game-city">{{ g.city }}</span>
          <span class="game-stage" [style.color]="getPhaseColor(g.year)">{{ getLifeStageLabel(g.year) }}</span>
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

    .bar-label {
      font-size: 0.55rem;
      font-weight: 900;
      letter-spacing: 0.2em;
      color: rgba(255,255,255,0.25);
      white-space: nowrap;
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
      padding: 0.25rem 0;
    }
    .games-scroll::-webkit-scrollbar { height: 0; }

    .game-pill {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.1rem;
      padding: 0.5rem 0.85rem;
      border-radius: 0.5rem;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.08);
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
      flex-shrink: 0;
    }
    .game-pill:hover { background: rgba(255,255,255,0.06); }
    .game-pill.active {
      background: rgba(197, 164, 78, 0.08);
      box-shadow: 0 0 12px rgba(197, 164, 78, 0.12);
    }
    .game-year { font-size: 0.75rem; font-weight: 800; color: white; }
    .game-city { font-size: 0.52rem; color: rgba(255,255,255,0.35); }
    .game-stage {
      font-size: 0.48rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      opacity: 0.85;
      margin-top: 0.1rem;
    }
  `]
})
export class TimelineComponent implements OnDestroy {
  private state = inject(StateService);
  private stream = inject(StreamService);
  private sub?: Subscription;

  /** Subset of games_manifest.json that the user is eligible for. */
  eligibleGames: GameEntry[] = [];
  activeYear: number | null = null;

  private readonly gamesManifest: GameEntry[] = gamesManifestData as GameEntry[];

  constructor() {
    // Calculate eligible games based on user's birth year
    const birthYear = this.state.metrics.birthYear;
    if (birthYear) {
      this.eligibleGames = this.gamesManifest.filter(g => {
        const age = g.year - birthYear;
        return age >= 16 && age <= 55;
      });
    } else {
      // Fallback: show upcoming games
      this.eligibleGames = this.gamesManifest;
    }
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

    // Set era context in state — interview component reads this to show the banner
    // and to know that any answer should trigger a full re-scout
    this.state.setActiveEraYear(game.year);
    this.state.addUserTrace(`Time traveling to The ${game.year} Games · ${this.getLifeStageLabel(game.year)}`);

    const body = {
      story: '',
      session_id: this.state.sessionId,
      height_cm: this.state.metrics.height,
      weight_kg: this.state.metrics.weight,
      birth_year: this.state.metrics.birthYear,
      conversation_history: this.state.getHistory(),
      target_game_year: game.year,
      is_ready_to_scout: false,  // Triggers TIME_TRAVEL_INTERVIEW — Narrator asks one question first
      era_history: this.state.getEraHistory()
    };

    this.state.setAppState('INTERVIEW');
    this.sub = this.stream.consume(body).subscribe({
      error: () => this.state.setAppState('RESULT')
    });
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }
}
