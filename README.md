# Project Lend

Autonomous food bank for TreeHacks 2026. xArm 1S sorts donated food, Claude agents coordinate donors + shelters.

## Hardware

- Hiwonder xArm 1S (USB) → Nvidia Jetson Orin Nano
- Camera module for vision classification

## Setup (Jetson / Linux)

```bash
# System deps for USB HID
sudo apt install python3-dev libusb-1.0-0-dev libudev-dev

# udev rule so xArm is accessible without root
sudo bash -c 'echo "SUBSYSTEM==\"usb\", ATTR{idVendor}==\"0483\", ATTR{idProduct}==\"5750\", MODE=\"0660\", GROUP=\"plugdev\"" > /etc/udev/rules.d/99-xarm.rules'
sudo udevadm control --reload-rules && sudo udevadm trigger

# Python env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Test xArm

```bash
python3 test_arm.py
```

Should print "Connected!", wiggle servo 2, and return it to its original position.
