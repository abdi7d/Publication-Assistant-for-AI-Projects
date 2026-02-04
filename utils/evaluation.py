from typing import List, Dict


def evaluate_recommendations(recommendation_obj) -> Dict[str, float]:
    """Lightweight evaluation placeholder.

    Returns simple counts and a mock score for use in tests or demos.
    """
    tags = getattr(recommendation_obj, 'tags', []) or []
    titles = getattr(recommendation_obj, 'title_suggestions', []) or []
    desc = getattr(recommendation_obj, 'short_description', '') or ''
    score = min(1.0, (len(tags) * 0.05) +
                (len(titles) * 0.1) + (0.2 if desc else 0))
    return {
        "tag_count": len(tags),
        "title_count": len(titles),
        "has_description": 1.0 if desc else 0.0,
        "mock_score": round(score, 2)
    }
