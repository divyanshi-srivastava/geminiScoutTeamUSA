import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { APP_STRINGS } from '../../constants';


@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  template: `
    <header class="app-header">
      <div class="header-shield">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z">
          </path>
        </svg>
      </div>
      <h1 class="header-title text-gradient-usa">Gemini Scout</h1>
      <p class="header-sub">{{ APP_STRINGS.FOOTER_TEXT}}</p>
    </header>
  `,
  styles: [`
    .app-header {
      width: 100%;
      padding: 2rem 1.5rem;
      background: rgba(10, 17, 40, 0.5);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      position: sticky;
      top: 0;
      z-index: 50;
      text-align: center;
    }
    .header-shield {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 3rem; height: 3rem;
      border-radius: 0.75rem;
      background: rgba(197, 164, 78, 0.08);
      border: 1px solid rgba(197, 164, 78, 0.15);
      margin-bottom: 0.75rem;
    }
    .header-shield svg { width: 1.5rem; height: 1.5rem; color: #d4b95e; }
    .header-title { font-size: 1.5rem; font-weight: 900; text-transform: uppercase; letter-spacing: -0.02em; }
    .header-sub { color: rgba(212, 185, 94, 0.5); font-size: 0.625rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3em; margin-top: 0.25rem; }
  `]
})
export class HeaderComponent {
  readonly APP_STRINGS = APP_STRINGS;
}

