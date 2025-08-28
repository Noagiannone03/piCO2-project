# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

My Pico is an open-source collaborative CO2 sensor network project using Raspberry Pi Pico 2W devices. The project combines hardware (CO2 sensors, OLED displays) with web applications and server infrastructure to create a real-time air quality monitoring network.

## Key Components

### Hardware (MicroPython)
- **Main firmware**: `aircarto_complete.py` - Complete sensor firmware with Firebase integration
- **Display driver**: `ssd1306.py` - OLED display driver for SSD1309 displays
- **Test scripts**: `main_spi.py`, `debug_mhz19c.py` - Hardware testing utilities
- **UI components**: `aircarto_mascot.py` - Display graphics and mascot animations

### Server Infrastructure (Python/Flask)
- **Main server**: `aircarto-server/server.py` - Flask server with InfluxDB integration
- **Fixed server**: `aircarto-server/server_fixed.py` - Alternative server implementation
- **Utilities**: Debug, diagnostic, and data management scripts in `aircarto-server/`
- **Docker setup**: `aircarto-server/docker-compose.yml` - Complete Docker stack with InfluxDB and Nginx

### Web Applications (HTML/CSS/JS)
- **Main site**: `index.html` - Project landing page
- **Dashboard**: `dashboard.html` - User dashboard for sensor management
- **Charts**: `charts.html` - Data visualization interface
- **Configuration**: `config.html`, `setup.html`, `device.html` - Setup and configuration pages

## Development Commands

### Server Development

**Start Docker Stack:**
```bash
cd aircarto-server
docker-compose up -d
```

**Install Python Dependencies:**
```bash
cd aircarto-server
pip install -r requirements.txt
```

**Run Development Server:**
```bash
cd aircarto-server
python server.py
```

**Debug InfluxDB:**
```bash
cd aircarto-server
python diagnose_influxdb.py
```

### Hardware Development (Raspberry Pi Pico)

**Test OLED Display (SPI):**
```bash
# Upload and run main_spi.py on Pico
mpremote cp main_spi.py :
mpremote run main_spi.py
```

**Test CO2 Sensor:**
```bash
# Upload and run debug script
mpremote cp debug_mhz19c.py :
mpremote run debug_mhz19c.py
```

**Deploy Complete Firmware:**
```bash
# Upload all necessary files to Pico
mpremote cp aircarto_complete.py :main.py
mpremote cp aircarto_mascot.py :
mpremote cp ssd1306.py :
```

## Architecture

### Data Flow
1. **Raspberry Pi Pico 2W** → Reads CO2 data from MH-Z19C sensor
2. **Local Display** → Shows data on SSD1309 OLED display  
3. **WiFi Upload** → Sends data to Firebase Realtime Database
4. **Web Dashboard** → Users access data via responsive web interface
5. **Alternative Backend** → InfluxDB server for local/enterprise deployments

### Hardware Connections
- **CO2 Sensor (MH-Z19C)**: UART on GPIO 8/9, 5V power via VBUS
- **OLED Display (SSD1309)**: SPI on GPIO 2,3,1,5,6, 3.3V power
- **WiFi**: Built-in Raspberry Pi Pico 2W connectivity

### Software Architecture
- **Frontend**: Vanilla HTML/CSS/JS with Chart.js and Leaflet.js
- **Backend**: Flask server with InfluxDB for time-series data
- **Firmware**: MicroPython with Firebase REST API integration
- **Deployment**: Docker Compose with Nginx reverse proxy

## Configuration

### Firebase Setup
- Project ID: `my-pico-cf271`
- Firestore for device registration and user management
- Realtime Database for sensor data streaming

### InfluxDB Setup
- Organization: `aircarto`
- Bucket: `co2_data`
- Default token: `aircarto-token-2024`
- API endpoint: `http://localhost:8086`

### Device Configuration
- Device IDs follow pattern: `picoAZ12`, `pico_001`, etc.
- Measurement interval: 60 seconds
- Upload interval: 300 seconds (5 minutes)
- Auto-calibration: 24-hour period for CO2 sensors

## Key File Locations

- **Firmware**: Root directory (`aircarto_complete.py`, `aircarto_mascot.py`, etc.)
- **Server**: `aircarto-server/` directory with all backend code
- **Web UI**: Root directory HTML files
- **Documentation**: `README.md` (comprehensive user guide), `firebase-architecture.md` (technical architecture)
- **Docker**: `aircarto-server/docker-compose.yml` for infrastructure

## Development Notes

- Web applications use modern CSS Grid and Flexbox for responsive design
- Firebase integration supports real-time updates and offline functionality
- InfluxDB provides alternative backend for privacy-conscious deployments
- Hardware supports both auto-calibration and manual calibration modes
- Mascot graphics and animations enhance user experience on OLED display