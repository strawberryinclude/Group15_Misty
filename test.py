from mistyPy.Robot import Robot
from mistyPy.Events import Events
import time

# --------------------------------------
# SETUP
# --------------------------------------
misty = Robot("192.168.1.237")

# ---- NEUTRAL STATE ----
def go_neutral():
    global current_zone, far_first_time, far_second_prompt_done
    global near_since, asked_for_pat, pat_received, pat_prompt_time, second_pat_prompt_done
    global far_for_neutral_since

    print("Going to NEUTRAL state")
    misty.display_image("e_DefaultContent.jpg")
    misty.change_led(0, 255, 0)          # green idle
    misty.move_head(0, 0, 0)
    misty.move_arm("left", 0, 50)        # arms down
    misty.move_arm("right", 0, 50)

    current_zone = None
    far_first_time = None
    far_second_prompt_done = False

    near_since = None
    asked_for_pat = False
    pat_received = False
    pat_prompt_time = None
    second_pat_prompt_done = False

    far_for_neutral_since = None

# global state
current_zone = None    # "far", "medium", "near"
far_first_time = None
far_second_prompt_done = False

near_since = None
asked_for_pat = False
pat_received = False
pat_prompt_time = None
second_pat_prompt_done = False

far_for_neutral_since = None

go_neutral()  # start neutral

