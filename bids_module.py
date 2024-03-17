"""from nipype.interfaces.dcm2nii import Dcm2niix
from nipype.interfaces import fsl"""
import os
import glob
import time
import json
#import pydicom
import subprocess
import shutil
import math
import copy

field_map_names = {'e1_1.nii': 'magnitude1.nii',
            'e1.json': 'magnitude1.json',
            'e2_1.nii': 'magnitude2.nii',
            'e2.json': 'magnitude2.json',
            'e2_ph_1.nii': 'phasediff.nii',
            'e2_ph.json': 'phasediff.json'}

anat_map = {'first_anat': 0, 
            'second_anat': 1} # anatomical images are mapped to these indexes for simplicity

def log_error(errors,text):
    errors.append(text)

def get_protocol_name(image_path):
    return pydicom.dcmread(image_path).ProtocolName

def get_image_in_dir(directory):
    dicom_list = os.listdir(directory)
    return os.path.join(directory,dicom_list[0])

def add_to_json(json_file,field,value):
    while not os.path.exists(json_file):
        time.sleep(0.00000001)

    line = '{\\\\n\\t' + '\\"' + field + '\\"' + ':\\"' + value + '\\",' 
    with open(json_file, "r+") as f:
        old = f.read()
        f.seek(0) 
        f.write(line + old[1:len(old)])

def write_json(data,output_dir,file_name):
    json_object = json.dumps(data,indent=4)
    outputJson = os.path.join(output_dir,file_name)
    with open(outputJson, "w+") as outfile:
        outfile.write(json_object)

def dicom_to_nifti(inputPath,outputPath,outputFile,singleFile=False,compression_level=1,z_flag='3',use_nipype=False):
    if use_nipype:
        converter = Dcm2niix()
        converter.inputs.source_dir = inputPath
        converter.inputs.output_dir = outputPath
        converter.inputs.out_filename = outputFile
        converter.inputs.single_file = singleFile
        #converter.inputs.compression = compression_level
        converter.inputs.compress = compress
        return converter.run()
    else:
        subprocess.run(["dcm2niix.exe", "-z", z_flag, "-o", outputPath, "-f", outputFile, inputPath])

def deface_image(inputPath):
    subprocess.run(["pydeface", "--outfile", outputPath, "--force", inputPath], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        universal_newlines=True)

def generate_task_jsons(task_settings,output_dir):
    ## generate json for the tasks
    for task_name in task_settings['task_names_full']:
        if task_name not in task_settings['ignore_tasks']:
            json_dict = {
                "RepetitionTime": 2,
                "TaskName": task_name,
                "Manufacturer": "Siemens",
                "ManufacturersModelName": "MAGNETOM Tim Trio",
                "MagneticFieldStrength": 3
            }
            json_object = json.dumps(json_dict, indent = 4)
            task = "task-" + task_name + '_bold.json'
            outputJson = os.path.join(output_dir,task)
            with open(outputJson, "w+") as outfile:
                outfile.write(json_object)

def check_progress(progress,progress_file_name,output_dir,all_sessions,subject_runs,progress_json_dir):

    f = os.path.join(progress_file_name)
    subjects_path = os.path.join(os.getcwd(),output_dir) # where to find subjects?
    
    # load json file, if it does not exist, create a new progress dict.
    if os.path.exists(progress_file_name):
        with open(f, 'r') as f:
            progress = json.load(f)
    elif not os.path.exists(progress_file_name):
        progress = {}

    # Check if new subjects or new sessions are added or not
    for session in all_sessions:
        if session not in progress.keys():
            progress[session] = {}

        for subject in subject_runs[session]:
            if subject not in progress[session].keys():
                progress[session][subject] = 'not_done'

    # check if subjects were processed properly or if there is missing data.
    for session in all_sessions:
        for subject in subject_runs[session]:
            subj_dir = os.path.join(subjects_path,subject,session)
            if os.path.exists(subj_dir):
                if progress[session][subject] == 'not_done':
                    print(subject," - ", session,": Process was interrupted. Participant will be re-processed.")
                    shutil.rmtree(subj_dir)
            else:
                if progress[session][subject] == 'done':
                    print(subject," - ",session,": Processed data not found. Participant will be re-processed.")
                    progress[session][subject] = 'not_done'    

    write_json(progress,progress_json_dir,progress_file_name)
    return progress

