#-*- coding: UTF-8 -*-
'''
Test case 2.
-- It is checked that Call trace file is added to Technical Log when some SW Component (e.g. RROM, TUPc, ENBC, BTSOM, HWAPI, CC&S, LOM and TRSW) crashes

####################################################################################################
Requirement :
    1. input parameter can be a zipped file or folder contained syslog log files
    2. zipped file need to extracted to local root folder\extracted_temp_folder (e.g.root_folder\zipped_file_name.zip)
    3. extracted file folder must be deleted when script done
    4. crash detecting keyword is 'calltrace size is' from each syslog log file 
    5. return dict. lenght of list is 0 means pass(no crash keyword deteched). length >0 means failed. 
        
####################################################################################################

Script info:

    Revision: 0.1
    Author: yong.yu@nokia.com
    date: 2016/12/6
    
    main functionality : case2(targetdir_or_zip_filename)
    input:
        @targetdir_or_zip_filename    :    zipped filename or folder contained syslog files
    
    output:
        a dict        :     key is filename find crash, value are lines contained keyword 'calltrace size is'
                            

Usage : 
    targetdir = r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\syslogs_from_different_crashes\syslog_BTSOM_crash_20161206-151123'
    targetdir1 = r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\syslogs_from_different_crashes\syslog_ENBC_crash.zip'
    ab = case2(targetdir)
    for a in ab.keys():
       print a,ab.get(a) 
'''




import zipfile
import time
import os
import re
import shutil

def case2(targetdir_or_zip_filename,txt_result_generate_boolean=False):
    folder_for_syslog = ''
    process_name = ''
    parant_folder_for_zipped_file = ''
    name_without_suffix = ''
    call_trace_re = r'>(.*)calltrace size is:\s*(\d{1,3})\s*entries'
    content_call_trace_re_matched = ''
    num_content_call_trace_re_matched = 0
    temp_tuple = ()
    result_dict = {}
    crash_re = 'calltrace size is'
    if zipfile.is_zipfile(targetdir_or_zip_filename):
        temp_list = targetdir_or_zip_filename.split('\\')
        name_without_suffix = temp_list[-1][:-4]
        del temp_list[-1]
        parant_folder_for_zipped_file = '\\'.join(temp_list)
 
        folder_for_syslog = unzip(targetdir_or_zip_filename,'\\'+name_without_suffix+'_'+time.strftime('%Y%m%d-%H%M%S'))
    else:
        if os.path.isdir(targetdir_or_zip_filename):
            folder_for_syslog = targetdir_or_zip_filename
        else:
            raise Exception,'input parameter %s is NOT a folder'% targetdir_or_zip_filename
    
    if os.path.exists(folder_for_syslog):
        process_name = folder_for_syslog.split('\\')[-1].split('_')[1]
        for root,dir,files in os.walk(folder_for_syslog):
            for file in files:
                result_list = []
                try:
                    fe = open(os.path.join(root,file))
                    num_temp = 0
                    for line in fe:
                        if num_temp !=0 and int(num_content_call_trace_re_matched) != 0 and num_temp > int(num_content_call_trace_re_matched):
                            num_temp = 0
                        if line.find(crash_re)>=0:
                            if process_name in line:
                                result_list.append(line)
                                matched = re.search(call_trace_re, line)
                                if matched:
                                    content_call_trace_re_matched = matched.group(1)
                                    num_content_call_trace_re_matched = matched.group(2)
                                    if len(content_call_trace_re_matched) > 0:
                                        temp_tuple = (matched.group(1),matched.group(2))
                            else:
                                continue
                        elif len(content_call_trace_re_matched) > 0 and num_temp <= int(num_content_call_trace_re_matched):
                                if num_temp == 0 and line.find(str(content_call_trace_re_matched).strip()+r' #'+str(num_temp)+r' ') < 0:
                                    num_temp += 1
                                if line.find(str(content_call_trace_re_matched).strip()+r' #'+str(num_temp)+r' ') >= 0:
                                    result_list.append(line)
                                    num_temp += 1
                                else:
                                    continue
                        else:
                            continue    
                            
                    fe.close()
                except Exception:
                    print 'file open error : '+file
                
                if len(result_list) != 0:
                    result_dict[os.path.join(root,file)] = result_list 
    else:
        raise Exception+'The folder not existed'
    
    if zipfile.is_zipfile(targetdir_or_zip_filename):
        shutil.rmtree(folder_for_syslog) 
    
    if zipfile.is_zipfile(targetdir_or_zip_filename):
        if txt_result_generate_boolean:
            txt_result_generate(parant_folder_for_zipped_file, result_dict,txt_result_name='case2_result'+name_without_suffix+'.txt')  
    else:
        if txt_result_generate_boolean:
            txt_result_generate(folder_for_syslog, result_dict,txt_result_name='case2_result.txt')    
        
    return result_dict
    

def unzip(filename,sub_folder_for_extract_zipped_file):
    folder_name_extract = ''
    try:
        fz = zipfile.ZipFile(filename)
        temp_list = filename.split('\\')
        del temp_list[-1]
        temp_folder = '\\'.join(temp_list)
        folder_name_extract = temp_folder+sub_folder_for_extract_zipped_file
        fz.extractall(folder_name_extract)
        fz.close()
    except Exception:
        print 'filename is not valid'
    
    return folder_name_extract


def txt_result_generate(folder_txt_located,dict_result,txt_result_name='case2_result.txt'):
    output1 = open(folder_txt_located+'\\'+txt_result_name,'w+')
    output1.write('*'*150)
    output1.write('\r\n')
    output1.write('Crash Keyword \'Calltrace size is\' Detected on following files !!!')
    output1.write('\r\n')
    output1.write('\r\n')
    for k in dict_result.keys():
        output1.write(k)
        output1.write('\r\n')
        output1.write('*'*150)
        output1.write('\r\n')
        for line_content in dict_result.get(k):
            output1.write(str(line_content))
            output1.write('\r\n')           
    output1.close()    

        
if __name__ == '__main__':
    targetdir = r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\syslogs_from_different_crashes\syslog_BTSOM_crash'
    targetdir1 = r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\syslogs_from_different_crashes\syslog_BTSOM_crash.zip'
    targetdir2 = r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\syslogs_from_different_crashes\syslog_ENBC_crash.zip'
    targetdir3 = r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\syslogs_from_different_crashes\syslog_RROM_crash.zip'
    targetdir4 = r'H:\BaiduYunDownload\python_tools\logs\syslog_TUPc_crash.zip'
    targetdir5 = r'H:\BaiduYunDownload\python_tools\logs\syslog_RROM_crash'
    ab = case2(targetdir4,True)
    for a in ab.keys():
       print a,ab.get(a) 