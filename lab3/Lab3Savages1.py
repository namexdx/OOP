import threading
import time
import sys

class Pot:
    def __init__(self, n):
        self.n = n
        self.current_portions = n
        self.lock = threading.RLock()
        self.empty_condition = threading.Condition(self.lock)
        self.full_condition = threading.Condition(self.lock)

class SavageThread(threading.Thread):
    def __init__(self, pot, savage_id):
        threading.Thread.__init__(self)
        self.pot = pot
        self.savage_id = savage_id

    def run(self):
        with self.pot.lock:
            while self.pot.current_portions == 0:
                print(f"Savage {self.savage_id} is waiting for food...")
                self.pot.empty_condition.wait()
            
            # Берем порцию
            self.pot.current_portions -= 1
            print(f"Savage {self.savage_id} took a portion. Remaining: {self.pot.current_portions}")
            
            if self.pot.current_portions == 0:
                self.pot.full_condition.notify()
                
class CookThread(threading.Thread):
    def __init__(self, pot):
        threading.Thread.__init__(self)
        self.pot = pot

    def run(self):
        with self.pot.lock:
            while self.pot.current_portions > 0:
                print("Cook is waiting for the pot to be empty...")
                self.pot.full_condition.wait()
                
            self.pot.current_portions = self.pot.n
            print(f"Cook filled the pot with {self.pot.n} portions")
            
            self.pot.empty_condition.notify_all()

def main():
    if len(sys.argv) != 2:
        print("Usage: python Lab3Savages1.py <n>")
        print("Where n is the number of portions in the pot")
        return

    n = int(sys.argv[1])
    
    pot = Pot(n)
    
    num_savages = n + 5
    
    savage_threads = []
    for i in range(num_savages):
        thread = SavageThread(pot, i)
        savage_threads.append(thread)
    
    cook_thread = CookThread(pot)
    
    start_time = time.time()
    
    cook_thread.start()
    
    for thread in savage_threads:
        thread.start()
    
    for thread in savage_threads:
        thread.join()
    
    cook_thread.join()
    
    end_time = time.time()
    
    print(f"Execution time: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    main()