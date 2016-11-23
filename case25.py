#-*- coding: UTF-8 -*-
import os
import os.path
import re
import copy
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
                iii.    RF type  :  <hwtype> checking only



Script information:
    Revision : 0.2
    Date: 2016/11/22
    Author: Dai Taylor & Yu Yong

    Function name:
        case25_S(filename)
            input : a specific file name
            output: a list which lines not matched system log format. output format as below
                output format:
                    [line_num, 'error reason', 'Original Line content']
            example(A line can be contained mutiple errors as following):
                [[1, 'Log Num Format Error:The String length is not 2', '4113-ENBCexe <2016-11-02T08:10:03.352258Z> ThrId-22 message recv ENBC_NetworkConfigReq(0x2332)'],
                 [1, 'HW Type Fomrat Error:There is no seperator - or seperator more than 3 ', '4113-ENBCexe <2016-11-02T08:10:03.352258Z> ThrId-22 message recv ENBC_NetworkConfigReq(0x2332)'],
                 [2, 'Log Num Format Error:The String length is not 2', '4113-ENBCexe <2016-11-02T08:10:03.352258Z> \tlnAdjList[0].mocId = 1']]

        case25_F(foldername)
            input : a folder name contained lots of log files
                    but script only scan *startup*, *runtime* log files under that folder
                    and matched file with different suffix (.zip, .shb, .csv,excel.xlsx, cpidInfo.log) is not checked
                    since there no needs to check. they are not such print like system log.
            output: a dict, key is filename, value is content case25_S(filename). output format as below
                output format:
                    {
                      filename:[[line_num,'error_reason','line_content'],[line_num],'error_reason','line_content']
                    }
            example:
                    {
                     D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\AfterTLDA\AfterTLDA\yuyong\BTS_L1143102326_RMOD_L_1_ram_runtime.log:[[16, 'Log Num Format Error:The log number is 00', "gg FRM_REL3 <1988-01-01T00:00:00.000000Z> 0 INF/CCS/AaConfigTag, AaConfigTagRegisterUnsafe(): 'ccs.service.aasyscom.online', callback addr = 0x22848e20"], [18, 'Log Num Format Error:The log number is 00', "00 FRM_REL3 <2004-01-01T00:00:10.199002Z> 1004A INF/CCS/AaConfigTag, AaConfigTagRegisterUnsafe(): 'ccs.service.aasyscom.online', callback addr = 0x227ef29c"]]
                     D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\AfterTLDA\AfterTLDA\yuyong\BTS_L1143102326_RMOD_L_1_ram_runtime.log.bak:[[18, 'Log Num Format Error:The log number is 00', "00 FRM_REL3 <2004-01-01T00:00:10.199002Z> 1004A INF/CCS/AaConfigTag, AaConfigTagRegisterUnsafe(): 'ccs.service.aasyscom.online', callback addr = 0x227ef29c"]]}
                    }
    Usage:

        #for case25_S()
        error_list = case25_S(filename)
        for error_entry in error_list:
            print error_entry

        #for case25_F()
        error_dict = case25_F(targetdir)
        for k in sorted(error_dict.keys()):
            print k, error_dict.get(k)


