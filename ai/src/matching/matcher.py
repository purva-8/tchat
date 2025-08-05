def find_best_matches(user_request, database, role):
    """
    Finds the top 3 best matching listings from the database based on user's request and role.

    Args:
        user_request (dict): Dictionary with extracted 'product', 'quantity', 'unit', 'price', 'currency'.
        database (list): The list of product listings (from DataManager).
        role (str): 'buyer' or 'seller'.

    Returns:
        list: A list of dictionaries, each containing a 'listing' and its 'score', sorted by score.
    """
    target_product = user_request.get('product')
    target_quantity = user_request.get('quantity')
    target_unit = user_request.get('unit')
    target_price = user_request.get('price')
    target_currency = user_request.get('currency')

    if not target_product:
        return [] # Cannot match without a product

    matches = []

    # Determine what type of listing to search for based on user's role
    # If user is a 'buyer', we look for 'selling' listings.
    # If user is a 'seller', we look for 'buying' listings.
    search_type = "selling" if role == "buyer" else "buying"

    for listing in database:
        # 1. Product Name Match (case-insensitive)
        if listing['type'] == search_type and listing['product_name'].lower() == target_product.lower():
            score = 0

            # 2. Quantity Matching
            if target_quantity and listing['quantity']:
                # Basic unit check for now. For a real app, implement robust unit conversion.
                is_unit_match = False
                if listing['unit'] and target_unit:
                    if listing['unit'].lower() == target_unit.lower():
                        is_unit_match = True
                    # Add more sophisticated unit conversion if needed (e.g., kg to grams)
                elif not listing['unit'] and not target_unit: # Both missing units, assume match for simplicity
                    is_unit_match = True

                if is_unit_match:
                    quantity_diff = abs(target_quantity - listing['quantity'])
                    # Reward closer quantities
                    if quantity_diff == 0:
                        score += 5 # Perfect quantity match
                    elif quantity_diff <= 0.05 * target_quantity: # within 5%
                        score += 4
                    elif quantity_diff <= 0.10 * target_quantity: # within 10%
                        score += 3
                    elif quantity_diff <= 0.25 * target_quantity: # within 25%
                        score += 2
                    elif quantity_diff <= 0.50 * target_quantity: # within 50%
                        score += 1
                else: # Unit mismatch, penalize or reduce score
                    # For this demo, if units don't match, we won't add quantity score
                    pass

            # 3. Price Matching (critical and depends on role)
            if target_price and listing['price_per_unit']:
                # Basic currency check. For real app, implement currency conversion.
                is_currency_match = False
                if listing['currency'] and target_currency:
                    if listing['currency'].lower() == target_currency.lower():
                        is_currency_match = True
                elif not listing['currency'] and not target_currency: # Both missing currency, assume match
                    is_currency_match = True

                if is_currency_match:
                    if role == "buyer":
                        # Buyer wants a lower price (or equal)
                        if listing['price_per_unit'] <= target_price:
                            score += 5 # Excellent price for buyer
                        elif listing['price_per_unit'] <= target_price * 1.05: # Up to 5% higher
                            score += 4
                        elif listing['price_per_unit'] <= target_price * 1.10: # Up to 10% higher
                            score += 3
                        elif listing['price_per_unit'] <= target_price * 1.20: # Up to 20% higher
                            score += 2
                        elif listing['price_per_unit'] <= target_price * 1.50: # Up to 50% higher
                            score += 1
                    elif role == "seller":
                        # Seller wants a higher price (or equal)
                        if listing['price_per_unit'] >= target_price:
                            score += 5 # Excellent price for seller
                        elif listing['price_per_unit'] >= target_price * 0.95: # Up to 5% lower
                            score += 4
                        elif listing['price_per_unit'] >= target_price * 0.90: # Up to 10% lower
                            score += 3
                        elif listing['price_per_unit'] >= target_price * 0.80: # Up to 20% lower
                            score += 2
                        elif listing['price_per_unit'] >= target_price * 0.50: # Up to 50% lower
                            score += 1
                else: # Currency mismatch, penalize or reduce score
                    pass # For this demo, won't add price score if currency mismatched


            # Only consider listings that have a positive score after product match
            if score > 0:
                matches.append({'listing': listing, 'score': score})

    # Sort matches: Primary by score (descending), Secondary by price
    # For buyers, lower price is better. For sellers, higher price is better.
    if role == "buyer":
        matches.sort(key=lambda x: (-x['score'], x['listing']['price_per_unit']))
    elif role == "seller":
        matches.sort(key=lambda x: (-x['score'], -x['listing']['price_per_unit']))

    return matches[:3] # Return top 3 matches