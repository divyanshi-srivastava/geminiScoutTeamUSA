import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { APP_STRINGS, PROJECT_LINKS } from '../../constants';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [CommonModule],
  template: `
    <footer class="app-footer">
      <p class="footer-disclaimer">
        {{ APP_STRINGS.DISCLAIMER_BOX }}
      </p>
      
      <p class="footer-data">
        Historical sporting data provided by the
        <a [href]="LINKS.HISTORICAL_RECORDS" target="_blank">Kaggle Adaptive Sport Records Dataset </a>
        and <a [href]="LINKS.KAGGE_DATA" target="_blank">Kaggle Historical Sport Records. </a>
        Dataset usage under fair-use for non-commercial athletic prospecting research.
      </p>

      <p class="footer-copyright">
        &copy; 2026 Gemini Scout | Team USA Hackathon
      </p>
    </footer>
  `,
  styles: [`
    .app-footer {
      width: 100%;
      padding: 3rem 1.5rem;
      background: rgba(10, 17, 40, 0.8);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      z-index: 10;
      text-align: center;
      margin-top: auto;
    }
    .footer-badge {
      display: inline-block;
      font-size: 0.6rem;
      font-weight: 900;
      color: rgba(255, 255, 255, 0.6);
      text-transform: uppercase;
      letter-spacing: 0.15em;
      padding: 0.4rem 1rem;
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 99px;
      margin-bottom: 1.5rem;
    }
    .footer-data {
      font-size: 0.6rem;
      line-height: 1.7;
      color: rgba(255, 255, 255, 0.4);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      font-weight: 500;
      max-width: 40rem;
      margin: 0 auto 1rem;
    }
    .footer-data a {
      text-decoration: underline;
      text-underline-offset: 2px;
      transition: color 0.2s;
      color: rgba(255, 255, 255, 0.4);
    }
    .footer-data a:hover { color: #d4b95e; }
    .footer-disclaimer {
      font-size: 0.55rem;
      color: rgba(255, 255, 255, 0.25);
      letter-spacing: 0.1em;
      text-transform: uppercase;
      font-style: italic;
      max-width: 32rem;
      margin: 0 auto;
      line-height: 1.5;
    }
    .footer-copyright {
      font-size: 0.6rem;
      color: rgba(255, 255, 255, 0.15);
      text-transform: uppercase;
      letter-spacing: 0.2em;
      margin-top: 2rem;
      font-weight: 700;
    }
  `]
})
export class FooterComponent {
  readonly APP_STRINGS = APP_STRINGS;
  readonly LINKS = PROJECT_LINKS;
}
