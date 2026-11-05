import { animate, query, style, transition, trigger } from '@angular/animations';
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { NavigationEnd, Router, RouterLink, RouterOutlet } from '@angular/router';
import { filter, map } from 'rxjs';

import { ThemeService } from './core/services/theme.service';

@Component({
  selector: 'app-root',
  imports: [MatButtonModule, MatIconModule, MatToolbarModule, RouterLink, RouterOutlet],
  animations: [
    trigger('routeFade', [
      transition('* <=> *', [
        query(
          ':enter',
          [
            style({ opacity: 0, transform: 'translateY(8px)' }),
            animate('200ms ease-out', style({ opacity: 1, transform: 'none' })),
          ],
          { optional: true },
        ),
      ]),
    ]),
  ],
  template: `
    <mat-toolbar class="toolbar">
      <a routerLink="/" class="brand">
        <mat-icon aria-hidden="true">insights</mat-icon>
        <span>AI Visibility Intelligence</span>
      </a>
      <span class="spacer"></span>
      <button
        mat-icon-button
        type="button"
        (click)="theme.toggle()"
        [attr.aria-label]="theme.isDark() ? 'Switch to light mode' : 'Switch to dark mode'"
      >
        <mat-icon>{{ theme.isDark() ? 'light_mode' : 'dark_mode' }}</mat-icon>
      </button>
    </mat-toolbar>
    <main [@routeFade]="routeKey()">
      <router-outlet />
    </main>
  `,
  styles: `
    .toolbar {
      background: var(--mat-sys-surface-container);
      border-bottom: 1px solid var(--mat-sys-outline-variant);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 8px;
      color: inherit;
      text-decoration: none;
      font: var(--mat-sys-title-medium);
    }
    .spacer {
      flex: 1;
    }
  `,
})
export class AppComponent {
  protected readonly theme = inject(ThemeService);

  // Keyed on the page, not the full URL, so switching profile tabs doesn't replay the transition.
  protected readonly routeKey = toSignal(
    inject(Router).events.pipe(
      filter((event) => event instanceof NavigationEnd),
      map((event) => event.urlAfterRedirects.split('/').slice(0, 3).join('/')),
    ),
  );
}
