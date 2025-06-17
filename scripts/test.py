import unittest
from route_finder import RouteFinder

class TestRouteFinderFuzzySearch(unittest.TestCase):
    def setUp(self):
        self.rf = RouteFinder()
        # Add your test stop names here
        self.test_stops = [
            'Grēcinieku iela',
            '13.janvāra iela',
            'Centrāltirgus',
            'Priežciems',
            'Purvciems',
            'Mežciems',

            'brivibas iela',
            'brīvibas iela',
            'Brivibas iela',
            'Brīvibas iela',

            'ežciems',
            'iežciems',
            'mžciems',
            'Ianta',
            'Jgla',
            'Centrārartirgus',
            'Grmzdas iel',
            'Arenes iela',

            'kebavas iea',
            '2.trolejbusu parks',
            '12.trolejbusu parks',
            'D/P',
            '32.janvāra iela',
            '20.janvāra iela',

            'MENESS IELA',
            'Mēness iela',
            'menes iela',

            'eksportostas',
            '13. janvāra ielu',
            '13 janvāra ielu',

            'Botānisko dārzu',
            'botanisko darzu',

            'Dole',
            'Eglaines iela/Dole',
            'ZOO',

            'csdd',
            '/csdd',
            '/CSDD',
            'CSDD'
        ]

    def test_fuzzy_search(self):
        for stop in self.test_stops:
            results = self.rf.search_bus_stop(stop)
            print(f"Query: {stop}")
            for name, score in results:
                print(f"  Match: {name} (confidence: {score:.2f})")
            print()

if __name__ == "__main__":
    unittest.main()
