import { Routes } from '@angular/router';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';

export const queriesRoutes: Routes = [
  {
    path: 'queries',
    loadComponent: () =>
      import('./queries-table/queries-table.component').then((m) => m.QueriesTableComponent),
  },
  {
    path: 'chart',
    providers: [provideCharts(withDefaultRegisterables())],
    loadComponent: () =>
      import('./opportunity-chart/opportunity-chart.component').then(
        (m) => m.OpportunityChartComponent,
      ),
  },
];
