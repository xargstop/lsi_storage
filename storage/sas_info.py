#!/usr/bin/python
#encoding=utf-8

'''
1. install sas2ircu
2. run as root
'''
import re
import commands
import json
import os

array_info = ['id', 'raid_level', 'size', 'disks']
disk_info = ['id', 'size', 'model', 'sn', 'realid']
pwd = os.path.dirname(os.path.abspath(__file__))

sas_cmd = os.path.join(pwd, './MegaCli/sas2ircu')

def get_controllers():
    cmd = sas_cmd+" LIST"
    st, out = commands.getstatusoutput(cmd)
    if st!=0:
        return []
    r = []
    for line in out.split('\n'):
        if re.match('^\s+[0-9]+\s+\w+.*', line):
            ctl_index, ctl_type = line.split()[0], line.split()[1]
            r.append((ctl_index, ctl_type))
    return r

def get_arrays():
    res = []
    _ctl_list = get_controllers()
    for r in _ctl_list:
        res.extend(
                [dict(zip(array_info, a)) for a in _get_array(r[0])]
                )
    return res

def _get_array(ctrlnmbr):
    cmd=sas_cmd+' '+ctrlnmbr+' DISPLAY'
    st, res = commands.getstatusoutput(cmd)
    if st!=0:
        return []
    list=[]
    disklist=[]
    arrayid=None
    raidlevel=''
    size=''
    for line in res.split('\n'):
        if re.match('^IR volume [0-9]+.*$',line):
            if arrayid is not None:
                list.append((arrayid,raidlevel,size,disklist))
                disklist=[]
            arrayid=re.match('^IR volume ([0-9]+).*$',line).group(1)
        if re.match('^\s*RAID level.*$',line):
            raidlevel=line.split(':')[1].strip()
        if re.match('^\s*Size \(in MB\)\s+.*$',line):
            size=line.split(':')[1].strip()
            size=str(int(round((float(size) / 1000))))+'G'
        if re.match('^\s*PHY\[[0-9]+\] Enclosure#/Slot#.*$',line):
            disksid=':'.join(line.split(':')[1:]).strip()
            disklist.append(disksid)
    list.append((arrayid,raidlevel,size,disklist))
    # ie: [0, 'Okay (OKY)', 'RAID1', '1800G', [['1', '0'], ['1', '1']]]
    return list

def get_disks():
    res = []
    _ctl_list = get_controllers()
    for r in _ctl_list:
        for d in _get_disks(r[0]):
            _disk = dict(zip(disk_info, d))
            res.append(_disk)
    return res

def _get_disks(ctrlnmbr):
    cmd = sas_cmd+' '+ctrlnmbr+' DISPLAY'
    st, res = commands.getstatusoutput(cmd)
    if st!=0:
        return []
    list=[]
    diskid=-1
    disksize=''
    diskmodel=''
    diskserial=''
    enclid=''
    slotid=''
    realid=['','']
    skipped = False
    for line in res.split('\n'):
        if re.match('^Device is a Enclosure services device.*$',line):
            skipped = True
        if re.match('^Device is a Hard disk.*$',line):
            skipped = False
            if diskid == -1:
                diskid=diskid+1
            else:
                list.append((str(diskid),disksize,diskmodel,diskserial,realid))
                diskid=diskid+1
        if not skipped:
            if re.match('^\s*Enclosure #.*$',line):
                enclid=line.split(':')[1].strip()
            if re.match('^\s*Slot #.*$',line):
                slotid=line.split(':')[1].strip()
                realid=':'.join([enclid,slotid])
            if re.match('^\s*Size.*$',line):
                disksize=line.split(':')[1].split('/')[0].strip()
                disksize=str(int(round((float(disksize) / 1000))))+'G'
            if re.match('^\s*Model Number.*$',line):
                diskmodel=line.split(':')[1].strip()
            if re.match('^\s*Serial No.*$',line):
                diskserial=line.split(':')[1].strip()
    # ie: [[0, '1000G', 'Hitachi HUA72202', 'JK1151YAHUYAZZ', ['1', '0']], 
    #      [1, '200G',  'Hitachi HUA72202', 'JK1151YAHUW1DZ', ['1', '1']]]
    list.append((str(diskid),disksize,diskmodel,diskserial,realid))
    return list

def get_sas_storage_info():
    import collections
    res = collections.defaultdict(dict)
    for r in get_controllers():
        _idx = r[0]
        res[_idx]['type'] = r[1]
        res[_idx]['arrays']={}
        res[_idx]['disks']={}
        for _array in _get_array(_idx):
            _array_id = _array[0]
            res[_idx]['arrays'][_array_id]={}
            res[_idx]['arrays'][_array_id].update(
                                    zip(array_info, _array)
                                    )

        for _disk in _get_disks(_idx):
            _disk_id = _disk[0]
            res[_idx]['disks'][_disk_id]={}
            res[_idx]['disks'][_disk_id].update(
                    zip(disk_info, _disk)
                    )

    return dict(res)

if __name__ == '__main__':
    try:
        print json.dumps(get_arrays(), default = repr, indent=4, sort_keys=True)
        print json.dumps(get_disks(), default = repr, indent=4, sort_keys=True)
    except Exception, ex:
        print ex
        import sys
        sys.exit(1)
