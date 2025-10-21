from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import logging
import json
import time
import uuid
from performance_metrics import PerformanceMetrics

logger = logging.getLogger(__name__)

class MeterValueFormatter:
    def __init__(self):
        self.json_template = {
            "ID": "",                      # Will be generated from chargePointId + timestamp
            "groupId": "EVSE",             # Static for EVSE devices
            "groupName": "Electric Vehicle Supply Equipment",  # Static for EVSE devices
            "deviceType": "EVSE",          # Static for EVSE devices
            "timestamp": "",
            "userName": "",                 # Initialize with empty string for timestamp
            "totalPower": 0.0,             # From Power.Active.Import
            "phase1Power": 0.0,           
            "phase2Power": 0.0,
            "phase3Power": 0.0,           
            "totalReactivePower": 0.0,    
            "phase1ReactivePower": 0.0,   
            "phase2ReactivePower": 0.0,   
            "phase3ReactivePower": 0.0,   
            "totalPowerFactor": 0.0,      
            "phase1PowerFactor": 0.0,     
            "phase2PowerFactor": 0.0,     
            "phase3PowerFactor": 0.0,     
            "phase1Voltage": 0.0,         
            "phase2Voltage": 0.0,         
            "phase3Voltage": 0.0,         
            "frequency": 0.0,             
            "deliveredEnergy": 0.0,       # From Energy.Active.Import.Register
            "suppliedEnergy": 0.0
      
        }
        self.metrics = PerformanceMetrics()
        self.logger = logging.getLogger('meter_formatter')

    def generate_unique_id(self, charge_point_id: str, timestamp: str) -> str:
        """Generate a unique ID using charge point ID and timestamp."""
        combined = f"{charge_point_id}_{timestamp}"
        hash_object = hashlib.md5(combined.encode())
        return hash_object.hexdigest()[:12]

    def extract_sampled_value(self, sampled_values: list, measurand: str) -> float:
        """Extract specific measurand value from sampled values."""
        try:
            # Log all available measurands for debugging
            logger.debug(f"Available measurands: {[v.get('measurand') for v in sampled_values]}")
            logger.debug(f"Looking for measurand: {measurand}")
            
            for value in sampled_values:
                current_measurand = value.get('measurand')
                logger.debug(f"Checking measurand: {current_measurand} == {measurand}")
                if current_measurand == measurand:
                    try:
                        raw_value = value.get('value')
                        logger.debug(f"Found {measurand}: {raw_value}")
                        return float(raw_value)
                    except (ValueError, TypeError):
                        logger.error(f"Invalid value for {measurand}")
                        return 0.0
            logger.warning(f"Measurand {measurand} not found in values")
            return 0.0
        except Exception as e:
            logger.error(f"Error extracting {measurand}: {e}")
            return 0.0

    def format_meter_values(self, charge_point_id: str, meter_data: Dict[str, Any],
                                user_name: Optional[str] = None) -> Dict[str, Any]:

        start_time = time.time()
        try:
            self.logger.info(f"[METER] Processing meter values for {charge_point_id}")
            self.logger.info(f"[METER] Raw meter_data: {json.dumps(meter_data, indent=2)}")
            
            if "meterValue" in meter_data and meter_data["meterValue"]:
                meter_value = meter_data["meterValue"][0]  # Take first meter value
                timestamp = meter_value.get("timestamp", "")
                formatted_data = self.json_template.copy()
                formatted_data["ID"] = self.generate_unique_id(charge_point_id, timestamp)
                formatted_data["timestamp"] = timestamp
                formatted_data["userName"] = user_name if user_name else "Unknown"

                # Try both camelCase and snake_case keys
                sampled_values = meter_value.get("sampledValue", meter_value.get("sampled_value", []))
                self.logger.info(f"[METER] Found {len(sampled_values)} sampled values")
                
                # Log all received values
                for val in sampled_values:
                    measurand = val.get('measurand', 'Unknown')
                    value = val.get('value', '0')
                    unit = val.get('unit', '')
                    self.logger.info(f"[METER] Processing value - Measurand: {measurand}, Value: {value}, Unit: {unit}")
                    
                    try:
                        if measurand == 'Power.Active.Import':
                            total_power = float(value)
                            formatted_data["totalPower"] = total_power
                            # Distribute total power equally among three phases
                            power_per_phase = total_power / 3.0
                            formatted_data["phase1Power"] = power_per_phase
                            formatted_data["phase2Power"] = power_per_phase
                            formatted_data["phase3Power"] = power_per_phase
                            self.logger.info(f"[METER] Set totalPower = {total_power}W, per phase = {power_per_phase}W")
                        elif measurand == 'Energy.Active.Import.Register':
                            formatted_data["deliveredEnergy"] = float(value)
                            self.logger.info(f"[METER] Set deliveredEnergy = {formatted_data['deliveredEnergy']}Wh")
                        
                    except (ValueError, TypeError) as e:
                        self.logger.error(f"[METER] Error converting value for {measurand}: {e}")
                
                # Set standard frequency
                formatted_data["frequency"] = 50.0
                
                # Log final values
                self.logger.info("[METER] Final formatted values:")
                self.logger.info(f"[METER] - Total Power: {formatted_data['totalPower']}W")
                self.logger.info(f"[METER] - Phase 1 Power: {formatted_data['phase1Power']}W")
                self.logger.info(f"[METER] - Phase 2 Power: {formatted_data['phase2Power']}W")
                self.logger.info(f"[METER] - Phase 3 Power: {formatted_data['phase3Power']}W")
                self.logger.info(f"[METER] - Frequency: {formatted_data['frequency']}Hz")
                self.logger.info(f"[METER] - Delivered Energy: {formatted_data['deliveredEnergy']}Wh")

                # Add metrics before returning
                process_time = time.time() - start_time
                self.metrics.update_meter_timing(process_time)
                
                return formatted_data
            else:
                self.logger.warning("[METER] No meter values found in data")
                process_time = time.time() - start_time
                self.metrics.update_meter_timing(process_time)
                return formatted_data
            
        except Exception as e:
            self.logger.error(f"[METER] Error formatting meter values: {e}")
            self.logger.error(f"[METER] Raw meter data: {meter_data}")
            process_time = time.time() - start_time
            self.metrics.update_meter_timing(process_time)
            raise e