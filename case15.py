#-*- coding: UTF-8 -*-
import os
import re
import datetime
from _bsddb import DB_LOCK_OLDEST


"""
Case 15: BTS Testability_Local time delivery to radio modules
-- LBT2338
    * It is checked that uniform time is used in RMOD_*_*_runtime.log
    * Used time in RMOD_*_*_runtime.log is reasonable compared to newest reset time stamp in *_1011_blackbox file.
    
the requirements of script need to done as following:
        1.  to check if there is a "T" letter between date and time
        2.  to check if there is a "Z" letter at the end of timestamp.
        3.  for date field, need to check if use "-" to differentiate year & month & day
        4.  for date field, need to check year value range should be: 1980-2050, month range should be: 1-12, day range should be : 1-31
        5.  for time field, need to check if use ":" to differentiate hour & minute & seconds
        6.  for time field, need to check hour value range should be : 0-23, minute range should be : 0-59, seconds range should be: 0-59
        7.  each line of RMOD_*_*_runtime.log need to check timestamp
        8.  only check RMOD_*_*_runtime.log first timestamp (began with 2016) is later *_1011_blackbox 鈥榮 latest timestamp ?
    
"""


"""
The script is debugged with Python2.7

Author    : yong.yu@nokia.com
date     : 2016/11/15

Revision: 0.4
    1. enhancement for compareTimeStamp()
        input changed to AfterTLDA folder, will automatically scan all files under that folder to search source: *_RMOD_*_*_ram_runtime.log
        and dest:1011_blackbox and get result 
    2. modify time_difference expression to time_difference>0
    
Revision: 0.3
    1. revision 0.3 covered above requirement 8 by function compareTimeStamp()

    
Revision: 0.2 
    1. year range changed to : 1980-2050
    2. timestamp re changed for adapting two kinds of files with different timestamp location
    3. script can display/output blank lines or lines without timestamp by new added parameters
    4. indicate if a file contain vaild lines with timestamp.
    5. revision 0.2 covered above requirements 1-7 by function open_file_and_get_incorrect_timestamp()

Usage: 
    :param    file                                     :    is the file need to check timestamp
            is_to_display_blank_lines                :    if to output "blank lines" to returned dict, default value is False
            is_to_display_lines_without_timestamp    :    if to output "lines without timestamp" to returned dict. default value is False
            is_to_display_correct_timestamp            :    if to only output "lines with correct timestamp" to returned dict.
            is_to_indicate_file_contain_timestamp   :    if indicate a file contain valid timestamp. defautl value is False.
                                                            if true, there is no valid timestamp when script check all lines of a file 
                                                            returned dict will be overwriteted by a line
                                                            -1 ['The file DO NOT include any lines with timestamp', '']
                                                            the key of dict only will be '-1' to means the file no valide timestamp
    :return dict:            return a dict. if length of dict is blank, means no line found for incorrect timestamp, case passed. 
                            if length of dict more than 0, means there existed lines with incorrected timestamp.
                            return value example as following:
                            {50793 ['There is no timestamp existed in line ', 'Is NTP Time: true']}
                            key    : Here 50793 means line number,
                            value  : a list with length=2
                                     list[0] is 'error reason'
                                     list[1] is 'timestamp'     when line existed a invalid timestamp
                                                ''                 when line is blank if is_to_display_blank_lines=True
                                                'line content'     when line have some strings but no timestamp if is_to_display_lines_without_timestamp=True
    :how to call:            just call open_file_and_get_incorrect_timestamp() is ok

Note:
    1. about re of get timestamp: '.?\d{4}-\d{2}-\d{2}.?\d{2}:\d{2}:\d{2}.?\d{2,6}.{2}'
       is tested can get two kind of timestamp from snapshot as following:
        a). BTS_L1143102326_RMOD_L_1_ram_runtime.log
            62 FRM_REL3 <2016-11-02T08:10:16.527998Z> 100C3 INF/LTX/MED_Generic, Sent automatic notification parValueChangeInd
            63 FRM_REL3 <2016-11-02T08:10:16.547997Z> 100C3 INF/LTX/MED_Generic, NotificationsCreator automatic notification header: to LBTS_OM_L9123000298, from /RMOD_L_1/RU_L_1, id 121, action OBSAI_CM, version 2.0, relatesTo 

        b). SiteManager.log
            2016-11-02T07:13:30.406Z [main] [com.nokia.em.poseidon.plugin.lifecycle.LifecycleManager] [DEBUG] Current Poseidon Lifecycle status set: NOT_STARTED

            2016-11-02T07:13:30.416Z [main] [com.nokia.em.poseidon.frameworks.i18n.I18nConfigurator] [DEBUG] Loading configuration file: /com/nokia/em/poseidon/config/poseidon_i18n.xml

            2016-11-02T07:13:30.416Z [main] [com.nokia.em.poseidon.frameworks.i18n.I18nConfigurator] [DEBUG] Loading configuration file: /com/nokia/em/sitemgr/config/sitemgr_i18n.xml
Examples:
    examples_input:
        path=r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\AfterTLDA\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS_L1143102326_RMOD_L_1_ram_runtime.log'
        abc = open_file_and_get_incorrect_timestamp(path)
        print len(abc)
        for key in sorted(abc.keys()):
            print key,abc[key]

    examples_output:
    9 1988-01-01T00:00:00.000000Z
    10 1988-01-01T00:00:00.000000Z
    11 1988-01-01T00:00:00.000000Z
    12 1988-01-01T00:00:00.000000Z
    21550 2016-11-02T08:24:23.091997
    21551 2056-11-02T08:24:23.383997Z
    21553 2016-11-0208:24:23.387998Z
"""

