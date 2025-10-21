# OCPP Central System Integration

## Overview
This OCPP 1.6 Central System is integrated with the EV Charging Dashboard. It runs alongside the FastAPI backend and shares the same data files for real-time synchronization.

## System Architecture

### Services Running:
1. **FastAPI Backend** (Port 8001): Dashboard REST API
2. **OCPP WebSocket Server** (Port 9000): Charger connections
3. **React Frontend** (Port 3000): Web dashboard UI

### Data Flow:
```
Chargers (WebSocket) → OCPP Server (Port 9000) → Data Files → FastAPI → Dashboard UI
                                                      ↓
                                              External API (Optional)
```

## Connecting Physical Chargers

### Connection URL:
```
ws://YOUR_SERVER_IP:9000/CHARGER_ID
```

**Example for LIVOLTEK_01:**
```
ws://144.122.166.37:9000/LIVOLTEK_01
```

### Supported Chargers:
- **LIVOLTEK** - Reports energy in kWh
- **SCHNEIDER / EVlinkProAC** - Reports energy in Wh (auto-converted to kWh)
- Any OCPP 1.6 compliant charger

### Configuration on Charger:
1. Access charger's admin interface
2. Navigate to OCPP settings
3. Set Central System URL: `ws://YOUR_SERVER_IP:9000/CHARGER_ID`
4. Set OCPP version: **1.6**
5. Save and reboot charger

## Data Files (Shared with Dashboard)

All files are located in `/app/backend/data/`:

### 1. users1.csv
User database with quotas:
```csv
id_tag,header name,surname,quota_kwh,unlimited
RFID001,John,Doe,150,FALSE
RFID002,Jane,Smith,200,FALSE
RFID003,Admin,User,0,TRUE
```

### 2. energy_usage.json
Real-time energy consumption per user:
```json
{
  "RFID001": 85.5,
  "RFID002": 120.3
}
```

### 3. active_transactions.json
Current charging sessions:
```json
{
  "1234567890": {
    "id_tag": "RFID001",
    "start_meter": 85.5,
    "start_time": "2025-01-15T10:30:00Z",
    "last_meter": 88.2,
    "full_name": "John Doe",
    "charger_id": "LIVOLTEK_01"
  }
}
```

### 4. charger_status.json
Charger states and information:
```json
{
  "LIVOLTEK_01": {
    "name": "LIVOLTEK_01",
    "brand": "LIVOLTEK",
    "status": "Charging",
    "last_heartbeat": "2025-01-15T10:35:00Z",
    "total_energy_delivered": 1523.5,
    "connector_id": 1
  }
}
```

### 5. meter_data_log.json
Historical meter readings (last 500 entries):
```json
[
  {
    "ID": "abc123def456",
    "timestamp": "2025-01-15T10:35:00Z",
    "userName": "John Doe",
    "chargerName": "LIVOLTEK_01",
    "totalPower": 7200,
    "deliveredEnergy": 88.2,
    "frequency": 50.0
  }
]
```

## OCPP Operations Handled

### From Charger to Server:
- ✅ **BootNotification** - Charger registration
- ✅ **Heartbeat** - Keep-alive (every 60s)
- ✅ **Authorize** - RFID tag authorization with quota check
- ✅ **StartTransaction** - Begin charging session (with quota validation)
- ✅ **StopTransaction** - End charging session
- ✅ **MeterValues** - Real-time power/energy readings
- ✅ **StatusNotification** - Charger state changes
- ✅ **SecurityEventNotification** - Security events

### From Server to Charger:
- ✅ **RemoteStopTransaction** - Stop charging when quota exceeded
- ✅ **GetConfiguration** - Request charger configuration

## Quota Management

### How It Works:
1. User swipes RFID tag
2. OCPP server checks user quota in `users1.csv`
3. If quota available → authorize charging
4. During charging, `MeterValues` updates `energy_usage.json` in real-time
5. If quota exceeded → automatic `RemoteStopTransaction`
6. Monthly auto-reset on 1st of each month

### Quota Plans:
- **Limited**: User has a monthly kWh quota
- **Unlimited**: No quota restrictions

## External API Integration

The system sends meter data to an external API:

**Endpoint:** `http://144.122.166.37:3005/api/readings/`
**Method:** POST
**Format:** JSON

