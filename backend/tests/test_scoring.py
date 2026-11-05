import pytest

from app.utils.scoring import find_position, opportunity_score


def test_absent_high_volume_easy_query_outranks_every_weaker_case():
    best = opportunity_score(50_000, 20, False, None)
    assert best > opportunity_score(500, 20, False, None)
    assert best > opportunity_score(50_000, 90, False, None)
    assert best > opportunity_score(50_000, 20, True, 3)


def test_lower_position_scores_higher_than_first_place():
    assert opportunity_score(5000, 40, True, 4) > opportunity_score(5000, 40, True, 1)


@pytest.mark.parametrize(
    "volume, difficulty",
    [(0, 100), (10_000_000, 0), (-5, 150)],
)
def test_score_stays_in_range_for_extreme_estimates(volume, difficulty):
    assert 0 <= opportunity_score(volume, difficulty, False, None) <= 1


@pytest.mark.parametrize(
    "mentions, expected",
    [
        ([("Clearscope", "clearscope.io"), ("Surfer", "www.surferseo.com")], 2),
        ([("Surfer SEO", None)], 1),
        ([("Blog", "https://blog.surferseo.com/post")], 1),
        ([("surferseo", None)], 1),
        ([("Notsurferseo", "notsurferseo.com")], None),
        ([], None),
    ],
)
def test_find_position_matches_domain_or_brand(mentions, expected):
    assert find_position(mentions, "surferseo.com", "Surfer SEO") == expected
