import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, map } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  BusinessProfile,
  ProfileCreateRequest,
  ProfileListResponse,
} from '../../shared/models/profile.model';
import { rethrowFriendly } from './http-error';

@Injectable({ providedIn: 'root' })
export class ProfileService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/api/v1/profiles`;

  list(): Observable<BusinessProfile[]> {
    return this.http.get<ProfileListResponse>(this.baseUrl).pipe(
      map((response) => response.items),
      catchError(rethrowFriendly),
    );
  }

  get(profileUuid: string): Observable<BusinessProfile> {
    return this.http
      .get<BusinessProfile>(`${this.baseUrl}/${profileUuid}`)
      .pipe(catchError(rethrowFriendly));
  }

  create(request: ProfileCreateRequest): Observable<BusinessProfile> {
    return this.http.post<BusinessProfile>(this.baseUrl, request).pipe(catchError(rethrowFriendly));
  }
}
