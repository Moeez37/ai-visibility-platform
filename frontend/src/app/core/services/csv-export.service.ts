import { DOCUMENT, Injectable, inject } from '@angular/core';

import { DiscoveredQuery } from '../../shared/models/query.model';

const HEADERS = [
  'Query',
  'Search volume',
  'Difficulty',
  'Opportunity score',
  'Visibility',
  'Position',
  'Discovered at',
];

function csvCell(value: string | number | null): string {
  let text = value === null ? '' : String(value);
  // Spreadsheets run cells starting with these as formulas, and this text comes from an LLM.
  if (typeof value === 'string' && /^[=+\-@\t\r]/.test(text)) {
    text = `'${text}`;
  }
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function queriesToCsv(queries: DiscoveredQuery[]): string {
  const rows = queries.map((query) => [
    query.query_text,
    query.estimated_search_volume,
    query.competitive_difficulty,
    query.opportunity_score,
    query.status,
    query.visibility_position,
    query.discovered_at,
  ]);
  return [HEADERS, ...rows].map((row) => row.map(csvCell).join(',')).join('\r\n');
}

@Injectable({ providedIn: 'root' })
export class CsvExportService {
  private readonly document = inject(DOCUMENT);

  download(queries: DiscoveredQuery[], filename: string): void {
    const url = URL.createObjectURL(new Blob([queriesToCsv(queries)], { type: 'text/csv' }));
    const link = this.document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }
}
