import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, map } from 'rxjs';

import { environment } from '../../../environments/environment';
import { DiscoveredQuery, PagedQueries, QueryFilters } from '../../shared/models/query.model';
import { rethrowFriendly } from './http-error';

const API_MAX_PER_PAGE = 100;

@Injectable({ providedIn: 'root' })
export class QueryService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/api/v1`;

  list(profileUuid: string, filters: QueryFilters = {}): Observable<PagedQueries> {
    let params = new HttpParams()
      .set('page', filters.page ?? 1)
      .set('per_page', filters.perPage ?? 20);
    if (filters.minScore) {
      params = params.set('min_score', filters.minScore);
    }
    if (filters.status) {
      params = params.set('status', filters.status);
    }
    return this.http
      .get<PagedQueries>(`${this.baseUrl}/profiles/${profileUuid}/queries`, { params })
      .pipe(catchError(rethrowFriendly));
  }

  // A run stores at most 20 queries, so one maximum-size page always holds them all.
  listAll(profileUuid: string, filters: QueryFilters = {}): Observable<DiscoveredQuery[]> {
    return this.list(profileUuid, { ...filters, page: 1, perPage: API_MAX_PER_PAGE }).pipe(
      map((response) => response.items),
    );
  }

  recheck(queryUuid: string): Observable<DiscoveredQuery> {
    return this.http
      .post<DiscoveredQuery>(`${this.baseUrl}/queries/${queryUuid}/recheck`, null)
      .pipe(catchError(rethrowFriendly));
  }
}
