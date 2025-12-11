from precious_gem import PreciousGem
from semi_precious_gem import SemiPreciousGem

def load_gemstones_from_file(filename):
    gemstones = []
    with open(filename, 'r') as file:
        for line in file:
            parts = line.strip().split(',')
            if parts[0] == 'precious':
                gem = PreciousGem(parts[1], float(parts[2]), float(parts[3]), float(parts[4]), parts[5])
            else:
                gem = SemiPreciousGem(parts[1], float(parts[2]), float(parts[3]), float(parts[4]))
            gemstones.append(gem)
    return gemstones

def calculate_total_weight(gemstones):
    return sum(gem.weight for gem in gemstones)

def calculate_total_value(gemstones):
    return sum(gem.value for gem in gemstones)

def sort_gemstones_by_value(gemstones):
    return sorted(gemstones, key=lambda gem: gem.get_value_per_carat(), reverse=True)

def find_gemstones_by_transparency(gemstones, low, high):
    return [gem for gem in gemstones if low <= gem.transparency <= high]

def main():
    gemstones = load_gemstones_from_file('gemstone.txt')
    
    total_weight = calculate_total_weight(gemstones)
    total_value = calculate_total_value(gemstones)
    
    print("Общий вес:", total_weight)
    print("Общая стоимость:", total_value)
    
    sorted_gemstones = sort_gemstones_by_value(gemstones)
    print("Сортированные драгоценные камни по стоимости:")
    for gem in sorted_gemstones:
        print(gem)

    low_transparency = 0.5
    high_transparency = 1.0
    filtered_gemstones = find_gemstones_by_transparency(gemstones, low_transparency, high_transparency)
    print(f"Драгоценные камни с прозрачностью между {low_transparency} и {high_transparency}:")
    for gem in filtered_gemstones:
        print(gem)

if __name__ == "__main__":
    main()