import web
import time
import json
import os.path
import logging
import logging.handlers

urls = (
    '/', 'Index',
    '/kloc', 'Collect',
    '/ota', 'Ota',
    '/record', 'Record',
    '/actual', 'Actual',
    '/history', 'History',
    '/(.*).png', 'Image',
    '/chartjs/dist/(.*)', 'Crapy',
)
app = web.application(urls, globals())
db = web.database(dbn='sqlite', db='gniot.db')

ALL_GNIOTS = (1, 2, 3, 4)

def sampleToText(temp, hum):
    iT = (int(temp) / 100)
    dT = (int(temp) % 100)
    iH = (int(hum) / 100)
    dH = (int(hum) % 100)
    return "%d.%d C %d.%d %% rh" % (iT, dT, iH, dH)
    
class Actual:
    
    def getOne(self, gid):
        ret = {"gniot_id" : gid}
        sel = db.select('sample', order="ts DESC", limit=4, vars={"gid": gid, "tnow" : time.time()}, where="gniot_id=$gid and ts <= $tnow")
        d = (0, 0)
        p = (0, 0)
        t = None
        h = None
        ts = None
        sel = list(sel)
        sel.reverse()
        for item in sel:
            t = item.get("temperature")
            h = item.get("humidity")
            ts = item.get("ts")
            
            if p != (0, 0):
                d = (d[0] + (t - p[0]), d[1] + (h - p[1]))
            p = (t, h)
            
        dt = time.time() - ts
        if ts and dt >= 0 and dt < 1000:
            ret["T"] = float(t) / 100.
            ret["RH"] = float(h) / 100.
            ret["ts"] = ts
            ret["T_d"] = d[0]
            ret["RH_d"] = d[1]
            
        return ret
        
    
    def GET(self):
        web.header('Content-Type', 'text/json')
        try:
            gid = int(web.input().get("gniot_id"))
        except:
            gid = None
        if gid is not None:
            return json.dumps(self.getOne(gid))
        return json.dumps([self.getOne(i) for i in ALL_GNIOTS])
        
        
class History:
    def getI(self, key, dflt=None):
        try:
            return int(web.input()[key])
        except:
            return dflt
            
    def getOne(self, gid, start, end):
        times = []
        temps = []
        hums = []
        data = {"gniot_id" : gid, "start" : start, "end" : end, "t" : times, "T" : temps, "rh" : hums}
        
        sel = db.select('sample', order="ts", vars={"gid" : gid, "start": start, "end": end},
                where="gniot_id=$gid and ts >= $start and ts <=$end")
        anything = False
        for item in sel:
            anything = True
            ts = item.get("ts")
            T = item.get("temperature")
            rh = item.get("humidity")
            times.append(ts)
            temps.append(float(T) / 100.)
            hums.append(float(rh) / 100.)
        
        if anything:
            data["Tmin"] = min(temps)
            data["Tmax"] = max(temps)
            data["rhmin"] = min(hums)
            data["rhmax"] = max(hums)
        return data
    
    def GET(self):
        web.header('Content-Type', 'text/json')
        gid = self.getI("gniot_id")
        tlen = self.getI("length", 4*60)
        start = self.getI("start")
        end = self.getI("end")
        
        if start is None and end is None:
            end = int(time.time())
            start = end - tlen * 60
        elif start is not None and end is not None:
            if start >= end or start < 0:
                raise web.webapi.badrequest("start, end must be positive numbers and end > start")
        else:
            raise web.webapi.badrequest("you must provide both start and end (or none of them)")
            
        if gid is not None:
            return json.dumps(self.getOne(gid, start, end))
        data = {}
        ts = []
        Ts = []
        hs = []
        for gid in ALL_GNIOTS:
            gd = self.getOne(gid, start, end)
            data[gid] = gd
            if gd["t"]:
                ts.append(gd["t"][0])
                ts.append(gd["t"][-1])
                Ts.append(gd["Tmin"])
                Ts.append(gd["Tmax"])
                hs.append(gd["rhmin"])
                hs.append(gd["rhmax"])
        if ts:
            data["tmin"] = min(ts)
            data["tmax"] = max(ts)
            data["Tmin"] = min(Ts)
            data["Tmax"] = max(Ts)
            data["rhmin"] = min(hs)
            data["rhmax"] = max(hs)
            
        return json.dumps(data)
    
class Record:
    def GET(self):
        txt = "<html><head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>"\
                +"<title>GNIOT</title></head><body>\n"
        sel = db.select('sample', order="date DESC", limit=500)
        idx = 0;
        try:
            txt += "<table>"
            try:
                while (1):
                    idx += 1
                    s = sel.next()
                    T = s.get("temperature")
                    H = s.get("humidity")
                    ts = s.get("ts")
                    if ts is not None:
                        tss = time.strftime("%H:%M:%S", time.localtime(ts))
                    else:
                        tss = ""
                    txt += "<tr><td>"
                    #txt += str(idx)
                    txt += "</td><td>"
                    txt += str(s.get("gniot_id", 0))
                    txt += "</td><td>"
                    txt += sampleToText(T, H)
                    txt += "</td><td>"
                    txt += str(s.get("date"))
                    txt += "</td><td>"
                    txt += tss
                    txt += "</td></tr>\n"
            except StopIteration:
                pass
            txt += "</table>"
        except StopIteration:
            txt += "Nuda. nic tu nie ma :("
        
        return txt + "</body></html>"

class Index:
    def GET(self):
        web.header('Content-Type', 'text/html')
        with open("html/index.html") as fp:
            return fp.read()
        
class Image:
    def GET(self, image):
        try:
            with open(os.path.join("html", image + ".png"), "rb") as fp:
                return fp.read()
        except:
            pass
            
class Crapy:
    def GET(self, crap):
        with open(os.path.join("chartjs/dist", crap), "rb") as fp:
            return fp.read()
    
class Collect:
    def GET(self):
        ipt = web.input()
        gid = int(ipt.get("id", "0"))
        logging.info("Message from GNIOT#%d" % gid)
        for key in ipt.keys():
            logging.info("    %s -> %s" % (key, ipt[key]))
            if key.startswith("m_"):
                try:
                    ts = int(key[2:])
                    value = int(ipt[key])
                    T = value & 0xFFFF
                    H = (value >> 16) & 0xFFFF
                    logging.info("GNIOT#%d  %d %d" % (gid, T, H))
                    db.insert("sample", temperature=T, humidity=H, gniot_id=gid, ts=ts)
                except:
                    pass
        text = ">gnIOT<\n"
        text += "timestamp %d\n" % (int(time.time()))
        try:
            with open("konfigur_%d" % gid) as fp:
                text += fp.read()
        except:
            pass
            
        return text + "\n"
        return text

class Ota:
    def GET(self):
        gid = int(web.input().get("id", "0"))
        logging.info("OTA GNIOTA#%d" % gid)
        with open("konfigur_%d" % gid, "w") as fp:
            fp.write("")
        with open("gniot_maly.ota.bin", "rb") as fp:
            data = fp.read()
            web.header('Content-Length', len(data))
            return data
            
def initLogging():
    
    FILENAME_LOG = "gniot.log"
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
