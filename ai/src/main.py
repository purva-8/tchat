import json # Not directly used here, but good practice if you load configs in main
from src.nlp.ner_extractor import AdvancedNERExtractor
from src.database.data_manager import DataManager
from src.matching.matcher import find_best_matches

class Chatbot:
    def __init__(self, config_path='config/ner_patterns.json'):
        # Initialize components, passing config path to NER
        self.ner_extractor = AdvancedNERExtractor(config_path=config_path)
        self.data_manager = DataManager()
        self.current_user_role = None # State variable to track user's role in the conversation

        print("AI Model: Welcome! Are you a 'buyer' or a 'seller'?")

    def process_user_input(self, user_input):
        user_input_lower = user_input.lower().strip()

        # --- Conversation State 1: Determine User Role ---
        if self.current_user_role is None:
            if user_input_lower in ["buyer", "i am a buyer", "i'm a buyer", "i want to buy"]:
                self.current_user_role = "buyer"
                print("AI: Alright. What do you wish to buy? (e.g., '100 kg apples for 10 rupees per kg')")
            elif user_input_lower in ["seller", "i am a seller", "i'm a seller", "i want to sell"]:
                self.current_user_role = "seller"
                print("AI: Okay. What do you wish to sell? (e.g., '50 kg rice at 50 rupees per kg')")
            else:
                print("AI: Please specify if you are a 'buyer' or 'seller'.")
            return

        # --- Conversation State 2: Process Request based on Role ---
        if self.current_user_role:
            # If user just acknowledges, re-prompt for the request
            if user_input_lower in ["alright", "okay", "yes", "sure", "go ahead"]:
                print(f"AI: Please tell me what you wish to {'buy' if self.current_user_role == 'buyer' else 'sell'}.")
                return

            # Extract entities from the user's request using NER
            extracted_info = self.ner_extractor.extract(user_input)

            product = extracted_info.get('product')
            quantity = extracted_info.get('quantity')
            price = extracted_info.get('price')

            # Basic validation: A product is essential for a search
            if not product:
                print("AI: I couldn't understand the product. Please specify what you wish to buy/sell (e.g., 'apples', 'rice').")
                # Don't reset role yet, allow user to re-enter the request
                return

            print(f"AI: Alright, detecting your request for {product}. Let me check the database...")
            # Optional: for debugging extracted entities
            # print(f"DEBUG: Extracted: {extracted_info}")

            # --- Core Logic: Search Database and Find Matches ---
            # Retrieve all listings and find the best matches
            all_listings = self.data_manager.get_all_listings()
            top_matches = find_best_matches(extracted_info, all_listings, self.current_user_role)

            # --- Respond with Results ---
            if top_matches:
                print(f"\nAI: These are the top {len(top_matches)} {'sellers' if self.current_user_role == 'buyer' else 'buyers'} as per your request for {product}:")
                for i, match in enumerate(top_matches):
                    listing = match['listing']
                    # Format output based on user's role
                    if self.current_user_role == "buyer":
                        print(f"  {i+1}. Seller ID: {listing['user_id']} is selling {listing['quantity']:.0f} {listing['unit']} of {listing['product_name']} at {listing['price_per_unit']:.2f} {listing['currency']} per {listing['unit']}.")
                    else: # seller
                        print(f"  {i+1}. Buyer ID: {listing['user_id']} is looking to buy {listing['quantity']:.0f} {listing['unit']} of {listing['product_name']} at {listing['price_per_unit']:.2f} {listing['currency']} per {listing['unit']}.")
            else:
                print(f"AI: I couldn't find any matching {'sellers' if self.current_user_role == 'buyer' else 'buyers'} for your request.")

            # Reset role to end the current transaction, allowing a new one to start
            self.current_user_role = None
            print("\nAI: Is there anything else I can help you with? Or, if you want to make another request, please tell me if you are a 'buyer' or 'seller' again.")

# --- Main Interaction Loop ---
if __name__ == "__main__":
    chatbot = Chatbot()
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("AI: Goodbye!")
            break
        chatbot.process_user_input(user_input)