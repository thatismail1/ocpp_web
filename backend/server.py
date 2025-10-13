from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import jwt
import os
import json
import csv
from pathlib import Path

app = FastAPI(title="OCPP CMS Dashboard API")

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

security = HTTPBearer()

# Data file paths
DATA_DIR = Path("/app/backend/data")
USERS_CSV = DATA_DIR / "users1.csv"
ENERGY_USAGE_JSON = DATA_DIR / "energy_usage.json"
ACTIVE_TRANSACTIONS_JSON = DATA_DIR / "active_transactions.json"
METER_DATA_LOG_JSON = DATA_DIR / "meter_data_log.json"
CHARGER_STATUS_JSON = DATA_DIR / "charger_status.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserQuota(BaseModel):
    id_tag: str
    header_name: str
    surname: str
    full_name: Optional[str] = None
    plan: str  # "limited" or "unlimited"
    quota_kwh: Optional[float] = None
    used_kwh: float = 0
    remaining_kwh: Optional[float] = None
    unlimited: bool = False

class UserCreate(BaseModel):
    id_tag: str
    header_name: str
    surname: str
    plan: str = "limited"
    quota_kwh: Optional[float] = 100.0

class UserUpdate(BaseModel):
    header_name: Optional[str] = None
    surname: Optional[str] = None
    plan: Optional[str] = None
    quota_kwh: Optional[float] = None

class DashboardStats(BaseModel):
    total_energy_today: float
    active_sessions: int
    total_users: int
    total_chargers: int
    active_chargers: int
    total_energy_delivered: float

# Helper functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

def load_json_file(filepath: Path, default=None):
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json_file(filepath: Path, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_users_csv():
    users = []
    if not USERS_CSV.exists():
        return users
    
    with open(USERS_CSV, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(row)
    return users

def save_users_csv(users):
    if not users:
        return
    
    fieldnames = ['id_tag', 'header name', 'surname', 'quota_kwh', 'unlimited']
    with open(USERS_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)

def get_user_quota_info(id_tag: str):
    users = load_users_csv()
    energy_usage = load_json_file(ENERGY_USAGE_JSON, {})
    
    for user in users:
        if user['id_tag'] == id_tag:
            unlimited = user.get('unlimited', 'FALSE').upper() == 'TRUE'
            quota_kwh = None if unlimited else float(user.get('quota_kwh', 0))
            used_kwh = energy_usage.get(id_tag, 0)
            remaining_kwh = None if unlimited else max(0, quota_kwh - used_kwh)
            
            return UserQuota(
                id_tag=id_tag,
                header_name=user.get('header name', ''),
                surname=user.get('surname', ''),
                full_name=f"{user.get('header name', '')} {user.get('surname', '')}",
                plan="unlimited" if unlimited else "limited",
                quota_kwh=quota_kwh,
                used_kwh=used_kwh,
                remaining_kwh=remaining_kwh,
                unlimited=unlimited
            )
    return None

# Initialize mock data
def initialize_mock_data():
    # Create users CSV
    if not USERS_CSV.exists():
        mock_users = [
            {'id_tag': 'RFID001', 'header name': 'John', 'surname': 'Doe', 'quota_kwh': '150', 'unlimited': 'FALSE'},
            {'id_tag': 'RFID002', 'header name': 'Jane', 'surname': 'Smith', 'quota_kwh': '200', 'unlimited': 'FALSE'},
            {'id_tag': 'RFID003', 'header name': 'Admin', 'surname': 'User', 'quota_kwh': '0', 'unlimited': 'TRUE'},
            {'id_tag': 'RFID004', 'header name': 'Bob', 'surname': 'Wilson', 'quota_kwh': '100', 'unlimited': 'FALSE'},
        ]
        save_users_csv(mock_users)
    
    # Energy usage
    if not ENERGY_USAGE_JSON.exists():
        save_json_file(ENERGY_USAGE_JSON, {
            'RFID001': 85.5,
            'RFID002': 120.3,
            'RFID004': 45.2
        })
    
    # Active transactions
    if not ACTIVE_TRANSACTIONS_JSON.exists():
        save_json_file(ACTIVE_TRANSACTIONS_JSON, {
            '1234567890': {
                'id_tag': 'RFID001',
                'start_meter': 85.5,
                'start_time': '2025-01-15T10:30:00Z',
                'last_meter': 88.2,
                'full_name': 'John Doe',
                'charger_id': 'LIVOLTEK_01'
            }
        })
    
    # Charger status
    if not CHARGER_STATUS_JSON.exists():
        save_json_file(CHARGER_STATUS_JSON, {
            'LIVOLTEK_01': {
                'name': 'LIVOLTEK_01',
                'brand': 'LIVOLTEK',
                'status': 'Charging',
                'last_heartbeat': datetime.now(timezone.utc).isoformat(),
                'total_energy_delivered': 1523.5,
                'uptime_hours': 720,
                'connector_id': 1
            },
            'SCHNEIDER_01': {
                'name': 'SCHNEIDER_01',
                'brand': 'SCHNEIDER',
                'status': 'Available',
                'last_heartbeat': datetime.now(timezone.utc).isoformat(),
                'total_energy_delivered': 2145.8,
                'uptime_hours': 680,
                'connector_id': 1
            },
            'LIVOLTEK_02': {
                'name': 'LIVOLTEK_02',
                'brand': 'LIVOLTEK',
                'status': 'Available',
                'last_heartbeat': datetime.now(timezone.utc).isoformat(),
                'total_energy_delivered': 989.2,
                'uptime_hours': 710,
                'connector_id': 1
            }
        })
    
    # Meter data logs
    if not METER_DATA_LOG_JSON.exists():
        logs = []
        for i in range(20):
            logs.append({
                'ID': f'log_{i:03d}',
                'timestamp': (datetime.now(timezone.utc) - timedelta(minutes=i*15)).isoformat(),
                'userName': ['John Doe', 'Jane Smith', 'Bob Wilson'][i % 3],
                'chargerName': ['LIVOLTEK_01', 'SCHNEIDER_01', 'LIVOLTEK_02'][i % 3],
                'totalPower': 7200 + (i * 100),
                'deliveredEnergy': 85.5 + (i * 2.5),
                'frequency': 50.0
            })
        save_json_file(METER_DATA_LOG_JSON, logs)

# Initialize on startup
initialize_mock_data()

# API Endpoints

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "OCPP CMS Dashboard"}

@app.post("/api/auth/login", response_model=Token)
async def login(request: LoginRequest):
    # Simple authentication (demo purposes - use proper auth in production)
    if request.username == "admin" and request.password == "admin123":
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": request.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
    )

