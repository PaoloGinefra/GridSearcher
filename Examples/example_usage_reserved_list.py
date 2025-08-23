from GridSearcher import GridSearcher
from alive_progress import alive_it
import time

gridConfig = {
    'test': {
        'category': [{'__range__': {'from': 1, 'to': 3}}, 'books', {
            'other': 'stuff',
            'var': {
                '__list__': {
                    'values': ['clothing', 'accessories']
                }
            }}],
    }
}
searcher = GridSearcher(gridConfig)
print(searcher)

print(len(searcher))

for i in alive_it(list(searcher)):
    time.sleep(0.5)
    searcher.logger.logger.info(f"Current config: {i}")
