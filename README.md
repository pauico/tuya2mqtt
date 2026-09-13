# tuya2mqtt: Tuya Devices to MQTT Bridge

`tuya2mqtt` is a Python script that connects Tuya smart devices to an MQTT broker. **It acts as a backend service that maintains a 24-hour TCP connection with registered Tuya devices. This allows it to instantly publish state changes to MQTT and enable device control via MQTT commands.**

-----

## Key Features

  * **Tuya Device Control**: Device state can be set via MQTT.
  * **Status Monitoring**: Real-time status updates (DPS) are received from Tuya devices and published to MQTT.
 
-----

## Important Notes & Recommendations

This script is intentionally streamlined and focused on **robustness**. However, it relies on several external dependencies.

  * **External Module Dependencies**: `tuya2mqtt` relies entirely on the `tinytuya` modules. Unexpected updates to these modules can impact the script's stability, so keeping the module versions stable is recommended.
      * **[tinytuya](https://github.com/jasonacox/tinytuya)**
  * **Network Resources**: As the number of Tuya devices increases, a large number of **TCP connections will be kept alive**. This can put a significant load on a router's resources, so a router with sufficient capacity should be used.
  * **MQTT Broker Environment**: As device connections and communication become more frequent, the MQTT broker may experience increased load. For **maximum performance**, it is recommended to be operated directly on `localhost`.
