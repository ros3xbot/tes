from app.client.engsel import send_api_request
from app.config.theme_config import get_theme
from app.menus.util import live_loading

def get_segments(
    api_key: str,
    tokens: dict,
    is_enterprise: bool = False,
):
    path = "api/v8/configs/store/segments"
    payload = {
        "is_enterprise": is_enterprise,
        "lang": "en"
    }
    
    res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")
    if res["status"] != "SUCCESS":
        print("Failed to fetch segments.")
        print(f"Error: {res}")
        return None
    
    return res

def segments(api_key: str, id_token: str, access_token: str, balance: int = 0) -> dict | None:
    path = "dashboard/api/v8/segments"
    payload = {
        "access_token": access_token,
        "app_version": "8.9.1",
        "current_balance": balance,
        "family_plan_role": "NO_ROLE",
        "is_enterprise": False,
        "lang": "id",
        "manufacturer_name": "samsung",
        "model_name": "SM-N935F"
    }

    theme = get_theme()
    with live_loading("Mengambil data segmen pengguna...", theme):
        try:
            res = send_api_request(api_key, path, payload, id_token, "POST")
        except Exception as e:
            print(f"❌ Gagal kirim request segments: {e}")
            return None

    if not (isinstance(res, dict) and "data" in res):
        err = res.get("error", "Unknown error") if isinstance(res, dict) else res
        print(f"❌ Error respons segments: {err}")
        return None

    data = res["data"]

    loyalty_data = data.get("loyalty", {}).get("data", {})
    loyalty_info = {
        "current_point": loyalty_data.get("current_point", 0),
        "tier_name": loyalty_data.get("detail_tier", {}).get("name", "")
    }

    notifications = data.get("notification", {}).get("data", [])

    sfy_data = data.get("special_for_you", {}).get("data", {})
    sfy_banners = sfy_data.get("banners", [])
    special_packages = []

    for pkg in sfy_banners:
        try:
            if not pkg.get("action_param"):
                continue

            kuota_total = sum(
                int(benefit.get("total", 0))
                for benefit in pkg.get("benefits", [])
                if benefit.get("data_type") == "DATA"
            )
            kuota_gb = kuota_total / (1024 ** 3)

            original_price = int(pkg.get("original_price", 0))
            discounted_price = int(pkg.get("discounted_price", original_price))
            diskon_percent = int(round((original_price - discounted_price) / original_price * 100)) if original_price else 0

            formatted_pkg = {
                "name": f"{pkg.get('family_name', '')} ({pkg.get('title', '')}) {pkg.get('validity', '')}",
                "kode_paket": pkg.get("action_param", ""),
                "original_price": original_price,
                "diskon_price": discounted_price,
                "diskon_percent": diskon_percent,
                "kuota_gb": kuota_gb
            }
            special_packages.append(formatted_pkg)
        except Exception as e:
            print(f"⚠️ Gagal parse paket SFY: {e}")
            continue

    return {
        "loyalty": loyalty_info,
        "notification": notifications,
        "special_packages": special_packages
    }
