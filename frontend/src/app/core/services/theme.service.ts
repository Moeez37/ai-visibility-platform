import { DOCUMENT, Injectable, effect, inject, signal } from '@angular/core';

const STORAGE_KEY = 'ai-visibility-theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  readonly isDark = signal(this.initialIsDark());

  constructor() {
    effect(() => {
      this.document.documentElement.classList.toggle('dark', this.isDark());
    });
  }

  toggle(): void {
    this.isDark.update((isDark) => !isDark);
    try {
      localStorage.setItem(STORAGE_KEY, this.isDark() ? 'dark' : 'light');
    } catch {
      // Storage can be blocked; the toggle still works for this visit.
    }
  }

  private initialIsDark(): boolean {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return saved === 'dark';
      }
    } catch {
      // Fall through to the system preference.
    }
    return this.document.defaultView?.matchMedia('(prefers-color-scheme: dark)').matches ?? false;
  }
}
