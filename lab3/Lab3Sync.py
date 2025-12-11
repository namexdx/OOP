import threading
import time
import sys

class Counter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

class IncrementThread(threading.Thread):
    def __init__(self, counter, iterations):
        threading.Thread.__init__(self)
        self.counter = counter
        self.iterations = iterations

    def run(self):
        for i in range(self.iterations):
            with self.counter.lock:
                temp = self.counter.value
                temp += 1
                self.counter.value = temp

class DecrementThread(threading.Thread):
    def __init__(self, counter, iterations):
        threading.Thread.__init__(self)
        self.counter = counter
        self.iterations = iterations

    def run(self):
        for i in range(self.iterations):
            with self.counter.lock:
                temp = self.counter.value
                temp -= 1
                self.counter.value = temp

def main():
    if len(sys.argv) != 3:
        print("Usage: python Lab3Sync.py <n> <m>")
        print("Where n is number of increment threads and m is number of decrement threads")
        return

    n = int(sys.argv[1])
    m = int(sys.argv[2])
    
    counter = Counter()
    threads = []
    
    start_time = time.time()
    
    for i in range(n):
        thread = IncrementThread(counter, 100000)
        threads.append(thread)
    
    for i in range(m):
        thread = DecrementThread(counter, 100000)
        threads.append(thread)
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    print(f"Final counter value: {counter.value}")
    print(f"Execution time: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    main()