# --------------------------------------
# PLAN: decide distance zone
# --------------------------------------
def get_zone(dist_meters):
    """
    Thresholds:
      far    : > 1.5 m
      medium : 0.7–1.5 m
      near   : < 0.7 m
    Adjust as needed after testing.
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
# ACT: distance behaviours
# --------------------------------------
def behavior_far_first():
    """User is far away – first friendly invitation."""
    print("Zone: FAR (first)")
    misty.display_image("e_Amazement.jpg")    # friendly / attentive
    misty.change_led(0, 0, 255)               # blue
    misty.move_arm("left", 80, 50)            # both arms up-ish
    misty.move_arm("right", 80, 50)
    misty.speak("Come closer!", 1)

def behavior_far_second():
    """User stayed far – second invitation."""
    print("Zone: FAR (second)")
    misty.display_image("e_Admiration.jpg")   # slightly different friendly face
    misty.change_led(0, 0, 255)               # blue
    misty.move_arm("left", 70, 50)            # slightly different pose
    misty.move_arm("right", 70, 50)
    misty.speak("Come on, come closer!", 1)

def behavior_medium():
    """User is a bit closer – invite them to sit."""
    global near_since, asked_for_pat, pat_received, pat_prompt_time, second_pat_prompt_done

    print("Zone: MEDIUM")
    misty.display_image("e_ContentRight.jpg") # warm / inviting
    misty.change_led(255, 255, 0)             # yellow
    # one arm down, one forward
    misty.move_arm("left", 0, 50)             # down
    misty.move_arm("right", 80, 50)           # forward
    misty.speak("Hello friend, have a seat!", 1)

    # reset pat-related state
    near_since = None
    asked_for_pat = False
    pat_received = False
    pat_prompt_time = None
    second_pat_prompt_done = False

def behavior_near():
    """User is closest – thank them for sitting."""
    global near_since, asked_for_pat, pat_received, pat_prompt_time, second_pat_prompt_done

    print("Zone: NEAR")
    misty.display_image("e_Joy2.jpg")         # very friendly / joyful
    misty.change_led(0, 255, 0)               # green
    # both arms forward
    misty.move_arm("left", -90, 50)
    misty.move_arm("right", -90, 50)
    misty.speak("Thank you for sitting down!", 1)

    # start timing for head-pat request
    near_since = time.time()
    asked_for_pat = False
    pat_received = False
    pat_prompt_time = None
    second_pat_prompt_done = False

# --------------------------------------
# ACT: head-pat requests & responses
# --------------------------------------
def ask_for_pat_first():
    global asked_for_pat, pat_prompt_time
    print("Asking for head pat (first time)")
    misty.display_image("e_Admiration.jpg")
    misty.change_led(0, 128, 255)             # soft blue
    misty.move_arm("left", 40, 50)
    misty.move_arm("right", 40, 50)
    misty.speak("If you would like to begin, please give me a gentle pat on my head.", 1)
    asked_for_pat = True
    pat_prompt_time = time.time()

def ask_for_pat_second():
    global second_pat_prompt_done, pat_prompt_time
    print("Asking for head pat (second time)")
    misty.display_image("e_Joy.jpg")
    misty.change_led(255, 192, 203)           # pinkish, extra friendly
    misty.move_arm("left", 50, 50)
    misty.move_arm("right", 50, 50)
    misty.speak("Pretty please, could you pat my head?", 1)
    second_pat_prompt_done = True
    pat_prompt_time = time.time()

def behavior_pat_thank_you():
    global pat_received
    print("Head pat received – thanking user")
    misty.display_image("e_JoyGoofy2.jpg")
    misty.change_led(0, 255, 0)               # bright green, happy
    misty.move_arm("left", -80, 50)
    misty.move_arm("right", -80, 50)
    misty.speak("Thank you for patting my head! Let's begin the tasks.", 1)
    pat_received = True

# --------------------------------------
# SENSE + PLAN + ACT: Time-of-Flight callback
# --------------------------------------
def tof_callback(data):
    """
    SENSE: read distance from center Time-of-Flight sensor.
    PLAN: decide zone & timing.
    ACT: trigger appropriate behavior.
    """
    global current_zone, far_first_time, far_second_prompt_done
    global near_since, asked_for_pat, pat_received, pat_prompt_time, second_pat_prompt_done
    global far_for_neutral_since

    # Only use the center TOF sensor
    if data["message"]["sensorPosition"] != "Center":
        return

    dist = data["message"]["distanceInMeters"]
    now = time.time()
    print("Distance (m):", dist)

    # PLAN: compute new zone
    new_zone = get_zone(dist)
    if new_zone is None:
        return

    # If zone changed → ACT with the corresponding behavior
    if new_zone != current_zone:
        current_zone = new_zone

        if new_zone == "far":
            far_first_time = now
            far_second_prompt_done = False
            far_for_neutral_since = now  # start counting for auto-neutral
            behavior_far_first()

        elif new_zone == "medium":
            far_first_time = None
            far_second_prompt_done = False
            far_for_neutral_since = None
            behavior_medium()

        elif new_zone == "near":
            far_first_time = None
            far_second_prompt_done = False
            far_for_neutral_since = None
            behavior_near()

    # --- extra logic while staying in same zone ---

    # FAR: second prompt + maybe neutral if far for a long time
    if current_zone == "far":
        # second prompt after 5s far
        if far_first_time is not None and not far_second_prompt_done:
            if now - far_first_time > 5:
                behavior_far_second()
                far_second_prompt_done = True
        # auto-neutral after 20s far (no user)
        if far_for_neutral_since is not None and (now - far_for_neutral_since > 20):
            go_neutral()
            return

    # NEAR: ask for head pat over time
    if current_zone == "near" and near_since is not None and not pat_received:
        # first request after 4 seconds near
        if not asked_for_pat and (now - near_since > 4):
            ask_for_pat_first()
        # second, kinder request after 6 seconds more
        elif asked_for_pat and not second_pat_prompt_done and pat_prompt_time is not None:
            if now - pat_prompt_time > 6:
                ask_for_pat_second()

# --------------------------------------
# SENSE: Touch sensors (for head pat)
# --------------------------------------
def touch_callback(data):
    """
    Detect a pat on Misty's head using the TouchSensor event.
    Based on Lesson 4 example: event_type=Events.TouchSensor.
    """
    global current_zone, pat_received

    sensor_pos = data["message"]["sensorPosition"]
    is_contacted = data["message"]["isContacted"]

    # Only react when actually touched and user is close
    if not is_contacted or current_zone != "near" or pat_received:
        return

    # Head sensors that count as "pat"
    head_sensors = ["HeadFront", "HeadBack", "HeadLeft", "HeadRight", "Scruff", "Chin"]

    if sensor_pos in head_sensors:
        behavior_pat_thank_you()

# --------------------------------------
# EVENT REGISTRATION (SENSE loop)
# --------------------------------------
misty.register_event(
    event_name='distance_event',
    event_type=Events.TimeOfFlight,
    callback_function=tof_callback,
    keep_alive=True,
    debounce=200
)

# TouchSensor (from Lesson 4)
misty.register_event(
    event_name='touch_event',
    event_type=Events.TouchSensor,
    callback_function=touch_callback,
    keep_alive=True,
    debounce=250
)

misty.keep_alive()
