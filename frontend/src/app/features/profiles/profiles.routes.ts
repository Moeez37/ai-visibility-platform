import { Routes } from '@angular/router';

export const profilesRoutes: Routes = [
  {
    path: 'new',
    loadComponent: () =>
      import('./profile-form/profile-form.component').then((m) => m.ProfileFormComponent),
  },
  {
    path: ':uuid',
    loadComponent: () =>
      import('./profile-detail/profile-detail.component').then((m) => m.ProfileDetailComponent),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'queries' },
      {
        path: '',
        loadChildren: () => import('../queries/queries.routes').then((m) => m.queriesRoutes),
      },
      {
        path: 'recommendations',
        loadComponent: () =>
          import('../recommendations/recommendations-list/recommendations-list.component').then(
            (m) => m.RecommendationsListComponent,
          ),
      },
    ],
  },
];
