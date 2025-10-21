import logging
from datetime import datetime
from collections import defaultdict
import time
import datetime

class PerformanceMetrics:
    def __init__(self):
        # API Performance
        self.min_api_time = float('inf')
        self.max_api_time = 0
        self.current_api_time = 0
        self.api_success = 0
        self.api_failure = 0
        self.last_api_call_time = None
        
        # Meter Processing
        self.min_meter_process_time = float('inf')
        self.max_meter_process_time = 0
        self.current_meter_process_time = 0
        self.total_meter_process_time = 0
        self.meter_process_count = 0
        
        # Connection Stats
        self.connection_drops = 0
        self.connection_start_time = None
        self.last_connection_time = None

        # New Transaction Metrics
        self.transaction_count = 0
        self.failed_transactions = 0
        self.transaction_durations = []
        self.current_transactions = {}  # {transaction_id: start_time}
        self.transaction_interruptions = defaultdict(int)
        self.state_transitions = defaultdict(lambda: defaultdict(int))  # {from_state: {to_state: count}}
        
        # New WebSocket Metrics
        self.message_latencies = []
        self.max_message_latency = 0
        self.min_message_latency = float('inf')
        self.failed_messages = 0
        self.message_queue_size = 0
        self.websocket_disconnects = 0
        self.last_message_time = None
        self.total_messages_sent = 0
        self.total_messages_received = 0

    def update_api_timing(self, response_time: float, success: bool):
        self.current_api_time = response_time
        if success:
            self.min_api_time = min(self.min_api_time, response_time)
            self.max_api_time = max(self.max_api_time, response_time)
            self.api_success += 1
        else:
            self.api_failure += 1
        self.last_api_call_time = datetime.datetime.now(datetime.UTC)

    def update_meter_timing(self, process_time: float):
        self.current_meter_process_time = process_time
        self.min_meter_process_time = min(self.min_meter_process_time, process_time)
        self.max_meter_process_time = max(self.max_meter_process_time, process_time)
        self.total_meter_process_time += process_time
        self.meter_process_count += 1

    def get_api_success_rate(self) -> float:
        total_calls = self.api_success + self.api_failure
        return (self.api_success / total_calls * 100) if total_calls > 0 else 0

    def get_average_meter_time(self) -> float:
        return self.total_meter_process_time / self.meter_process_count if self.meter_process_count > 0 else 0

    def get_uptime(self) -> float:
        if not self.connection_start_time:
            return 0
        return (datetime.datetime.now(datetime.UTC) - self.connection_start_time).total_seconds()

    def start_transaction(self, transaction_id):
        """Record the start of a transaction."""
        self.current_transactions[transaction_id] = datetime.datetime.now(datetime.UTC)
        self.transaction_count += 1

    def end_transaction(self, transaction_id, was_successful=True):
        """Record the end of a transaction."""
        if transaction_id in self.current_transactions:
            duration = (datetime.datetime.now(datetime.UTC) - self.current_transactions[transaction_id]).total_seconds()
            self.transaction_durations.append(duration)
            del self.current_transactions[transaction_id]
            if not was_successful:
                self.failed_transactions += 1

    def record_state_transition(self, from_state, to_state):
        """Record a state transition."""
        self.state_transitions[from_state][to_state] += 1
        if to_state == "Available" and from_state == "Charging":
            self.transaction_interruptions[from_state] += 1

    def record_message_metrics(self, latency, is_sent=True, failed=False):
        """Record WebSocket message metrics."""
        if failed:
            self.failed_messages += 1
        else:
            self.message_latencies.append(latency)
            self.max_message_latency = max(self.max_message_latency, latency)
            self.min_message_latency = min(self.min_message_latency, latency)
            if is_sent:
                self.total_messages_sent += 1
            else:
                self.total_messages_received += 1
        self.last_message_time = datetime.datetime.now(datetime.UTC)

    def update_queue_size(self, size):
        """Update the message queue size."""
        self.message_queue_size = size

    def record_websocket_disconnect(self):
        """Record a WebSocket disconnection."""
        self.websocket_disconnects += 1

    def get_transaction_success_rate(self) -> float:
        """Calculate transaction success rate."""
        total = self.transaction_count
        return ((total - self.failed_transactions) / total * 100) if total > 0 else 0

    def get_average_transaction_duration(self) -> float:
        """Calculate average transaction duration."""
        return sum(self.transaction_durations) / len(self.transaction_durations) if self.transaction_durations else 0

    def get_average_message_latency(self) -> float:
        """Calculate average message latency."""
        return sum(self.message_latencies) / len(self.message_latencies) if self.message_latencies else 0

    def log_metrics(self):
        current_time = datetime.datetime.now(datetime.UTC)
        
        logging.info("\n=== Performance Metrics ===")
        logging.info(f"Timestamp: {current_time.isoformat()}")
        
        logging.info("\n--- Current Operation ---")
        logging.info(f"Current API Response Time: {self.current_api_time:.3f}s")
        logging.info(f"Current Meter Process Time: {self.current_meter_process_time:.3f}s")
        
        logging.info("\n--- API Performance ---")
        logging.info(f"Min Response Time: {self.min_api_time:.3f}s")
        logging.info(f"Max Response Time: {self.max_api_time:.3f}s")
        logging.info(f"Success/Failure: {self.api_success}/{self.api_failure}")
        logging.info(f"Success Rate: {self.get_api_success_rate():.1f}%")
        
        logging.info("\n--- Processing Performance ---")
        logging.info(f"Meter Processing - Min: {self.min_meter_process_time:.3f}s")
        logging.info(f"Meter Processing - Max: {self.max_meter_process_time:.3f}s")
        logging.info(f"Meter Processing - Avg: {self.get_average_meter_time():.3f}s")
        
        logging.info("\n--- Transaction Metrics ---")
        logging.info(f"Total Transactions: {self.transaction_count}")
        logging.info(f"Failed Transactions: {self.failed_transactions}")
        logging.info(f"Transaction Success Rate: {self.get_transaction_success_rate():.1f}%")
        logging.info(f"Average Transaction Duration: {self.get_average_transaction_duration():.1f}s")
        logging.info(f"Active Transactions: {len(self.current_transactions)}")
        logging.info(f"Transaction Interruptions: {sum(self.transaction_interruptions.values())}")
        
        logging.info("\n--- WebSocket Performance ---")
        logging.info(f"Total Messages Sent/Received: {self.total_messages_sent}/{self.total_messages_received}")
        logging.info(f"Failed Messages: {self.failed_messages}")
        logging.info(f"Current Queue Size: {self.message_queue_size}")
        logging.info(f"Message Latency - Min: {self.min_message_latency:.3f}s")
        logging.info(f"Message Latency - Max: {self.max_message_latency:.3f}s")
        logging.info(f"Message Latency - Avg: {self.get_average_message_latency():.3f}s")
        logging.info(f"WebSocket Disconnections: {self.websocket_disconnects}")
        
        logging.info("\n--- Connection Status ---")
        logging.info(f"Uptime: {self.get_uptime():.1f} seconds")
        logging.info(f"Connection Drops: {self.connection_drops}")
        logging.info("========================\n")