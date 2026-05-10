import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StateService } from '../services/state.service';
import { StreamService } from '../services/stream.service';

interface GameEntry {
  year: number;
  city: string;
  season: string;
  vibe: string;
}

@Component({
  selector: 'app-timeline',
  standalone: true,
  imports: [CommonModule],
  template: `
    <nav class="timeline-bar glass-card" *ngIf="eligibleGames.length > 0">
      <span class="bar-label">TIME TRAVEL</span>
      <div class="games-scroll">
        <button
          *ngFor="let g of eligibleGames"
          class="game-pill"
          [class.active]="g.year === activeYear"
          [style.borderColor]="getPhaseColor(g.year)"
          (click)="travelTo(g)">
          <span class="game-year">{{ g.year }}</span>
          <span class="game-city">{{ g.city }}</span>
        </button>
      </div>
    </nav>
  `,
  styles: [`
    .timeline-bar {
      display: flex;
      align-items: center;
      gap: 1.25rem;
      padding: 0.75rem 1.5rem;
      margin-bottom: 1.5rem;
      overflow: hidden;
    }
    .bar-label {
      font-size: 0.55rem;
      font-weight: 900;
      letter-spacing: 0.2em;
      color: rgba(255,255,255,0.25);
      white-space: nowrap;
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
      gap: 0.15rem;
      padding: 0.4rem 0.75rem;
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
      background: rgba(197, 164, 78, 0.1);
      border-color: #c5a44e;
      box-shadow: 0 0 12px rgba(197, 164, 78, 0.15);
    }
    .game-year { font-size: 0.75rem; font-weight: 800; color: white; }
    .game-city { font-size: 0.55rem; color: rgba(255,255,255,0.35); }
  `]
})
export class TimelineComponent {
  private state = inject(StateService);
  private stream = inject(StreamService);

  /** Subset of games_manifest.json that the user is eligible for. */
  eligibleGames: GameEntry[] = [];
  activeYear: number | null = null;

  /** Full games manifest (embedded for frontend use). */
  private readonly gamesManifest: GameEntry[] = [
    { year: 2024, city: 'Paris',         season: 'Summer', vibe: 'The Wide Open Games' },
    { year: 2026, city: 'Milano Cortina', season: 'Winter', vibe: 'The Glamour and the Grind' },
    { year: 2028, city: 'Los Angeles',    season: 'Summer', vibe: 'The Cinematic Frontier' },
    { year: 2030, city: 'French Alps',    season: 'Winter', vibe: 'The Sustainable Summit' },
    { year: 2032, city: 'Brisbane',       season: 'Summer', vibe: 'The Sunshine State Shine' },
    { year: 2034, city: 'Salt Lake City', season: 'Winter', vibe: 'The Great Salt Return' },
    { year: 2036, city: 'Ahmedabad',      season: 'Summer', vibe: 'The Vibrant Bharat Ascent' },
  ];

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
    if (age < 20)  return '#34d399';  // Rising Star
    if (age <= 32) return '#facc15';  // Elite Peak
    if (age <= 45) return '#60a5fa';  // Veteran
    return '#a78bfa';                 // Legacy Coach
  }

  travelTo(game: GameEntry) {
    this.activeYear = game.year;

    const body = {
      story: '',
      height_cm: this.state.metrics.height,
      weight_kg: this.state.metrics.weight,
      birth_year: this.state.metrics.birthYear,
      conversation_history: this.state.getHistory(),
      target_game_year: game.year,
      is_ready_to_scout: true
    };

    this.state.setAppState('SCOUTING');
    this.stream.consume(body).subscribe();
  }
}
