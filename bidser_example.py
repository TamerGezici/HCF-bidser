import os
import sys
sys.path.insert(1, r'.') # path to "bids_module.py"
from bids_module import process_subjects

use_nipype = False # if you are able to use nipype, set this to true (for now, don't use nipype)
deface_anatomical = False
auto_detect_progress = True
process_field_maps = True
z_flag = "3" # corresponds to -z flag of dcm2niix. "3" will output 3D NIfTI files., "n" will output to 4D NIfTI files.
input_dir = 'raw'
output_dir = 'bids_ses'
progress_json_dir = '.'
progress_file_name = output_dir + '_progress' + '.json'

subs = [name for name in os.listdir(input_dir) if os.path.join(os.getcwd(), input_dir,name) and name.find('sub') != -1] # all subject directories
exclude_subjects = [] # exclude subjects from analysis

# if your subject complies to the regular way of you collecting data, which means all sessions are in the same order and exactly same, you use this layout.
# #block type (condition) session name,  task_name, run no, anatomical image to use
runs = {
    'ses-preop01':{
        'mike': {'SESSION_1':('ruleswitch','01','first_anat'),
                'SESSION_2':('audnback','01','first_anat')},
    },
    'ses-preop02': {
        'mike': {'TACTILE_1':('tactile','01','first_anat'),
                'AUD_NBACK_1':('audnback','01','first_anat'),
                'AUD_LANGLOC':('audlangloc','01','first_anat')},      
    },
     'ses-preop03': {
        'mike': {'SENTCOMP_1':('sentencecomp','01','first_anat'),
                    'SENTCOMP_2':('sentencecomp','02','first_anat')},      
    },
    'ses-postop01': {
        'mike': {'RULESWITCH_1_0007':('ruleswitch','01','first_anat'),
                  'RULESWITCH_2_0011':('sentencecomp','02','first_anat')},
    },
    'ses-postop02': {
            'mike': {'V1_LOCALIZER':('visuallocalizer','01','first_anat'),
                'MEMLOC1':('memorylocalizer','01','first_anat'),
                'MEMLOC2':('memorylocalizer','02','first_anat')},   
    }
}

# map each subject to their specific run type, which is defined above
subject_runs = {
    'ses-preop01': {
        'sub-01': 'mike',
    },
    'ses-preop02': {
        'sub-01' : 'mike',
    },
    'ses-preop03': {
        'sub-01' : 'mike',
    },
    'ses-postop01': {
        'sub-01' : 'mike',
    },
    'ses-postop02': {
        'sub-01' : 'mike',
    },
}

subject_blocks = {}

## task settings
task_settings = {'task_names_cond': [],
                'task_names_full': [],
                'ignore_tasks': []}

process_subjects(subs,auto_detect_progress,process_field_maps,input_dir,output_dir,progress_json_dir,progress_file_name,runs,subject_runs,task_settings,z_flag,use_nipype,deface_anatomical,subject_blocks,exclude_subjects)