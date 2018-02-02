# PictureDrawingSearch Param overrides

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
default_timeout_message = "Too slow!"

#########################################
# EyeLink Sensitivities
#########################################
view_distance = 57 # in centimeters
saccadic_velocity_threshold = 20
saccadic_acceleration_threshold = 5000
saccadic_motion_threshold = 0.15

#########################################
# Experiment Structure
#########################################
multi_session_project = False
collect_demographics = True
manual_demographics_collection = False
manual_eyelink_setup = True
practicing = False
trials_per_block = 3
trials_per_practice_block = 0
blocks_per_experiment = 1
practice_blocks_per_experiment = 0
trials_per_participant = 0
table_defaults = {}

#########################################
# Development Mode Settings
#########################################
dm_suppress_debug_pane = False
dm_auto_threshold = True
dm_trial_show_mouse = True
dm_ignore_local_overrides = False

#########################################
# Data Export Settings
#########################################
data_columns = None
default_participant_fields = [["userhash", "participant"], "sex", "age", "handedness"]
default_participant_fields_sf = [["userhash", "participant"], "random_seed", "sex", "age", "handedness"]

#########################################
# PROJECT-SPECIFIC VARS
#########################################
central_mask_size = 16
peripheral_mask_size = 8