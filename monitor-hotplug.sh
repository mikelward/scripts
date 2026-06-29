#!/usr/bin/bash

INTERNAL_PORT="/sys/class/drm/card0/card0-eDP-1"
EXTERNAL_PORTS=("/sys/class/drm/card0/card0-DP-1" "/sys/class/drm/card0/card0-DP-2" "/sys/class/drm/card0/card0-HDMI-A-1")

# Force the kernel to refresh the status of external ports
for port_path in "${EXTERNAL_PORTS[@]}"; do
    if [ -f "$port_path/status" ]; then
        echo "detect" | tee "$port_path/status" > /dev/null 2>&1
    fi
done

# Small delay to give the kernel a moment to process the hardware state change
sleep 0.5

# Check if ALL external monitors are now disconnected
ANY_CONNECTED=false
for port_path in "${EXTERNAL_PORTS[@]}"; do
    if [ -f "$port_path/status" ] && [ "$(cat "$port_path/status")" = "connected" ]; then
        ANY_CONNECTED=true
    fi
done

# If no external displays are found, forcefully wake up the internal display
if [ "$ANY_CONNECTED" = false ]; then
    if [ -f "$INTERNAL_PORT/status" ]; then
        logger -t monitor-hotplug.sh -p user.info "External displays disconnected, turning on internal display"
        # Writing 'on' overrides the compositor's deactivation and forces the link back up
        echo "on" | tee "$INTERNAL_PORT/status" > /dev/null 2>&1
        # Trigger an updated uevent so the Wayland compositor acknowledges the change
        echo "change" | tee "$INTERNAL_PORT/uevent" > /dev/null 2>&1
    fi
fi
