# GridLink

**See who you hear. Reach the ones you can’t.**

**HF • DIGITAL • CELLULAR**

---




## 🚀 Overview

GridLink is a companion application for amateur radio operators using **VarAC** and **JS8Call**.

It combines RF activity awareness, mapping, and Telegram message transmission into one field-ready tool.

GridLink helps operators:

* 📡 Visualize stations heard over RF
* 🗺️ View JS8Call and VarAC activity on an interactive map
* 📊 Review propagation and station activity
* 📲 Relay short messages from RF → Telegram via gateway stations
* 🔁 Receive Telegram replies back over RF via gateway stations
* 🧭 Access various tools such as Q-code reference, Zulu time reference, grid coordinate conversion, offline callsign lookup, and propagation reports.

GridLink turns radio into a **hybrid HF • digital • cellular communication system** for home, off-grid, and field operations.

---

## ✨ Key Features

### 🗺️ RF Activity Map

* Internet and offline map modes
* JS8Call and VarAC station plotting
* Time-based activity filtering
* Clickable station markers
* Station details with grid, distance, bearing, band, time, and SNR when available

---


### 🗺️ Map Marker Guide

#### Marker Colors

* 🔵 Blue markers = JS8Call activity
* 🔴 Red markers = VarAC activity
* 🟢 Green markers = gateway stations

#### Black Center Dot

Some station markers may display a small black center dot.

This indicates:

* You have heard the station over RF
* There is no confirmed evidence the station hears you

This helps operators quickly distinguish between:
* stations simply heard locally
* stations with confirmed two-way activity

#### Map Interaction

* Double-click markers to open station details
* Use **Center Map** to jump directly to a station
* Feed selections synchronize with map markers
* Time filters affect which markers are displayed

#### Offline Maps

GridLink supports both:

* Internet map mode
* Offline MBTiles-based map mode

Offline maps are useful for:
* field operations
* portable stations
* low-connectivity environments
* emergency communications

---

### 📲 Telegram Relay Messaging

* Send messages from RF → Telegram users via gateway stations running GridLink with internet access.
* Receive Telegram replies for relay back over RF from gateway stations running GridLink.
* Alias-based routing
* No Telegram credentials stored on the GridLink client
* Supports JS8Call and VarAC workflows

---

### 🔁 Gateway Relay Workflow

* A Gateway station is a station with GridLink program installed and running.
* Outgoing Telegram delivery is automatic once the RF message reaches the gateway station.
* When Telegram user replies, the reply is routed back to Gateway station and an alert is placed on dashboard.
* Once alerted, the gateway station then copy/pastes the message for transmission over RF back to originating station.
* Relay is done through either VarAC vmail or JS8Call message.
* Relay will be routed back using the same mode the original message was received with.

---

## 🧱 Architecture

```
RF (VarAC / JS8Call)
   ↓
GridLink Gateway (local)
   ↓
Relay Server (VPS)
   ↓
Telegram Bot
   ↓
Telegram User
```
Return path:

```
Telegram → Relay → Gateway → RF (manual send)
```

## Gateway Dashboard Status Indicators

The Gateway Dashboard displays the current RF and relay status of known GridLink gateway stations.

Status indicators:

- `[D]` = **Detected**
  - The station is internet-connected and currently detected by the GridLink relay system.
  - No recent RF activity has been seen within the activity window.

- `[A]` = **Active**
  - Recent RF activity has been detected within the last activity window, currently approximately 2 hours.
  - Activity may come from:
    - VarAC advanced beacons
    - JS8Call heartbeat / SNR interaction activity

- `[T]` = **Trusted Gateway**
  - Operator-designated trusted gateway station.
  - Trusted gateways are configured locally by the operator.
  - The gateway is trusted, but not currently detected online and not currently active on RF.

Examples:

- `[T]   ` = Trusted gateway not currently detected or active
- `[T][A]` = Trusted gateway with recent RF activity
- `[T][D]` = Trusted gateway detected online but not recently active on RF
- `   [A]` = Active non-trusted gateway
- `   [D]` = Detected non-trusted gateway

