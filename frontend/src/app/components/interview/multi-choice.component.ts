import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-multi-choice',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="chip-grid">
      <button
        *ngFor="let option of options"
        class="chip btn-gold"
        [disabled]="chosen !== null"
        [class.chosen]="chosen === option"
        (click)="pick(option)">
        {{ option }}
      </button>
    </div>
  `,
  styles: [`
    .chip-grid { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 1rem; }
    .chip {
      padding: 0.75rem 1.5rem;
      font-size: 0.85rem;
      letter-spacing: 0.04em;
      border-radius: 99px;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .chip.chosen {
      box-shadow: 0 0 0 2px #c5a44e, 0 4px 20px rgba(197, 164, 78, 0.4);
      transform: scale(1.05);
    }
  `]
})
export class MultiChoiceComponent {
  @Input() options: string[] = [];
  @Output() selected = new EventEmitter<string>();

  chosen: string | null = null;

  pick(option: string) {
    this.chosen = option;
    this.selected.emit(option);
  }
}
