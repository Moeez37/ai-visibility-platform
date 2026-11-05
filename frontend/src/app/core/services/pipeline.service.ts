import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import {
  Observable,
  catchError,
  interval,
  retry,
  startWith,
  switchMap,
  takeUntil,
  takeWhile,
  timer,
} from 'rxjs';

import { environment } from '../../../environments/environment';
import { DashboardSummary, PipelineRun } from '../../shared/models/profile.model';
import { rethrowFriendly } from './http-error';

const POLL_INTERVAL_MS = 2000;
const POLL_RETRIES = 3;

@Injectable({ providedIn: 'root' })
export class PipelineService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/api/v1`;

  // Bumped when a run finishes, so the profile tabs know to reload their data.
  readonly resultsVersion = signal(0);

  start(profileUuid: string): Observable<PipelineRun> {
    return this.http
      .post<PipelineRun>(`${this.baseUrl}/profiles/${profileUuid}/run`, null)
      .pipe(catchError(rethrowFriendly));
  }

  getRun(runUuid: string): Observable<PipelineRun> {
    return this.http
      .get<PipelineRun>(`${this.baseUrl}/runs/${runUuid}`)
      .pipe(catchError(rethrowFriendly));
  }

  pollRun(runUuid: string, stop$: Observable<unknown>): Observable<PipelineRun> {
    return interval(POLL_INTERVAL_MS).pipe(
      startWith(0),
      switchMap(() =>
        this.getRun(runUuid).pipe(
          retry({ count: POLL_RETRIES, delay: () => timer(POLL_INTERVAL_MS) }),
        ),
      ),
      takeWhile((run) => run.status === 'running', true),
      takeUntil(stop$),
    );
  }

  summary(): Observable<DashboardSummary> {
    return this.http
      .get<DashboardSummary>(`${this.baseUrl}/dashboard/summary`)
      .pipe(catchError(rethrowFriendly));
  }

  markResultsChanged(): void {
    this.resultsVersion.update((version) => version + 1);
  }
}