@app.get("/api/auth/verify")
async def verify(username: str = Depends(verify_token)):
    return {"username": username, "authenticated": True}

@app.get("/api/stats", response_model=DashboardStats)
async def get_dashboard_stats(username: str = Depends(verify_token)):
    energy_usage = load_json_file(ENERGY_USAGE_JSON, {})
    active_transactions = load_json_file(ACTIVE_TRANSACTIONS_JSON, {})
    chargers = load_json_file(CHARGER_STATUS_JSON, {})
    users = load_users_csv()
    
    # Calculate today's energy (mock - in production would filter by date)
    total_energy_today = sum(energy_usage.values()) * 0.3  # Mock calculation
    
    # Total energy delivered across all chargers
    total_energy_delivered = sum(c.get('total_energy_delivered', 0) for c in chargers.values())
    
    active_chargers = sum(1 for c in chargers.values() if c.get('status') == 'Charging')
    
    return DashboardStats(
        total_energy_today=round(total_energy_today, 2),
        active_sessions=len(active_transactions),
        total_users=len(users),
        total_chargers=len(chargers),
        active_chargers=active_chargers,
        total_energy_delivered=round(total_energy_delivered, 2)
    )

@app.get("/api/chargers")
async def get_chargers(username: str = Depends(verify_token)):
    chargers = load_json_file(CHARGER_STATUS_JSON, {})
    return {"chargers": list(chargers.values())}

