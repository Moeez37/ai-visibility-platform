import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Subject } from 'rxjs';
import { vi } from 'vitest';

import { PipelineRun, RunStatus } from '../../shared/models/profile.model';
import { PipelineService } from './pipeline.service';

function runWithStatus(status: RunStatus): PipelineRun {
  return {
    run_uuid: 'r1',
    profile_uuid: 'p1',
    profile_name: 'Surfer SEO',
    status,
    llm_model: 'scripted',
    queries_discovered: 0,
    queries_scored: 0,
    tokens_used: 0,
    error_message: null,
    started_at: '2026-01-01T00:00:00+00:00',
    completed_at: null,
  };
}

describe('PipelineService.pollRun', () => {
  let service: PipelineService;
  let http: HttpTestingController;

  beforeEach(() => {
    vi.useFakeTimers();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(PipelineService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    vi.useRealTimers();
    http.verify();
  });

  it('polls until the run leaves running, emits the final state, then stops', () => {
    const seen: RunStatus[] = [];
    service.pollRun('r1', new Subject()).subscribe((run) => seen.push(run.status));

    http.expectOne((req) => req.url.endsWith('/runs/r1')).flush(runWithStatus('running'));
    vi.advanceTimersByTime(2000);
    http.expectOne((req) => req.url.endsWith('/runs/r1')).flush(runWithStatus('completed'));
    vi.advanceTimersByTime(10000);

    expect(seen).toEqual(['running', 'completed']);
    http.expectNone((req) => req.url.endsWith('/runs/r1'));
  });

  it('stops polling when the stop signal fires', () => {
    const stop$ = new Subject<void>();
    service.pollRun('r1', stop$).subscribe();

    http.expectOne((req) => req.url.endsWith('/runs/r1')).flush(runWithStatus('running'));
    stop$.next();
    vi.advanceTimersByTime(10000);

    http.expectNone((req) => req.url.endsWith('/runs/r1'));
  });

  it('keeps following a run through one failed poll', () => {
    const seen: RunStatus[] = [];
    service.pollRun('r1', new Subject()).subscribe((run) => seen.push(run.status));

    http.expectOne((req) => req.url.endsWith('/runs/r1')).error(new ProgressEvent('error'));
    vi.advanceTimersByTime(2000);
    http.expectOne((req) => req.url.endsWith('/runs/r1')).flush(runWithStatus('completed'));

    expect(seen).toEqual(['completed']);
  });
});