def open_file_and_get_incorrect_timestamp(file,is_to_display_blank_lines=False,is_to_display_lines_without_timestamp=False,is_to_display_correct_timestamp=False,is_to_indicate_file_contain_timestamp=False):
    file_dict        =        {}
    timestamp_re    =        '.?\d{4}-\d{2}-\d{2}.?\d{2}:\d{2}:\d{2}.?\d{1,6}.{2}'
    line_num        =        0
    file_list       =       []

    logFile            =        open(file)
    numTimeStamp    =        0
    for raw_line in logFile:
        line_num    =        line_num + 1
        line         =        raw_line.strip()
        if line == "":    ###skip the blank line
            # print 'blank line: length is %s' % len(raw_line)
            if is_to_display_blank_lines:
                file_dict[line_num]=['Blank line ', raw_line]
            continue
        else:
            match                =        re.search(timestamp_re,line)
            if match:
                # print 'matched group is %s' % match.group()
                numTimeStamp     =    numTimeStamp + 1
                matched_result    =    ""
                if ('>' in match.group()):
                    matched_result    =    match.group()[1:-1]
                else:
                    matched_result    =    match.group().strip()
                file_dict.update(timeStampAllChecking(matched_result,line_num,is_to_display_correct_timestamp))
            else:
                # print ('Line : %s There is no timestamp   %s' % (line_num,line))
                if is_to_display_lines_without_timestamp:
                    file_dict[line_num]=['There is no timestamp existed in line ', line]
            # print line
    logFile.close()
    if numTimeStamp == 0 and is_to_indicate_file_contain_timestamp:
        file_dict   =  {-1:['The file DO NOT include any lines with timestamp','']}
    return   file_dict

def timeStampAllChecking(timestamp_line,line_num,isDisplayCorrectTime):
    file_dict          = {}
    correct_timestamp  = True
    if allStringChecking(timestamp_line):
        correct_timestamp  = True
    else:
        # file_list.append(match.group())
        correct_timestamp  = False
        if not correct_timestamp:
            file_dict[line_num]=['Failed to check string \'T\' \'Z\' and \'-\' \':\' of timestamp',timestamp_line]
            print 'Failed to check string \'T\' \'Z\' and \'-\' \':\' of timestamp on line : %s' % line_num

    if dateFormatChecking(timestamp_line):
        correct_timestamp  = True
    else:
        correct_timestamp  = False
        if not correct_timestamp:
            file_dict[line_num]=['Failed to check date format of timestamp',timestamp_line]
            print 'Failed to check date format of timestamp on line : %s' % line_num

    if timeFormatChecking(timestamp_line):
        correct_timestamp  = True
    else:
        correct_timestamp  = False
        if not correct_timestamp:
            file_dict[line_num]=['Failed to check time format of timestamp',timestamp_line]
            print 'Failed to check time format of timestamp on line : %s' % line_num
    
    if isDisplayCorrectTime and correct_timestamp:
        file_dict[line_num]=['Timestamp is OK',timestamp_line]

    return file_dict

