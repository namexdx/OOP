class House:
    def __init__(self, house_id, apartment_number, area, floor, rooms, street, building_type, exploitation_period):
        self.house_id = house_id
        self.apartment_number = apartment_number
        self.area = area
        self.floor = floor
        self.rooms = rooms
        self.street = street
        self.building_type = building_type
        self.exploitation_period = exploitation_period

    def set_tun(self, rooms):
        self.rooms = rooms

    def get_tun(self):
        return self.rooms

    def __str__(self):
        return (f'Дом(id = {self.house_id}, номер = {self.apartment_number}, площадь = {self.area}, '
                f'этаж = {self.floor}, комната = {self.rooms}, улица = {self.street}, '
                f'тип = {self.building_type}, срок = {self.exploitation_period})')

    def __hash__(self):
        return hash((self.house_id, self.apartment_number))

def filter_apartments(houses, criteria):
    return [house for house in houses if criteria(house)]

def rooms_equal_criteria(target_rooms):
    return lambda house: house.rooms == target_rooms

def rooms_and_floor_criteria(target_rooms, min_floor, max_floor):
    return lambda house: house.rooms == target_rooms and min_floor <= house.floor <= max_floor

def area_greater_than_criteria(min_area):
    return lambda house: house.area > min_area

houses = [
    House(1, 101, 55, 2, 3, "ул. Пушкина", "Кирпичное здание", 30),
    House(2, 202, 80, 4, 3, "ул. Яз", "Кирпичное здание", 15),
    House(3, 201, 40, 1, 2, "ул. Героев Сталинграда", "Деревянное здание", 20),
    House(4, 102, 75, 3, 4, "ул. Ухтомского", "Металлическое здание", 25),
    House(5, 301, 60, 2, 3, "ул. 8 Марта", "Бетонное здание", 10),
]

print(houses[1])

print("Квартиры с 3 комнатами:")
for house in filter_apartments(houses, rooms_equal_criteria(3)):
    print(house)

print("\nКвартиры с 3 комнатами на этажах 2-3:")
for house in filter_apartments(houses, rooms_and_floor_criteria(3, 2, 3)):
    print(house)

print("\nКвартиры с площадью больше 60:")
for house in filter_apartments(houses, area_greater_than_criteria(60)):
    print(house)



  