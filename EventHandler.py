import time

class EventHandler:
    def __init__(self):
        self.functions = []
        self.current_index = 0
        self.last_run_times = {}
        self.function_intervals = {}
        self.max_execution_time = 0.1  # Max time each function can run (100ms)
        
    def register_function(self, func, interval=1.0, name=None):
        """Register a function to run at specified intervals"""
        if name is None:
            name = func.__name__
            
        self.functions.append({
            'func': func,
            'name': name,
            'interval': interval
        })
        self.last_run_times[name] = 0
        self.function_intervals[name] = interval
        
    def should_run(self, func_name):
        """Check if enough time has passed to run this function"""
        current_time = time.time()
        return (current_time - self.last_run_times[func_name]) >= self.function_intervals[func_name]
    
    def run_cycle(self):
        """Run one cycle through all functions"""
        if not self.functions:
            return
            
        # Get current function
        func_info = self.functions[self.current_index]
        func_name = func_info['name']
        
        # Check if it's time to run this function
        if self.should_run(func_name):
            try:
                # Record start time
                start_time = time.time()
                
                # Run the function with timeout protection
                result = func_info['func']()
                
                # Check execution time
                execution_time = time.time() - start_time
                if execution_time > self.max_execution_time:
                    print(f"Warning: {func_name} took {execution_time:.3f}s (> {self.max_execution_time}s)")
                
                # Update last run time
                self.last_run_times[func_name] = time.time()
                
                # Optional: handle return values
                if result is not None:
                    self.handle_result(func_name, result)
                    
            except Exception as e:
                print(f"Error in {func_name}: {e}")
                # Update last run time even on error to prevent spam
                self.last_run_times[func_name] = time.time()
        
        # Move to next function
        self.current_index = (self.current_index + 1) % len(self.functions)
    
    def handle_result(self, func_name, result):
        """Handle function results (override this if needed)"""
        if isinstance(result, dict) and result.get('error'):
            print(f"{func_name} returned error: {result['error']}")
        elif isinstance(result, dict) and result.get('status'):
            print(f"{func_name}: {result['status']}")