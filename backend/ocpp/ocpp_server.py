import asyncio
import logging
from datetime import datetime
from ocpp.v16 import ChargePoint as cp
from ocpp.v16 import call_result
from ocpp.v16 import call
from ocpp.v16.enums import Action, RegistrationStatus, AuthorizationStatus, RemoteStartStopStatus
from ocpp.routing import on
from websockets.server import serve
import websockets
from meter_formatter import MeterValueFormatter
from api_sender import ApiSender
from performance_metrics import PerformanceMetrics
import time
from datetime import datetime, timezone
import csv
import json
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# Data directory path
DATA_DIR = Path("/app/backend/data")


class QuotaManager:
    def __init__(self, csv_path=None, usage_file=None, tx_file=None):
        self.csv_path = csv_path or DATA_DIR / "users1.csv"
        self.usage_file = usage_file or DATA_DIR / "energy_usage.json"
        self.tx_file = tx_file or DATA_DIR / "active_transactions.json"
        self.users = {}
        self.energy_usage = {}
        self.active_transactions = {}  # Track ongoing transactions
        self.stop_pending = set()  # Track transactions with pending stop commands
        self.load_user_data()
        self.load_usage_data()
        self.load_active_transactions()

    def save_active_transactions(self):
        """Persist active transactions to file."""
        try:
            with open(self.tx_file, "w") as f:
                json.dump(self.active_transactions, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving active transactions: {e}")

    def load_active_transactions(self):
        """Load active transactions from file."""
        try:
            if os.path.exists(self.tx_file):
                with open(self.tx_file, "r") as f:
                    self.active_transactions = json.load(f)
            else:
                self.active_transactions = {}
            logging.info(f"Loaded {len(self.active_transactions)} active transactions from {self.tx_file}")
        except Exception as e:
            logging.error(f"Error loading active transactions: {e}")
            self.active_transactions = {}

    def load_user_data(self):
        """Load user data from CSV including quotas."""
        self.users = {}
        try:
            with open(self.csv_path, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    tag = row["id_tag"].strip()
                    full_name = f"{row['header name'].strip()} {row['surname'].strip()}"
                    plan = "unlimited" if row["unlimited"].strip().upper() == "TRUE" else "limited"

                    quota_kwh = None
                    if plan == "limited":
                        if row.get("quota_kwh") and row.get("quota_kwh").strip():
                            quota_kwh = float(row["quota_kwh"])
                        else:
                            logging.warning(
                                f"[USER] {tag} has no quota defined in CSV and is marked as limited → blocking user")

                    self.users[tag] = {
                        "full_name": full_name,
                        "plan": plan,
                        "quota_kwh": quota_kwh  # None for unlimited users
                    }
            logging.info(f"Loaded {len(self.users)} users from {self.csv_path}")
        except Exception as e:
            logging.error(f"Error loading user data: {e}")

    def load_usage_data(self):
        """Load existing energy usage data."""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    self.energy_usage = json.load(f)
            else:
                self.energy_usage = {}
            logging.info(f"Loaded energy usage data for {len(self.energy_usage)} users")
        except Exception as e:
            logging.error(f"Error loading usage data: {e}")
            self.energy_usage = {}

    def save_usage_data(self):
        """Save current energy usage to file."""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.energy_usage, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving usage data: {e}")

    def get_user_info(self, id_tag):
        user = self.users.get(id_tag)
        if not user:
            return None
        current_usage = self.energy_usage.get(id_tag, 0)
        remaining_quota = None
        if user["plan"] == "limited" and user["quota_kwh"] is not None:
            remaining_quota = max(0, user["quota_kwh"] - current_usage)
        return {
            "full_name": user["full_name"],
            "plan": user["plan"],
            "quota_kwh": user["quota_kwh"],
            "used_kwh": current_usage,
            "remaining_kwh": remaining_quota
        }

    def can_start_transaction(self, id_tag):
        user_info = self.get_user_info(id_tag)
        if not user_info:
            return False, "User not found"
        if user_info["plan"] == "unlimited":
            return True, "Unlimited plan"
        if user_info["remaining_kwh"] is None or user_info["remaining_kwh"] <= 0:
            return False, f"Quota exceeded. Used: {user_info['used_kwh']:.2f}kWh, Quota: {user_info['quota_kwh']:.2f}kWh"
        return True, f"Available quota: {user_info['remaining_kwh']:.2f}kWh"

    def start_transaction(self, transaction_id, id_tag, initial_meter_kwh, charger_id):
        tx_id_str = str(transaction_id) 
        user_info = self.get_user_info(id_tag)
        full_name = user_info["full_name"] if user_info else "Unknown"
        self.active_transactions[str(transaction_id)] = {
            "id_tag": id_tag,
            "start_meter": initial_meter_kwh,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "last_meter": initial_meter_kwh,
            "full_name": full_name,
            "charger_id": charger_id
        }
        # Clear any pending stop flag when starting new transaction
        self.stop_pending.discard(tx_id_str)
        self.save_active_transactions()
        logging.info(f"[QUOTA] Transaction {transaction_id} started for {id_tag}")

    def update_transaction_usage(self, transaction_id, current_meter_kwh):
        transaction_id = str(transaction_id)
        if transaction_id not in self.active_transactions:
            return False
        # Don't check quota if stop is already pending
        if transaction_id in self.stop_pending:
            logging.debug(f"[QUOTA] Stop already pending for transaction {transaction_id}, skipping quota check")
            return False

        transaction = self.active_transactions[transaction_id]
        id_tag = transaction["id_tag"]

        # Use last_meter if available, otherwise start_meter
        last_meter = transaction.get("last_meter", transaction["start_meter"])
        energy_increment = max(0, current_meter_kwh - last_meter)

        # Persist the updated last_meter
        transaction["last_meter"] = current_meter_kwh

        # Update quota file
        self.energy_usage[id_tag] = self.energy_usage.get(id_tag, 0) + energy_increment
        self.save_usage_data()
        self.save_active_transactions()

        logging.info(
            f"[DEBUG] Updating energy_usage.json for {id_tag}: +{energy_increment:.3f} kWh "
            f"(Total: {self.energy_usage[id_tag]:.3f} kWh)"
        )

        user_info = self.get_user_info(id_tag)
        if not user_info or user_info["plan"] == "unlimited":
            return False

        if user_info["quota_kwh"] and user_info["used_kwh"] >= user_info["quota_kwh"]:
            self.stop_pending.add(transaction_id)
            logging.info(f"[QUOTA] Marking transaction {transaction_id} for stop (quota exceeded)")
            return True
        
        return False

    def end_transaction(self, transaction_id, final_meter_kwh):
        transaction_id = str(transaction_id)
        if transaction_id not in self.active_transactions:
            return
        transaction = self.active_transactions[transaction_id]
        id_tag = transaction["id_tag"]

        # Update last meter for recordkeeping
        transaction["last_meter"] = final_meter_kwh

        # Do not increment usage again; already updated in real time
        del self.active_transactions[transaction_id]

        # Cleanup
        self.stop_pending.discard(transaction_id)
        self.save_usage_data()
        self.save_active_transactions()

        logging.info(
            f"[QUOTA] Transaction {transaction_id} ended for {id_tag}, "
            f"final meter {final_meter_kwh:.3f}kWh (no extra increment)"
        )

    def reset_monthly_usage(self):
        """Reset all user energy usage at the start of a new month."""
        current_month = datetime.now().strftime("%Y-%m")
        reset_file = DATA_DIR / "last_reset.txt"

        # Check when we last reset
        last_reset_month = None
        if os.path.exists(reset_file):
            with open(reset_file, "r") as f:
                last_reset_month = f.read().strip()

        # If it's a new month, reset usage
        if last_reset_month != current_month:
            logging.info(f"[RESET] New month detected ({current_month}) → resetting all user usage.")
            for user_id in self.energy_usage.keys():
                self.energy_usage[user_id] = 0.0
            self.save_usage_data()

            # Save last reset month
            with open(reset_file, "w") as f:
                f.write(current_month)
        else:
            logging.info(f"[RESET] Usage file already reset for {current_month}, skipping.")


class ChargePoint(cp):
    def __init__(self, id, connection, meter_formatter: MeterValueFormatter, api_sender: ApiSender,
                 quota_manager: QuotaManager, charger_status_manager):
        super().__init__(id, connection)
        self.id = id
        self.heartbeat_interval = 60
        self.meter_formatter = meter_formatter
        self.api_sender = api_sender
        self.current_state = "Available"
        self._message_start_time = None
        self.quota_manager = quota_manager
        self.energy_unit_factor = 1  # Energy values are in kWh
        self.charger_status_manager = charger_status_manager

    def convert_to_kwh(self, energy_value):
        """
        Convert energy value to kWh.
        Schneider/EVlinkProAC chargers send values in Wh,
        while others (e.g., Livoltek) send kWh.
        """
        try:
            # Normalize the ID once for comparison
            charger_id = str(self.id).upper()

            # Detect Schneider/EVlinkProAC chargers by ID
            if "SCHNEIDER" in charger_id or "EVLINKPROAC" in charger_id or "EVLINK" in charger_id:
                value_kwh = float(energy_value) / 1000.0  # Wh → kWh
                logging.info(f"[CONVERT] {self.id}: Converted {energy_value} Wh → {value_kwh:.3f} kWh")
                return value_kwh

            # Other brands already report in kWh
            return float(energy_value)

        except (ValueError, TypeError):
            logging.error(f"[METER] Invalid energy value: {energy_value}")
            return 0.0

    async def send_call(self, call):
        """Override to track message metrics."""
        try:
            self._message_start_time = time.time()
            response = await super().send_call(call)
            latency = time.time() - self._message_start_time
            self.api_sender.metrics.record_message_metrics(latency, is_sent=True)
            return response
        except Exception as e:
            if self._message_start_time:
                latency = time.time() - self._message_start_time
                self.api_sender.metrics.record_message_metrics(latency, is_sent=True, failed=True)
            raise e

    async def _handle_call(self, message):
        """Override to track message metrics."""
        try:
            start_time = time.time()
            response = await super()._handle_call(message)
            latency = time.time() - start_time
            self.api_sender.metrics.record_message_metrics(latency, is_sent=False)
            return response
        except Exception as e:
            self.api_sender.metrics.record_message_metrics(0, is_sent=False, failed=True)
            raise e

    async def stop_transaction_remotely(self, transaction_id):
        """Send RemoteStopTransaction command to the charger."""
        try:
            # Ensure transaction_id is an integer - convert from string if needed
            if isinstance(transaction_id, str):
                tx_id = int(transaction_id)
            else:
                tx_id = transaction_id
            
            logging.info(f"[REMOTE_STOP] Sending stop command for transaction {tx_id}")
            
            # Create the request
            request = call.RemoteStopTransactionPayload(transaction_id=tx_id)
            
            # Send the command without waiting for confirmation
            # The charger will send StopTransaction message when it actually stops
            response = await self.call(request)
            
            if response.status == RemoteStartStopStatus.accepted:
                logging.info(f"[REMOTE_STOP] ✓ Charger accepted stop command for transaction {tx_id}")
                return True
            else:
                logging.warning(f"[REMOTE_STOP] ✗ Charger rejected stop command for transaction {tx_id}: {response.status}")
                # Clear the pending flag if rejected
                self.quota_manager.stop_pending.discard(str(tx_id))
                return False
                
        except asyncio.TimeoutError:
            # Timeout is actually OK - the charger might still stop the transaction
            # It just took longer than 30s to respond
            logging.warning(f"[REMOTE_STOP] ⏱ Timeout waiting for response on transaction {tx_id}, but command was sent")
            return True  # Consider it successful since command was sent
            
        except Exception as e:
            logging.error(f"[REMOTE_STOP] ✗ Failed to send stop command for transaction {transaction_id}: {e}")
            # Clear the pending flag on error
            self.quota_manager.stop_pending.discard(str(transaction_id))
            return False

    @on(Action.BootNotification)
    async def on_boot_notification(self, charging_station=None, charge_point_model=None, charge_point_vendor=None,
                                   **kwargs):
        """Handle BootNotification from Charge Point."""
        try:
            logging.info(f'Received boot notification from {self.id}')
            if charging_station:
                logging.info(f'Charge station: {charging_station}')
            if charge_point_model:
                logging.info(f'Model: {charge_point_model}')
            if charge_point_vendor:
                logging.info(f'Vendor: {charge_point_vendor}')

            # Update charger status file
            self.charger_status_manager.update_charger_boot(
                self.id,
                charge_point_vendor or "Unknown",
                charge_point_model or "Unknown"
            )

            return call_result.BootNotificationPayload(
                current_time=datetime.now(timezone.utc).isoformat(),
                interval=self.heartbeat_interval,
                status=RegistrationStatus.accepted
            )
        except Exception as e:
            logging.error(f'Error in boot notification: {e}')
            return call_result.BootNotificationPayload(
                current_time=datetime.now(timezone.utc).isoformat(),
                interval=self.heartbeat_interval,
                status=RegistrationStatus.accepted
            )

    @on(Action.Heartbeat)
    async def on_heartbeat(self):
        """Handle Heartbeat from Charge Point."""
        logging.info(f'Received heartbeat from {self.id}')
        
        # Update charger status - heartbeat indicates charger is online
        self.charger_status_manager.update_charger_heartbeat(self.id)
        
        return call_result.HeartbeatPayload(
            current_time=datetime.now(timezone.utc).isoformat()
        )

    @on(Action.MeterValues)
    async def on_meter_values(self, connector_id=None, meter_value=None, **kwargs):
        """Handle MeterValues from Charge Point with quota checking."""
        try:
            # Log raw incoming data
            logging.info(f'[METER] Received meter values from {self.id}')
            logging.info(f'[METER] Connector ID: {connector_id}')

            # Extract energy value for quota checking
            current_energy_kwh = None
            transaction_id = kwargs.get('transaction_id')

            user_name = "Unknown"
            if transaction_id:
                tx_id_str = str(transaction_id)
                if tx_id_str in self.quota_manager.active_transactions:
                    user_name = self.quota_manager.active_transactions[tx_id_str].get("full_name", "Unknown")

            if meter_value:
                for value in meter_value:
                    # Support both camelCase and snake_case
                    samples = value.get('sampledValue') or value.get('sampled_value', [])
                    for val in samples:
                        measurand = val.get('measurand', 'Energy.Active.Import.Register')

                        if measurand in ['Energy.Active.Import.Register', 'Energy']:
                            try:
                                raw_energy = float(val.get('value', 0))
                                current_energy_kwh = self.convert_to_kwh(raw_energy)
                                logging.info(f'[METER] Energy reading: {current_energy_kwh:.3f}kWh')

                            except (ValueError, TypeError) as e:
                                logging.error(f'[METER] Error parsing energy value: {e}')

            # Check active transactions for quota violations
            if current_energy_kwh is not None:
                transactions_to_stop = []

                # If we have a specific transaction ID, check only that one
                if transaction_id and transaction_id in self.quota_manager.active_transactions:
                    quota_exceeded = self.quota_manager.update_transaction_usage(transaction_id, current_energy_kwh)
                    if quota_exceeded:
                        transactions_to_stop.append(transaction_id)
                else:
                    # Only update transactions from the same charger
                    for tid, transaction in self.quota_manager.active_transactions.items():
                        charger_name = transaction.get("charger_id")
                        if charger_name == self.id:
                            quota_exceeded = self.quota_manager.update_transaction_usage(tid, current_energy_kwh)
                            if quota_exceeded:
                                transactions_to_stop.append(tid)

                # Stop transactions that exceeded quota
                for tid in transactions_to_stop:
                    user_info = self.quota_manager.get_user_info(self.quota_manager.active_transactions[tid]["id_tag"])
                    user_name = user_info["full_name"] if user_info else "Unknown"
                    logging.warning(f"[QUOTA] Remote stop triggered for {user_name} (ID {tid}) due to quota exceeded")
                    await self.stop_transaction_remotely(tid)
            
            # Format meter values for API (with user name)
            try:
                formatted_data = self.meter_formatter.format_meter_values(
                    self.id,
                    {
                        "connectorId": connector_id,
                        "meterValue": meter_value,
                        **kwargs
                    },
                    user_name=user_name
                )
                formatted_data["chargerName"] = self.id

                # Save to meter_data_log.json
                self.charger_status_manager.append_meter_log(formatted_data)

            except Exception as format_error:
                logging.error(f'[METER] Failed to format meter data: {str(format_error)}')
                return call_result.MeterValuesPayload()

            # Log formatted data
            logging.info(f'[METER] Formatted data:')
            logging.info(f'[METER] ID: {formatted_data["ID"]}')
            logging.info(f'[METER] User: {user_name}')
            logging.info(f'[METER] Timestamp: {formatted_data["timestamp"]}')
            logging.info(f'[METER] Total Power: {formatted_data["totalPower"]}W')
            logging.info(f'[METER] Delivered Energy: {formatted_data["deliveredEnergy"]}Wh')

            # Send to external API
            try:
                success = await self.api_sender.send_meter_data(formatted_data)
                if success:
                    logging.info(f'[METER] Successfully sent meter data to API')
                else:
                    logging.error(f'[METER] Failed to send meter data to API')
            except Exception as api_error:
                logging.error(f'[METER] API Error: {str(api_error)}')

            return call_result.MeterValuesPayload()

        except Exception as e:
            logging.error(f'[METER] Error processing meter values: {str(e)}')
            return call_result.MeterValuesPayload()

    @on(Action.Authorize)
    async def on_authorize(self, id_tag: str, **kwargs):
        logging.info(f"[AUTH] RFID Tag {id_tag} requesting authorization on station {self.id}")

        if self.id != "BEDAS01":
            user_info = self.quota_manager.get_user_info(id_tag)

            if user_info:
                can_charge, reason = self.quota_manager.can_start_transaction(id_tag)
                if can_charge:
                    status = AuthorizationStatus.accepted
                    logging.info(f"[AUTH] {id_tag} ({user_info['full_name']}) AUTHORIZED - {reason}")
                else:
                    status = AuthorizationStatus.invalid
                    logging.warning(f"[AUTH] {id_tag} ({user_info['full_name']}) DENIED - {reason}")
            else:
                status = AuthorizationStatus.invalid
                logging.warning(f"[AUTH] {id_tag} is NOT authorized - User not found")
        else:
            status = AuthorizationStatus.accepted
            logging.info(f"[AUTH] Charger {self.id} not restricted. {id_tag} auto-authorized")

        return call_result.AuthorizePayload(
            id_tag_info={'status': status}
        )

    @on(Action.StartTransaction)
    async def on_start_transaction(self, connector_id, id_tag, meter_start, timestamp, **kwargs):
        """Handle StartTransaction with quota checking."""
        # Check quota before allowing transaction
        can_charge, reason = self.quota_manager.can_start_transaction(id_tag)

        if not can_charge and self.id != "BEDAS01":
            logging.warning(f'[TRANSACTION] Start DENIED - Station: {self.id}, RFID: {id_tag}, Reason: {reason}')
            return call_result.StartTransactionPayload(
                transaction_id=0,  # Invalid transaction ID
                id_tag_info={'status': AuthorizationStatus.invalid}
            )

        transaction_id = int(time.time())  # Simple transaction ID generation
        meter_start_kwh = self.convert_to_kwh(meter_start)

        # Record transaction start
        self.quota_manager.start_transaction(transaction_id, id_tag, meter_start_kwh, self.id)

        self.api_sender.metrics.start_transaction(transaction_id)

        user_info = self.quota_manager.get_user_info(id_tag)
        user_name = user_info['full_name'] if user_info else 'Unknown'

        logging.info(
            f'[TRANSACTION] Start APPROVED - Station: {self.id}, Connector: {connector_id}, User: {user_name} ({id_tag}), Initial Meter: {meter_start_kwh:.3f}kWh, Transaction ID: {transaction_id}')

        if user_info and user_info['remaining_kwh'] is not None:
            logging.info(f'[QUOTA] Available quota for {id_tag}: {user_info["remaining_kwh"]:.3f}kWh')

        # Update charger status to Charging
        self.charger_status_manager.update_charger_status(self.id, "Charging", connector_id)

        return call_result.StartTransactionPayload(
            transaction_id=transaction_id,
            id_tag_info={'status': AuthorizationStatus.accepted}
        )

    @on(Action.StopTransaction)
    async def on_stop_transaction(self, meter_stop, timestamp, transaction_id, **kwargs):
        """Handle StopTransaction with quota update."""
        reason = kwargs.get('reason', None)
        was_successful = reason not in ['Error', 'EVDisconnected', 'DeAuthorized', 'EmergencyStop']

        meter_stop_kwh = self.convert_to_kwh(meter_stop)

        # Update quota usage
        self.quota_manager.end_transaction(transaction_id, meter_stop_kwh)
        self.api_sender.metrics.end_transaction(transaction_id, was_successful)

        logging.info(
            f'[TRANSACTION] Stop completed - Station: {self.id}, Transaction ID: {transaction_id}, Final Meter: {meter_stop_kwh:.3f}kWh, Success: {was_successful}')

        # Update charger status back to Available
        self.charger_status_manager.update_charger_status(self.id, "Available")

        return call_result.StopTransactionPayload(
            id_tag_info={'status': AuthorizationStatus.accepted}
        )

    @on(Action.SecurityEventNotification)
    async def on_security_event_notification(self, type: str, timestamp: str, **kwargs):
        """Handle security event notifications from Charge Point."""
        logging.info(f'[SECURITY] Event from {self.id} - Type: {type}, Time: {timestamp}')
        if kwargs:
            logging.info(f'[SECURITY] Additional info: {kwargs}')
        return call_result.SecurityEventNotificationPayload()

    @on(Action.StatusNotification)
    async def on_status_notification(self, connector_id: int, error_code: str, status: str, **kwargs):
        """Handle StatusNotification with state transition tracking."""
        old_state = self.current_state
        self.current_state = status
        self.api_sender.metrics.record_state_transition(old_state, status)
        
        # Update charger status in file
        self.charger_status_manager.update_charger_status(self.id, status, connector_id)
        
        logging.info(f'[STATUS] Station: {self.id}, Connector: {connector_id}, Status: {status}, Error: {error_code}')
        return call_result.StatusNotificationPayload()


class ChargerStatusManager:
    """Manages charger_status.json file for dashboard integration."""
    
    def __init__(self):
        self.status_file = DATA_DIR / "charger_status.json"
        self.meter_log_file = DATA_DIR / "meter_data_log.json"
        self.chargers = {}
        self.load_charger_status()
    
    def load_charger_status(self):
        """Load existing charger status."""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    self.chargers = json.load(f)
            else:
                self.chargers = {}
            logging.info(f"Loaded {len(self.chargers)} chargers from status file")
        except Exception as e:
            logging.error(f"Error loading charger status: {e}")
            self.chargers = {}
    
    def save_charger_status(self):
        """Save charger status to file."""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.chargers, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving charger status: {e}")
    
    def update_charger_boot(self, charger_id, brand, model):
        """Update charger info on boot notification."""
        if charger_id not in self.chargers:
            self.chargers[charger_id] = {
                "name": charger_id,
                "brand": brand,
                "model": model,
                "status": "Available",
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                "total_energy_delivered": 0,
                "uptime_hours": 0,
                "connector_id": 1
            }
        else:
            self.chargers[charger_id]["brand"] = brand
            self.chargers[charger_id]["model"] = model
            self.chargers[charger_id]["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
        
        self.save_charger_status()
        logging.info(f"[STATUS] Updated boot info for charger {charger_id}")
    
    def update_charger_heartbeat(self, charger_id):
        """Update last heartbeat time."""
        if charger_id in self.chargers:
            self.chargers[charger_id]["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
            self.save_charger_status()
    
    def update_charger_status(self, charger_id, status, connector_id=None):
        """Update charger status (Charging, Available, etc)."""
        if charger_id not in self.chargers:
            self.chargers[charger_id] = {
                "name": charger_id,
                "brand": "Unknown",
                "model": "Unknown",
                "status": status,
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                "total_energy_delivered": 0,
                "uptime_hours": 0,
                "connector_id": connector_id or 1
            }
        else:
            self.chargers[charger_id]["status"] = status
            self.chargers[charger_id]["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
            if connector_id is not None:
                self.chargers[charger_id]["connector_id"] = connector_id
        
        self.save_charger_status()
        logging.info(f"[STATUS] Updated status for charger {charger_id}: {status}")
    
    def append_meter_log(self, meter_data):
        """Append meter reading to meter_data_log.json."""
        try:
            # Load existing logs
            logs = []
            if os.path.exists(self.meter_log_file):
                with open(self.meter_log_file, 'r') as f:
                    logs = json.load(f)
            
            # Append new log
            logs.append(meter_data)
            
            # Keep only last 500 entries to prevent file from growing too large
            if len(logs) > 500:
                logs = logs[-500:]
            
            # Save back
            with open(self.meter_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
            
            logging.info(f"[METER_LOG] Appended meter reading to log file")
        except Exception as e:
            logging.error(f"[METER_LOG] Error appending to meter log: {e}")


class CentralSystem:
    def __init__(self, port=9000, api_url=None, api_key=None, csv_path=None):
        self.chargers = {}
        self.port = port
        self.meter_formatter = MeterValueFormatter()
        self.api_sender = ApiSender(api_url, api_key)
        self.quota_manager = QuotaManager(csv_path)
        self.charger_status_manager = ChargerStatusManager()

    async def run_daily_reset(self):
        """Background task to run monthly reset once a day."""
        while True:
            try:
                logging.info("[RESET] Daily check for monthly usage reset...")
                self.quota_manager.reset_monthly_usage()
            except Exception as e:
                logging.error(f"[RESET] Error during monthly reset check: {e}")

            # Sleep for 24 hours (86400 seconds)
            await asyncio.sleep(86400)

    def configure_api(self, api_url: str, api_key: str = None):
        """Configure the API endpoint and key."""
        self.api_sender.configure(api_url, api_key)

    async def on_connect(self, websocket, path):
        """Handle incoming WebSocket connections."""
        try:
            charge_point_id = path.strip("/")

            cp = ChargePoint(
                charge_point_id, 
                websocket, 
                self.meter_formatter, 
                self.api_sender, 
                self.quota_manager,
                self.charger_status_manager
            )
            self.chargers[charge_point_id] = cp

            # Add connection metrics
            self.api_sender.metrics.connection_start_time = datetime.now(timezone.utc)
            self.api_sender.metrics.last_connection_time = datetime.now(timezone.utc)

            logging.info(f'[CONNECT] Charger {charge_point_id} connected')

            await cp.start()

            # Wait for charger to finish BootNotification and be ready
            await asyncio.sleep(2)

            # Request ALL configuration keys
            request = call.GetConfigurationPayload()

            try:
                response = await cp.send_call(request)
                logging.info(f"[CONFIG] Received ALL configuration keys from {charge_point_id}:")
                for item in response.configuration_key:
                    logging.info(f"[CONFIG] {item.key}: {item.value} (ReadOnly={item.readonly})")
                if response.unknown_key:
                    logging.warning(f"[CONFIG] Unknown keys (unrecognized by charger): {response.unknown_key}")
            except Exception as e:
                logging.error(f"[CONFIG] Failed to get configuration: {str(e)}")

        except Exception as e:
            logging.error(f'Error on connection: {e}')
        finally:
            if charge_point_id in self.chargers:
                # Add disconnection metrics
                self.api_sender.metrics.connection_drops += 1
                del self.chargers[charge_point_id]
                
                # Update charger status to Offline
                self.charger_status_manager.update_charger_status(charge_point_id, "Offline")
                
                logging.info(f'[CONNECT] Charger {charge_point_id} disconnected')

    async def start(self):
        """Start the OCPP server."""
        server = await serve(
            self.on_connect,
            "0.0.0.0",
            self.port,
            subprotocols=["ocpp1.6"],
            ping_interval=None,
            ping_timeout=None
        )
        logging.info(f'OCPP Server started on port {self.port}')
        logging.info(f'Chargers can connect via: ws://<host>:{self.port}/<charger_id>')

        # Start daily background reset task
        asyncio.create_task(self.run_daily_reset())
        await server.wait_closed()

    def get_quota_status(self, id_tag=None):
        """Get quota status for a user or all users."""
        if id_tag:
            return self.quota_manager.get_user_info(id_tag)
        else:
            status = {}
            for tag in self.quota_manager.users.keys():
                status[tag] = self.quota_manager.get_user_info(tag)
            return status


def main():
    try:
        logging.info("Starting OCPP Central System with Quota Management...")
        logging.info(f"Data directory: {DATA_DIR}")
        
        central_system = CentralSystem(
            port=9000,
            api_url='http://144.122.166.37:3005/api/readings/',
            api_key='None',
            csv_path=DATA_DIR / 'users1.csv'
        )
        asyncio.run(central_system.start())
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
