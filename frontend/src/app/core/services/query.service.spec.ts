import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { QueryService } from './query.service';

describe('QueryService', () => {
  let service: QueryService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(QueryService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('sends only the filters that are set', () => {
    service.list('abc', { minScore: 0.5, status: 'visible', page: 2, perPage: 5 }).subscribe();

    const request = http.expectOne((req) => req.url.endsWith('/api/v1/profiles/abc/queries'));
    expect(request.request.params.toString()).toBe(
      'page=2&per_page=5&min_score=0.5&status=visible',
    );
    request.flush({ items: [], page: 2, per_page: 5, total: 0, pages: 0 });
  });

  it('leaves out a zero minimum score and an empty status', () => {
    service.list('abc', { minScore: 0, status: null }).subscribe();

    const request = http.expectOne((req) => req.url.endsWith('/queries'));
    expect(request.request.params.toString()).toBe('page=1&per_page=20');
    request.flush({ items: [], page: 1, per_page: 20, total: 0, pages: 0 });
  });

  it('turns API validation details into a readable message', () => {
    let message = '';
    service.list('abc').subscribe({ error: (error: Error) => (message = error.message) });

    http
      .expectOne((req) => req.url.endsWith('/queries'))
      .flush(
        {
          error: {
            code: 'validation_error',
            message: 'The request is not valid.',
            details: [{ field: 'per_page', message: 'Too large' }],
          },
        },
        { status: 400, statusText: 'Bad Request' },
      );

    expect(message).toBe('per_page: Too large');
  });

  it('explains when the backend cannot be reached', () => {
    let message = '';
    service.recheck('q1').subscribe({ error: (error: Error) => (message = error.message) });

    http
      .expectOne((req) => req.url.endsWith('/queries/q1/recheck'))
      .error(new ProgressEvent('error'));

    expect(message).toContain('Check that the backend is running');
  });
});
