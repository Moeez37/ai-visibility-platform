import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'profiles',
    loadChildren: () => import('./features/profiles/profiles.routes').then((m) => m.profilesRoutes),
  },
  { path: '**', redirectTo: '' },
];
