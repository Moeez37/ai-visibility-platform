import { Component, DestroyRef, OnInit, computed, inject, input, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable, toSignal } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';

import { PipelineService } from '../../../core/services/pipeline.service';
import { RecommendationService } from '../../../core/services/recommendation.service';
import { SkeletonComponent } from '../../../shared/components/skeleton.component';
import { StateMessageComponent } from '../../../shared/components/state-message.component';
import {
  ContentRecommendation,
  ContentType,
  Priority,
} from '../../../shared/models/recommendation.model';

@Component({
  selector: 'app-recommendations-list',
  imports: [
    MatButtonModule,
    MatButtonToggleModule,
    MatCardModule,
    MatChipsModule,
    ReactiveFormsModule,
    SkeletonComponent,
    StateMessageComponent,
  ],
  templateUrl: './recommendations-list.component.html',
  styleUrl: './recommendations-list.component.scss',
})
export class RecommendationsListComponent implements OnInit {
  private readonly recommendationService = inject(RecommendationService);
  private readonly pipelineService = inject(PipelineService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly resultsChanged$ = toObservable(this.pipelineService.resultsVersion);

  readonly uuid = input.required<string>();

  protected readonly priorityFilter = new FormControl<Priority | 'all'>('all', {
    nonNullable: true,
  });
  private readonly selectedPriority = toSignal(this.priorityFilter.valueChanges, {
    initialValue: 'all',
  });

  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly recommendations = signal<ContentRecommendation[]>([]);
  protected readonly visible = computed(() => {
    const priority = this.selectedPriority();
    return this.recommendations().filter(
      (item) => priority === 'all' || item.priority === priority,
    );
  });

  protected readonly typeLabels: Record<ContentType, string> = {
    blog_post: 'Blog post',
    landing_page: 'Landing page',
    faq: 'FAQ',
  };
  protected readonly priorityClasses: Record<Priority, string> = {
    high: 'chip-red',
    medium: 'chip-yellow',
    low: 'chip-green',
  };

  ngOnInit(): void {
    this.resultsChanged$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => this.load());
  }

  protected load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.recommendationService.list(this.uuid()).subscribe({
      next: (items) => {
        this.recommendations.set(items);
        this.loading.set(false);
      },
      error: (error: Error) => {
        this.error.set(error.message);
        this.loading.set(false);
      },
    });
  }
}
