import math
from collections.abc import Iterable

VOLUME_CEILING = 100_000
VOLUME_WEIGHT = 0.55
EASE_WEIGHT = 0.45


def visibility_gap(domain_visible: bool, position: int | None) -> float:
    if not domain_visible:
        return 1.0
    # Ranking first leaves little to gain; lower placements leave more, capped below "absent".
    return min(0.1 + 0.15 * ((position or 1) - 1), 0.7)


def opportunity_score(
    search_volume: int, difficulty: int, domain_visible: bool, position: int | None
) -> float:
    capped_volume = min(max(search_volume, 0), VOLUME_CEILING)
    # Log scale, so one huge head term doesn't flatten every other query to near zero.
    demand = math.log10(capped_volume + 1) / math.log10(VOLUME_CEILING + 1)
    ease = 1 - min(max(difficulty, 0), 100) / 100
    score = (VOLUME_WEIGHT * demand + EASE_WEIGHT * ease) * visibility_gap(domain_visible, position)
    # Two decimals, so the displayed value, its colour band and the min_score filter always agree.
    return round(score, 2)


def normalize_domain(value: str) -> str:
    domain = value.strip().lower().removeprefix("https://").removeprefix("http://")
    return domain.split("/")[0].removeprefix("www.")


def _compact(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def find_position(
    mentions: Iterable[tuple[str, str | None]], domain: str, brand_name: str
) -> int | None:
    target = normalize_domain(domain)
    brand_names = {_compact(brand_name), _compact(target.split(".")[0])}
    for position, (name, mention_domain) in enumerate(mentions, start=1):
        if mention_domain:
            mentioned = normalize_domain(mention_domain)
            if mentioned == target or mentioned.endswith(f".{target}"):
                return position
        if _compact(name) in brand_names:
            return position
    return None
