from GridSearcher import GridSearcher
from alive_progress import alive_it
import time

gridConfig = {
    'test': {
        'category': ['electronics', 'books', 'clothing'],
        'price': range(1, 5),
        'yolo': ['yes', 'no'],
        'sus': {
            '__range__': {
                'from': 1,
                'to': 3,
            }
        },
        'Listed': {
            '__list__': {
                'values': ['first', 'second']
            }
        },
        'nested': {
            'range': {
                '__range__': {
                    'from': 1,
                    'to': 4,
                }
            }
        }
    }
}
searcher = GridSearcher(gridConfig)
print(searcher)

print(len(searcher))

for i in alive_it(list(searcher)):
    time.sleep(0.5)
    searcher.logger.logger.info(f"Current config: {i}")