def process_subjects(subs,auto_detect_progress,process_field_maps,input_dir,output_dir,progress_json_dir,progress_file_name,runs,subject_runs,task_settings,z_flag="3",use_nipype=False,deface_anatomical=False,subject_blocks={},exclude_subjects=[]):
    
    progress = {}
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for subject in exclude_subjects:
        subs.remove(subject)

    all_sessions = runs.keys()
    if auto_detect_progress:
        progress = check_progress(progress,progress_file_name,output_dir,all_sessions,subject_runs,progress_json_dir)

    errors = []
    for session in all_sessions:
        for subject in subs:           
            if subject in progress[session]:
                if progress[session][subject] == 'done':
                    continue

            print("processing participant:", session, subject)

            ######### check if subject run exists
            if subject not in subject_runs[session]:
                err = subject + " " + session + ": " + "does not have a specific subject run assigned! Check the subject_runs dictionary!"
                log_error(errors,err)
                print(err)
                continue

            subject_run = subject_runs[session][subject]

            if subject_run not in runs[session]:
                err = subject + ": " + "run type " + subject_run + " was not found in the runs dictionary"
                log_error(errors,err)
                print(err)
                continue

            subject_run_type = runs[session][subject_run]
            subject_dir = os.path.join(input_dir, subject, session) # this may change later on
            session_directory = session

            if not os.path.exists(subject_dir):
                message = "Path " + subject_dir + " does not exist for " + subject + " in the input folder."
                raise Exception(message)

            ############ process the T1's
            anatomical_images = [name for name in glob.glob(subject_dir+'/*T1_MPR*')]
            anatomical_image_out = 'anat' # output directory name
            anatomical_outputPath = os.path.join(os.getcwd(),output_dir,subject,session_directory,anatomical_image_out)

            if not os.path.exists(anatomical_outputPath):
                os.makedirs(anatomical_outputPath)

            for anat_image in anatomical_images:
                inputPath = os.path.join(anat_image)
                outputFile = subject + "_" + session_directory + '_run-' + str(anatomical_images.index(anat_image)+1) + "_T1w"
                dicom_to_nifti(inputPath,anatomical_outputPath,outputFile,z_flag=z_flag)
                if deface_anatomical:
                    deface_image(inputPath)

            ##### process field maps
            if process_field_maps:      
                field_maps = [name for name in glob.glob(subject_dir+'/*FIELD*')]
                field_maps = [field_maps[x:x+2] for x in range(0, len(field_maps), 2)]

                fieldmap_out = 'fmap' # output directory name
                fieldmap_outputpath = os.path.join(output_dir,subject,session_directory,fieldmap_out)
                if not os.path.exists(fieldmap_outputpath):
                    os.makedirs(fieldmap_outputpath)

                # convert every fieldmap
                for i in range(len(field_maps)):
                    for f_file in field_maps[i]:
                        inputPath = os.path.join(f_file)
                        outputFile = subject + "_" + session_directory + '_run-' + str(i+1)
                        dicom_to_nifti(inputPath,fieldmap_outputpath,outputFile,z_flag=z_flag)

                for name in field_map_names:
                    globber = '/*' + name + '*'
                    files = [name for name in glob.glob(fieldmap_outputpath+globber)]
                    for file_name in files:
                        change_to = field_map_names[name]
                        new_name = file_name.replace(name,change_to)
                        os.rename(file_name, new_name)

            ##### process functional images
            #functional_images = [name for name in os.listdir(subject_dir) if name.find(select_func) != -1]
            functional_images = list(subject_run_type.keys())
            functional_image_out = "func"
            outputPath = os.path.join(output_dir,subject,session_directory,functional_image_out)

            if not os.path.exists(outputPath):
                os.makedirs(outputPath)

            for func_image in functional_images:
                if func_image in subject_run_type:
                    taskName = subject_run_type[func_image][0]

                    if taskName not in task_settings['ignore_tasks']:
                        run_anat = subject_run_type[func_image][2] # the anatomical image corresponding to this run
                        anat_index = anat_map[run_anat]
                        anat_file = anatomical_images[anat_index]

                        inputPath = os.path.join(subject_dir,func_image)
                        #print(get_protocol_name(get_image_in_dir(inputPath)))
                        
                        if taskName in task_settings['task_names_cond']:
                            block_name = subject_blocks[subject]
                            taskName = taskName + block_name

                        outputFile = subject + "_" + session_directory + "_task-" + taskName + "_run-" + subject_run_type[func_image][1] + "_bold"
                        dicom_to_nifti(inputPath,outputPath,outputFile,z_flag=z_flag)

                        # if the 2nd anatomical image is paired with any functional image
                        if anat_index != 0:
                            err = subject + ": Anatomical image " + anat_file[anat_file.find("T1"):] + " will be used for " + func_image
                            log_error(errors,err)
            
            # if there were functional image folders in the directory which did not exist in the run dictionary, or visa-versa.
            image_diff = set(list(subject_run_type.keys())).symmetric_difference(set(functional_images))
            if len(image_diff) > 0:
                err = subject + ": " + str(image_diff) + " was not paired with a corresponding functional image folder in the directory or in the run dictionary."
                log_error(errors,err)

            if auto_detect_progress:
                progress[session][subject] = 'done'
                write_json(progress,progress_json_dir,progress_file_name)
    
    print("****************** CONVERSION COMPLETED ******************")
    print("**********************************************************")
    print("**********************************************************")
    print("Errors and notes regarding the BIDS conversion process will be printed below.")
    for error in errors:
        print(error)