@app.get("/api/users", response_model=List[UserQuota])
async def get_users(username: str = Depends(verify_token)):
    users = load_users_csv()
    energy_usage = load_json_file(ENERGY_USAGE_JSON, {})
    
    result = []
    for user in users:
        id_tag = user['id_tag']
        unlimited = user.get('unlimited', 'FALSE').upper() == 'TRUE'
        quota_kwh = None if unlimited else float(user.get('quota_kwh', 0))
        used_kwh = energy_usage.get(id_tag, 0)
        remaining_kwh = None if unlimited else max(0, quota_kwh - used_kwh) if quota_kwh else 0
        
        result.append(UserQuota(
            id_tag=id_tag,
            header_name=user.get('header name', ''),
            surname=user.get('surname', ''),
            full_name=f"{user.get('header name', '')} {user.get('surname', '')}",
            plan="unlimited" if unlimited else "limited",
            quota_kwh=quota_kwh,
            used_kwh=used_kwh,
            remaining_kwh=remaining_kwh,
            unlimited=unlimited
        ))
    
    return result

@app.post("/api/users", response_model=UserQuota)
async def create_user(user: UserCreate, username: str = Depends(verify_token)):
    users = load_users_csv()
    
    # Check if user already exists
    if any(u['id_tag'] == user.id_tag for u in users):
        raise HTTPException(status_code=400, detail="User with this ID tag already exists")
    
    unlimited = user.plan == "unlimited"
    new_user = {
        'id_tag': user.id_tag,
        'header name': user.header_name,
        'surname': user.surname,
        'quota_kwh': '0' if unlimited else str(user.quota_kwh),
        'unlimited': 'TRUE' if unlimited else 'FALSE'
    }
    
    users.append(new_user)
    save_users_csv(users)
    
    return get_user_quota_info(user.id_tag)

@app.put("/api/users/{id_tag}", response_model=UserQuota)
async def update_user(id_tag: str, user_update: UserUpdate, username: str = Depends(verify_token)):
    users = load_users_csv()
    
    user_found = False
    for user in users:
        if user['id_tag'] == id_tag:
            user_found = True
            if user_update.header_name:
                user['header name'] = user_update.header_name
            if user_update.surname:
                user['surname'] = user_update.surname
            if user_update.plan:
                unlimited = user_update.plan == "unlimited"
                user['unlimited'] = 'TRUE' if unlimited else 'FALSE'
                if unlimited:
                    user['quota_kwh'] = '0'
            if user_update.quota_kwh is not None and user_update.plan != "unlimited":
                user['quota_kwh'] = str(user_update.quota_kwh)
            break
    
    if not user_found:
        raise HTTPException(status_code=404, detail="User not found")
    
    save_users_csv(users)
    return get_user_quota_info(id_tag)

@app.delete("/api/users/{id_tag}")
async def delete_user(id_tag: str, username: str = Depends(verify_token)):
    users = load_users_csv()
    
    users = [u for u in users if u['id_tag'] != id_tag]
    save_users_csv(users)
    
    # Also remove from energy usage
    energy_usage = load_json_file(ENERGY_USAGE_JSON, {})
    if id_tag in energy_usage:
        del energy_usage[id_tag]
        save_json_file(ENERGY_USAGE_JSON, energy_usage)
    
    return {"message": "User deleted successfully"}

@app.post("/api/users/{id_tag}/reset")
async def reset_user_usage(id_tag: str, username: str = Depends(verify_token)):
    energy_usage = load_json_file(ENERGY_USAGE_JSON, {})
    
    if id_tag in energy_usage:
        energy_usage[id_tag] = 0
        save_json_file(ENERGY_USAGE_JSON, energy_usage)
    
    return {"message": f"Usage reset for user {id_tag}", "user": get_user_quota_info(id_tag)}

@app.get("/api/transactions")
async def get_transactions(username: str = Depends(verify_token)):
    transactions = load_json_file(ACTIVE_TRANSACTIONS_JSON, {})
    return {"transactions": transactions}

@app.get("/api/logs")
async def get_logs(username: str = Depends(verify_token), charger: Optional[str] = None, limit: int = 50):
    logs = load_json_file(METER_DATA_LOG_JSON, [])
    
    if charger:
        logs = [log for log in logs if log.get('chargerName') == charger]
    
    return {"logs": logs[:limit]}

@app.get("/api/usage/history")
async def get_usage_history(username: str = Depends(verify_token), days: int = 7):
    # Mock historical data for charts
    history = []
    for i in range(days):
        date = datetime.now(timezone.utc) - timedelta(days=days-i-1)
        history.append({
            'date': date.strftime('%Y-%m-%d'),
            'energy': round(50 + (i * 15) + (i % 3 * 10), 2)
        })
    return {"history": history}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)