To disable or change:
1. Edit `/app/backend/ocpp/ocpp_server.py`
2. Modify `main()` function:
```python
central_system = CentralSystem(
    port=9000,
    api_url='http://YOUR_API_URL',  # Change here
    api_key='YOUR_API_KEY',          # Change here
    csv_path=DATA_DIR / 'users1.csv'
)
```
3. Restart: `supervisorctl restart ocpp_server`

## Logs and Monitoring

### View OCPP Server Logs:
```bash
# Real-time logs
tail -f /var/log/supervisor/ocpp_server.err.log

# Last 100 lines
tail -100 /var/log/supervisor/ocpp_server.err.log
```

### Key Log Messages:
- `[CONNECT]` - Charger connected/disconnected
- `[AUTH]` - Authorization requests
- `[TRANSACTION]` - Start/stop transactions
- `[METER]` - Meter value readings
- `[QUOTA]` - Quota checks and remote stops
- `[STATUS]` - Charger status updates

### Service Management:
```bash
# Check status
supervisorctl status

# Restart services
supervisorctl restart ocpp_server
supervisorctl restart backend
supervisorctl restart all

# View all logs
supervisorctl tail -f ocpp_server
```

## Testing the Integration

### 1. Check Services Running:
```bash
supervisorctl status
```
Expected:
- backend: RUNNING
- frontend: RUNNING
- ocpp_server: RUNNING

### 2. Verify OCPP Server is Listening:
```bash
netstat -tuln | grep 9000
```
Should show: `0.0.0.0:9000` LISTEN

### 3. Test Charger Connection:
Use a WebSocket client (e.g., `wscat`) or configure your physical charger:
```bash
# Install wscat (if needed)
npm install -g wscat

# Test connection
wscat -c "ws://localhost:9000/TEST_CHARGER" -s ocpp1.6
```

### 4. Access Dashboard:
Open browser: `https://YOUR_PREVIEW_URL`
- Login: `admin` / `admin123`
- View real-time charger status
- Monitor active transactions
- Check user quotas

## Troubleshooting

### OCPP Server Won't Start:
```bash
# Check logs
cat /var/log/supervisor/ocpp_server.err.log

# Check data directory
ls -la /app/backend/data/

# Verify dependencies
cd /app/backend && pip list | grep -E "ocpp|websockets|aiohttp"
```

### Charger Won't Connect:
1. Verify charger OCPP URL: `ws://SERVER_IP:9000/CHARGER_ID`
2. Check firewall/network access to port 9000
3. Verify OCPP version is set to 1.6
4. Check OCPP server logs for connection attempts

### Quota Not Working:
1. Verify user exists in `/app/backend/data/users1.csv`
2. Check RFID tag matches exactly (case-sensitive)
3. View energy usage: `cat /app/backend/data/energy_usage.json`
4. Check logs for `[QUOTA]` messages

### Dashboard Not Updating:
1. Backend should read same data files as OCPP server
2. Dashboard auto-refreshes every 10 seconds
3. Check browser console for errors
4. Verify FastAPI backend is running: `supervisorctl status backend`

## File Structure
```
/app/backend/
├── ocpp/
│   ├── __init__.py
│   ├── ocpp_server.py          # Main OCPP WebSocket server
│   ├── api_sender.py            # External API integration
│   ├── meter_formatter.py       # Meter data formatting
│   ├── performance_metrics.py   # Performance tracking
│   └── README.md                # This file
├── data/                        # Shared data directory
│   ├── users1.csv
│   ├── energy_usage.json
│   ├── active_transactions.json
│   ├── charger_status.json
│   └── meter_data_log.json
├── server.py                    # FastAPI dashboard backend
└── requirements.txt
```

## Performance Monitoring

The system tracks:
- API response times
- Meter processing times
- Transaction success rates
- WebSocket message latency
- Connection uptime

Metrics are logged automatically with each operation.

## Security Notes

⚠️ **Production Recommendations:**
1. Use wss:// (WebSocket Secure) instead of ws://
2. Implement proper authentication for chargers
3. Use environment variables for API keys
4. Set up firewall rules for port 9000
5. Enable SSL/TLS certificates
6. Implement rate limiting
7. Regular security audits

## Support

For issues or questions:
1. Check logs first
2. Review this README
3. Verify all services are running
4. Test with simple WebSocket client before connecting physical chargers

## Version Information
- OCPP Version: **1.6**
- Python: 3.11
- websockets: 12.0
- ocpp library: 0.22.0
- aiohttp: 3.9.1
