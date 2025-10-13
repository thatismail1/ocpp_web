# EV Charging Management System (CMS) Dashboard

A modern, full-featured web dashboard for managing OCPP 1.6 EV charging stations (LIVOLTEK and SCHNEIDER).

## 🚀 Features

### ✅ Implemented Features

1. **Authentication System**
   - JWT-based login
   - Secure token management
   - Auto-redirect on unauthorized access

2. **Dashboard Overview**
   - Real-time key metrics (energy today, active sessions, total users, active chargers)
   - Energy usage trend charts (Recharts)
   - Total lifetime energy delivered
   - Active charging sessions display with user details

3. **Charger Management**
   - View all chargers with status (Charging, Available, Offline)
   - Filter by brand (LIVOLTEK, SCHNEIDER)
   - Display total energy delivered, uptime, and last heartbeat
   - Connection status indicator

4. **User & Quota Management** (Full CRUD)
   - View all users with quota information
   - Add new users with RFID tags
   - Edit user details and quotas
   - Delete users
   - Reset individual user usage
   - Visual progress bars for quota usage
   - Support for unlimited and limited plans

5. **Energy Logs**
   - Real-time meter data readings
   - Search by user, charger, or log ID
   - Filter by charger
   - Display power, energy, and frequency data

6. **Settings**
   - API configuration display
   - Monthly reset schedule information
   - System information
   - Data files documentation

7. **Auto-Polling**
   - Dashboard refreshes every 10 seconds
   - Real-time data updates without manual refresh

## 🔐 Login Credentials

```
Username: admin
Password: admin123
```

## 📁 Project Structure

```
/app/
├── backend/
│   ├── server.py              # FastAPI backend with all REST endpoints
│   ├── requirements.txt       # Python dependencies
│   └── data/                  # Mock data files (JSON/CSV)
│       ├── users1.csv
│       ├── energy_usage.json
│       ├── active_transactions.json
│       ├── meter_data_log.json
│       └── charger_status.json
│
└── frontend/
    ├── src/
    │   ├── App.js             # Main app component
    │   ├── contexts/
    │   │   └── AuthContext.js # Authentication context
    │   ├── pages/             # All page components
    │   │   ├── Login.js
    │   │   ├── Dashboard.js
    │   │   ├── Chargers.js
    │   │   ├── Users.js
    │   │   ├── Logs.js
    │   │   └── Settings.js
    │   ├── components/
    │   │   ├── Layout.js      # Sidebar and layout
    │   │   └── ui/            # Shadcn/ui components
    │   └── utils/
    │       └── api.js         # Axios API configuration
    └── package.json
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - Login with credentials
- `GET /api/auth/verify` - Verify JWT token

### Dashboard
- `GET /api/stats` - Dashboard statistics
- `GET /api/usage/history` - Historical usage data for charts

### Chargers
- `GET /api/chargers` - Get all chargers with status

### Users (Full CRUD)
- `GET /api/users` - Get all users with quota info
- `POST /api/users` - Add new user
- `PUT /api/users/{id_tag}` - Update user
- `DELETE /api/users/{id_tag}` - Delete user
- `POST /api/users/{id_tag}/reset` - Reset user usage

### Transactions & Logs
- `GET /api/transactions` - Get active transactions
- `GET /api/logs` - Get meter data logs (with filtering)

## 🎨 Design Features

- **Modern UI**: Clean, professional design with Space Grotesk font
- **Responsive**: Mobile-friendly layout
- **Dark Theme Ready**: Using Tailwind CSS with dark mode support
- **Shadcn/UI Components**: Beautiful, accessible components
- **Color Scheme**: Emerald/teal gradients for EV charging theme
- **Real-time Updates**: Auto-polling every 10 seconds
- **Toast Notifications**: User feedback for all actions

## 🔧 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **JWT** - JSON Web Token authentication
- **Pydantic** - Data validation
- **Python 3.11**

### Frontend
- **React 19** - Latest React version
- **React Router v7** - Client-side routing
- **Axios** - HTTP client
- **Tailwind CSS** - Utility-first CSS
- **Shadcn/UI** - Component library
- **Recharts** - Charting library
- **Lucide React** - Icon library
- **Sonner** - Toast notifications

## 🚦 Running the Application

The application is already running and accessible at:
https://smart-chargers.preview.emergentagent.com

### Services Status
```bash
# Check services
sudo supervisorctl status

# Restart backend
sudo supervisorctl restart backend

# Restart frontend
sudo supervisorctl restart frontend

# Restart all
sudo supervisorctl restart all
```

### Backend Logs
```bash
# View backend logs
tail -f /var/log/supervisor/backend.*.log

# View frontend logs
tail -f /var/log/supervisor/frontend.*.log
```

## 📊 Mock Data

The system uses mock data stored in `/app/backend/data/`:

- **users1.csv**: 4 demo users with different quota plans
- **energy_usage.json**: Current energy consumption per user
- **active_transactions.json**: 1 active charging session
- **charger_status.json**: 3 chargers (2 LIVOLTEK, 1 SCHNEIDER)
- **meter_data_log.json**: 20 sample meter readings

## 🔄 Integration with Real OCPP Backend

To connect to your actual OCPP CMS backend:

1. **Update API endpoints in backend/server.py** to read from your actual data sources
2. **Modify data loading functions** to connect to your WebSocket server
3. **Update file paths** to point to your actual CSV/JSON files
4. **Configure real-time updates** via WebSocket instead of polling

Example integration points:
```python
# In server.py, replace mock data loading with:
# - WebSocket connection to OCPP server
# - Database queries (if using MongoDB)
# - File watchers for CSV/JSON updates
```

## 🎯 Next Steps

### Recommended Enhancements
1. **Real-time WebSocket Connection** - Replace polling with live updates
2. **Advanced Charts** - Add more detailed analytics and reporting
3. **User Permissions** - Add role-based access control
4. **Export Features** - CSV/PDF export for logs and reports
5. **Email Notifications** - Alert admins when quotas are exceeded
6. **Mobile App** - React Native companion app
7. **Database Migration** - Move from file-based to MongoDB storage
8. **Unit Tests** - Add comprehensive test coverage

## 📝 Notes

- **Auto-polling**: Dashboard updates every 10 seconds automatically
- **JWT Expiry**: Tokens expire after 8 hours
- **Monthly Reset**: Usage counters reset on the 1st of each month (automated)
- **Quota Tracking**: Real-time quota updates during charging sessions
- **Data Persistence**: All changes are saved to JSON/CSV files

## 🐛 Troubleshooting

### Frontend not loading?
```bash
cd /app/frontend
yarn install
sudo supervisorctl restart frontend
```

### Backend API errors?
```bash
cd /app/backend
pip install -r requirements.txt
sudo supervisorctl restart backend
```

### Check data files exist?
```bash
ls -la /app/backend/data/
```

## 📄 License

This dashboard was built for the OCPP 1.6 CMS system managing LIVOLTEK and SCHNEIDER EV chargers.

---

**Built with ❤️ using React + FastAPI + TailwindCSS + Shadcn/UI**
