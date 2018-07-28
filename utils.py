class CityRepository:
    def __init__(self):
        with open('files/cities.txt') as f:
            self.city_list = set(city.lower().strip() for city in f.readlines())

    def try_get_city(self, city_name):
        return city_name if city_name.lower() in self.city_list else None


def filter_stop_words(lemmas):
    return [item for item in lemmas if len(item) > 3]
