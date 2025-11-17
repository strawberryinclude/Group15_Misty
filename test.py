from mistyPy.Robot import Robot
from mistyPy.Events import Events
import time

# --------------------------------------
# Setup
# --------------------------------------
# Replace with your robot's IP, or just Robot() if you’re running on-board in Misty Studio.
misty = Robot("192.168.1.237")

misty.change_led(0, 255, 0)              # green = ready
misty.move_head(0, 0, 0)                 # neutral head position
misty.display_image("e_DefaultContent.jpg")

# We'll keep track of the current distance "zone"
current_zone = None   # "far", "medium", "near"

# --------------------------------------
# Helper: decide which zone the user is in
# --------------------------------------
def get_zone(dist_meters):
    """
    Simple thresholds:
      far    : > 1.5 m
      medium : 0.7–1.5 m
      near   : < 0.7 m
    Adjust these after testing with your real Misty.
    """
    if dist_meters is None:
        return None
    if dist_meters > 1.5:
        return "far"
    elif dist_meters > 0.7:
        return "medium"
    else:
        return "near"

# --------------------------------------
# Social behaviors for each distance
# --------------------------------------
def behavior_far():
    """User is far away – attract them, friendly/encouraging."""
    print("Zone: FAR")
    misty.display_image("e_Surprise.jpg")      # or another "curious" face
    misty.change_led(0, 0, 255)                # blue
    misty.speak("Hi there! Come a bit closer so we can work together.", 1)

def behavior_medium():
    """Nice interaction distance – neutral / cooperative."""
    print("Zone: MEDIUM")
    misty.display_image("e_ContentLeft.jpg")   # relaxed/friendly
    misty.change_led(0, 255, 0)                # green
    misty.speak("This is perfect. I can see you well. Let's focus on the task.", 1)

def behavior_near():
    """Very close – more task-focused / slightly authoritative."""
    print("Zone: NEAR")
    misty.display_image("e_Focused.jpg")       # pick a serious/attentive face you like
    misty.change_led(255, 0, 0)                # red
    misty.speak("You are very close. Please concentrate and continue with the task.", 1)

# --------------------------------------
# Time-of-Flight event callback
# --------------------------------------
def tof_callback(data):
    """
    Called whenever Misty’s TOF sensors get a new reading.
    We use only the Center sensor like in the 'Misty OA' example.
    """
    global current_zone

    # Only react to the center sensor
    if data["message"]["sensorPosition"] != "Center":
        return

    dist = data["message"]["distanceInMeters"]
    print("Distance (m):", dist)

    new_zone = get_zone(dist)

    # If zone hasn’t changed, do nothing (avoid spamming behaviors)
    if new_zone is None or new_zone == current_zone:
        return

    current_zone = new_zone

    # Trigger the corresponding behavior
    if new_zone == "far":
        behavior_far()
    elif new_zone == "medium":
        behavior_medium()
    elif new_zone == "near":
        behavior_near()

# --------------------------------------
# Register TOF event + keep script alive
# --------------------------------------
misty.register_event(
    event_name='distance_event',
    event_type=Events.TimeOfFlight,    # same event as in "Misty OA"
    callback_function=tof_callback,
    keep_alive=True,
    debounce=200                       # ms between callbacks
)

misty.keep_alive()
