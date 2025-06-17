from route_finder import RouteFinder

def test_jugla_to_imanta():
    rf = RouteFinder()
    result = rf.find_route("Jugla", "Imanta")
    print(result)

if __name__ == "__main__":
    test_jugla_to_imanta()
