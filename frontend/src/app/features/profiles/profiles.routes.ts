import { Routes } from '@angular/router';

export const profilesRoutes: Routes = [
  {
    path: 'new',
    loadComponent: () =>
      import('./profile-form/profile-form.component').then((m) => m.ProfileFormComponent),
  },
];
