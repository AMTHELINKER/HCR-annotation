import os
import re
import csv
import logging
from rapidfuzz import process, fuzz

from backend import config

logger = logging.getLogger(__name__)

class MedicalSpellChecker:
    """Correcteur orthographique contextuel basé sur le dictionnaire médical.
    
    Conçu pour rattraper les fautes de l'OCR sur des mots isolés avant le matching.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MedicalSpellChecker, cls).__new__(cls)
            cls._instance.vocab = []
            cls._instance.is_loaded = False
        return cls._instance
        
    def load(self):
        if self.is_loaded:
            return
            
        vocab_set = set()
        
        # Ajouter les mots du dictionnaire
        if os.path.exists(config.MEDS_CSV_PATH):
            with open(config.MEDS_CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    text = row[0]
                    words = text.split()
                    for w in words:
                        # Nettoyer la ponctuation
                        clean_w = re.sub(r'[^a-zA-ZÀ-ÿ0-9]', '', w.lower())
                        # On ne garde que les mots (pas les nombres purs)
                        if clean_w and not clean_w.isdigit():
                            vocab_set.add(clean_w)
        else:
            logger.warning(f"SpellChecker: Fichier {config.MEDS_CSV_PATH} introuvable.")
            
        # Ajouter les abréviations courantes explicites
        vocab_set.update(["comprime", "sirop", "gelule", "suppositoire", "ampoule", "flacon", "sachet", "mg", "ml"])
        
        self.vocab = list(vocab_set)
        self.is_loaded = True
        logger.info(f"SpellChecker chargé avec un vocabulaire de {len(self.vocab)} mots uniques.")
        
    def correct_text(self, text: str) -> str:
        """Corrige les mots individuels du texte en fonction du vocabulaire médical."""
        if not self.is_loaded:
            self.load()
            
        if not text or not self.vocab:
            return text
            
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Ne pas corriger les mots très courts ou les chiffres
            clean_word = re.sub(r'[^a-zA-ZÀ-ÿ]', '', word)
            if len(clean_word) < 4 or word.replace(',', '').replace('.', '').isdigit():
                corrected_words.append(word)
                continue
                
            # Recherche du mot le plus proche dans le vocabulaire
            # On cherche sur la version lower, mais on préserve la casse d'origine si possible
            # Pour la casse, on va simplifier : on remplace par le mot du dico en lower, 
            # puis on le capitalise si l'original l'était.
            lower_word = word.lower()
            res = process.extractOne(lower_word, self.vocab, scorer=fuzz.ratio)
            
            if res:
                match_str, score, _ = res
                # Seuil de correction : 80% (ex: Doliprane vs Doliprrane = 95%)
                if score >= 80 and score < 100:
                    logger.debug(f"SpellChecker: '{word}' corrigé en '{match_str}' (score={score:.1f})")
                    # Remplacer tout en gardant la ponctuation originale si possible ?
                    # Faisons simple : on remplace juste le mot textuel par la correspondance
                    
                    # Restaurer la majuscule initiale si présente
                    if word[0].isupper():
                        match_str = match_str.capitalize()
                        
                    corrected_words.append(match_str)
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
                
        return " ".join(corrected_words)
