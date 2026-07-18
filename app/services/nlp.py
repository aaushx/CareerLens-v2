import re

from sklearn.feature_extraction.text import TfidfVectorizer

from app.data.skills import ALL_SKILLS


def get_tfidf_vectorizer() -> TfidfVectorizer:
    """Create a new TfidfVectorizer instance for semantic similarity.
    TF-IDF is lightweight and works well for this use case without heavy ML models.
    This function is thread-safe and instantiates a new vectorizer on every call.
    """
    return TfidfVectorizer(max_features=5000, stop_words="english", lowercase=True)


def extract_skills(text_lower: str) -> list[str]:
    """Scans lowercase text against the technical skills catalog, returning matching skills list."""
    matches = []
    for skill in ALL_SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
        for m in re.finditer(pattern, text_lower):
            matches.append((m.start(), m.end(), skill))

    filtered_skills = set()
    for s1, e1, skill1 in matches:
        is_sub = False
        for s2, e2, skill2 in matches:
            if s2 <= s1 and e1 <= e2:
                if (s1, e1) != (s2, e2):
                    is_sub = True
                    break
                elif skill1 != skill2 and len(skill1) < len(skill2):
                    is_sub = True
                    break
        if not is_sub:
            filtered_skills.add(skill1)

    return list(filtered_skills)
