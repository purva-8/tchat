from src.database.dummy_data import database_listings

class DataManager:
    def __init__(self):
        self.listings = database_listings

    def get_all_listings(self):
        """Returns all listings from the database."""
        return self.listings

    # In a real application, you'd add methods for:
    # def add_listing(self, listing_data): ...
    # def get_listing_by_id(self, listing_id): ...
    # def update_listing(self, listing_id, new_data): ...
    # def delete_listing(self, listing_id): ...
    # And it would interact with a real DB (SQLAlchemy, psycopg2, etc.)