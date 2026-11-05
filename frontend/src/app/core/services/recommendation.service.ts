import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, map } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  ContentRecommendation,
  RecommendationListResponse,
} from '../../shared/models/recommendation.model';
import { rethrowFriendly } from './http-error';

@Injectable({ providedIn: 'root' })
export class RecommendationService {
  private readonly http = inject(HttpClient);

  list(profileUuid: string): Observable<ContentRecommendation[]> {
    return this.http
      .get<RecommendationListResponse>(
        `${environment.apiUrl}/api/v1/profiles/${profileUuid}/recommendations`,
      )
      .pipe(
        map((response) => response.items),
        catchError(rethrowFriendly),
      );
  }
}
