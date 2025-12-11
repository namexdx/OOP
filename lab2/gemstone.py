class Gemstone:
    def __init__(self, name, weight, value, transparency):
        self.name = name
        self.weight = weight
        self.value = value
        self.transparency = transparency


    def __str__(self):
        return f"{self.name}: {self.weight} ct, ${self.value}, Прозрачность: {self.transparency}"

    def get_value_per_carat(self):
        return self.value / self.weight if self.weight else 0