"""Test observable failure behavior and evidence sufficiency, not just formulas."""
import json
from pathlib import Path

import pytest

from policy_retrieval.baseline import PageIndex, assess, run


def test_unscoped_search_ties_oov_and_raw_input_preservation():
    pages = {('z.pdf', 1): 'maternity\n  benefit', ('a.pdf', 1): 'maternity\n  benefit'}
    original = dict(pages)
    index = PageIndex(pages, r'(?u)\b\w\w+\b')
    assert index.search('maternity', 2)[0][0] == ('a.pdf', 1)
    assert index.search('unknownword', 2) == []
    assert pages == original


def test_multiple_spans_on_one_page_deduplicate_but_two_pages_require_both():
    record = {'evidence_spans': [
        {'source_file': 'a.pdf', 'source_page': 1},
        {'source_file': 'a.pdf', 'source_page': 1},
        {'source_file': 'a.pdf', 'source_page': 2},
    ]}
    hits = [{'source_file': 'a.pdf', 'page_number': 1, 'rank': 1},
            {'source_file': 'wrong.pdf', 'page_number': 2, 'rank': 2},
            {'source_file': 'a.pdf', 'page_number': 2, 'rank': 3}]
    result = assess(record, hits, [1, 2, 3])
    assert result['at_k']['1']['gold_page_recall'] == .5
    assert not result['at_k']['2']['all_gold_pages_retrieved']
    assert result['at_k']['2']['wrong_document_count'] == 1
    assert result['at_k']['3']['all_gold_pages_retrieved']


def baseline(tmp_path, dataset=Path('evals/retrieval_pilot.draft.json')):
    return run(dataset, Path('artifacts/extraction/policy_pages.jsonl'),
               Path('corpus/metadata.json'), Path('corpus/policy_wordings'),
               Path('evals/retrieval_baseline.config.json'), tmp_path)


def test_refuses_examples_only(tmp_path):
    with pytest.raises(ValueError, match='must not be scored'):
        baseline(tmp_path, Path('evals/gold_dataset.examples.json'))


def test_repeated_runs_preserve_inputs_ids_ranking_scores_and_accounting(tmp_path):
    paths = [Path('artifacts/extraction/policy_pages.jsonl'),
             Path('artifacts/extraction/extraction_metrics.json'), Path('corpus/metadata.json')]
    before = [path.read_bytes() for path in paths]
    first = baseline(tmp_path / 'one')
    second = baseline(tmp_path / 'two')
    def stable_rows(path):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        for row in rows:
            row.pop('retrieval_latency_ms')
            row.pop('query_wall_latency_ms')
        return rows
    assert stable_rows(tmp_path / 'one/query_results.jsonl') == stable_rows(tmp_path / 'two/query_results.jsonl')
    assert first['experiment_id'] == second['experiment_id']
    assert first['pages_indexed'] == 170
    assert first['aggregate']['n'] == 10
    assert first['slices']['table_dependent']['n'] == 4
    assert first['slices']['plus_problem_pages']['n'] == 3
    assert first['token_usage']['llm_input_tokens'] == 0
    assert first['cost_per_experiment']['paid_api_cost'] == 0
    assert first['cost_per_experiment']['compute_cost'] is None
    assert first['version_slice']['status'] == 'not_testable'
    assert [path.read_bytes() for path in paths] == before


def test_failed_queries_remain_in_denominator_and_are_logged(tmp_path, monkeypatch):
    def fail(self, question, k):
        raise RuntimeError('simulated retrieval failure')
    monkeypatch.setattr(PageIndex, 'search', fail)
    result = baseline(tmp_path)
    assert result['aggregate']['runtime_failures'] == 10
    assert result['aggregate']['at_k']['10']['page_sufficiency_rate'] == 0
    assert result['cost_per_experiment']['successful_queries'] == 0
    assert result['cost_per_experiment']['paid_api_cost_per_successful_query'] is None
    rows = [json.loads(line) for line in (tmp_path / 'query_results.jsonl').read_text().splitlines()]
    assert all(row['error']['type'] == 'RuntimeError' for row in rows)


def test_rejects_incomplete_extraction_instead_of_scoring(tmp_path):
    pages = Path('artifacts/extraction/policy_pages.jsonl').read_text().splitlines()
    path = tmp_path / 'missing.jsonl'
    path.write_text('\n'.join(pages[1:]) + '\n')
    with pytest.raises(ValueError, match='coverage'):
        run(Path('evals/retrieval_pilot.draft.json'), path, Path('corpus/metadata.json'),
            Path('corpus/policy_wordings'), Path('evals/retrieval_baseline.config.json'), tmp_path / 'out')
