import { Component, EventEmitter, Output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { StateService } from '../../services/state.service';

@Component({
  selector: 'app-metrics',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="metrics-form animate-fade-in">
      <h2 class="form-title">Establishing Your Physical Legacy</h2>
      <p class="form-sub">Before we begin the narrative, we need your baseline physical metrics.</p>

      <div class="metrics-grid">
        <!-- Height -->
        <div class="metric-card">
          <div class="metric-header">
            <label>Height</label>
            <span class="metric-value">{{ formatHeight(heightInches) }}</span>
          </div>
          <input type="range" min="48" max="96" [(ngModel)]="heightInches" class="gold-range">
          <div class="range-labels"><span>4'0"</span><span>8'0"</span></div>
        </div>

        <!-- Weight -->
        <div class="metric-card">
          <div class="metric-header">
            <label>Weight</label>
            <span class="metric-value">{{ weightLbs }} <small>lbs</small></span>
          </div>
          <input type="range" min="70" max="450" [(ngModel)]="weightLbs" class="gold-range">
          <div class="range-labels"><span>70 lbs</span><span>450 lbs</span></div>
        </div>

        <!-- Birth Year -->
        <div class="metric-card">
          <div class="metric-header">
            <label>Birth Year</label>
            <span class="metric-value">{{ birthYear }} <small>age {{ currentAge }}</small></span>
          </div>
          <input type="range" min="1950" max="2010" [(ngModel)]="birthYear" class="gold-range">
          <div class="range-labels"><span>1950</span><span>2010</span></div>
        </div>
      </div>

      <p class="age-warning" *ngIf="ageWarning">{{ ageWarning }}</p>

      <button class="btn-gold submit-btn" (click)="submit()" [disabled]="currentAge < 16">
        LOCK IN METRICS
      </button>
    </div>
  `,
  styles: [`
    .metrics-form { display: flex; flex-direction: column; gap: 1.5rem; }
    .form-title { font-size: 1.5rem; font-weight: 900; color: white; margin: 0; }
    .form-sub { font-size: 0.9rem; color: rgba(255,255,255,0.5); margin-bottom: 1rem; }

    .metrics-grid { display: flex; flex-direction: column; gap: 2rem; }
    
    .metric-card { display: flex; flex-direction: column; gap: 0.75rem; }
    .metric-header { display: flex; justify-content: space-between; align-items: flex-end; }
    .metric-header label { font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(255,255,255,0.4); }
    .metric-value { font-size: 1.75rem; font-weight: 900; color: #c5a44e; line-height: 1; }
    .metric-value small { font-size: 0.8rem; color: rgba(255,255,255,0.3); font-weight: 400; }

    .gold-range {
      -webkit-appearance: none;
      width: 100%;
      height: 4px;
      background: rgba(255,255,255,0.1);
      border-radius: 2px;
      outline: none;
    }
    .gold-range::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 20px; height: 20px;
      background: #c5a44e;
      border-radius: 50%;
      cursor: pointer;
      box-shadow: 0 0 10px rgba(197, 164, 78, 0.4);
    }

    .range-labels { display: flex; justify-content: space-between; font-size: 0.6rem; font-weight: 700; color: rgba(255,255,255,0.2); text-transform: uppercase; }

    .age-warning { font-size: 0.75rem; color: #e8a04a; text-align: center; margin: 0; }
    .submit-btn { margin-top: 1rem; padding: 1.25rem; font-size: 0.9rem; letter-spacing: 0.15em; }
    .submit-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  `]
})
export class MetricsComponent {
  private state = inject(StateService);
  @Output() completed = new EventEmitter<void>();

  heightInches = 70;
  weightLbs = 175;
  birthYear = 1995;

  formatHeight(totalInches: number): string {
    const feet = Math.floor(totalInches / 12);
    const inches = totalInches % 12;
    return `${feet}' ${inches}"`;
  }

  get currentAge(): number {
    return new Date().getFullYear() - this.birthYear;
  }

  get ageWarning(): string | null {
    const age = this.currentAge;
    if (age < 16) return 'You must be at least 16 to be scouted.';
    if (age > 55) return 'Our scouting model covers ages 16–55. Results may be less precise.';
    return null;
  }

  submit() {
    if (this.currentAge < 16) return;
    this.state.setMetrics({
      height: Math.round(this.heightInches * 2.54),
      weight: Math.round(this.weightLbs * 0.453592),
      birthYear: this.birthYear
    });
    this.completed.emit();
  }
}