The `SRC` column identifies the activity source:
- `VAC` = VarAC activity
- `JS8` = JS8Call activity

---

### 📊 Propagation and Activity Tools

Combines multiple RF data sources:

* VarAC QSO history
* VarAC beacon/heard activity
* JS8Call activity

Provides:

* Callsign activity review
* Band and time observations
* SNR and distance context
* Operator-friendly station details

---

### 📡 JS8Call Integration

* Reads activity from `DIRECTED.TXT`
* Displays JS8 stations in dashboard
* Enhances propagation reports

Useful when QSO logs are limited — provides passive RF insight.

---

### 🔎 Offline Callsign Lookup

* Built-in FCC database (no internet required)
* Displays callsign, name, location, license class
* Grid may be enriched from local RF activity





---

## 🛠️ Requirements

### Linux (Primary)

* Linux Mint / Ubuntu
* Python 3.10+
* VarAC (via Wine)
* VarAC SQLite DB

### Windows

* Planned (packaged version coming)

---

## 📦 Installation (Linux – Simple Method)

---

### 🟢 Step 1 — Download GridLink

* Download the latest release from GitHub
* Extract the ZIP file

After extraction, you will have a folder named:

```
GridLink
```

---

### 🟢 Step 2 — Open Terminal in GridLink Folder

1. Open your file manager
2. Navigate to the **GridLink** folder
3. **Right-click inside the folder**
4. Click **“Open in Terminal”**

---

### 🟢 Step 3 — Run Installer

Paste:

```bash
chmod +x install.sh uninstall.sh
./install.sh
```

---

### 🟢 Step 4 — Launch

* Open system menu
* Type **GridLink**
* Launch the application

---

## ⚠️ First Run

On first launch, the **Station Setup window will open automatically**.

Enter:

* Callsign
* Grid (6-character Maidenhead)
* VarAC database path

Setup will only appear once unless reset.

---

## ⚙️ Setup

### VarAC 

Menu:

```
Setup → Select VarAC Database
```

Typical location:

```
~/.wine/drive_c/VarAC/VarAC.db
~/.wine-vara/drive_c/VarAC/VarAC.db
```

---

### JS8Call 

Menu:

```
Setup → Select JS8Call DIRECTED.TXT
```

Typical location:

```
~/.local/share/JS8Call/DIRECTED.TXT
```

---

## 📲 Telegram Setup

1. Open Telegram App on cell phone.
2. Search for: **@Grid_Link_Bot** in search bar.

   IMPORTANT:
   * The underscores are part of the official bot username.
   * Verify that the bot shows the blue-and-gold GridLink shield icon before pressing START.

3. Send `/start`
4. Choose an alias (Think of alias as a handle for cb radio.  Something to identify you other than username)
5. Alias should be as short as possible and only one word (no spaces in alias).
6. Share your alias with radio operators who will be contacting you via GridLink.

---

## 📡 Sending Telegram Messages over RF

### Using VarAC

1. Find an active gateway station in the Gateway Dashboard
2. Click **Send Telegram**
3. Enter:

   * Gateway callsign
   * Alias of Telegram User you want to contact.
   * Message
4. Copy fields into VarAC vmail and send.
5. Connect to Gateway station.

---

### Using JS8Call

1. Build message in GridLink
2. Format:

```
TG:<ALIAS> <MESSAGE>
```

3. Transmit via JS8Call directed message to Gateway station.

Example:

```
CALLSIGN TG:ALIAS HELLO FROM JS8
```

JS8Call handles segmentation and relay automatically.

---

## 🔁 Receiving Replies

At gateway station:

* Reply button turns **red**
* Open Reply window
* Copy fields into RF message
* Send via VarAC or JS8Call
* Click **Mark Handled**

---


## 🧭 Roadmap for future versions

* Offline Map improvements to include local maps for land navigation.
* The ability use map to post various markers.
* Offline VHF/UHF Repeater reference to find nearest repeaters from your location.
* Windows release

---

## ⚠️ Disclaimer

For amateur radio use only.
Operators must comply with regulations.

---

## 📡 Final Note

GridLink connects **RF networks with modern messaging**.

Use responsibly. Test thoroughly. Improve continuously.
