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
from collections import defaultdict


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

# Dynamically resolve data folder based on current file location
# ✅ Always point to the same data folder used by OCPP server
DATA_DIR = Path(__file__).resolve().parent / "data"
if not DATA_DIR.exists():
    fallback = Path(__file__).resolve().parents[1] / "backend" / "data"
    if fallback.exists():
        DATA_DIR = fallback
    else:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

print(f"✅ Unified backend DATA_DIR = {DATA_DIR}")



# Define your data file paths
USERS_CSV = DATA_DIR / "users1.csv"
ENERGY_USAGE_JSON = DATA_DIR / "energy_usage.json"
ACTIVE_TRANSACTIONS_JSON = DATA_DIR / "active_transactions.json"
METER_DATA_LOG_JSON = DATA_DIR / "meter_data_log.json"
CHARGER_STATUS_JSON = DATA_DIR / "charger_status.json"

print(f"✅ Data directory: {DATA_DIR}")

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
     # Active transactions — start empty
    if not ACTIVE_TRANSACTIONS_JSON.exists():
        save_json_file(ACTIVE_TRANSACTIONS_JSON, {})
    # Charger status
    # Charger status — start empty (no dummy chargers)
    if not CHARGER_STATUS_JSON.exists():
        save_json_file(CHARGER_STATUS_JSON, {})
    
    
    
    # Meter data logs
    

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
async def get_dashboard_stats():
    """
    Return live dashboard statistics using corrected logic for Schneider & Livoltek chargers.

    - Schneider/EVLINK: cumulative lifetime Wh → convert to kWh & take daily delta (last - first)
    - Livoltek: already sends incremental kWh → also handled as first–last for consistency
    """
    from collections import defaultdict

    # --- Load data files ---
    energy_usage = load_json_file(ENERGY_USAGE_JSON, {})
    active_transactions = load_json_file(ACTIVE_TRANSACTIONS_JSON, {})
    chargers = load_json_file(CHARGER_STATUS_JSON, {})
    users = load_users_csv()
    logs = load_json_file(METER_DATA_LOG_JSON, [])

    today = datetime.now(timezone.utc).date()
    total_energy_today = 0.0
    energy_by_charger = defaultdict(list)

    # --- Step 1: Group today's readings per charger ---
    for rec in logs:
        try:
            ts_str = rec.get("timestamp")
            if not ts_str:
                continue

            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts.date() != today:
                continue  # Only include today's entries

            delivered = float(rec.get("deliveredEnergy", 0))
            charger_name = str(rec.get("chargerName", "UNKNOWN")).upper()

            # Schneider → cumulative Wh → convert to kWh
            if "SCHNEIDER" in charger_name or "EVLINK" in charger_name:
                delivered /= 1000.0  # Wh → kWh

            # Store (timestamp, delivered_kWh)
            energy_by_charger[charger_name].append((ts, delivered))
        except Exception as e:
            print(f"⚠️ Skipping invalid record: {e}")

    # --- Step 2: Compute per-charger daily delta ---
    for charger, readings in energy_by_charger.items():
        readings.sort(key=lambda x: x[0])
        first, last = readings[0][1], readings[-1][1]
        delta = max(0.0, last - first)  # Prevent negative values
        total_energy_today += delta

    # --- Step 3: Aggregate dashboard stats ---
    total_energy_delivered = sum(
        c.get("total_energy_delivered", 0) for c in chargers.values()
    )
    active_chargers = sum(
        1 for c in chargers.values() if c.get("status") == "Charging"
    )

    # --- Step 4: Return unified response ---
    return DashboardStats(
        total_energy_today=round(total_energy_today, 3),
        active_sessions=len(active_transactions),
        total_users=len(users),
        total_chargers=len(chargers),
        active_chargers=active_chargers,
        total_energy_delivered=round(total_energy_delivered, 3),
    )







@app.get("/api/chargers")
async def get_charger_status():
    try:
        if CHARGER_STATUS_JSON.exists():
            with open(CHARGER_STATUS_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)

            chargers_list = []
            for charger_id, charger_data in data.items():
                charger_data["id"] = charger_id
                brand = charger_data.get("brand", "Unknown")
                name_upper = charger_data["name"].upper()
                if brand == "Unknown":
                    if "LIVOLTEK" in name_upper:
                        brand = "LIVOLTEK"
                    elif "SCHNEIDER" in name_upper or "EVLINK" in name_upper:
                        brand = "SCHNEIDER"
                charger_data["brand"] = brand
                chargers_list.append(charger_data)

            # 👇 Return in a structure your frontend expects
            return {"chargers": chargers_list}
        else:
            print("⚠️ Charger status file missing, returning empty list.")
            return {"chargers": []}
    except Exception as e:
        print(f"Error reading charger_status.json: {e}")
        return {"chargers": []}


@app.get("/api/users", response_model=List[UserQuota])
async def get_users():

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
async def get_usage_history(days: int = 7):
    """
    Compute daily total energy (in kWh) for all chargers.
    Works for Schneider (cumulative Wh) and Livoltek (incremental kWh).
    Always returns at least last 7 days, even if some days have 0.
    """
    from collections import defaultdict

    log_path = METER_DATA_LOG_JSON
    history = []
    energy_by_day = defaultdict(float)

    if not log_path.exists():
        return {"history": []}

    # Load all records
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        print("⚠️ Could not parse meter_data_log.json:", e)
        return {"history": []}

    per_day_charger = defaultdict(lambda: defaultdict(list))

    for rec in records:
        try:
            ts_raw = rec.get("timestamp")
            if not ts_raw:
                continue

            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            day = ts.date().isoformat()
            charger = str(rec.get("chargerName", "UNKNOWN")).upper()
            delivered = float(rec.get("deliveredEnergy", 0))

            if "SCHNEIDER" in charger or "EVLINK" in charger:
                delivered /= 1000.0  # Wh → kWh

            per_day_charger[day][charger].append((ts, delivered))
        except Exception as e:
            print("⚠️ Skipping record:", e)

    # Compute daily deltas
    for day, chargers in per_day_charger.items():
        total_day = 0.0
        for charger, readings in chargers.items():
            readings.sort(key=lambda x: x[0])
            if len(readings) >= 2:
                first, last = readings[0][1], readings[-1][1]
                total_day += max(0.0, last - first)
        energy_by_day[day] = total_day

    # Fill last 7 days (even if zero)
    today = datetime.now(timezone.utc).date()
    for i in range(days):
        d = (today - timedelta(days=days - i - 1)).isoformat()
        history.append({"date": d, "energy": round(energy_by_day.get(d, 0.0), 3)})

    print("✅ Computed daily energy history:", history)
    return {"history": history}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)