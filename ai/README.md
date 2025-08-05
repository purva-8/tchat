
## Features

- **Role Selection:** Users can specify if they are a 'buyer' or a 'seller'.
- **Named Entity Recognition (NER):** Extracts 'product', 'quantity', and 'price' from user input using SpaCy and custom rules.
- **Product Matching:** Searches a dummy database for listings that match the user's request.
- **Scoring System:** Ranks matches based on criteria like quantity and price proximity, optimized for buyer (lower price) or seller (higher price) preferences.
- **Top 3 Results:** Displays the top 3 most relevant matches.
