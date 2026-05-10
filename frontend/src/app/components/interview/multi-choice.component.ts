import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-multi-choice',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="option-list">
      <button
        *ngFor="let option of options"
        class="option-row"
        [disabled]="chosen !== null"
        [class.chosen]="chosen === option"
        (click)="pick(option)">
        <span class="option-marker"></span>
        <span class="option-text">{{ option }}</span>
      </button>
    </div>
  `,
  styles: [`
    .option-list {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
      margin-top: 1.25rem;
    }
    .option-row {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      width: 100%;
      padding: 0.85rem 1rem;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 0.5rem;
      cursor: pointer;
      text-align: left;
      transition: all 0.18s ease;
      font-family: inherit;
    }
    .option-row:hover:not(:disabled) {
      background: rgba(197,164,78,0.06);
      border-color: rgba(197,164,78,0.25);
    }
    .option-row.chosen {
      background: rgba(197,164,78,0.08);
      border-color: #c5a44e;
    }
    .option-row:disabled:not(.chosen) {
      opacity: 0.4;
      cursor: not-allowed;
    }
    .option-marker {
      flex-shrink: 0;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      border: 1.5px solid rgba(197,164,78,0.4);
      margin-top: 2px;
      transition: all 0.18s ease;
    }
    .option-row.chosen .option-marker {
      background: #c5a44e;
      border-color: #c5a44e;
      box-shadow: 0 0 8px rgba(197,164,78,0.5);
    }
    .option-text {
      font-size: 0.88rem;
      font-weight: 500;
      color: rgba(255,255,255,0.75);
      line-height: 1.45;
    }
    .option-row.chosen .option-text {
      color: #e3ce6f;
      font-weight: 600;
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
