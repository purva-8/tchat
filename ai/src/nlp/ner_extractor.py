import spacy
from spacy.matcher import Matcher
import re
import json

class AdvancedNERExtractor:
    def __init__(self, config_path='config/ner_patterns.json'):
        self.nlp = spacy.load("en_core_web_sm")
        self.matcher = Matcher(self.nlp.vocab)

        self.patterns = self._load_patterns(config_path)

        # Define patterns for product, quantity, and price using loaded config
        product_keywords = self.patterns.get("product_keywords", [])
        if product_keywords:
            self.matcher.add("PRODUCT_KEYWORD", [[{"LOWER": {"IN": product_keywords}}]])

        quantity_units = self.patterns.get("quantity_units", [])
        if quantity_units:
            self.matcher.add("QUANTITY", [
                [{"LIKE_NUM": True}, {"LOWER": {"IN": quantity_units}}]
            ])
            # Also add a pattern for just numbers, sometimes units are implied or missing
            self.matcher.add("QUANTITY_NUM_ONLY", [[{"LIKE_NUM": True}]])


        price_currencies = self.patterns.get("price_currencies", [])
        if price_currencies:
            self.matcher.add("PRICE", [
                [{"LOWER": {"IN": price_currencies}, "OP": "?"}, {"LIKE_NUM": True}], # e.g., "100 rupees", "rs 100"
                [{"LIKE_NUM": True}, {"LOWER": {"IN": price_currencies}, "OP": "?"}]  # e.g., "$50", "50 dollars"
            ])

    def _load_patterns(self, config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config['patterns']
        except FileNotFoundError:
            print(f"Error: Config file not found at {config_path}. Using default patterns if available.")
            return {} # Return empty dict if file not found, handle gracefully

    def extract(self, text):
        doc = self.nlp(text)

        extracted_entities = {
            'product': None,
            'quantity': None,
            'unit': None,
            'price': None,
            'currency': None
        }

        # --- Phase 1: Use SpaCy's built-in NER ---
        for ent in doc.ents:
            if ent.label_ == "PRODUCT" and not extracted_entities['product']:
                extracted_entities['product'] = ent.text
            elif ent.label_ == "QUANTITY" and not extracted_entities['quantity']:
                num_match = re.search(r'\d+(\.\d+)?', ent.text)
                if num_match:
                    extracted_entities['quantity'] = float(num_match.group())
                    # Attempt to extract unit from SpaCy's QUANTITY entity text
                    unit_match = re.search(r'(kg|kgs|kilograms|liter|liters|units|g|grams|ml|milliliters|dozen|pounds|lbs|oz|ounces|bags|crates|boxes|cans|bottles|packs|pieces)', ent.text, re.IGNORECASE)
                    if unit_match:
                        extracted_entities['unit'] = unit_match.group().lower()
            elif ent.label_ == "MONEY" and not extracted_entities['price']:
                num_match = re.search(r'\d+(\.\d+)?', ent.text)
                if num_match:
                    extracted_entities['price'] = float(num_match.group())
                    # Attempt to extract currency from SpaCy's MONEY entity text
                    currency_match = re.search(r'(rupees|rs|dollars|usd|eur|pounds|inr|aed|qar|qatar riyals|riyals|\$|€|£)', ent.text, re.IGNORECASE)
                    if currency_match:
                        extracted_entities['currency'] = currency_match.group().lower()

        # --- Phase 2: Use custom Matcher for more specific or missed patterns ---
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]

            if label == "PRODUCT_KEYWORD" and not extracted_entities['product']:
                extracted_entities['product'] = span.text
            elif label == "QUANTITY" and not extracted_entities['quantity']:
                num_match = re.search(r'\d+(\.\d+)?', span.text)
                if num_match:
                    extracted_entities['quantity'] = float(num_match.group())
                    unit_match = re.search(r'(kg|kgs|kilograms|liter|liters|units|g|grams|ml|milliliters|dozen|pounds|lbs|oz|ounces|bags|crates|boxes|cans|bottles|packs|pieces)', span.text, re.IGNORECASE)
                    if unit_match:
                        extracted_entities['unit'] = unit_match.group().lower()
            elif label == "QUANTITY_NUM_ONLY" and not extracted_entities['quantity']:
                 # This captures numbers not associated with a unit by SpaCy or QUANTITY matcher
                 num_match = re.search(r'\d+(\.\d+)?', span.text)
                 if num_match:
                     extracted_entities['quantity'] = float(num_match.group())
                     # No unit extracted here, it's just a number
            elif label == "PRICE" and not extracted_entities['price']:
                num_match = re.search(r'\d+(\.\d+)?', span.text)
                if num_match:
                    extracted_entities['price'] = float(num_match.group())
                    currency_match = re.search(r'(rupees|rs|dollars|usd|eur|pounds|inr|aed|qar|qatar riyals|riyals|\$|€|£)', span.text, re.IGNORECASE)
                    if currency_match:
                        extracted_entities['currency'] = currency_match.group().lower()

        # --- Phase 3: Normalization (optional but good practice) ---
        if extracted_entities['unit']:
            normalized_units = {
                'kgs': 'kg', 'kilograms': 'kg', 'pounds': 'lb', 'lbs': 'lb',
                'oz': 'ounce', 'ounces': 'ounce', 'g': 'gram', 'grams': 'gram',
                'liters': 'liter', 'ml': 'milliliter', 'milliliters': 'milliliter',
                'bags': 'bag', 'crates': 'crate', 'boxes': 'box', 'cans': 'can',
                'bottles': 'bottle', 'packs': 'pack', 'pieces': 'piece'
            }
            extracted_entities['unit'] = normalized_units.get(extracted_entities['unit'], extracted_entities['unit'])

        if extracted_entities['currency']:
            normalized_currencies = {
                'rs': 'rupees', 'inr': 'rupees', 'usd': 'dollars', '$': 'dollars',
                '€': 'eur', '£': 'pounds', 'qar': 'qatar riyals', 'riyals': 'qatar riyals'
            }
            extracted_entities['currency'] = normalized_currencies.get(extracted_entities['currency'], extracted_entities['currency'])

        return extracted_entities