from gemstone import Gemstone

class SemiPreciousGem(Gemstone):
    def __init__(self, name, weight, value, transparency):
        super().__init__(name, weight, value, transparency)

    def __str__(self):
        return super().__str__()