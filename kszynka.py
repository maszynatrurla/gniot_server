import web
import time
import os.path
import json
import logging
import logging.handlers

urls = (
    '/', 'Index',
    '/kszy_history.html', 'UserHistory',
    '/kszynka', 'Collect',
    '/teraz', 'Actual',
    '/history', 'History',
    '/chartjs/dist/(.*)', 'Crapy',
)
app = web.application(urls, globals())
db = web.database(dbn='sqlite', db='kszynka.db')
        
DB_KEYS = {    
    "pm1_0"     : "smog_pm1_0",
    "pm2_5"     : "smog_pm2_5",
    "pm2_5_cf1" : "smog_pm2_5_cf1",
    "dte_T"     : "temperature_dht",
    "part1_0"   : "smog_part1_0",
    "part2_5"   : "smog_part2_5",
    "bosz_T"    : "temperature_bmp",
    "pm10"      : "smog_pm10",
    "humidity"  : "humidity",
    "lux"       : "solar_mv",
    "pm10_cf1"  : "smog_pm10_cf1",
    "part0_5"   : "smog_part0_5",
    "pm1_0_cf1" : "smog_pm1_0_cf1",
    "pressure"  : "pressure",
    "part5_0"   : "smog_part5_0",
    "part10"    : "smog_part10",
    "part0_3"   : "smog_part0_3",
}

class Collect:
    def GET(self):
        ipt = web.input()
        gid = int(ipt.get("id", "0"))
        logging.info("Message from KSZYNKA#%d" % gid)
        ciapy = {}
        for key in ipt.keys():
            logging.info("    %s -> %s" % (key, ipt[key]))
            if key in DB_KEYS:
                ciapy[DB_KEYS[key]] = ipt[key]
        if ciapy:
            db.insert("pogoda", **ciapy)
 
        text = ">gnIOT<\n"
        text += "timestamp %d\n" % (int(time.time()))
        try:
            with open("kszyfigur_%d" % gid) as fp:
                text += fp.read()
        except:
            pass
            
        return text + "\n"

class Index:
    def GET(self):
        web.header('Content-Type', 'text/html')
        with open("html/kszynka.html") as fp:
            return fp.read()
            
class UserHistory:
    def GET(self):
        web.header('Content-Type', 'text/html')
        with open("html/kszy_history.html") as fp:
            return fp.read()
            
class Pudlo:
    def __init__(self):
        self.krapy = {}
        
    def add(self, ts, key, val):
        if val is not None:
            (last, last_ts), (mini, mini_ts), (maxi, maxi_ts) = self.krapy.get(key, ((val, ts), (val, ts), (val, ts)))
            if mini > val:
                mini = val
                mini_ts = ts
            if maxi < val:
                maxi = val
                maxi_ts = ts
            self.krapy[key] = ((val, ts), (mini, mini_ts), (maxi, maxi_ts))
    
    def isEmpty(self):
        return 0 == len(self.krapy)
        
    def serialize(self):
        val = {}
        for k,v in self.krapy.items():
            (last, last_ts), (mini, mini_ts), (maxi, maxi_ts) = v
            val[k] = {
                "latest" : {
                    "ts" : int(last_ts),
                    "localtime" : time.strftime("%Y.%m.%d %H:%M:%S", time.localtime(int(last_ts))),
                    "value" : last
                },
                "minimal" : {
                    "ts" : int(mini_ts),
                    "localtime" : time.strftime("%Y.%m.%d %H:%M:%S", time.localtime(int(mini_ts))),
                    "value" : mini
                },
                "maximal" : {
                    "ts" : int(maxi_ts),
                    "localtime" : time.strftime("%Y.%m.%d %H:%M:%S", time.localtime(int(maxi_ts))),
                    "value" : maxi
                }
            }
        
        return val

