import requests
import json
import logging
import datetime
import os
import typing
import fpdf
import tqdm

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO)

log_info = lambda log_msg : logging.log(logging.INFO, log_msg)

class ProxyPrinter():
    base_uri = "https://api.scryfall.com/"
    bulk_data_file = os.path.join(__location__, "scryfall_bulk_data.json")
    database_file = os.path.join(__location__, "scryfall_database.json")
    bulk_data = None
    database = None
    last_update = None
    modes = {
        "simplified",
        "default",
    }
    def __init__(self) -> None:
        if os.path.exists(self.bulk_data_file) and os.path.exists(self.database_file):
            log_info("found existing database")
            self.load_database()
        else:
            log_info("did not find existing database")
        self.update_database()
        for mode in self.modes:
            mode_cache = os.path.join(__location__, "cache", mode)
            if not os.path.exists(mode_cache):
                os.makedirs(mode_cache)
    def load_database(self) -> None:
        log_info("loading existing database...")
        with open(self.bulk_data_file, "r") as file:
            self.bulk_data = json.load(file)
        with open(self.database_file, "r") as file:
            self.database = json.load(file)
        self.set_last_update()
        log_info("load complete")
    def update_database(self) -> None:
        if self.is_out_of_date():
            log_info("updating database...")
            bulk_data_response = requests.get(f"{self.base_uri}bulk-data")
            bulk_data_response.raise_for_status()
            self.bulk_data = bulk_data_response.json()
            self.set_last_update()
            success = False
            for bulk_data_item in self.bulk_data["data"]:
                # NOTE "Oracle Cards" has exactly one object for each legal card name
                # alternatively "Default Cards" has a card object for each printing of each card name
                if bulk_data_item["name"] == "Oracle Cards":
                    database_response = requests.get(bulk_data_item["download_uri"])
                    database_response.raise_for_status()
                    self.database = database_response.json()
                    with open(self.bulk_data_file, "w") as file:
                        json.dump(self.bulk_data, file, indent=4)
                    with open(self.database_file, "w") as file:
                        json.dump(self.database, file, indent=4)
                    success = True
                    log_info("update complete")
                    break
            if not success:
                raise KeyError("bulk data response did not include required bulk data set...")
    def is_out_of_date(self) -> bool:
        if self.last_update is None:
            logging.warning("did not find record of last update")
            return True
        if (datetime.datetime.now(datetime.timezone.utc) - self.last_update).days > 0:
            logging.warning("database out of date")
            return True
        log_info("database up to date")
        return False
    def set_last_update(self) -> None:
        self.last_update = datetime.datetime.strptime(self.bulk_data["data"][0]["updated_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
    def get_card_data(self, card_name: str) -> typing.Union[dict, None]:
        for card_data in self.database:
            if card_data["name"] == card_name:
                return card_data
            if card_data["layout"] in {"transform", "modal_dfc", "flip", "split"}:
                if card_data["card_faces"][0]["name"] == card_name:
                    # for the case that users lazily write only "Front Side" and not "Front Side // Back Side"
                    return card_data
        logging.warning(f"card name {card_name} not found in database...")
        return None
    def parse_card_list(self, card_list_file: str) -> typing.List[dict]:
        deck_list_terms = {
            "deck",
            "main deck",
            "mainboard",
            "sideboard",
            "maybeboard",
            "companion",
            "commander",
        }
        card_list = []
        if not os.path.exists(card_list_file) and not os.path.dirname(card_list_file):
            card_list_file = os.path.join(__location__, card_list_file)
        with open(card_list_file, "r") as file:
            for line in file:
                line = line.strip()
                if not line or line.lower().rstrip(":") in deck_list_terms:
                    continue
                number_of_copies, card_name = line.split(maxsplit=1) if line[0].isnumeric() else (1, line)
                number_of_copies = int(number_of_copies)
                card_data = self.get_card_data(card_name)
                if card_data is None:
                    logging.warning(f"skipping {card_name} in print out...\n    this should probably never happen...\n    unless it was an unneeded DFC back face?")
                    continue
                for _ in range(number_of_copies):
                    if card_data["layout"] in {"transform", "modal_dfc"}:
                        card_list.append({
                            "file_name": card_data["card_faces"][0]["name"],
                            "image_uri": card_data["card_faces"][0]["image_uris"]["png"],
                            "card_data": card_data,
                            "is_dfc_front": True,
                            "is_dfc_back": False,
                        })
                        card_list.append({
                            "file_name": card_data["card_faces"][1]["name"],
                            "image_uri": card_data["card_faces"][1]["image_uris"]["png"],
                            "card_data": card_data,
                            "is_dfc_front": False,
                            "is_dfc_back": True,
                        })
                    else:
                        card_list.append({
                            "file_name": card_data["name"].replace("//", "--"),
                            "image_uri": card_data["image_uris"]["png"],
                            "card_data": card_data,
                            "is_dfc_front": False,
                            "is_dfc_back": False,
                        })
        return card_list
    def build_card_image(self, card_dict: dict, image_file: str, mode: str) -> str:
        # TODO implement this
        raise NotImplementedError("build_card_image() not yet implemented...")
    def build_print_out(self, card_list_file: str, mode: str="default") -> None:
        # TODO implement additional card art selection (low prio)
        if mode not in self.modes:
            logging.warning(f"invalid mode '{mode}' - valid modes are: \n{self.modes}\nproceeding with 'default' mode")
            mode = "default"
        card_list = self.parse_card_list(card_list_file)
        pdf = fpdf.FPDF("P", "in", "Letter")
        for i, card_dict in enumerate(tqdm.tqdm(card_list, desc="building print out")):
            file_name = card_dict["file_name"]
            image_uri = card_dict["image_uri"]
            image_file = os.path.join(__location__, "cache", mode, f"{file_name}.png")
            if not os.path.exists(image_file):
                if mode == "default":
                    image_response = requests.get(image_uri)
                    image_response.raise_for_status()
                    with open(image_file, "wb") as file:
                        file.write(image_response.content)
                else:
                    self.build_card_image(card_dict, image_file, mode)
            if not i%9:
                pdf.add_page()
            x = 0.5 + 2.5 * (i%3)
            y = 0.25 + 3.5 * (i//3%3)
            pdf.image(image_file, x, y, 2.5, 3.5)
        pdf.output(os.path.join(__location__, f"{card_list_file.split('.')[0]}.pdf"), "F")

if __name__ == "__main__":
    printer = ProxyPrinter()
    printer.build_print_out("test.txt")
