# =============================================================
# Service Matching — Matching intelligent des transcriptions HTR
# =============================================================
# Algorithme multi-stratégie spécialisé pour les prescriptions
# médicales manuscrites, avec gestion des abréviations,
# noms partiels, erreurs OCR et dosages.
# =============================================================

import os
import re
import logging
from functools import lru_cache

from rapidfuzz import fuzz, process
from unidecode import unidecode

from backend.config import MEDS_CSV_PATH, MATCHING_CUTOFF
from backend.db.connection import check_connection
from backend.db.repositories import MedicamentRepo

logger = logging.getLogger(__name__)


# =============================================================
# Dictionnaire d'abréviations médicales bi-directionnel
# =============================================================
# Clé = abréviation fréquente en écriture manuscrite
# Valeur = liste de formes possibles dans la base de référence
#
# IMPORTANT : la base de référence utilise ELLE-MÊME des
# abréviations (CP, SP, GEL, SACH, etc.). Il ne faut donc
# PAS développer les abréviations en mots complets mais
# plutôt mapper les variantes manuscrites vers les formes
# effectivement utilisées dans la base.
# =============================================================

_ABBREV_TO_REF = {
    # Formes galéniques — écritures manuscrites → forme(s) dans la base
    "cp":       ["CP", "COMP", "CPR"],
    "cps":      ["CP", "COMP", "CPR"],
    "comp":     ["CP", "COMP", "CPR"],
    "cpr":      ["CP", "COMP", "CPR"],
    "comprime": ["CP", "COMP", "CPR"],
    "comprimé": ["CP", "COMP", "CPR"],
    "comprimes":["CP", "COMP", "CPR"],
    "comprimés":["CP", "COMP", "CPR"],

    "sp":       ["SP", "SIROP", "SIR"],
    "sir":      ["SP", "SIROP", "SIR"],
    "spr":      ["SP", "SIROP", "SPR"],
    "sirop":    ["SP", "SIROP", "SIR"],

    "gel":      ["GEL", "GELU", "GÉLULE"],
    "gelu":     ["GEL", "GELU"],
    "gelule":   ["GEL", "GELU"],
    "gélule":   ["GEL", "GELU"],
    "caps":     ["CAPS", "GEL", "GELU"],

    "inj":      ["INJ", "INJECT"],
    "inject":   ["INJ", "INJECT"],
    "injection":["INJ", "INJECT"],

    "amp":      ["AMP", "AMPOULE"],
    "ampoule":  ["AMP"],

    "sach":     ["SACH", "SACHET"],
    "sachet":   ["SACH", "SACHET"],

    "supp":     ["SUPPO", "SUPP"],
    "suppo":    ["SUPPO", "SUPP"],
    "suppositoire": ["SUPPO", "SUPP"],

    "sol":      ["SOL", "SOLUTION"],
    "solution": ["SOL"],

    "susp":     ["SUSP", "SUS"],
    "sus":      ["SUSP", "SUS"],
    "suspension": ["SUSP", "SUS"],

    "pdre":     ["PDR", "PDRE", "POUDRE"],
    "pdr":      ["PDR", "PDRE", "POUDRE"],
    "poudre":   ["PDR", "PDRE", "POUDRE"],

    "fl":       ["FL", "FLACON"],
    "flacon":   ["FL"],

    "cr":       ["CR", "CRM", "CREME", "CRÈME"],
    "crm":      ["CR", "CRM", "CREME"],
    "creme":    ["CR", "CRM", "CREME"],
    "crème":    ["CR", "CRM", "CREME"],

    "pom":      ["POM", "POMMADE"],
    "pommade":  ["POM", "POMMADE"],

    "gtte":     ["GTTE", "GOUTTE", "GTTES", "GOUTTES"],
    "goutte":   ["GTTE", "GTTES"],
    "gouttes":  ["GTTE", "GTTES"],

    "cy":       ["CY", "COLLYRE"],
    "collyre":  ["CY", "COLLYRE"],

    "eff":      ["EFF"],
    "effervescent": ["EFF"],
    "effervescents": ["EFF"],

    "buv":      ["BUV", "BUVABLE"],
    "buvable":  ["BUV"],

    "drag":     ["DRAG", "DRAGÉE", "DRAGEE"],
    "dragée":   ["DRAG"],

    "aer":      ["AER", "AEROSOL"],
    "aerosol":  ["AER"],

    "tb":       ["T", "TUBE"],
    "tube":     ["T"],
}


# =============================================================
# Nettoyage et normalisation
# =============================================================