class Actual:
    
    def handleDbData(self, dbselect):
        values = Pudlo()
        for item in dbselect:
            ts = item.get("ts")
            values.add(ts, "temperature", item.get("temperature_bmp"))
            values.add(ts, "humidity",    item.get("humidity"))
            values.add(ts, "pressure",    item.get("pressure"))
            values.add(ts, "solar_mv",    item.get("solar_mv"))
            values.add(ts, "pm1_0",       item.get("smog_pm1_0"))
            values.add(ts, "pm2_5",       item.get("smog_pm2_5"))
            values.add(ts, "pm10",        item.get("smog_pm10"))
        return values
    
    def GET(self):
        ipt = web.input()
        zero_hour = ipt.get("zero_hour")
        ts = int(ipt.get("ts", int(time.time())))
        local_ts = time.localtime(ts)
        
        if zero_hour is None:
            # 24 hour window
            start_ts = ts - 24*3600
        else:
            # daily reset on zero hour
            zero_hour = int(zero_hour)
            
            if local_ts.tm_hour >= zero_hour:
                # hour align
                start_ts = ts - local_ts.tm_hour * 3600 - local_ts.tm_min * 60 - local_ts.tm_sec
                ts += zero_hour * 3600
                
            else:
                # hour align
                start_ts = ts - local_ts.tm_min * 60 - local_ts.tm_sec
                start_ts = start_ts - (24 - zero_hour + local_ts.tm_hour)*3600 
        
        sel = db.select('pogoda', what='strftime("%s", date) as ts,humidity,pressure,temperature_bmp,solar_mv,smog_pm1_0,smog_pm2_5,smog_pm10',
                where='ts >= "%s"' % start_ts)
                
        values = self.handleDbData(sel)
                
        if values.isEmpty():
            # nothing was found since start_time, try again - this time just get the most recent data point
            sel = db.select('pogoda', what='strftime("%s", date) as ts,humidity,pressure,temperature_bmp,solar_mv,smog_pm1_0,smog_pm2_5,smog_pm10',
                order="ts DESC", limit=1)
            values = self.handleDbData(sel)
        
        web.header('Content-Type', 'text/json')
        return json.dumps(values.serialize())
        
class History:
    
    def GET(self):
        ipt = web.input()
        key = ipt.get("key")
        end_ts = int(ipt.get("end_ts", int(time.time())))
        start_ts = int(ipt.get("start_ts", end_ts - 48*3600))
        
        if key is None:
            kys = "humidity,pressure,temperature_bmp,solar_mv,smog_pm1_0,smog_pm2_5,smog_pm10"
        else:
            kys = {"humidity" : "humidity",
                    "pressure" : "pressure",
                    "temperature" : "temperature_bmp",
                    "solar_mv" : "solar_mv",
                    "pm1_0" : "smog_pm1_0",
                    "pm2_5" : "smog_pm2_5",
                    "pm10" : "smog_pm10"}.get(key)
            if kys is None:
                raise web.webapi.badrequest("Unknown key")
        
        sel = db.select('pogoda', what='strftime("%s", date) as ts,' + kys,
                where='ts >= "%s" and ts <= "%s"' % (start_ts, end_ts))
        vals = []
        
        for item in sel:
            d = {
                "ts"          : item.get("ts"),
                "localtime"   : time.strftime("%Y.%m.%d %H:%M:%S", time.localtime(int(item.get("ts")))),
            }
            if "temperature" in kys: d["temperature"] = item.get("temperature_bmp")
            if "humidity"    in kys: d["humidity"]    = item.get("humidity")
            if "pressure"    in kys: d["pressure"]    = item.get("pressure")
            if "solar_mv"    in kys: d["solar_mv"]    = item.get("solar_mv")
            if "pm1_0"       in kys: d["pm1_0"]       = item.get("smog_pm1_0")
            if "pm2_5"       in kys: d["pm2_5"]       = item.get("smog_pm2_5")
            if "pm10"        in kys: d["pm10"]        = item.get("smog_pm10")
            vals.append(d)
        
        web.header('Content-Type', 'text/json')
        return json.dumps(vals)

class Crapy:
    def GET(self, crap):
        with open(os.path.join("chartjs/dist", crap), "rb") as fp:
            return fp.read()
            
def initLogging():
    
    FILENAME_LOG = "kszynka.log"
    LOG_MAX_FILESIZE = 5*1024*1024
    LOG_BACKUPS = 2
    
    logLevel = "INFO"
    FORMAT = '%(asctime)s %(message)s'

    logger = logging.getLogger()

    formatter = logging.Formatter(FORMAT, datefmt="%s")
    
    handler = logging.handlers.RotatingFileHandler(FILENAME_LOG,
            maxBytes=LOG_MAX_FILESIZE, backupCount=LOG_BACKUPS)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(logLevel)

if __name__ == "__main__":
    initLogging()
    app.run()
