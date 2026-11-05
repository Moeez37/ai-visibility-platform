import { DiscoveredQuery } from '../../shared/models/query.model';
import { queriesToCsv } from './csv-export.service';

function queryWithText(query_text: string): DiscoveredQuery {
  return {
    query_uuid: 'q1',
    profile_uuid: 'p1',
    run_uuid: 'r1',
    query_text,
    estimated_search_volume: null,
    competitive_difficulty: 40,
    opportunity_score: 0.5,
    domain_visible: null,
    visibility_position: null,
    status: 'unknown',
    discovered_at: '2026-01-01',
  };
}

describe('queriesToCsv', () => {
  it('quotes commas and doubles embedded quotes', () => {
    const row = queriesToCsv([queryWithText('Is "A", or B, better?')]).split('\r\n')[1];

    expect(row).toBe('"Is ""A"", or B, better?",,40,0.5,unknown,,2026-01-01');
  });

  it('stops LLM text from running as a spreadsheet formula', () => {
    const row = queriesToCsv([queryWithText('=HYPERLINK("http://evil.test")')]).split('\r\n')[1];

    expect(row.startsWith(`"'=HYPERLINK`)).toBe(true);
  });
});