def _normalize(text: str) -> str:
    """Normalise un texte pour le matching.
    
    - Majuscules
    - Suppression des accents
    - Remplacement des caractères spéciaux
    - Normalisation des espaces
    """
    if not text:
        return ""
    text = str(text).upper().strip()
    text = unidecode(text)  # Supprime accents : é→e, ô→o, etc.
    # Remplacer les séparateurs courants par des espaces
    text = re.sub(r"[/\\,;:(){}[\]_\-]+", " ", text)
    # Supprimer les caractères spéciaux restants sauf points et chiffres
    text = re.sub(r"[^A-Z0-9.\s]", "", text)
    # Normaliser les espaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_name_token(text: str) -> str:
    """Extrait le token principal (nom du médicament) du texte.
    
    Le nom est généralement le premier mot significatif (> 2 car)
    qui n'est pas un dosage ou une forme galénique.
    """
    tokens = text.split()
    dosage_forms = {
        "CP", "SP", "GEL", "GELU", "INJ", "AMP", "SOL", "SACH", "SUPP", "SUPPO",
        "COMP", "CPR", "SIR", "SIROP", "PDR", "PDRE", "FL", "CR", "CRM", "POM",
        "GTTE", "GTTES", "CY", "EFF", "BUV", "DRAG", "AER", "SUSP", "SUS",
        "CAPS", "PELL", "DISP", "CROQ", "GRAN", "SACH", "TUBE",
        "MG", "ML", "G", "KG", "MCG", "UI", "IU",
        "B", "BL", "BT", "T", "NF", "AFR", "AD", "ENF", "PED", "BB", "NN",
    }
    name_tokens = []
    for tok in tokens:
        clean = re.sub(r"[^A-Z]", "", tok)
        # Ignorer les dosages purs (chiffres + unité)
        if re.match(r"^\d+[.,]?\d*(MG|ML|G|MCG|UI|IU|%)?$", tok):
            continue
        # Ignorer les formes galéniques
        if clean in dosage_forms:
            continue
        # Ignorer les quantités pures
        if tok.replace(".", "").replace(",", "").isdigit():
            continue
        if len(clean) >= 2:
            name_tokens.append(tok)
    return " ".join(name_tokens)


def _extract_dosage(text: str) -> str:
    """Extrait les dosages d'un texte (ex: '500MG', '1G', '100MG/5ML')."""
    dosages = re.findall(r"\d+[.,]?\d*\s*(?:MG|ML|G|MCG|UI|IU|%)", text)
    return " ".join(dosages)


def _expand_abbreviations(text: str) -> list[str]:
    """Génère toutes les variantes possibles d'un texte en
    remplaçant les abréviations manuscrites par les formes de la base.
    
    Retourne une liste de variantes (la première = originale).
    """
    tokens = text.split()
    variants = [tokens[:]]  # commencer avec l'original
    
    for i, tok in enumerate(tokens):
        tok_lower = tok.lower()
        # Aussi vérifier sans point final
        tok_stripped = tok_lower.rstrip(".")
        
        expansions = _ABBREV_TO_REF.get(tok_lower) or _ABBREV_TO_REF.get(tok_stripped)
        if expansions:
            new_variants = []
            for variant in variants:
                for exp in expansions:
                    new_v = variant[:]
                    new_v[i] = exp
                    new_variants.append(new_v)
            variants.extend(new_variants)
    
    # Limiter le nombre de variantes pour éviter explosion combinatoire
    seen = set()
    result = []
    for v in variants:
        s = " ".join(v)
        if s not in seen:
            seen.add(s)
            result.append(s)
        if len(result) >= 20:
            break
    return result


# =============================================================
# Index de référence pré-calculé
# =============================================================

