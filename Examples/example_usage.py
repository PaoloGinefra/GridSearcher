from GridSearcher import GridSearcher
from alive_progress import alive_it
import time

gridConfig = {
    'category': ['electronics', 'books', 'clothing'],
    'price': range(1, 5),
    'yolo': ['yes', 'no'],
    'sus': True
}
searcher = GridSearcher(gridConfig)
print(searcher)

print(len(searcher))

for i in alive_it(list(searcher)):
    time.sleep(0.5)
    print(i)
