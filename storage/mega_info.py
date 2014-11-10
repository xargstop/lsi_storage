#!/usr/bin/python
#encoding=utf-8

'''
1. install MegaCli or megacli
2. install glibc.i686
3. run as root
'''
import ptree
import commands
import json
import os

pwd = os.path.dirname(os.path.abspath(__file__))

megaclicmd = os.path.join(pwd, './MegaCli/MegaCli64')
tmp_file = os.path.join(pwd, 'mega_info.tmp')

cmds = {
        "adapter": " -AdpAllInfo -aAll -NoLog",
        "lds": " -LdPdInfo -aAll -NoLog",
        }

info_structure = {
        "adapter": {
            "^(Adapter\s*#\d+)$" : {
                "^Product Name\s*:\s*(.*)$" : "product"
                }
            },
        "lds":{
            "^(Adapter\s*#\d+)$" : {
                r"(^Virtual Drive:\s*\d+)": {
                    r'Number Of Drives\s*(?:per span)?:\s*(\d+)$': 'disks_span',
                    r'Span Depth *:\s*(\d+)$': 'span_num',
                    r'^RAID Level\s*:\s*(.*)$': 'raid_level',
                    r'^Size\s*:\s*(.*)$': 'size',
                    r'(Span: \d+)':{
                        r'(PD:\s*\d+) Information.*$': {
                            r'Firmware state:\s*(.*)\s*$': 'state',
                            r'Inquiry Data:\s*(.*)\s*$': 'model',
                            r'Coerced Size:\s*(\d+).*$': 'size'
                        }
                    }
                }
            }
        }
    }

def store_out_file(cmd, filename):
    st, out = commands.getstatusoutput(cmd)
    if st!=0:
        return False
    try:
        with open(filename, 'w') as fo:
            fo.write(out)
    except Exception, ex:
        raise ex
    return True

def get_common_dict(rule_name):
    cmd = megaclicmd + cmds[rule_name]
    _f = tmp_file
    if store_out_file(cmd, _f):
        rule_def = info_structure[rule_name]
        t = ptree.rulesTree(rule_def, data_tree_root_name=rule_name)
        with open(_f) as fp:
            t.build_data_tree(fp)
        os.remove(tmp_file)
        return t.convert_data_dict()
    else:
        print "call cmd fail: %s" % cmd
        return None

def _mega_info(adp, ld):
    import collections
    r = collections.defaultdict(dict)
    for a in adp['adapter'].keys():
        for k,v in adp['adapter'][a].items():
            r[a][k] = v
        for k,v in ld['lds'][a].items():
            r[a][k] = v
    return dict(r)

def mega_info():
    try:
        adp = get_common_dict('adapter')
        lds = get_common_dict('lds')
        _info = _mega_info(adp, lds )
        return _info
    except Exception,ex:
        raise ex

if __name__ == '__main__':
    try:
        print json.dumps(mega_info(), default = repr, indent=4, sort_keys=True)
    except Exception, ex:
        print ex
        import sys
        sys.exit(1)