class MedsIndex:
    """Index optimisé pour le matching de médicaments.
    
    Pré-calcule et organise les données de référence pour
    un matching rapide multi-stratégie.
    """
    
    def __init__(self, reference_list: list[str]):
        self.originals = reference_list
        # Noms normalisés pour matching
        self.normalized = [_normalize(ref) for ref in reference_list]
        # Map normalisé → original
        self.norm_to_orig = {}
        for orig, norm in zip(reference_list, self.normalized):
            if norm not in self.norm_to_orig:
                self.norm_to_orig[norm] = orig
        
        # Index par premier token (nom du médicament) pour recherche rapide
        self.name_index: dict[str, list[int]] = {}
        for idx, norm in enumerate(self.normalized):
            tokens = norm.split()
            if tokens:
                first = tokens[0]
                if first not in self.name_index:
                    self.name_index[first] = []
                self.name_index[first].append(idx)
                # Indexer aussi les 2-3 premiers caractères pour matching partiel
                for prefix_len in range(2, min(len(first) + 1, 6)):
                    prefix = first[:prefix_len]
                    key = f"_pfx_{prefix}"
                    if key not in self.name_index:
                        self.name_index[key] = []
                    self.name_index[key].append(idx)
    
    def get_candidates_by_prefix(self, query_name: str, max_candidates: int = 200) -> list[int]:
        """Retourne les indices des candidats dont le premier token
        partage un préfixe significatif avec la requête."""
        tokens = query_name.split()
        if not tokens:
            return list(range(min(len(self.normalized), max_candidates)))
        
        first = tokens[0]
        candidates = set()
        
        # Correspondance exacte du premier token
        if first in self.name_index:
            candidates.update(self.name_index[first])
        
        # Correspondance par préfixe décroissant
        for prefix_len in range(min(len(first), 5), 1, -1):
            prefix = first[:prefix_len]
            key = f"_pfx_{prefix}"
            if key in self.name_index:
                candidates.update(self.name_index[key])
                if len(candidates) >= max_candidates:
                    break
        
        # Si très peu de candidats, élargir la recherche
        if len(candidates) < 10:
            return list(range(len(self.normalized)))
        
        return list(candidates)[:max_candidates]


# =============================================================
# Cache global de l'index
# =============================================================

_cached_index: MedsIndex | None = None
_cached_refs: list[str] | None = None


def _get_index(reference_list: list[str]) -> MedsIndex:
    """Retourne l'index (avec cache pour éviter recalculs)."""
    global _cached_index, _cached_refs
    if _cached_refs is not reference_list or _cached_index is None:
        _cached_index = MedsIndex(reference_list)
        _cached_refs = reference_list
    return _cached_index


# =============================================================
# Chargement des noms de référence
# =============================================================

