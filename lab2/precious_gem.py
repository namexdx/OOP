from gemstone import Gemstone

class PreciousGem(Gemstone):
    def __init__(self, name, weight, value, transparency, rarity):
        super().__init__(name, weight, value, transparency)
        self.rarity = rarity

    def __str__(self):
        return super().__str__() + f", Редкость: {self.rarity}"