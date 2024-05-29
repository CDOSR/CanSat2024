def timeConverter(lt):
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    year = lt[0]
    month = months[lt[1]-1]
    day = lt[2]
    hour = lt[3]
    minute = lt[4]
    sec = lt[5]
    ctime = '{:04d}-{}-{:02d}T{:02d}:{:02d}:{:02d}'.format(year, month, day, hour, minute, sec)
    return ctime

def fn_timeConverter(lt):
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    year = lt[0]
    month = months[lt[1]-1]
    day = lt[2]
    hour = lt[3]
    minute = lt[4]
    sec = lt[5]
    ctime = '{:04d}{}{:02d}T{:02d}{:02d}{:02d}'.format(year, month, day, hour, minute, sec)
    return ctime

def weekDay(lt):
    wdays = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    wd = wdays[lt[6]]
    return wd

def yearDate(lt):
    return int(lt[7])

def epoch2UTC(et):
    yr = int(et / 31556926) + 1970
    mo = int((et % 31556926) / 2629743) + 1
    da = int(((et % 31556926) % 2629743) / 86400)
    ho = int((((et % 31556926) % 2629743) % 86400) / 3600)
    mi = int(((((et % 31556926) % 2629743) % 86400) % 3600) / 60)
    print('{}, {}, {}-{}:{}'.format(yr, mo, da, ho, mi))