def load_reference_names() -> list[str]:
    """Charge la liste des noms de médicaments de référence.
    
    Stratégie : charge le CSV complet (source principale, ~7800 entrées)
    puis fusionne les éventuels ajouts MongoDB par-dessus.
    Le CSV contient la base exhaustive des médicaments ; MongoDB
    peut contenir des ajouts manuels par les utilisateurs.
    """
    names_set = set()
    names_list = []

    # 1. Source principale : CSV complet
    if os.path.exists(MEDS_CSV_PATH):
        try:
            with open(MEDS_CSV_PATH, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            if lines:
                start = 1 if "Reference" in lines[0] else 0
                for l in lines[start:]:
                    name = l.strip().strip('"').strip("'").strip()
                    if name and name not in names_set:
                        names_set.add(name)
                        names_list.append(name)
        except Exception as e:
            logger.warning(f"Erreur lecture CSV: {e}")

    # 2. Fusion des ajouts MongoDB (si disponible)
    try:
        status = check_connection()
        if status["connected"]:
            mongo_names = MedicamentRepo.get_all_names()
            if mongo_names:
                for name in mongo_names:
                    name = str(name).strip()
                    if name and name not in names_set:
                        names_set.add(name)
                        names_list.append(name)
    except Exception:
        pass

    logger.info(f"Base de référence : {len(names_list)} médicaments chargés")
    return names_list


# =============================================================
# Algorithme de matching multi-stratégie
# =============================================================

def fuzzy_match(query: str, reference_list: list[str]) -> tuple[str, float]:
    """Matching intelligent d'une transcription contre la base de référence.
    
    Stratégies appliquées (par ordre de priorité) :
    
    1. **Correspondance exacte** (après normalisation)
    2. **Matching du nom seul** — ignore dosage/forme, match le nom
       de médicament en isolation
    3. **Expansion d'abréviations** — génère les variantes possibles
       (sp→SP, cp→CP, etc.) et tente le matching
    4. **Matching partiel par tokens** — score basé sur les tokens
       communs entre la requête et la référence (token_set_ratio)
    5. **Matching flou pur** — ratio de similarité global
    
    Le score final est le maximum des stratégies pondérées.
    
    Args:
        query: Texte brut issu du HTR (ex: "amoxicil 500 cp").
        reference_list: Liste de noms de médicaments de référence.
    
    Returns:
        (nom_correspondant, score_similarite) — score entre 0.0 et 1.0.
    """
    if not reference_list or not query or not str(query).strip():
        return "N/A", 0.0

    index = _get_index(reference_list)
    query_norm = _normalize(query)
    
    if not query_norm:
        return "N/A", 0.0

    # --- Stratégie 1 : Correspondance exacte ---
    if query_norm in index.norm_to_orig:
        return index.norm_to_orig[query_norm], 1.0

    # Extraire les composants de la requête
    query_name = _extract_name_token(query_norm)
    query_dosage = _extract_dosage(query_norm)
    
    best_match = "Aucun résultat trouvé"
    best_score = 0.0

    # --- Stratégie 2 : Matching sur le nom extrait + dosage ---
    if query_name:
        candidates_idx = index.get_candidates_by_prefix(query_name)
        candidate_norms = [index.normalized[i] for i in candidates_idx]
        candidate_origs = [index.originals[i] for i in candidates_idx]
        
        if candidate_norms:
            # 2a. Match du nom seul (token_sort_ratio = insensible à l'ordre)
            name_results = process.extract(
                query_name, 
                [_extract_name_token(c) for c in candidate_norms],
                scorer=fuzz.token_sort_ratio,
                limit=10,
            )
            
            for match_name, score_pct, match_idx in name_results:
                ref_idx = candidates_idx[match_idx]
                ref_norm = index.normalized[ref_idx]
                ref_orig = index.originals[ref_idx]
                
                # Score de base sur le nom (poids dominant)
                name_score = score_pct / 100.0
                
                # Bonus dosage : si les dosages concordent
                ref_dosage = _extract_dosage(ref_norm)
                dosage_bonus = 0.0
                if query_dosage and ref_dosage:
                    dosage_sim = fuzz.ratio(query_dosage, ref_dosage) / 100.0
                    dosage_bonus = dosage_sim * 0.15  # Bonus jusqu'à +15%
                
                # Score combiné
                combined = min(name_score * 0.85 + dosage_bonus, 1.0)
                
                if combined > best_score:
                    best_score = combined
                    best_match = ref_orig

    # --- Stratégie 3 : Expansion d'abréviations ---
    query_variants = _expand_abbreviations(query_norm)
    
    for variant in query_variants[1:]:  # Skip l'original déjà testé
        variant_name = _extract_name_token(variant)
        if not variant_name:
            variant_name = variant
        
        candidates_idx = index.get_candidates_by_prefix(variant_name)
        candidate_norms = [index.normalized[i] for i in candidates_idx]
        
        if candidate_norms:
            result = process.extractOne(
                variant,
                candidate_norms,
                scorer=fuzz.token_set_ratio,
            )
            if result:
                match_text, score_pct, match_idx = result
                ref_idx = candidates_idx[match_idx]
                score = score_pct / 100.0
                
                if score > best_score:
                    best_score = score
                    best_match = index.originals[ref_idx]

    # --- Stratégie 4 : token_set_ratio global (insensible à l'ordre/tokens manquants) ---
    if best_score < 0.7:
        result = process.extractOne(
            query_norm,
            index.normalized,
            scorer=fuzz.token_set_ratio,
        )
        if result:
            match_text, score_pct, match_idx = result
            score = score_pct / 100.0 * 0.95  # Léger malus vs matching ciblé
            if score > best_score:
                best_score = score
                best_match = index.originals[match_idx]

    # --- Stratégie 5 : Matching flou pur (partial_ratio pour sous-chaînes) ---
    if best_score < 0.6:
        # Utiliser partial_ratio qui tolère les sous-chaînes
        result = process.extractOne(
            query_norm,
            index.normalized,
            scorer=fuzz.partial_ratio,
        )
        if result:
            match_text, score_pct, match_idx = result
            score = score_pct / 100.0 * 0.90  # Malus plus important
            if score > best_score:
                best_score = score
                best_match = index.originals[match_idx]

    # --- Seuil minimum ---
    if best_score < MATCHING_CUTOFF:
        return "Aucun résultat trouvé", 0.0

    return best_match, round(best_score, 4)


# =============================================================
# Classification du score
# =============================================================

def classify_score(score: float) -> tuple[str, str]:
    """Classifie un score de matching en catégorie et badge CSS.
    
    Returns:
        (badge_class, badge_label) pour le frontend.
    """
    from backend.config import MATCHING_HIGH_SCORE, MATCHING_MEDIUM_SCORE
    if score >= MATCHING_HIGH_SCORE:
        return "high", "Excellente"
    elif score >= MATCHING_MEDIUM_SCORE:
        return "med", "Moyenne"
    return "low", "Faible"
