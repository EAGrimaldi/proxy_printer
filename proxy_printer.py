import requests
import json
import logging
import datetime
import os
import typing

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO)

log_info = lambda log_msg : logging.log(logging.INFO, log_msg)

class ScryfallDatabase():
    base_uri = "https://api.scryfall.com/"
    bulk_data_file = os.path.join(__location__, "scryfall_bulk_data.json")
    database_file = os.path.join(__location__, "scryfall_database.json")
    bulk_data = None
    database = None
    last_update = None
    def __init__(self) -> None:
        if os.path.exists(self.bulk_data_file) and os.path.exists(self.database_file):
            log_info("loading existing database")
            self.load_database()
        else:
            log_info("did not find existing database")
        self.update_database()
    def load_database(self) -> None:
        with open(self.bulk_data_file, 'r') as file:
            self.bulk_data = json.load(file)
        with open(self.database_file, 'r') as file:
            self.database = json.load(file)
        self.set_last_update()
    def update_database(self) -> None:
        if self.is_out_of_date():
            logging.warning("database out of date") # should this be in self.is_out_of_date()?
            log_info("updating database...")
            bulk_data_response = requests.get(f"{self.base_uri}bulk-data")
            bulk_data_response.raise_for_status()
            self.bulk_data = bulk_data_response.json()
            self.set_last_update()
            success = False
            for bulk_data_item in self.bulk_data["data"]:
                # NOTE other bulk data options include card art, possibly multiple arts per card name
                if bulk_data_item["name"] == "Oracle Cards":
                    database_response = requests.get(bulk_data_item["download_uri"])
                    database_response.raise_for_status()
                    self.database = database_response.json()
                    with open(self.bulk_data_file, 'w') as file:
                        json.dump(self.bulk_data, file, indent=4)
                    with open(self.database_file, 'w') as file:
                        json.dump(self.database, file, indent=4)
                    success = True
                    log_info("update complete")
            if not success:
                raise IndexError("bulk data response did not include required bulk data set...")
        else:
            log_info("database up-to-date")
    def is_out_of_date(self) -> bool:
        if self.last_update is None:
            return True
        return True if (datetime.datetime.now(datetime.timezone.utc) - self.last_update).days > 1 else False
    def set_last_update(self):
        self.last_update = datetime.datetime.strptime(self.bulk_data["data"][0]["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
    def get_card(self, card_name: str) -> typing.Union[dict, None]:
        for card in self.database:
            if card["name"] == card_name:
                return card
        logging.warning(f"card name {card_name} not found in database...")
        return None

# TODO
# - move database to SQL
# - implement card image assembler        
# - implement print out formatter

if __name__ == "__main__":
    db = ScryfallDatabase()