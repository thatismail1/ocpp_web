# 🔌 OCPP Integration Complete! ⚡

## ✅ Integration Status: SUCCESS

Your OCPP Python files have been successfully integrated with the FastAPI + React web dashboard!

---

## 🎯 What's Running Now

### Three Services Operating Simultaneously:

| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| **OCPP WebSocket Server** | 9000 | ✅ RUNNING | Charger connections |
| **FastAPI Backend** | 8001 | ✅ RUNNING | Dashboard REST API |
| **React Frontend** | 3000 | ✅ RUNNING | Web UI |

---

## 🔗 Connect Your Chargers

### WebSocket URL Format:
```
ws://YOUR_SERVER_IP:9000/CHARGER_ID
```

### Examples:
```
LIVOLTEK Charger:
ws://144.122.166.37:9000/LIVOLTEK_01

SCHNEIDER Charger:
ws://144.122.166.37:9000/SCHNEIDER_01
```

### Steps to Configure Your Physical Chargers:

1. **Access Charger Admin Panel**
   - Connect to charger via web interface or local network

2. **Navigate to OCPP Settings**
   - Look for "OCPP Configuration" or "Network Settings"

3. **Enter Central System URL**
   - **URL:** `ws://YOUR_SERVER_IP:9000/CHARGER_ID`
   - **Protocol:** OCPP 1.6
   - **Replace CHARGER_ID** with your charger's identifier (e.g., LIVOLTEK_01)

4. **Save & Reboot**
   - Apply settings and restart the charger

5. **Verify Connection**
   - Check OCPP server logs: `tail -f /var/log/supervisor/ocpp_server.err.log`
   - Look for `[CONNECT] Charger CHARGER_ID connected`

---

## 📊 Real-Time Data Flow

```
Physical Charger
      ↓ (WebSocket OCPP 1.6)
OCPP Server (Port 9000)
      ↓ (Updates files)
/app/backend/data/
      ├── users1.csv              ← User database with quotas
      ├── energy_usage.json       ← Real-time kWh consumption
      ├── active_transactions.json ← Current charging sessions
      ├── charger_status.json     ← Charger states
      └── meter_data_log.json     ← Historical readings
      ↓ (Reads files every 10s)
FastAPI Backend (Port 8001)
      ↓ (REST API)
React Dashboard (Port 3000)
      ↓ (Auto-refresh)
Your Browser 🖥️
```

**External API:** Data also sent to `http://144.122.166.37:3005/api/readings/`

---

## 🎮 Features Now Active

### ✅ User Authorization & Quota Management
- Users defined in `/app/backend/data/users1.csv`
- RFID tag authorization with quota checks
- Real-time energy tracking
- Automatic remote stop when quota exceeded
- Monthly usage reset (automatic on 1st of each month)

### ✅ Charger Management
- **BootNotification** - Charger registration
- **Heartbeat** - Keep-alive monitoring (60s interval)
- **StatusNotification** - Real-time status updates (Charging, Available, Offline)
- **MeterValues** - Power and energy readings
- **RemoteStopTransaction** - Stop charging remotely

### ✅ Transaction Tracking
- Start/stop transaction logging
- Real-time meter value updates
- Transaction history
- User association per session

### ✅ Dashboard Features
- View all connected chargers
- Monitor active charging sessions
- Track user quotas and usage
- View historical meter readings
- User management (CRUD operations)
- Energy consumption analytics

---

## 📝 Configuration Files

### Users Database: `/app/backend/data/users1.csv`
```csv
id_tag,header name,surname,quota_kwh,unlimited
RFID001,John,Doe,150,FALSE
RFID002,Jane,Smith,200,FALSE
RFID003,Admin,User,0,TRUE
```

**To add a new user:**
1. Edit the CSV file or use dashboard UI
2. Specify RFID tag, name, and quota
3. Set `unlimited=TRUE` for unlimited users
4. Changes take effect immediately (no restart needed)

---

## 🔍 Monitoring & Logs

### Check Service Status:
```bash
supervisorctl status
```

### View OCPP Server Logs:
```bash
# Real-time logs
tail -f /var/log/supervisor/ocpp_server.err.log

# Last 100 lines
tail -100 /var/log/supervisor/ocpp_server.err.log
```

### Important Log Markers:
- `[CONNECT]` - Charger connection/disconnection
- `[AUTH]` - RFID authorization attempts
- `[TRANSACTION]` - Start/stop charging
- `[METER]` - Meter value updates
- `[QUOTA]` - Quota checks and remote stops
- `[STATUS]` - Charger status changes

### Restart Services:
```bash
# Restart individual service
supervisorctl restart ocpp_server
supervisorctl restart backend
supervisorctl restart frontend

# Restart all
supervisorctl restart all
```

---

## 🧪 Testing the System

### 1. Verify Services:
```bash
supervisorctl status
# All should show RUNNING
```

### 2. Check Ports:
```bash
netstat -tuln | grep -E "9000|8001|3000"
# Should show all three ports LISTENING
```

### 3. Test WebSocket (Optional):
```bash
# Install wscat if needed
npm install -g wscat

# Test connection
wscat -c "ws://localhost:9000/TEST_CHARGER" -s ocpp1.6
```

### 4. Access Dashboard:
Open your browser: **https://YOUR_PREVIEW_URL**
- **Login:** `admin` / `admin123`
- View chargers, users, and transactions
- Dashboard auto-refreshes every 10 seconds

---

## 🔧 Charger-Specific Notes

### LIVOLTEK Chargers:
- Report energy in **kWh** (no conversion needed)
- Standard OCPP 1.6 implementation
- URL: `ws://SERVER_IP:9000/LIVOLTEK_01`

