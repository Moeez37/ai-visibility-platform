import { Component, DestroyRef, OnInit, computed, inject, input, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { ChartConfiguration } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

import { PipelineService } from '../../../core/services/pipeline.service';
import { QueryService } from '../../../core/services/query.service';
import { ThemeService } from '../../../core/services/theme.service';
import { SkeletonComponent } from '../../../shared/components/skeleton.component';
import { StateMessageComponent } from '../../../shared/components/state-message.component';
import { DiscoveredQuery } from '../../../shared/models/query.model';

const VISIBLE_COLOUR = '#1f77d0';
const NOT_VISIBLE_COLOUR = '#f28c28';
const MAX_LABEL_LENGTH = 30;

function truncate(text: string): string {
  return text.length > MAX_LABEL_LENGTH ? `${text.slice(0, MAX_LABEL_LENGTH - 1)}…` : text;
}

@Component({
  selector: 'app-opportunity-chart',
  imports: [BaseChartDirective, MatButtonModule, SkeletonComponent, StateMessageComponent],
  template: `
    @if (loading()) {
      <app-skeleton [lines]="1" [lineHeight]="400" />
    } @else if (error(); as message) {
      <app-state-message
        icon="error_outline"
        title="Couldn't load the chart"
        [message]="message"
        tone="error"
      >
        <button mat-stroked-button type="button" (click)="load()">Try again</button>
      </app-state-message>
    } @else if (scored().length === 0) {
      <app-state-message
        icon="bar_chart"
        title="Nothing to chart yet"
        message="Run the pipeline to score queries by opportunity."
      />
    } @else {
      <div class="legend">
        <span><i [style.background]="visibleColour"></i>Domain visible</span>
        <span><i [style.background]="notVisibleColour"></i>Not visible</span>
      </div>
      <div class="chart">
        <canvas
          baseChart
          type="bar"
          role="img"
          [attr.aria-label]="'Opportunity score for ' + scored().length + ' queries'"
          [data]="chartData()"
          [options]="chartOptions()"
        ></canvas>
      </div>
      @if (unscoredCount() > 0) {
        <p class="muted">{{ unscoredCount() }} unscored queries are not shown.</p>
      }
    }
  `,
  styles: `
    .legend {
      display: flex;
      gap: 24px;
      margin-bottom: 12px;
    }
    .legend span {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .legend i {
      width: 14px;
      height: 14px;
      border-radius: 3px;
    }
    .chart {
      position: relative;
      height: 460px;
    }
  `,
})
export class OpportunityChartComponent implements OnInit {
  private readonly queryService = inject(QueryService);
  private readonly pipelineService = inject(PipelineService);
  private readonly theme = inject(ThemeService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly resultsChanged$ = toObservable(this.pipelineService.resultsVersion);

  readonly uuid = input.required<string>();

  protected readonly visibleColour = VISIBLE_COLOUR;
  protected readonly notVisibleColour = NOT_VISIBLE_COLOUR;
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  private readonly queries = signal<DiscoveredQuery[]>([]);

  protected readonly scored = computed(() =>
    this.queries().filter((query) => query.opportunity_score !== null),
  );
  protected readonly unscoredCount = computed(() => this.queries().length - this.scored().length);

  protected readonly chartData = computed<ChartConfiguration<'bar'>['data']>(() => ({
    labels: this.scored().map((query) => truncate(query.query_text)),
    datasets: [
      {
        label: 'Opportunity score',
        data: this.scored().map((query) => query.opportunity_score ?? 0),
        backgroundColor: this.scored().map((query) =>
          query.domain_visible ? VISIBLE_COLOUR : NOT_VISIBLE_COLOUR,
        ),
      },
    ],
  }));

  protected readonly chartOptions = computed<ChartConfiguration<'bar'>['options']>(() => {
    const text = this.theme.isDark() ? '#e3e3e3' : '#444746';
    const grid = this.theme.isDark() ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)';
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => this.scored()[items[0].dataIndex].query_text,
          },
        },
      },
      scales: {
        x: {
          ticks: { color: text, autoSkip: false, maxRotation: 60, minRotation: 45 },
          grid: { display: false },
        },
        y: {
          min: 0,
          max: 1,
          title: { display: true, text: 'Opportunity score', color: text },
          ticks: { color: text },
          grid: { color: grid },
        },
      },
    };
  });

  ngOnInit(): void {
    this.resultsChanged$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => this.load());
  }

  protected load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.queryService.listAll(this.uuid()).subscribe({
      next: (queries) => {
        this.queries.set(queries);
        this.loading.set(false);
      },
      error: (error: Error) => {
        this.error.set(error.message);
        this.loading.set(false);
      },
    });
  }
}
