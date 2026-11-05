import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { RouterLink } from '@angular/router';
import { exhaustMap, forkJoin, takeWhile, timer } from 'rxjs';

import { PipelineService } from '../../core/services/pipeline.service';
import { ProfileService } from '../../core/services/profile.service';
import { SkeletonComponent } from '../../shared/components/skeleton.component';
import { StateMessageComponent } from '../../shared/components/state-message.component';
import { BusinessProfile, DashboardSummary, RunStatus } from '../../shared/models/profile.model';

const REFRESH_WHILE_RUNNING_MS = 3000;

@Component({
  selector: 'app-dashboard',
  imports: [
    DatePipe,
    DecimalPipe,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatIconModule,
    MatListModule,
    RouterLink,
    SkeletonComponent,
    StateMessageComponent,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private readonly pipelineService = inject(PipelineService);
  private readonly profileService = inject(ProfileService);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly summary = signal<DashboardSummary | null>(null);
  protected readonly profiles = signal<BusinessProfile[]>([]);
  protected readonly hasData = computed(() => this.profiles().length > 0);

  ngOnInit(): void {
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.error.set(null);
    timer(0, REFRESH_WHILE_RUNNING_MS)
      .pipe(
        exhaustMap(() =>
          forkJoin({
            summary: this.pipelineService.summary(),
            profiles: this.profileService.list(),
          }),
        ),
        takeWhile(
          ({ summary }) => summary.recent_runs.some((run) => run.status === 'running'),
          true,
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: ({ summary, profiles }) => {
          this.summary.set(summary);
          this.profiles.set(profiles);
          this.error.set(null);
          this.loading.set(false);
        },
        error: (error: Error) => {
          this.error.set(error.message);
          this.loading.set(false);
        },
      });
  }

  protected statusClass(status: RunStatus): string {
    return { completed: 'chip-green', failed: 'chip-red', running: 'chip-blue' }[status];
  }
}
