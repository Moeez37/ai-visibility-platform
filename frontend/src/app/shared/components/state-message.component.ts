import { Component, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-state-message',
  imports: [MatIconModule],
  template: `
    <div
      class="state"
      [class.error]="tone() === 'error'"
      [attr.role]="tone() === 'error' ? 'alert' : null"
    >
      <div class="illustration" aria-hidden="true">
        <mat-icon>{{ icon() }}</mat-icon>
      </div>
      <h2>{{ title() }}</h2>
      <p class="muted">{{ message() }}</p>
      <ng-content />
    </div>
  `,
  styles: `
    .state {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 16px;
      text-align: center;
    }
    .illustration {
      display: grid;
      place-items: center;
      width: 80px;
      height: 80px;
      margin-bottom: 16px;
      border-radius: 50%;
      background: var(--mat-sys-surface-container-high);
      color: var(--mat-sys-primary);
    }
    .illustration mat-icon {
      width: 40px;
      height: 40px;
      font-size: 40px;
    }
    .error .illustration {
      background: var(--mat-sys-error-container);
      color: var(--mat-sys-on-error-container);
    }
    p {
      max-width: 480px;
      margin: 0 0 16px;
    }
  `,
})
export class StateMessageComponent {
  readonly icon = input.required<string>();
  readonly title = input.required<string>();
  readonly message = input.required<string>();
  readonly tone = input<'neutral' | 'error'>('neutral');
}
