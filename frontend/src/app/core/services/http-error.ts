import { HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';

interface ApiErrorBody {
  error?: {
    message?: string;
    details?: { field: string; message: string }[];
  };
}

export function friendlyMessage(response: HttpErrorResponse): string {
  if (response.status === 0) {
    return `Can't reach the API at ${environment.apiUrl}. Check that the backend is running.`;
  }
  const body = response.error as ApiErrorBody | null;
  const details = body?.error?.details ?? [];
  if (details.length > 0) {
    return details.map((detail) => `${detail.field}: ${detail.message}`).join(' ');
  }
  return body?.error?.message || 'Something went wrong. Please try again.';
}

export function rethrowFriendly(response: HttpErrorResponse): Observable<never> {
  return throwError(() => new Error(friendlyMessage(response)));
}