"""

file_name_regex = '.*startup.*'
file_name_regex_1 = '.*runtime.*'
file_name_regex_2 = '.*_RMOD_.*'
file_name_regex_3 = '.*routeInfo.*'
file_name_regex_node = '.*_\d{3}._.*'
file_number_regex = '\d.*'
file_context_regex = '.*-.*'
file_context_regex_node_eeName = '^\w{2}.*-\d{3}.*'
file_context_regex_euID_euName = '.*-\w{2}'
file_table = {}
file_table_list = []
file_table_list_1 = []
file_table_list_2 = []
check_list = []
wrong_result_list = []
right_result_list = []
node_id_list = []
euID_list = []
line_num = 0
node = None
cpidInfo_file_list = []
node_id_list = []
table_list = []
table_list_1 = []
table_dict = {}
table_list_final = []
cpidInfo_table = {}
cpidInfo_table_final = {}
cpidInfo_regex = '.*cpidInfo.*'
nodeid_regex = '_\d{3}._'
CPID_regex = '0x.*'
number_regex = '\d'
abc_regex = '\s'
cross_regex = '-*'
euID_list = []
eename_list = []
euname_list = []
def get_re_object(pattern, line):
    reg_item = re.compile(pattern, 0)
    result_item = reg_item.search(line)
    return result_item

def get_cpidInfo_file_list(targetdir, cpidInfo_file_list):
    for root, dirs, files in os.walk(targetdir):
        for file in files:
            if get_re_object(cpidInfo_regex, file):
                cpidInfo_file_list.append(os.path.join(root, file))
    return cpidInfo_file_list

def get_node_id(cpidInfo_file):
    node_id = get_re_object(nodeid_regex, cpidInfo_file).group().strip('_')
    return node_id

def find_cpidInfo_table(targetdir, cpidInfo_file_list):
     cpidInfo_file_list = get_cpidInfo_file_list(targetdir, cpidInfo_file_list)
     for cpidInfo_file in cpidInfo_file_list:
         node_id = get_node_id(cpidInfo_file)
         node_id_list.append(node_id)
         file = open(cpidInfo_file, 'r')
         # print cpidInfo_file
         while True:
             table = file.readline()
             if table:
                 table_list = table.strip('     \n').split(' ')
                 for item in table_list:
                     if item == '':
                         continue
                     else:
                         table_list_1.append(item)
                 if get_re_object(CPID_regex, table_list[0]):
                     if table_list_1:
                         euName = table_list_1.pop()
                     if table_list_1:
                         eeName = table_list_1.pop()
                     if table_list_1:
                         euID = table_list_1.pop()
                     if table_list_1:
                         CPID = table_list_1.pop()
                     table_dict['CPID'] = CPID
                     table_dict['euID'] = euID
                     table_dict['eeName'] = eeName
                     table_dict['euName'] = euName
                     table_list_final.append(copy.deepcopy(table_dict))
                     table_dict.clear()
                 else:
                     while table_list_1:
                         table_list_1.pop()

             else:
                 break
         cpidInfo_table[node_id] = copy.deepcopy(table_list_final)
         while table_list_final:
             table_list_final.pop()
     return cpidInfo_table

def find_euID_node_id_list(cpidInfo_table):
    for item in cpidInfo_table:
        node_id_list.append(item)
        for item_1 in cpidInfo_table[item]:
            euID_list.append(item_1['euID'][2:])
    return euID_list, node_id_list


def get_cpidInfo_dict_and_euid_node_list(targetdir, cpidInfo_file_list):
    tep_list = []
    cpidInfo_table = find_cpidInfo_table(targetdir, cpidInfo_file_list)
    [euID_list, node_id_list] = find_euID_node_id_list(cpidInfo_table)
    tep_list.append(cpidInfo_table)
    tep_list.append([euID_list, node_id_list])
    return tep_list
def finial_check_cpidInfo(line_num, result, check_list, line_1):
    if len(result) == 0:
        #print line_num, 'did not find euID in cpInfo log', line_1, file
        wrong_result_list.append([line_num, 'did not find euID in cpInfo log', line_1])

    else:
        if check_list[3] in result[0]:
            right_result_list.append([line_num, line_1])
        else:
            #print line_num, 'eeName Error: eename of line NOT matched cpid file', line_1, file
            # wrong_result_list.append([line_num, 'eeName Error: eename of line NOT matched cpid file', line_1])
            pass
        if result[1] in check_list[5]:
            right_result_list.append([line_num, line_1])
        else:
            #print line_num, 'euName Error: euname of line NOT matched cpid file', line_1, file
            wrong_result_list.append([line_num, 'euName Error: euname of line NOT matched cpid file', line_1])
    return wrong_result_list

def find_cpidInfo_string(file, cpidInfo_table, euID_list, node_id_list):
    wrong_result_list = []
    if get_re_object(file_name_regex_node, file):
        node = file.split('\\')[-1].split('_')[1]
        if node in node_id_list:
            f = open(file, 'r')
            line_num = 0
            while True:
                line = f.readline()
                line_num += 1
                file_table.update([])
                if line:
                    line_1 = line.strip('\n')
                    line_list_1 = line.split(' ')
                    try:
                        check_list = (line_list_1[1]+'-'+line_list_1[3]).split('-')
                        if check_list[1] != node:
                            #print line_num, 'wrong node_id', line_1, file
                            wrong_result_list.append([line_num, 'wrong node_id', line_1])
                            continue
                        else:
                            result = find_cpidInfo_table_1(check_list[1], check_list[4], cpidInfo_table, euID_list)
                            wrong_result_list = finial_check_cpidInfo(line_num,result, check_list, line_1)
                    except:
                        continue
                else:
                    break
            # print wrong_result_list
        else:
            print 'The log node %s does not have cpidInfo file, so could not be checked' %file
            wrong_result_list = [-1]  ###
    else:
        f = open(file, 'r')
        line_num = 0
        while True:
            line = f.readline()
            line_num += 1
            file_table.update([])
            if line:
                line_1 = line.strip('\n')
                line_list_1 = line.split(' ')
                try:
                    check_list = (line_list_1[1]+'-'+line_list_1[3]).split('-')
                    node = check_list[1]
                    result = find_cpidInfo_table_1(check_list[1], check_list[4], cpidInfo_table, euID_list)
                    wrong_result_list = finial_check_cpidInfo(line_num,result, check_list, line_1)
                except:
                    continue
            else:
                break
    return wrong_result_list

def find_cpidInfo_table_1(node_id, euid, cpidInfo_table, euID_list):
    if euid in euID_list:
        for item in cpidInfo_table[node_id]:
            if item['euID'][2:] == euid:
                #print item['eeName'], item['euName']
                return item['eeName'], item['euName']
    else:
        #print 'not find the euID'
        return []

    # get_cpidInfo_dict_and_euid_node_list(targetdir, cpidInfo_file_list)

    find_cpidInfo_string(filename, dictname, euID_list, node_id_list)
####################################################################################
'''
Above codes made by Taylor
'''
####################################################################################

def case25_F(targetdir):
    file_list_temp = search_folder_for_startup_runingtime_files(targetdir)
    # print file_list_temp
    file_dict_requirement2 = {}
    file_dict_temp = {}
    tep_list = []
    tep_list_1 = []
    tep_list = get_cpidInfo_dict_and_euid_node_list(targetdir, cpidInfo_file_list)
    file_dict_requirement2 = tep_list[0]
    tep_list_1 = tep_list[1]
    euID_list = tep_list_1[0]
    node_id_list = tep_list_1[1]
    #find_cpidInfo_string(file, dictname, euID_list, node_id_list)
    for file_temp in file_list_temp:
        file_dict_temp[file_temp] = case25_S(file_temp,file_dict_requirement2)
    return file_dict_temp


def search_folder_for_startup_runingtime_files(foldername,startup_pattern=r'.*startup.*',runtime_pattern=r'.*runtime.*'):
    excluded_files_list = ['.shb','excel.xlsx','.zip','.csv','cpidInfo.log','gnss_logs_external_runtime','.shb.txt']
    # excluded_files_list = []
    matched_file_list   = []
    is_exclued_boolean  = False

    for root, dirs, files in os.walk(foldername):
        for file in files:
            if re.search(startup_pattern,file) or re.search(runtime_pattern,file):
                is_exclued_boolean = is_excluded(file,excluded_files_list)
                if is_exclued_boolean:
                        continue
                else:
                    matched_file_list.append(os.path.join(root,file))
    return matched_file_list

def case25_S(file, dict_for_search,is_to_display_blank_lines=False):
    file_dict        =        {}
    file_list        =        []
    line_num         =        0
    logFile          =        open(file)
    is_RF_Module_File_Temp = is_RF_Module_file(file)

    # print file
    ###below codes used for get eename from cpid files
    cpid_file_list_temp      = find_cpidInfo_table(targetdir,cpidInfo_file_list)
    eename_list_temp         = get_eename_from_cpid_file_without_duplication_values(cpid_file_list_temp)

    for raw_line in logFile:
        line_num    =        line_num + 1
        line         =        raw_line.strip()
        if line == "":    ###skip the blank line

            if is_to_display_blank_lines:
                file_list.append([line_num, 'Blank line ', raw_line])
            continue

        else:
            splitted_list   = re.split(r'\s',line)
            hwtype_list     = []
            LOG_NUM         = ''
            HW_TYPE         = ''
            TIME_STAMP      = ''
            PID             = ''
            try:
                LOG_NUM         = splitted_list[line_log_offset_definition('lognum')]
                HW_TYPE         = splitted_list[line_log_offset_definition('hwtype')]
                TIME_STAMP      = splitted_list[line_log_offset_definition('timestamp')]
                PID             = splitted_list[line_log_offset_definition('pid')]
            except Exception:
                file_list.append([line_num, 'The Line is NOT matched syslog format',line])
                continue

            if log_number_checking(LOG_NUM) == 1:
                pass
            else:
                print 'hh'
                file_list.append([line_num, log_number_checking(LOG_NUM),line])


            if is_RF_Module_File_Temp:
                if hwtype_checking_for_RMOD(HW_TYPE.strip()) == 1:
                    pass
                else:
                    file_list.append([line_num, hwtype_eename_seperator_checking_for_not_RMOD(HW_TYPE),line])
            else:
                if hwtype_eename_seperator_checking_for_not_RMOD(HW_TYPE.strip()) == 1:
                    pass
                else:
                    file_list.append([line_num, hwtype_eename_seperator_checking_for_not_RMOD(HW_TYPE),line])
                    continue

                if int(HW_TYPE.strip().count("-")) != 1:
                    hwtype_list = HW_TYPE.split('-')


                    if node_id_checking(hwtype_list[1]) == 1:
                        pass
                    else:
                        file_list.append([line_num, node_id_checking(hwtype_list[1]),line])


                    if domain_id_checking(hwtype_list[2]) == 1:
                        pass
                    else:
                        file_list.append([line_num, domain_id_checking(hwtype_list[2]),line])



                    if eename_checking(hwtype_list[3],eename_list_temp) == 1:
                        pass
                    else:
                        file_list.append([line_num,eename_checking(hwtype_list[3],eename_list_temp),line])

                    """
                    EUNAME_checking
                    """
    
    file_list.extend(find_cpidInfo_string(file, dict_for_search, euID_list, node_id_list))


    logFile.close()
    return   sorted(file_list)

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
        'hwtype'    :0,
        'nodeid'    :1,
        'domainid'  :2,
        'eename'    :3
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

def node_id_error_reasons(name):
    node_id_error_reasons_dict = {
        'blankstring'           :'Node ID Format Error:The String is blank',
    }
    return node_id_error_reasons_dict.get(name)

def domain_id_error_reasons(name):
    domain_id_error_reasons_dict = {
        'blankstring'           :'DomainID Format Error:The String is blank',
        'hex'                   :'DomainID Fomrat Error:There is no hex string'
    }
    return domain_id_error_reasons_dict.get(name)

def eename_error_reasons(name):
    eename_error_reasons_dict = {
        'blankstring'           :'eeName Format Error:The String is blank',
        'notmatched'            :'eeName Fomrat Error:eename of line NOT matched cpid file'
    }
    return eename_error_reasons_dict.get(name)

def log_number_checking(hexString):
    if len(hexString) == 2:
        try:
            if hex_to_dec(hexString) > 0:
                return 1
            else:
                return log_print(lognum_error_reasons('zero'))
        except Exception:
            return log_print(lognum_error_reasons('nothexstring'))
    else:
        return log_print(lognum_error_reasons('lengthnotmatched'))

def hwtype_eename_seperator_checking_for_not_RMOD(hwtypeString):
    seperator_string = int(hwtypeString.count("-"))
    splitted_hwtype_list = hwtypeString.split("-")
    if seperator_string == 0 or seperator_string == 2 or seperator_string > 3:
        # print log_print(hwtype_error_reasons('seperator'))
        return log_print(hwtype_error_reasons('seperator'))
    else:
        return  1

def domain_id_checking(domainID):
    if len(domainID) == 0:
        return log_print(domain_id_error_reasons('blankstring'))
    elif hex_to_dec(domainID) > 15 or hex_to_dec(domainID) == -1:
        return log_print(domain_id_error_reasons('hex'))
    else:
        # print hex_to_dec(domainID)
        return 1

def node_id_checking(nodeID):
    if len(nodeID) == 0:
        return log_print(node_id_error_reasons('blankstring'))
    else:
        return 1

def hwtype_checking_for_RMOD(hwtypeString):
    if hwtypeString.strip() == "":
        return log_print(hwtype_error_reasons('blankstring'))
    else:
        return 1

def eename_checking(eename,eename_list_from_cpid_file):
    eename_finding_result = True
    if len(eename) == 0:
        return log_print(eename_error_reasons('blankstring'))

    for content_temp in eename_list_from_cpid_file:
        # print eename_content.find(eename)
        if int(content_temp.find(eename)) >= 0:
            return 1
        else:
            eename_finding_result = False
    # print 'hello'
    if not eename_finding_result:
        return log_print(eename_error_reasons('notmatched'))

def hex_to_dec(hexString):
    dec_value = 0
    try:
        dec_value = int(hexString,16)
    except Exception:
        dec_value = -1
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

def get_eename_from_cpid_file_without_duplication_values(file_dict):
    result_list = []
    result_clear_duplication_list = []
    for k, v in file_dict.items():
        for content in v:
            result_list.append(content.get('eeName'))
    for result_temp in result_list:
        if not result_temp in result_clear_duplication_list:
            result_clear_duplication_list.append(result_temp)
    return result_clear_duplication_list


def is_excluded(filename,excludedlistname):
    result = False
    for i in excludedlistname:
        if i.startswith('.'):
            if filename.endswith(i):
                result = True
        else:
            if filename.find(i) >= 0:
                result = True
    return result



if __name__ == '__main__':
#         print key,abc[key]
    runtimeFilePath=r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\AfterTLDA\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS3244_1011_startup\startup_BTSOM.log'
    runtimeFilePath1=r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\AfterTLDA\AfterTLDA\yuyong\runtime_default.log'
    cpid=r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\AfterTLDA\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS3244_120D_runtime_cpidInfo.log'
    cpid=r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\AfterTLDA\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS3244_120D_runtime_cpidInfo.log'
    # blackboxFilePath=r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\AfterTLDA\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS3244_1011_blackbox'
    # path=r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\Snapshot_MRBTS-3244_FL17_FSM3_9999_161031_033736_eNB2213_20161102-1023\logs\SiteManager.log'
    targetdir=r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\AfterTLDA\AfterTLDA'
    singlefile=r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\AfterTLDA\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS3244_1011_runtime\runtime_BTSOM.log'
#     path=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS3244_1011_blackbox'
    # path=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA\extracted\snapshot.properties'
    # tep_list = get_cpidInfo_dict_and_euid_node_list(targetdir, cpidInfo_file_list)
    # file_dict_requirement2 = tep_list[0]
    # # a = find_cpidInfo_string(singlefile, file_dict_requirement2, euID_list, node_id_list)
    # abc = case25_S(singlefile,file_dict_requirement2,True)
    # for i in abc:
    #     print i
    abcd = case25_F(targetdir)
    for k in sorted(abcd.keys()):
        print '*'*50
        print k
        for i in abcd.get(k):
            print i
    # print len(abcd)
    '''
    for a,b in sorted(abcd.items()):
    # for b in abc:
        # if a.find('BTS3244_1253_runtime.log'):
            print a, abcd.get(a)
    # is_RF_Module_file(blackboxFilePath)
    # print len(abc)
    # print len(abc)
    # for key in sorted(abc.keys()):
        # print key,abc[key]
    # compareTimeStamp(runtimeFilePath, blackboxFilePath)
        # print allStringChecking(abc[key])
        # print dateFormatChecking(abc[key])
    # ab = find_cpidInfo_table(targetdir,cpidInfo_file_list)
    # result = get_eename_from_cpid_file_without_duplication_values(ab,'120D')
    # print result
    '''