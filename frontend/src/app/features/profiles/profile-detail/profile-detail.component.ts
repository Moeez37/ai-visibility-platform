import { DecimalPipe } from '@angular/common';
import { Component, OnDestroy, OnInit, computed, inject, input, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';

import { NotificationService } from '../../../core/services/notification.service';
import { PipelineService } from '../../../core/services/pipeline.service';
import { ProfileService } from '../../../core/services/profile.service';
import { SkeletonComponent } from '../../../shared/components/skeleton.component';
import { StateMessageComponent } from '../../../shared/components/state-message.component';
import { BusinessProfile, PipelineRun } from '../../../shared/models/profile.model';

const OFFLINE_MODEL = 'offline-demo';

@Component({
  selector: 'app-profile-detail',
  imports: [
    DecimalPipe,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTabsModule,
    RouterLink,
    RouterLinkActive,
    RouterOutlet,
    SkeletonComponent,
    StateMessageComponent,
  ],
  templateUrl: './profile-detail.component.html',
  styleUrl: './profile-detail.component.scss',
})
export class ProfileDetailComponent implements OnInit, OnDestroy {
  private readonly profileService = inject(ProfileService);
  private readonly pipelineService = inject(PipelineService);
  private readonly notifications = inject(NotificationService);
  private readonly destroy$ = new Subject<void>();

  readonly uuid = input.required<string>();

  protected readonly tabs = [
    { path: 'queries', label: 'Queries' },
    { path: 'chart', label: 'Chart' },
    { path: 'recommendations', label: 'Recommendations' },
  ];

  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly profile = signal<BusinessProfile | null>(null);
  protected readonly run = signal<PipelineRun | null>(null);
  protected readonly starting = signal(false);
  protected readonly running = computed(() => this.starting() || this.run()?.status === 'running');
  protected readonly isOffline = computed(() => this.run()?.llm_model === OFFLINE_MODEL);

  ngOnInit(): void {
    this.load();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  protected load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.profileService
      .get(this.uuid())
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (profile) => {
          this.profile.set(profile);
          this.run.set(profile.latest_run);
          this.loading.set(false);
          if (profile.latest_run?.status === 'running') {
            this.followRun(profile.latest_run.run_uuid);
          }
        },
        error: (error: Error) => {
          this.error.set(error.message);
          this.loading.set(false);
        },
      });
  }

  protected startRun(): void {
    this.starting.set(true);
    this.pipelineService
      .start(this.uuid())
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (run) => {
          this.run.set(run);
          this.starting.set(false);
          this.notifications.success('Pipeline started.');
          this.followRun(run.run_uuid);
        },
        error: (error: Error) => {
          this.starting.set(false);
          this.notifications.error(error.message);
        },
      });
  }

  private followRun(runUuid: string): void {
    this.pipelineService.pollRun(runUuid, this.destroy$).subscribe({
      next: (run) => {
        this.run.set(run);
        if (run.status !== 'running') {
          this.pipelineService.markResultsChanged();
          if (run.status === 'completed') {
            this.notifications.success('Pipeline complete.');
          } else {
            this.notifications.error(run.error_message ?? 'The pipeline failed.');
          }
        }
      },
      error: (error: Error) => {
        this.run.update((run) =>
          run ? { ...run, status: 'failed', error_message: error.message } : run,
        );
        this.notifications.error(`Lost contact with the pipeline run. ${error.message}`);
      },
    });
  }
}
