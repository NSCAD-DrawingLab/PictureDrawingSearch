# PictureDrawingSearch Param overrides

#########################################
# Runtime Settings
#########################################
collect_demographics = True
run_practice_blocks = True
view_distance = 57 # in centimeters

#########################################
# Available Hardware
#########################################
eye_tracker_available = True
eye_tracking = True
labjack_available = False
labjacking = False

#########################################
# Environment Aesthetic Defaults
#########################################
default_fill_color = (45, 45, 45, 255)
default_color = (255, 255, 255, 255)
default_font_size = 28
default_font_name = 'Frutiger'

#########################################
# EyeLink Settings
#########################################
manual_eyelink_setup = True
manual_eyelink_recording = False

saccadic_velocity_threshold = 20
saccadic_acceleration_threshold = 5000
saccadic_motion_threshold = 0.15

#########################################
# Experiment Structure
#########################################
multi_session_project = False
trials_per_block = 3
blocks_per_experiment = 1
table_defaults = {}

#########################################
# Development Mode Settings
#########################################
dm_auto_threshold = True
dm_trial_show_mouse = True
dm_ignore_local_overrides = False
dm_show_gaze_dot = True

#########################################
# Data Export Settings
#########################################
primary_table = "trials"
unique_identifier = "userhash"
default_participant_fields = [["userhash", "participant"], "sex", "age", "handedness"]
default_participant_fields_sf = [["userhash", "participant"], "random_seed", "sex", "age", "handedness"]

#########################################
# PROJECT-SPECIFIC VARS
#########################################
central_mask_size = 16
peripheral_mask_size = 8