def stringChecking(timestamp_line,string_to_be_checked,string_offset):
    getString        =    ""
    try:
        getString         =    timestamp_line[string_offset]
    except IndexError,e:
        return False
    if getString.strip() == string_to_be_checked:
        return True
    else:
        return False

def allStringChecking(timestamp_line):
    result            =    True
    if stringChecking(timestamp_line,'T',10) and stringChecking(timestamp_line,'Z',-1) \
        and stringChecking(timestamp_line,'-',4) and stringChecking(timestamp_line,'-',7) \
        and stringChecking(timestamp_line,':',13) and stringChecking(timestamp_line,':',16):
        result = True
    else:
        result = False
    return result


def valueRangeChecking(num_to_be_checked, minimum,maximum):
    if int(num_to_be_checked) >= int(minimum) and int(num_to_be_checked) <= int(maximum):
        result = True
    else:
        result = False
    return result

def dateFormatChecking(timestamp_line):
    result            = True
    date_re         = '\d\d\d\d-\d\d-\d\d'
    date             = re.search(date_re,timestamp_line)
    # print 'date.group is %s' % date.group()
    year,month,day  = date.group().split('-')
    # print year,month,day
    if valueRangeChecking(year.strip(),1980,2050) and valueRangeChecking(month.strip(),1,12) and valueRangeChecking(day.strip(),1,31):
        result=True
    else:
        result=False
    return result


def timeFormatChecking(timestamp_line):
    result            = True
    time_re         = '\d\d:\d\d:\d\d'
    time                     = re.search(time_re,timestamp_line)
    hour,minute,second        = time.group().split(":")
    if valueRangeChecking(hour,0,23) and valueRangeChecking(minute,0,59) and valueRangeChecking(second,0,59):
        result=True
    else:
        result=False
    return result


"""
how to use:
    path=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA'
    compareTimeStamp(path)

    ###if you need to change re to match other file, just do as following:
    compareTimeStamp(path, souc=r'xxx', dest=r'xxxx')

return value:
    True   :    Passed! means runtimelog timestamp is after blackboxfilelog
    False  :    Failed! means runtimelog timestamp is not after blackboxfile
"""

def compareTimeStamp(afterTLDAFolder,sour=r'.*_RMOD_.*_.*_ram_runtime.log',dest=r'.*1011_blackbox$'):
#     sour=r'.*_RMOD_.*_.*_ram_runtime.log'
#     dest=r'.*1011_blackbox$'
    source_file_list      = scanFolderAndGetSpecificFileLocation(afterTLDAFolder, sour)
    destination_file_list = scanFolderAndGetSpecificFileLocation(afterTLDAFolder, dest)
    result = True

    if len(destination_file_list) == 0:
        print 'Warning: There is no 1011_blackbox file found'
        raise Exception
    elif len(destination_file_list) > 1:
        print 'Warning: There are more than 1 file named: 1011_blackbox'
        raise Exception
    else:
        pass

    if len(source_file_list) == 0:
        print 'Warning: There is no matched ram_runtime.log file found'
        raise Exception

    for runtimelog_file in source_file_list:
        if doCompareTimeStamp(runtimelog_file,destination_file_list[0]):
            result = True
        else:
            result = False
            if not result:
                return False
                raise Exception

def doCompareTimeStamp(runtimeFilePath,blackboxFilePath):
    source_dict                         =   {}
    target_dict                         =   {}
    runtime_first_timestamp             =   ""
    runtime_first_timestamp_line_num    =   0
    blackbox_latest_timestamp           =   ""
    temp                                =   []
    source_dict                         =   open_file_and_get_incorrect_timestamp(runtimeFilePath, False, False, True, False)
    target_dict                         =   open_file_and_get_incorrect_timestamp(blackboxFilePath, False, False, True, False)
    
    #below for loop to get key of dict(the maximum value of key means last timestamp from blackbox file
