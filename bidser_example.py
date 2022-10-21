import os
import sys
sys.path.insert(1, 'path/to/bids_module/') # Insert the directory where bids_module.py exists

from bids_module import process_subjects

use_nipype = False # if you are able to use nipype, set this to true (for now, don't use nipype)
deface_anatomical = False
auto_detect_progress = True
process_field_maps = True
z_flag = "3" # corresponds to -z flag of dcm2niix. "3" will output 3D NIfTI files., "n" will output to 4D NIfTI files.
input_dir = 'raw_data'
output_dir = 'output'
progress_json_dir = '.'
progress_file_name = output_dir + '_progress' + '.json'

subs = [name for name in os.listdir(input_dir) if os.path.join(os.getcwd(), input_dir,name) and name.find('sub') != -1] # all subject directories
exclude_subjects = [] # exclude subjects from analysis

# if your subject complies to the regular way of you collecting data, which means all sessions are in the same order and exactly same, you use this layout.
# #block type (condition) session name,  task_name, run no, anatomical image to use
runs = {
    'run_type_1': {'MOCOSERIES_0004':('sometask','01','first_anat'),
                    'MOCOSERIES_0006':('sometask','02','first_anat'),
                    'MOCOSERIES_0008':('sometask','03','first_anat'),
                    'MOCOSERIES_0010':('someothertask','01','first_anat'),
                    'MOCOSERIES_0012':('someothertask','02','first_anat')}
}

# map each subject to their specific run type, which is defined above
subject_runs = {
    'sub-01': 'run_type_1',
}

## task settings
task_settings = {'task_names_cond': [],
                'task_names_full': ['sometask','someothertask'],
                'ignore_tasks': []}

process_subjects(subs,auto_detect_progress,process_field_maps,input_dir,output_dir,progress_json_dir,progress_file_name,runs,subject_runs,task_settings,z_flag,use_nipype,deface_anatomical,[],exclude_subjects)