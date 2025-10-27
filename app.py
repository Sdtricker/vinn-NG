# 🚗 PAYDROID VEHICLE INFO API (FULL VERSION for VERCEL)
# Author: @NGYT777GG | All sections included | Deploys directly (no folder)

import re
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36",
    "Referer": "https://vahanx.in/",
    "Accept-Language": "en-US,en;q=0.9"
}

# ============================================================
# Helper functions
# ============================================================
def clean_dict(d):
    if isinstance(d, dict):
        cleaned = {}
        for k, v in d.items():
            if v and v != "":
                cleaned[k] = clean_dict(v)
        return cleaned
    return d


def extract_card(soup, label):
    for div in soup.select(".hrcd-cardbody"):
        span = div.find("span")
        if span and label.lower() in span.text.lower():
            p = div.find("p")
            return p.get_text(strip=True) if p else None
    return None


def extract_section(soup, header_text, keys):
    section = soup.find("h3", string=lambda s: s and header_text.lower() in s.lower())
    card = section.find_parent("div", class_="hrc-details-card") if section else None
    data = {}
    if card:
        for key in keys:
            span = card.find("span", string=lambda s: s and key in s)
            if span:
                val = span.find_next("p")
                data[key.lower().replace(" ", "_")] = val.get_text(strip=True) if val else None
    return data


def get_value(soup, label):
    span = soup.find("span", string=label)
    if span:
        p = span.find_parent("div").find("p")
        return p.get_text(strip=True) if p else None
    return None


# ============================================================
# Scraper logic
# ============================================================
def get_vehicle_details(rc_number):
    rc = rc_number.strip().upper()
    url = f"https://vahanx.in/rc-search/{rc}"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        return {"error": f"Failed to fetch data: {e}"}

    try:
        registration_number = soup.find("h1").text.strip()
    except:
        registration_number = rc

    # BASIC INFO
    modal_name = extract_card(soup, "Model Name") or get_value(soup, "Model Name")
    owner_name = extract_card(soup, "Owner Name") or get_value(soup, "Owner Name")
    code = extract_card(soup, "Code")
    city = extract_card(soup, "City Name") or get_value(soup, "City Name")
    phone = extract_card(soup, "Phone") or get_value(soup, "Phone")
    website = extract_card(soup, "Website")
    address = extract_card(soup, "Address") or get_value(soup, "Address")

    # OWNERSHIP DETAILS
    ownership = extract_section(soup, "Ownership Details", [
        "Owner Name", "Father's Name", "Owner Serial No", "Registration Number", "Registered RTO"
    ])

    # VEHICLE DETAILS
    vehicle = extract_section(soup, "Vehicle Details", [
        "Model Name", "Maker Model", "Vehicle Class", "Fuel Type", "Fuel Norms",
        "Cubic Capacity", "Seating Capacity", "Chassis Number", "Engine Number"
    ])

    # INSURANCE DETAILS
    insurance_box = soup.select_one(".insurance-alert-box.expired .title")
    expired_days = None
    if insurance_box:
        match = re.search(r"(\d+)", insurance_box.text)
        expired_days = int(match.group(1)) if match else None
    insurance_status = "Expired" if expired_days else "Active"

    insurance = extract_section(soup, "Insurance Information", [
        "Insurance Company", "Insurance No", "Insurance Expiry", "Insurance Upto", "Insurance Type"
    ])

    # VALIDITY DETAILS
    validity = extract_section(soup, "Important Dates", [
        "Registration Date", "Vehicle Age", "Fitness Upto", "Insurance Upto",
        "Insurance Expiry In", "Tax Upto", "Tax Paid Upto"
    ])

    # PUC DETAILS
    puc = extract_section(soup, "PUC Details", ["PUC No", "PUC Upto"])

    # OTHER INFO
    other = extract_section(soup, "Other Information", [
        "Financer Name", "Financier Name", "Permit Type", "Blacklist Status", "NOC Details", "Hypothecation"
    ])

    # COMPILE FULL DATA
    data = {
        "registration_number": registration_number,
        "status": "success",
        "basic_info": {
            "model_name": modal_name,
            "owner_name": owner_name,
            "fathers_name": get_value(soup, "Father's Name") or ownership.get("father's_name"),
            "code": code,
            "city": city,
            "phone": phone,
            "website": website,
            "address": address
        },
        "ownership_details": {
            "owner_name": ownership.get("owner_name") or owner_name,
            "fathers_name": ownership.get("father's_name"),
            "serial_no": ownership.get("owner_serial_no") or get_value(soup, "Owner Serial No"),
            "rto": ownership.get("registered_rto") or get_value(soup, "Registered RTO")
        },
        "vehicle_details": {
            "maker": vehicle.get("model_name") or modal_name,
            "model": vehicle.get("maker_model") or get_value(soup, "Maker Model"),
            "vehicle_class": vehicle.get("vehicle_class") or get_value(soup, "Vehicle Class"),
            "fuel_type": vehicle.get("fuel_type") or get_value(soup, "Fuel Type"),
            "fuel_norms": vehicle.get("fuel_norms") or get_value(soup, "Fuel Norms"),
            "cubic_capacity": vehicle.get("cubic_capacity"),
            "seating_capacity": vehicle.get("seating_capacity"),
            "chassis_number": vehicle.get("chassis_number"),
            "engine_number": vehicle.get("engine_number")
        },
        "insurance": {
            "status": insurance_status,
            "company": insurance.get("insurance_company"),
            "policy_number": insurance.get("insurance_no"),
            "insurance_type": insurance.get("insurance_type"),
            "expiry_date": insurance.get("insurance_expiry"),
            "valid_upto": insurance.get("insurance_upto"),
            "expired_days_ago": expired_days
        },
        "validity": {
            "registration_date": validity.get("registration_date"),
            "vehicle_age": validity.get("vehicle_age"),
            "fitness_upto": validity.get("fitness_upto"),
            "insurance_upto": validity.get("insurance_upto"),
            "insurance_status": validity.get("insurance_expiry_in"),
            "tax_upto": validity.get("tax_upto") or validity.get("tax_paid_upto")
        },
        "puc_details": {
            "puc_number": puc.get("puc_no"),
            "puc_valid_upto": puc.get("puc_upto")
        },
        "other_info": {
            "financer": other.get("financer_name") or other.get("financier_name"),
            "permit_type": other.get("permit_type"),
            "blacklist_status": other.get("blacklist_status"),
            "noc": other.get("noc_details"),
            "hypothecation": other.get("hypothecation")
        }
    }

    return clean_dict(data)


# ============================================================
# ROUTES
# ============================================================
@app.route("/")
def home():
    base = request.host_url.rstrip("/")
    return jsonify({
        "status": "online",
        "api": "Paydroid Vehicle Info Full API 🚗",
        "developer": "@NGYT777GG",
        "version": "5.0",
        "endpoints": {
            "vehicle_info": f"{base}/api/vehicle-info?rc=MH12DE1433",
            "health": f"{base}/health"
        }
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})


@app.route("/api/vehicle-info")
def vehicle_info():
    rc = request.args.get("rc")
    if not rc:
        return jsonify({"error": "Missing rc parameter"}), 400
    data = get_vehicle_details(rc)
    if "error" in data:
        return jsonify(data), 404
    return jsonify(data)


# ============================================================
# Local run (Vercel auto-detects)
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
