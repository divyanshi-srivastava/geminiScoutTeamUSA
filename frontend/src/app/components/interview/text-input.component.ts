import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-text-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="input-group">
      <textarea 
        [(ngModel)]="val" 
        placeholder="Type your response..."
        (keydown.enter)="$event.preventDefault(); submit()">
      </textarea>
      <button 
        class="send-btn" 
        [disabled]="!val.trim()" 
        (click)="submit()">
        CONTINUE JOURNEY
      </button>
    </div>
  `,
  styles: [`
    .input-group { display: flex; flex-direction: column; gap: 1.5rem; margin-top: 2rem; }
    textarea { 
      background: #0f172a; 
      border: 1px solid #334155; 
      color: white; 
      padding: 1.5rem; 
      border-radius: 1rem; 
      min-height: 120px; 
      font-size: 1rem;
      resize: none;
      transition: border-color 0.2s;
    }
    textarea:focus { outline: none; border-color: #eab308; }
    
    .send-btn { 
      background: #eab308; 
      color: #0f172a; 
      padding: 1rem; 
      border-radius: 0.75rem; 
      font-weight: 900; 
      letter-spacing: 0.1em;
      transition: all 0.2s;
    }
    .send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .send-btn:not(:disabled):hover { transform: scale(1.02); filter: brightness(1.1); }
  `]
})
export class TextInputComponent {
  val = '';
  @Output() submitted = new EventEmitter<string>();

  submit() {
    if (this.val.trim()) {
      this.submitted.emit(this.val);
      this.val = '';
    }
  }
}
