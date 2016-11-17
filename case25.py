#-*- coding: UTF-8 -*-
import os
import os.path
import re

"""
Case infomation:
    Case 25: BTS Testability_SysLog - Logging
    -- LBT2678, CNI-2746 AaSyslog header format enhancement with eu(thread) name
        https://jira3.int.net.nokia.com/browse/CNI-2746
    -- Steps 4-10 executed
    -- Testing scope:
    ---- Checking that new optional log information (euname) exists and can be enabled / disabled with config tag "ccs.service.aasyslog.euname.printing.enabled" (see DOORS: WBTS_TEST_7891)
    ---- It is also checked that log print format is correct (see DOORS: WBTS_TEST_7891) 
    Above test case requirements parsed as following:
    Input:     
        1.    Case25_S.py : A script input only for a specific file path 
        2.    Case25_F.py : A script input for a folder name so that all type of files(*startup*, *runtime*) under that folder can be scanned and checked
    Output:     
        1.    Case25_S.py : a dict included all not matched line content & line num , key is line number, value is line content not matched checking
        2.    Case25_F.py : a txt file will be generated to record lines not matched for each file under folder.
    Script checking:
        1.    It is need to check config tag  "ccs.service.aasyslog.euname.printing.enabled" , then start script checking
        2.    Euname & euid mapping should be checked according to runtime_cpidInfo.log, if not matched found, just record in returned dict
        3.    All *startup* , *runtime* files under afterTLDA folder should be checked
        4.    Log print format quoted “b6 <hwtype>-<nodeid>[-<domainid>-eename] <2014-01-01T00:00:00.318123Z> PID[-euname] SEVER/FEAT, xxx”
            a)    B6 – log number need to be checked . range must be : hex 1-255, exception 0
            b)    Hwtype – no definition , but can not be blank. (a dict interface can be reserved when more definition provided in the future)
            c)    Nodeid -  length 4, hex string , range must be (0000-ffff)
            d)    Domainid – length 1, hex string, range may be (0-f)
            e)    Eename – same as euname, definition can be found from runtime_cpidInfo.log
            f)    Timestamp checking already covered by case15 or case19, so will not checking
            g)    Pid & euname – same as requirement 2.
            h)    Two kinds of format for RF modules file & FCT files need to be checked
                i.    FCT type:  <hwtype>-<nodeid>-<domainid>-<eename>
                ii.    FCT type separator must be “-“
                iii.    RF type  :  <hwtype> only
Script information:
    Revision : 0.1
    Date: 2016/11/16
"""


def case25_open_file_and_check_if_matched_syslog_format(file,is_to_display_blank_lines=False):
    file_dict        =        {}
    file_list		 =		  []
    line_num         =        0
    logFile          =        open(file)
    for raw_line in logFile:
        line_num    =        line_num + 1
        line         =        raw_line.strip()
        if line == "":    ###skip the blank line
            # print 'blank line: length is %s' % len(raw_line)
            if is_to_display_blank_lines:
                file_list.append([line_num, 'Blank line ', raw_line])
            continue

        else:
            splitted_list   = re.split(r'\s',line)
            LOG_NUM         = splitted_list[line_log_offset_definition('lognum')]
            HW_TYPE         = splitted_list[line_log_offset_definition('hwtype')]
            TIME_STAMP      = splitted_list[line_log_offset_definition('timestamp')]
            PID             = splitted_list[line_log_offset_definition('pid')]
            # file_dict[line_num]=splitted_list
            if log_number_checking(LOG_NUM) == 1:
            	pass
            else:
                file_list.append([line_num, log_number_checking(LOG_NUM),line])

            if is_RF_Module_file(file):
                if hwtype_checking_for_RMOD(HW_TYPE.strip()) == 1:
                    pass
                else:
                    file_list.append([line_num, hwtype_checking_for_RMOD(HW_TYPE),line])
            else:
                if hwtype_checking_for_not_RMOD(HW_TYPE.strip()) == 1:
                    pass
                else:
                    file_list.append([line_num, hwtype_checking_for_not_RMOD(HW_TYPE),line])
                
    logFile.close()
    return   file_list

