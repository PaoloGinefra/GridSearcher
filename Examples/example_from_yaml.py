from GridSearcher import GridSearcher
from alive_progress import alive_it
import time

searcher = GridSearcher.fromYAML("./Examples/test.yaml")
print(searcher)

print(len(searcher))

for i in alive_it(list(searcher)):
    time.sleep(0.5)
    print(i)