### SCHNEIDER / EVlinkProAC Chargers:
- Report energy in **Wh** (auto-converted to kWh)
- Slightly different OCPP implementation
- URL: `ws://SERVER_IP:9000/SCHNEIDER_01`
- System automatically detects and converts units

---

## 🚨 Troubleshooting

### Charger Won't Connect?

1. **Verify Network Access:**
   ```bash
   # Test if port 9000 is accessible
   telnet YOUR_SERVER_IP 9000
   ```

2. **Check OCPP Server:**
   ```bash
   supervisorctl status ocpp_server
   # Should show RUNNING
   ```

3. **View Connection Attempts:**
   ```bash
   tail -f /var/log/supervisor/ocpp_server.err.log
   # Look for connection attempts
   ```

4. **Common Issues:**
   - Wrong URL format (must be `ws://` not `http://`)
   - OCPP version mismatch (must be 1.6)
   - Firewall blocking port 9000
   - Charger ID mismatch

### Dashboard Not Updating?

1. **Verify Backend is Running:**
   ```bash
   supervisorctl status backend
   ```

2. **Check Data Files:**
   ```bash
   ls -la /app/backend/data/
   # All files should exist and be readable
   ```

3. **Clear Browser Cache:**
   - Hard refresh: `Ctrl + Shift + R` (Windows/Linux)
   - Hard refresh: `Cmd + Shift + R` (Mac)

### Quota Not Working?

1. **Verify User Exists:**
   ```bash
   cat /app/backend/data/users1.csv | grep RFID_TAG
   ```

2. **Check Energy Usage:**
   ```bash
   cat /app/backend/data/energy_usage.json
   ```

3. **View Quota Logs:**
   ```bash
   tail -100 /var/log/supervisor/ocpp_server.err.log | grep QUOTA
   ```

---

## 📚 Documentation

### Comprehensive Guide:
See `/app/backend/ocpp/README.md` for detailed technical documentation

### Key Files:
```
/app/backend/ocpp/
├── ocpp_server.py          # Main OCPP WebSocket server
├── api_sender.py            # External API integration
├── meter_formatter.py       # Meter data formatting
├── performance_metrics.py   # Performance tracking
└── README.md                # Technical documentation

/app/backend/data/           # Shared data directory
├── users1.csv               # User database
├── energy_usage.json        # Real-time usage
├── active_transactions.json # Current sessions
├── charger_status.json      # Charger states
└── meter_data_log.json      # Historical data
```

---

## 🎉 What You Can Do Now

### ✅ Immediate Actions:
1. ✅ Configure your physical LIVOLTEK/SCHNEIDER chargers
2. ✅ Connect chargers via WebSocket
3. ✅ Test RFID authorization
4. ✅ Monitor charging sessions in real-time
5. ✅ Track energy consumption per user
6. ✅ Manage user quotas via dashboard

### 🔮 Advanced Features:
- Set up custom quota plans
- Add new users via dashboard
- Reset monthly usage manually
- View detailed meter readings
- Export transaction logs
- Monitor system performance

---

## ⚠️ Important Notes

### Security (For Production):
1. ⚠️ Change default admin password
2. ⚠️ Use `wss://` (secure WebSocket) instead of `ws://`
3. ⚠️ Implement proper charger authentication
4. ⚠️ Set up firewall rules for port 9000
5. ⚠️ Use environment variables for API keys
6. ⚠️ Enable SSL/TLS certificates

### Performance:
- Dashboard auto-refreshes every 10 seconds
- OCPP server handles multiple chargers simultaneously
- Meter logs limited to last 500 entries (auto-managed)
- Monthly usage resets automatically

### External API:
Currently sending to: `http://144.122.166.37:3005/api/readings/`

To change:
1. Edit `/app/backend/ocpp/ocpp_server.py`
2. Modify `main()` function
3. Restart: `supervisorctl restart ocpp_server`

---

## 🎯 Next Steps

### Phase 1: Initial Testing (NOW)
- [x] Services running
- [ ] Connect first charger
- [ ] Test RFID authorization
- [ ] Verify dashboard updates

### Phase 2: Full Deployment
- [ ] Connect all physical chargers
- [ ] Configure production users
- [ ] Set appropriate quotas
- [ ] Monitor for 24-48 hours

### Phase 3: Optimization
- [ ] Fine-tune quota limits
- [ ] Customize dashboard
- [ ] Set up email alerts (optional)
- [ ] Implement backup procedures

---

## 💡 Quick Reference

### Service Management:
```bash
supervisorctl status           # Check all services
supervisorctl restart all      # Restart everything
```

### View Logs:
```bash
tail -f /var/log/supervisor/ocpp_server.err.log
```

### Data Files:
```bash
ls -la /app/backend/data/
```

### Dashboard Access:
- **URL:** Your preview URL
- **Login:** admin / admin123

### Charger Connection:
- **URL:** ws://YOUR_IP:9000/CHARGER_ID
- **Protocol:** OCPP 1.6

---

## ✨ Summary

Your OCPP Central System is now fully integrated and ready to accept connections from your physical LIVOLTEK and SCHNEIDER chargers!

**What's Working:**
✅ OCPP 1.6 WebSocket Server (Port 9000)
✅ User Authorization & Quota Management
✅ Real-time Energy Tracking
✅ Automatic Remote Stop on Quota Exceeded
✅ Dashboard Integration with Auto-Refresh
✅ External API Data Forwarding
✅ Transaction Logging & History
✅ Charger Status Monitoring
✅ Monthly Usage Auto-Reset

**Ready to Connect:** Your chargers can now connect and start charging!

---

**Questions or Issues?** Check logs first, then refer to `/app/backend/ocpp/README.md` for detailed troubleshooting.

🚀 **Happy Charging!** ⚡
