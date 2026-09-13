import json
import time
import base64
import threading
import tinytuya
import paho.mqtt.client as mqtt

DEVICES_FILE = "devices.json"
PROFILES_DIR = "dp_profiles"
MQTT_HOST = "localhost"
MQTT_PORT = 1883

tinytuya.set_debug(False)  # flip to True for troubleshooting a specific device

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_start()


def load_json(path):
    with open(path) as f:
        return json.load(f)


def decode_raw_field(raw_bytes, field):
    start, length, scale = field["start"], field["length"], field["scale"]
    value = int.from_bytes(raw_bytes[start:start + length], "big")
    return value / scale


def publish(device_name, suffix, value, ts_iso):
    client.publish(f"tuya/{device_name}/{suffix}", value)
    client.publish(f"tuya/{device_name}/{suffix}_ts", ts_iso)


def handle_dp(device_name, dp_id, value, device_ts, profile):
    dp_def = profile["dps"].get(dp_id)
    if not dp_def:
        return  # DP not in profile, ignore silently for MQTT (still visible in console log)

    ts_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(device_ts))
    dp_type = dp_def["type"]
    code = dp_def["code"]

    if dp_type == "value":
        scale = dp_def.get("scale", 1)
        publish(device_name, code, value / scale, ts_iso)

    elif dp_type == "enum":
        publish(device_name, code, value, ts_iso)

    elif dp_type == "raw":
        decoder = profile["decoders"][dp_def["decoder"]]
        raw_bytes = base64.b64decode(value)
        for field in decoder["fields"]:
            decoded = decode_raw_field(raw_bytes, field)
            publish(device_name, field["name"], decoded, ts_iso)

    print(f"[{device_name}] {ts_iso} DP {dp_id} ({code}) -> {value}")


def run_device(dev_cfg):
    name = dev_cfg["name"]
    profile = load_json(f"{PROFILES_DIR}/{dev_cfg['dp_profile']}.json")

    def connect():
        d = tinytuya.OutletDevice(
            dev_cfg["device_id"], 
            dev_cfg["ip"], 
            dev_cfg["local_key"],
            version=dev_cfg["version"], 
            persist=True
        )
        d.status(nowait=True)
        return d

    d = connect()
    last_poll = time.time()
    print(f"[{name}] Connected, listening for pushed updates...")

    while True:
        try:
            data = d.receive()
            if data and "dps" in data:
                device_ts = data.get("t", time.time())
                for dp_id, value in data["dps"].items():
                    handle_dp(name, dp_id, value, device_ts, profile)
            elif not data:
                d.heartbeat()

            if "poll_interval_seconds" in dev_cfg:
                if time.time() - last_poll > dev_cfg["poll_interval_seconds"]:
                    d.status(nowait=True)  # nudge for a fresh push, non-blocking
                    last_poll = time.time()

        except Exception as e:
            print(f"[{name}] Connection error: {e}, reconnecting...")
            time.sleep(2)
            d = connect()
            last_poll = time.time()


def main():
    devices = load_json(DEVICES_FILE)
    threads = []
    for dev_cfg in devices:
        t = threading.Thread(target=run_device, args=(dev_cfg,), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
