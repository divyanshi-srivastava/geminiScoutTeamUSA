import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import legacyFacts from '../../assets/data/legacy_facts.json';

interface LegacyFact {
  year: number;
  sport: string;
  fact_story: string;
  citation_note: string;
  source_credit: string;
}

@Component({
  selector: 'app-fact-rotator',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="fact-rotator" [class.visible]="visible">
      <div class="fact-sport-tag">
        <span class="sport-name">{{ current.sport }}</span>
        <span class="games-year">The {{ current.year }} Games</span>
      </div>
      <p class="fact-story">{{ current.fact_story }}</p>
      <p class="fact-source">{{ current.source_credit }}</p>
    </div>
  `,
  styles: [`
    .fact-rotator {
      max-width: 560px;
      margin: 2rem auto 0;
      padding: 1.25rem 1.5rem;
      border-radius: 0.75rem;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.07);
      opacity: 0;
      transform: translateY(6px);
      transition: opacity 0.6s ease, transform 0.6s ease;
      text-align: left;
    }
    .fact-rotator.visible {
      opacity: 1;
      transform: translateY(0);
    }
    .fact-sport-tag {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 0.75rem;
    }
    .sport-name {
      font-size: 0.6rem;
      font-weight: 900;
      letter-spacing: 0.15em;
      color: #c5a44e;
      text-transform: uppercase;
    }
    .games-year {
      font-size: 0.6rem;
      letter-spacing: 0.1em;
      color: rgba(255,255,255,0.25);
      text-transform: uppercase;
    }
    .fact-story {
      font-size: 0.8rem;
      line-height: 1.6;
      color: rgba(255,255,255,0.7);
      margin: 0 0 0.6rem;
    }
    .fact-source {
      font-size: 0.55rem;
      color: rgba(255,255,255,0.2);
      letter-spacing: 0.05em;
      margin: 0;
    }
  `]
})
export class FactRotatorComponent implements OnInit, OnDestroy {
  private readonly facts: LegacyFact[] = legacyFacts as LegacyFact[];
  private index = Math.floor(Math.random() * this.facts.length);
  private interval?: ReturnType<typeof setInterval>;

  current: LegacyFact = this.facts[this.index];
  visible = false;

  ngOnInit() {
    // Fade in after a short delay so it doesn't compete with the spinner entrance
    setTimeout(() => { this.visible = true; }, 300);

    this.interval = setInterval(() => {
      this.visible = false;
      setTimeout(() => {
        this.index = (this.index + 1) % this.facts.length;
        this.current = this.facts[this.index];
        this.visible = true;
      }, 650);
    }, 6000);
  }

  ngOnDestroy() {
    clearInterval(this.interval);
  }
}
