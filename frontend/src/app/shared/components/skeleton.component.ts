import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-skeleton',
  template: `
    <div class="skeleton" role="status" aria-label="Loading">
      @for (line of lineList(); track line) {
        <div class="line" [style.height.px]="lineHeight()"></div>
      }
    </div>
  `,
  styles: `
    .skeleton {
      display: grid;
      gap: 12px;
    }
    .line {
      border-radius: 8px;
      background: linear-gradient(
        90deg,
        var(--mat-sys-surface-container) 25%,
        var(--mat-sys-surface-container-highest) 50%,
        var(--mat-sys-surface-container) 75%
      );
      background-size: 200% 100%;
      animation: shimmer 1.4s linear infinite;
    }
    @keyframes shimmer {
      from {
        background-position: 200% 0;
      }
      to {
        background-position: -200% 0;
      }
    }
    @media (prefers-reduced-motion: reduce) {
      .line {
        animation: none;
      }
    }
  `,
})
export class SkeletonComponent {
  readonly lines = input(5);
  readonly lineHeight = input(40);
  protected readonly lineList = computed(() => Array.from({ length: this.lines() }, (_, i) => i));
}
