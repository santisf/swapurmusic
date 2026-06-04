import os
import re
import json
import unicodedata

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

# Try local sentence-transformers as secondary local AI fallback
try:
    from sentence_transformers import SentenceTransformer, util
    HAS_SENTENCE_TRANSFORMERS = True
except Exception:
    HAS_SENTENCE_TRANSFORMERS = False

# Try Gemini API client as primary serverless AI fallback
HAS_GEMINI = False
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key and gemini_api_key != "MY_GEMINI_API_KEY":
    try:
        # We can support either the modern google-genai or legacy google-generativeai
        try:
            from google import genai
            from google.genai import types
            ai_client = genai.Client(api_key=gemini_api_key)
            USE_NEW_SDK = True
            HAS_GEMINI = True
        except ImportError:
            import google.generativeai as gen_ai
            gen_ai.configure(api_key=gemini_api_key)
            USE_NEW_SDK = False
            HAS_GEMINI = True
    except Exception as e:
        print(f"Failed to initialize Gemini AI Matcher client: {e}")

class Matcher:
    def __init__(self):
        self.model = None
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                # Load specified local model on CPU
                self.model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
            except Exception as e:
                print(f"Warning: SentenceTransformer 'all-MiniLM-L6-v2' could not load: {e}")

    def clean_text(self, text):
        if not text:
            return ""
        # Remove any parentheses/brackets that contain common video/audio metadata tags
        text = re.sub(
            r'[\(\[][^\)\]]*(?:video|audio|official|music|clip|hd|definition|remastered|remaster|lyrics?|version|live|acoustic)[^\)\]]*[\)\]]',
            '',
            text,
            flags=re.IGNORECASE
        )
        # Remove any empty or trailing parentheses/brackets
        text = re.sub(r'\(\s*\)|\[\s*\]', '', text)
        # Clean up multiple whitespaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()

    def normalize_text(self, text: str) -> str:
        """
        Full normalization:
        - remove diacritics
        - convert to lowercase
        - strip punctuation (keep alphanumerics and spaces)
        - collapse multiple spaces
        """
        if not text:
            return ""
        # 1. Remove diacritics
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ASCII', 'ignore').decode('ASCII')
        # 2. Lowercase
        text = text.lower()
        # 3. Strip punctuation (keep only alphanumerics and spaces)
        text = re.sub(r"[^\w\s]", " ", text)
        # 4. Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def check_version_mismatch(self, title1, title2):
        t1, t2 = title1.lower(), title2.lower()
        keywords = ['remix', 'live', 'acoustic', 'unplugged', 'cover', 'instrumental', 'slowed', 'reverb', 'synthwave', 'demo', 'radio edit']
        for kw in keywords:
            has1 = kw in t1
            has2 = kw in t2
            if has1 != has2:
                return True
        return False

    def levenshtein_distance(self, s1, s2):
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + 1)
        return dp[m][n]

    def token_sort_ratio(self, s1, s2):
        if HAS_RAPIDFUZZ:
            return fuzz.token_sort_ratio(s1, s2)

        # Manual fallback token_sort_ratio
        clean1 = self.clean_text(s1)
        clean2 = self.clean_text(s2)
        if clean1 == clean2:
            return 100

        t1 = sorted(clean1.split())
        t2 = sorted(clean2.split())

        sorted1 = " ".join(t1)
        sorted2 = " ".join(t2)

        max_len = max(len(sorted1), len(sorted2))
        if max_len == 0:
            return 100

        dist = self.levenshtein_distance(sorted1, sorted2)
        return round(((max_len - dist) / max_len) * 100)

    def partial_ratio(self, s1, s2):
        """Partial ratio matching for typo tolerance"""
        if HAS_RAPIDFUZZ:
            return fuzz.partial_ratio(s1, s2)
        clean1 = self.clean_text(s1)
        clean2 = self.clean_text(s2)
        if clean1 in clean2 or clean2 in clean1:
            return 100
        # Fallback to token sort
        return self.token_sort_ratio(s1, s2)

    def weighted_fuzzy_score(self, query, candidate, query_field, candidate_field):
        """
        Calculate weighted fuzzy score between two text fragments.
        Gives higher weight to title matches, lower to artist matches.
        Returns 0.0 to 1.0
        """
        q_text = self.normalize_text(query).lower()
        c_text = self.normalize_text(candidate).lower()

        if not q_text or not c_text:
            return 0.0

        # Use both token sort and partial ratio
        token_score = fuzz.token_sort_ratio(q_text, c_text) / 100.0 if HAS_RAPIDFUZZ else self.token_sort_ratio(q_text, c_text) / 100.0
        partial_scr = fuzz.partial_ratio(q_text, c_text) / 100.0 if HAS_RAPIDFUZZ else token_score

        # Combine scores - partial helps with typos
        combined = (token_score * 0.6 + partial_scr * 0.4)

        return round(combined, 3)

    def compute_score(self, song1, artist1, song2, artist2, candidate=None):
        """
        Compute a hybrid similarity score with improved ranking:
        - 40% embedding similarity (Gemini / Sentence‑Transformers)
        - 35% weighted fuzzy score (title vs artist)
        - 15% popularity
        - 10% exact title match bonus
        - Penalty: -0.2 if title fuzzy < 0.4 (hard penalty for mismatched titles)
        """
        # Normalise query strings
        q_title_norm = self.normalize_text(song1)
        q_artist_norm = self.normalize_text(artist1)
        c_title_norm = self.normalize_text(song2)
        c_artist_norm = self.normalize_text(artist2)

        clean_q = f"{q_title_norm} {q_artist_norm}"
        clean_t = f"{c_title_norm} {c_artist_norm}"

        # ---- 1️⃣ Weighted fuzzy scores ----
        title_fuzzy = self.weighted_fuzzy_score(q_title_norm, c_title_norm, song1, song2)
        artist_fuzzy = self.weighted_fuzzy_score(q_artist_norm, c_artist_norm, artist1, artist2)
        fuzzy_score_val = (title_fuzzy * 0.7 + artist_fuzzy * 0.3)

        # ---- 2️⃣ AI / semantic similarity ----
        ai_similarity_val = fuzzy_score_val  # default fallback

        # Priority A: Gemini evaluation (lightweight, API based)
        if HAS_GEMINI:
            try:
                prompt = f"""Match track item attributes representing semantic similarity.
Query: "{song1}" by "{artist1}"
Candidate: "{song2}" by "{artist2}"
Return only a JSON object matching this schema:
{{
  "semanticSimilarity": number (0.0 to 1.0),
  "isVersionMismatch": boolean
}}"""
                if USE_NEW_SDK:
                    res = ai_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                else:
                    model = gen_ai.GenerativeModel('gemini-2.5-flash')
                    res = model.generate_content(
                        prompt,
                        generation_config={"response_mime_type": "application/json"}
                    )
                text_out = res.text
                info = json.loads(text_out.strip())
                if info.get("isVersionMismatch"):
                    ai_similarity_val = info.get("semanticSimilarity", 0.0) * 0.4
                else:
                    ai_similarity_val = info.get("semanticSimilarity", 0.0)
            except Exception as e:
                print(f"Gemini math evaluation bypassed: {e}")
                ai_similarity_val = fuzzy_score_val

        # Priority B: Sentence‑Transformers evaluation (local deep embedding model)
        elif self.model:
            try:
                embeddings = self.model.encode([clean_q, clean_t], convert_to_tensor=True)
                cos_sim = util.cos_sim(embeddings[0], embeddings[1])
                ai_similarity_val = float(cos_sim.item())
                ai_similarity_val = max(0.0, min(1.0, ai_similarity_val))
            except Exception as e:
                print(f"SentenceTransformers evaluation bypassed: {e}")

        # ---- 3️⃣ Popularity weight (optional) ----
        pop_score = float(candidate.get("popularity", 0)) / 100.0 if candidate else 0.0

        # ---- 4️⃣ Exact match bonus ----
        bonus = 0.0
        if q_title_norm == c_title_norm:
            bonus += 0.1

        # ---- 5️⃣ Penalty for low title similarity ----
        # If title fuzzy score is very low, heavily penalize the final score
        penalty = 0.0
        if title_fuzzy < 0.4:
            penalty = 0.2  # Hard penalty for mismatched titles

        # ---- 6️⃣ Final weighted hybrid score ----
        final_score = (
            0.4 * ai_similarity_val +
            0.35 * fuzzy_score_val +
            0.15 * pop_score +
            bonus -
            penalty
        )

        # Clamp to [0, 1]
        final_score = max(0.0, min(1.0, final_score))
        return round(final_score, 3)

    def classify_match(self, score):
        if score >= 0.80:
            return "High", "🟢 High"
        elif score >= 0.65:
            return "Probable", "🟡 Probable"
        else:
            return "Low", "🔵 Low"

    def find_best_match(self, query_song, query_artist, candidates):
        if not candidates:
            return None, 0.0, "Not Found"

        best_candidate = None
        best_score = -1.0

        for candidate in candidates:
            c_song = candidate.get("title", "")
            c_artist = candidate.get("artist", "")
            # Pass the candidate to compute_score so we can use its popularity if present
            score = self.compute_score(query_song, query_artist, c_song, c_artist, candidate)
            if score > best_score:
                best_score = score
                best_candidate = candidate

        status = self.classify_match(best_score)[0]
        if status == "Not Found" or best_score < 0.60:
            return None, best_score, "Not Found"

        return best_candidate, best_score, status