def line_log_offset_definition(name):
    log_offset_definition_dict   =    {
        'lognum':0,
        'hwtype':1,
        'timestamp':2,
        'pid':3,
        }
    return int(log_offset_definition_dict.get(name))

def hwtype_offset_definition(name):
    hwtype_offset_definition_dict   =   {
        hwtype:0,
        nodeid:1,
        domainid:2,
        eename:3
    }
    return int(hwtype_offset_definition_dict.get(name))

def lognum_error_reasons(name):
    lognum_error_reasons_dict = {
        'nothexstring'          :'Log Num Format Error:The String is NOT hex String',
        'lengthnotmatched'      :'Log Num Format Error:The String length is not 2',
        'zero'                  :'Log Num Format Error:The log number is 00'
    }
    return lognum_error_reasons_dict.get(name)

def hwtype_error_reasons(name):
    hwtype_error_reasons_dict = {
        'blankstring'           :'HW Type Format Error:The String is blank',
        'seperator'             :'HW Type Fomrat Error:There is no seperator - or seperator more than 3 ',
        'nid'                   :'HW Type Format Error:node id is NOT existed',
        'did'                   :'HW Type Format Error:Domain id is NOT existed',
        'eename'                :'HW Type Format Error:EENAME is not matched '
    }
    return hwtype_error_reasons_dict.get(name)

def log_number_checking(hexString):
    if len(hexString) == 2:
        try:
            if hex_to_dec(hexString) >0:
                return 1
            else:
                return log_print(lognum_error_reasons('zero'))
        except Exception:
            return log_print(lognum_error_reasons('nothexstring'))
    else:
        return log_print(lognum_error_reasons('lengthnotmatched'))

def hwtype_checking_for_not_RMOD(hwtypeString):
    seperator_string = hwtypeString.count("-")
    splitted_hwtype_list = hwtypeString.split("-")
    if seperator_string == 0 or seperator_string == 2 or seperator_string > 3:
    	# print log_print(hwtype_error_reasons('seperator'))
        return log_print(hwtype_error_reasons('seperator'))
    elif seperator_string == 1 and len(splitted_hwtype_list) == 2:
        if len(splitted_hwtype_list[0].strip()) != 0 and len(splitted_hwtype_list[1].strip()) != 0:
            return 1
        else:
            return log_print(hwtype_error_reasons('blankstring'))
    else:
        if len(splitted_hwtype_list[2].strip()) == 1 and hex_to_dec(splitted_hwtype_list[2].strip()) > 15 :
            return 1
        elif 
        else:
            return  log_print(hwtype_error_reasons('did'))
        



def hwtype_checking_for_RMOD(hwtypeString):
    if hwtypeString.strip() == "":
        return log_print(hwtype_error_reasons('blankstring'))
    else:
        return 1

def hex_to_dec(hexString):
    dec_value = int(hexString,16)
    return dec_value

def log_print(errorReason):
    return errorReason

def is_RF_Module_file(file):
    file_slice = file.split("\\")
    file_name  = ""
    if file_slice[-1].strip() == "":
        file_name = file_slice[-2]
    else:
        file_name = file_slice[-1]  
    try:        
        match = file_name.index("RMOD")
        if match:
            return True
    except Exception:
        return False

def eename_match(file_dict):
	


if __name__ == '__main__':
#         print key,abc[key]
    # runtimeFilePath=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS_L1143102326_RMOD_L_1_ram_runtime.log'
    runtimeFilePath=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS_L1143102326_RMOD_L_1_ram_runtime.log'
    # blackboxFilePath=r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\AfterTLDA\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS3244_1011_blackbox'
    # path=r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\Snapshot_MRBTS-3244_FL17_FSM3_9999_161031_033736_eNB2213_20161102-1023\logs\SiteManager.log'
    # path=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA\AfterTLDA\merged_dsp_syslogs.log'
#     path=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS3244_1011_blackbox'
    # path=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA\extracted\snapshot.properties'
    abc = case25_open_file_and_check_if_matched_syslog_format(runtimeFilePath)
    # is_RF_Module_file(blackboxFilePath)
    # print len(abc)
    # print len(abc)
    for key in abc:
        print key
    # compareTimeStamp(runtimeFilePath, blackboxFilePath)    
        # print allStringChecking(abc[key])
        # print dateFormatChecking(abc[key])