#     print target_dict
    for key in sorted(target_dict.keys()):
        temp.append(key)
    blackbox_latest_timestamp           = target_dict[temp[-1]][1]    #the last element of temp list as key(maximum) of target_dict
    blackbox_latest_timestamp_line_num  = temp[-1]
    
    #below for loop is to find which line used the timestamp from blackbox
    for key in sorted(source_dict.keys()):
#         print key, source_dict[key]
        if source_dict[key][1][:4] == blackbox_latest_timestamp[:4]:
            runtime_first_timestamp = source_dict[key][1]
            runtime_first_timestamp_line_num = key
            break
    
#     print runtime_first_timestamp
#     print blackbox_latest_timestamp
#     
    runtime_first_timestamp_converted = returnTimeSeconds(runtime_first_timestamp[:-1])
    blackbox_latest_timestamp_converted = returnTimeSeconds(blackbox_latest_timestamp[:-1])
    
    time_difference = (runtime_first_timestamp_converted - blackbox_latest_timestamp_converted).total_seconds()
    
    if time_difference > 0:
        print 'Passed!'
        print '%s on line %d   from file %s'%  (str(blackbox_latest_timestamp_converted),blackbox_latest_timestamp_line_num,blackboxFilePath)
        print '%s on line %d   from file %s'%  (str(runtime_first_timestamp_converted),runtime_first_timestamp_line_num,runtimeFilePath)
        print 'time difference is %s seconds'% str(time_difference)
        return True
    else:
        print 'Failed!'
        print '%s on line %d   from file %s'%  (str(blackbox_latest_timestamp_converted),blackbox_latest_timestamp_line_num,blackboxFilePath)
        print '%s on line %d   from file %s'%  (str(runtime_first_timestamp_converted),runtime_first_timestamp_line_num,runtimeFilePath)
        print 'time difference is %s seconds'% str(time_difference)
        return False
#     print runtime_first_timestamp_converted
#     print blackbox_latest_timestamp_converted

def scanFolderAndGetSpecificFileLocation(path,pattern):
    result_list = []
    for root,dirs,files in os.walk(path):
        find_file   =   re.compile(pattern)
        for f in files:
            matchresult = find_file.search(f)
            if matchresult:
                result_list.append(os.path.join(root,f))
                # print matchresult.group()
                # print result_list
    return result_list

def msExtend2SixDigitalNum(ms):
    length        =    len(str(ms))
    switch_dict   =    {
        1:100000,
        2:10000,
        3:1000,
        4:100,
        5:10,
        6:1
        }
#     print switch_dict
    return int(switch_dict.get(length))

def returnTimeSeconds(time_stamp): 
    year,month,day              =   time_stamp[:10].split("-")
    hour,minute,second          =   time_stamp[11:19].split(":")
    ms                          =   time_stamp[20:]
    ms_extend                   =   int(ms)*msExtend2SixDigitalNum(ms)
    timestamp_converted = datetime.datetime(int(year),int(month),int(day),int(hour),int(minute),int(second),int(ms_extend))
    return timestamp_converted
       
    
if __name__ == '__main__':
    runtimeFilePath=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS_L1143102326_RMOD_L_1_ram_runtime.log'
    # blackboxFilePath=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS3244_1011_blackbox'
    # path=r'D:\userdata\yongyu\Desktop\WMP_Support\automation_20161103\Snapshot_MRBTS-3244_FL17_FSM3_9999_161031_033736_eNB2213_20161102-1023\logs\SiteManager.log'
    path=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA'
#     path=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA\extracted\LTEBTS\BTSLogFiles\BTS3244_1011_blackbox'
    # path=r'C:\Users\personalpc\Desktop\wmp support\AfterTLDA\extracted\snapshot.properties'
    # abc = open_file_and_get_incorrect_timestamp(runtimeFilePath,False,False,True,False)
#     # print len(abc)
#     print len(abc)
    # for key in sorted(abc.keys()):
        # print key,abc[key]
    compareTimeStamp(path)    
        # print allStringChecking(abc[key])
        # print dateFormatChecking(abc[key])