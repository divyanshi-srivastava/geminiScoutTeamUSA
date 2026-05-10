import { Component, inject, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StateService } from '../services/state.service';

@Component({
  selector: 'app-logger',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="logger-panel">
      <div class="header">
        <div class="live-dot"></div>
        <h3>ORCHESTRATION TRACE</h3>
      </div>

      <div class="trace-scroll" #scrollContainer>
        <div *ngFor="let t of traces$ | async; let i = index"
             class="trace-row"
             [attr.data-event]="t.event"
             [style.animation-delay]="i * 50 + 'ms'">
          <div class="row-meta">
            <span class="ts">{{ t.timestamp }}</span>
            <span class="agent-tag" [attr.data-agent]="t.agent">
              {{ formatAgent(t.agent) }}
            </span>
          </div>
          <p class="row-body">{{ t.detail || t.event }}</p>
        </div>

        <div *ngIf="(traces$ | async)?.length === 0" class="empty-state">
          <p>Waiting for orchestration events…</p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .logger-panel {
      background: #020617;
      border-radius: 0.75rem;
      border: 1px solid rgba(255,255,255,0.06);
      display: flex;
      flex-direction: column;
      font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
      overflow: hidden;
    }

    /* Header */
    .header {
      padding: 1.25rem 1.5rem;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }
    .live-dot {
      width: 7px; height: 7px;
      background: #22c55e;
      border-radius: 50%;
      box-shadow: 0 0 6px #22c55e;
      animation: blink 2s ease-in-out infinite;
    }
    @keyframes blink { 0%,100%{ opacity:1 } 50%{ opacity:0.3 } }
    h3 {
      font-size: 0.6rem;
      font-weight: 900;
      color: rgba(255,255,255,0.3);
      letter-spacing: 0.2em;
      margin: 0;
    }

    /* Trace List */
    .trace-scroll {
      max-height: 800px;
      overflow-y: auto;
      padding: 1rem 1.25rem;
      scrollbar-width: thin;
      scrollbar-color: rgba(197, 164, 78, 0.25) transparent;
    }
    .trace-scroll::-webkit-scrollbar { width: 4px; }
    .trace-scroll::-webkit-scrollbar-track { background: transparent; }
    .trace-scroll::-webkit-scrollbar-thumb {
      background: rgba(197, 164, 78, 0.25);
      border-radius: 10px;
    }

    .trace-row {
      margin-bottom: 1.25rem;
      padding-left: 0.75rem;
      border-left: 2px solid rgba(255,255,255,0.06);
      animation: fadeInUp 0.3s ease-out both;
    }

    .row-meta {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.15rem;
    }
    .ts { color: rgba(255,255,255,0.2); font-size: 0.6rem; }
    .agent-tag {
      font-size: 0.55rem;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      padding: 1px 6px;
      border-radius: 3px;
      background: rgba(255,255,255,0.04);
    }
    .agent-tag[data-agent*="scout"]      { color: #c5a44e; background: rgba(197,164,78,0.08); border: 1px solid rgba(197,164,78,0.15); }
    .agent-tag[data-agent*="narrator"]   { color: #e3ce6f; }
    .agent-tag[data-agent*="compliance"] { color: #f87171; background: rgba(248,113,113,0.06); border: 1px solid rgba(248,113,113,0.12); }
    .agent-tag[data-agent*="supervisor"] { color: #a78bfa; }
    .agent-tag[data-agent*="logger"]     { color: #34d399; }
    .agent-tag[data-agent*="system"]     { color: #94a3b8; font-style: italic; }
    .agent-tag[data-agent="user"]        { color: #a5f3fc; background: rgba(165,243,252,0.06); border: 1px solid rgba(165,243,252,0.12); }

    .row-body {
      color: rgba(255,255,255,0.65);
      font-size: 0.76rem;
      line-height: 1.55;
      margin: 0;
    }

    /* Final agent output */
    .trace-row[data-event="Thought"] .row-body {
      color: rgba(255,255,255,0.82);
    }
    .trace-row[data-event="Thought"] {
      border-left-color: rgba(52, 211, 153, 0.3);
    }

    /* Thinking tokens — dimmer, italic, indented to feel like internal monologue */
    .trace-row[data-event="Thinking"] {
      border-left-color: rgba(255,255,255,0.04);
      padding-left: 1.25rem;
    }
    .trace-row[data-event="Thinking"] .row-body {
      color: rgba(255,255,255,0.35);
      font-style: italic;
      font-size: 0.7rem;
    }

    .empty-state {
      text-align: center;
      padding: 3rem 1rem;
      color: rgba(255,255,255,0.15);
      font-size: 0.75rem;
    }

    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }
  `]
})
export class LoggerComponent implements AfterViewChecked {
  private state = inject(StateService);

  traces$ = this.state.traces$;
  @ViewChild('scrollContainer') private scrollRef!: ElementRef;

  formatAgent(name: string): string {
    if (name === 'user') return 'USER';
    return name.replace('_agent', '').replace('_', ' ');
  }

  ngAfterViewChecked() {
    try {
      const el = this.scrollRef.nativeElement;
      el.scrollTop = el.scrollHeight;
    } catch { }
  }
}
