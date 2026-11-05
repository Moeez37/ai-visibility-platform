import { DecimalPipe } from '@angular/common';
import { Component, DestroyRef, OnInit, computed, inject, input, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSliderModule } from '@angular/material/slider';
import { MatTableModule } from '@angular/material/table';
import { EMPTY, Subject, catchError, debounceTime, merge, switchMap, tap } from 'rxjs';

import { CsvExportService } from '../../../core/services/csv-export.service';
import { NotificationService } from '../../../core/services/notification.service';
import { PipelineService } from '../../../core/services/pipeline.service';
import { QueryService } from '../../../core/services/query.service';
import { SkeletonComponent } from '../../../shared/components/skeleton.component';
import { StateMessageComponent } from '../../../shared/components/state-message.component';
import { DiscoveredQuery, VisibilityStatus } from '../../../shared/models/query.model';

@Component({
  selector: 'app-queries-table',
  imports: [
    DecimalPipe,
    MatButtonModule,
    MatChipsModule,
    MatFormFieldModule,
    MatIconModule,
    MatPaginatorModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatSliderModule,
    MatTableModule,
    ReactiveFormsModule,
    SkeletonComponent,
    StateMessageComponent,
  ],
  templateUrl: './queries-table.component.html',
  styleUrl: './queries-table.component.scss',
})
export class QueriesTableComponent implements OnInit {
  private readonly queryService = inject(QueryService);
  private readonly pipelineService = inject(PipelineService);
  private readonly notifications = inject(NotificationService);
  private readonly csvExport = inject(CsvExportService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly reload$ = new Subject<void>();
  private readonly resultsChanged$ = toObservable(this.pipelineService.resultsVersion);

  readonly uuid = input.required<string>();

  protected readonly columns = ['query', 'volume', 'difficulty', 'score', 'visibility', 'action'];
  protected readonly filters = new FormGroup({
    minScore: new FormControl(0, { nonNullable: true }),
    status: new FormControl<VisibilityStatus | null>(null),
  });

  protected readonly loading = signal(true);
  protected readonly exporting = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly queries = signal<DiscoveredQuery[]>([]);
  protected readonly total = signal(0);
  protected readonly pageIndex = signal(0);
  protected readonly pageSize = signal(10);
  protected readonly rechecking = signal<ReadonlySet<string>>(new Set());
  protected readonly filtersActive = signal(false);
  protected readonly isEmpty = computed(
    () => !this.loading() && !this.error() && this.total() === 0,
  );

  ngOnInit(): void {
    const filterChanges$ = this.filters.valueChanges.pipe(
      debounceTime(250),
      tap(() => {
        this.pageIndex.set(0);
        const { minScore, status } = this.filters.getRawValue();
        this.filtersActive.set(minScore > 0 || status !== null);
      }),
    );

    merge(filterChanges$, this.reload$, this.resultsChanged$)
      .pipe(
        tap(() => {
          this.loading.set(true);
          this.error.set(null);
        }),
        switchMap(() =>
          this.queryService
            .list(this.uuid(), {
              ...this.filters.getRawValue(),
              page: this.pageIndex() + 1,
              perPage: this.pageSize(),
            })
            .pipe(
              catchError((error: Error) => {
                this.error.set(error.message);
                this.loading.set(false);
                return EMPTY;
              }),
            ),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((page) => {
        this.queries.set(page.items);
        this.total.set(page.total);
        this.loading.set(false);
      });
  }

  protected reload(): void {
    this.reload$.next();
  }

  protected onPage(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
    this.reload$.next();
  }

  protected recheck(query: DiscoveredQuery): void {
    this.setRechecking(query.query_uuid, true);
    this.queryService
      .recheck(query.query_uuid)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (updated) => {
          this.queries.update((rows) =>
            rows.map((row) => (row.query_uuid === updated.query_uuid ? updated : row)),
          );
          this.setRechecking(query.query_uuid, false);
          this.notifications.success('Recheck done.');
        },
        error: (error: Error) => {
          this.setRechecking(query.query_uuid, false);
          this.notifications.error(error.message);
        },
      });
  }

  protected exportCsv(): void {
    this.exporting.set(true);
    this.queryService
      .listAll(this.uuid(), this.filters.getRawValue())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (queries) => {
          this.csvExport.download(queries, 'queries.csv');
          this.exporting.set(false);
        },
        error: (error: Error) => {
          this.exporting.set(false);
          this.notifications.error(error.message);
        },
      });
  }

  protected scoreClass(score: number | null): string {
    if (score === null) {
      return 'chip-grey';
    }
    if (score >= 0.7) {
      return 'chip-green';
    }
    return score >= 0.4 ? 'chip-yellow' : 'chip-red';
  }

  private setRechecking(queryUuid: string, active: boolean): void {
    this.rechecking.update((current) => {
      const next = new Set(current);
      if (active) {
        next.add(queryUuid);
      } else {
        next.delete(queryUuid);
      }
      return next;
    });
  }
}
