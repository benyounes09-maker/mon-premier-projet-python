"""
keygen.py — Générateur de clés OptiGest Pro  [OUTIL PRIVÉ]
===========================================================
Lance : python keygen.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hashlib, hmac, datetime

_SECRET = b"0ptiG3st#Qu3id!2025$M@roc"

def generate_key(machine_id: str, expiry: str) -> str:
    mid_clean = machine_id.replace("-", "").upper()
    payload   = f"{mid_clean}:{expiry}".encode()
    digest    = hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()
    if expiry == "permanent":
        prefix = "PERM"
    else:
        d    = datetime.datetime.strptime(expiry, "%Y-%m-%d")
        days = (d - datetime.datetime(2020, 1, 1)).days
        prefix = f"{days:04X}"
    raw = (prefix + digest[:16]).upper()
    return f"{raw[0:5]}-{raw[5:10]}-{raw[10:15]}-{raw[15:20]}"

def main():
    print("=" * 50)
    print("  OptiGest Pro — Générateur de Licences")
    print("=" * 50)

    mid = input("\nMachine ID du client (ex: XXXX-XXXX-XXXX-XXXX) : ").strip()
    if not mid:
        print("Annulé.")
        return

    print("\nDurée :")
    print("  1. 1 mois")
    print("  2. 3 mois")
    print("  3. 6 mois")
    print("  4. 1 an")
    print("  5. 2 ans")
    print("  6. Permanent")
    choix = input("\nChoix [1-6] : ").strip()

    today = datetime.date.today()
    durees = {
        "1": today + datetime.timedelta(days=30),
        "2": today + datetime.timedelta(days=90),
        "3": today + datetime.timedelta(days=180),
        "4": today + datetime.timedelta(days=365),
        "5": today + datetime.timedelta(days=730),
        "6": None,
    }
    if choix not in durees:
        print("Choix invalide.")
        return

    expiry = "permanent" if choix == "6" else durees[choix].strftime("%Y-%m-%d")
    key    = generate_key(mid, expiry)

    print("\n" + "=" * 50)
    print(f"  CLÉ : {key}")
    exp_txt = "Permanente" if expiry == "permanent" else f"Expire le : {expiry}"
    print(f"  {exp_txt}")
    print("=" * 50)

    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys_log.txt")
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}]  MID: {mid}  Expiry: {expiry:<12}  Key: {key}\n")
    print(f"  (Enregistré dans keys_log.txt)")

if __name__ == "__main__":
    main()
