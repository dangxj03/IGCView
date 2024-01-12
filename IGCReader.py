import time
import io
import math
import numpy as np


class IGCReader():
    def __init__(self):
        self.xs = np.array([1])
        self.ys = np.array([1])
        self.zs = np.array([1])
        self.zs1 = np.array([1])
        self.tm= np.array([1])
        self.infoFile={}
        self.infoTrack={}
        self.datestr="010203"
        self.vv = np.array([1])
        self.vv2 = np.array([1])
        self.vv5 = np.array([1])
        self.vh = np.array([1]) #水平速度 ，i路程
        self.v3d = np.array([1])
        self.dis= np.array([1])

    # %%
    # linebs= "B1234567890123E56789012W A567890123456"
    #  B 123456 78 90123 E 567 89012 W A 56789 01234
    #     时间   度  分      度   分       高度P  高度
    def parseIGC_B(self, ss):
        dat = {"time": time.mktime(time.strptime(self.datestr+ss[1:7], "%d%m%y%H%M%S"))-time.timezone,
               "lat": float(ss[7:9]) + float(ss[9:11] + '.' + ss[11:14]) / 60,
               "lon": float(ss[15:18]) + float(ss[18:20] + '.' + ss[20:23]) / 60,
               "altP": int(ss[25:30]),
               "altG": int(ss[30:35])}
        return dat

    def parseAll(self, gcl):
        dl = []
        for g in gcl:
            dl.append(self.parseIGC_B(g))
        return dl

    def readIGCLines(self, fname):
        ltxt = io.TextIOWrapper(io.BufferedReader(io.FileIO(fname))).readlines()
        for i in range(1,12):
            ss=ltxt[i].split(':')
            self.infoFile[ss[0]]=ss[1].strip('\n')
        for d in ltxt:
            if d.startswith("HFDTEDATE"):
                self.datestr =d[10:16]
                break

        gcl = []
        for s in ltxt:
            if s[0] == 'B':
                gcl.append(s)
        return gcl

    def lat2m(self, Latitude, Longitude):
        '''
        度数与弧度转化公式:1°= π/180°，1rad=180°/π。
        地球半径:6371000M
        地球周长:2*6371000M * π= 40030173
        纬度 38°地球周长:40030173*cos38 = 31544206M
        任意地球经度周长:40030173M
        经度(东西方向)1M实际度:360*/31544206M =1.141255544679108e-5=0.00001141
        纬度(南北方向)1M实际度:360°/40030173M=8.993216192195822e-6=0.00000899
        '''
        R = 6371000
        L = 2 * math.pi * R
        Lat_l = L * math.cos(Latitude * math.pi / 180)  # 当前纬度地球周长，弧度转化为度数
        Lng_l = 40030173  # 当前经度地球周长
        Latitude_m = Latitude * Lat_l / 360
        Longitude_m = Longitude * Lng_l / 360
        return Latitude_m, Longitude_m

    def readFile(self, fname):
        ltxt = self.readIGCLines(fname)
        ldat = self.parseAll(ltxt)
        lat0, lon0 = self.lat2m(ldat[0]["lat"], ldat[0]["lon"])
        n = len(ldat)
        self.xs=np.zeros(n)
        self.ys=np.zeros(n)
        self.zs=np.zeros(n)
        self.zs1=np.zeros(n)
        self.tm=np.zeros(n)
        for i in range(n):
            lat, lon = self.lat2m(ldat[i]["lat"], ldat[i]["lon"])
            self.xs[i] = lon - lon0
            self.ys[i] = lat - lat0
            self.zs[i] = ldat[i]["altG"]
            self.zs1[i] = ldat[i]["altP"]
            self.tm[i] = ldat[i]["time"]
        self.vv = np.gradient(self.zs)
        self.vv2 = np.convolve(self.vv,np.ones(2))/2
        self.vv5 = np.convolve(self.vv,np.ones(5))/5
        self.vh = np.sqrt(np.square(np.diff(self.xs))+np.square(np.diff(self.ys)))*3.6
        self.v3d = np.sqrt(np.square(np.diff(self.xs))+np.square(np.diff(self.ys))+np.square(np.diff(self.zs)))*3.6
        self.dis= np.sqrt(np.square(self.xs)+np.square(self.ys))
        #绘图数据
        self.dataP=np.column_stack ([self.xs,self.ys,self.zs])
        self.sizeP=np.fabs((self.vv+1)*2)
        self.colorP=np.zeros((self.dataP.shape[0],4))
        self.colorP[:,3]=0.8
        self.colorP[self.vv>0,0]=np.clip(self.vv/5,0,1)[self.vv>0]
        self.colorP[:,2]=0
        self.colorP[self.vv<2,1]=np.clip(-(self.vv+1)/5,0,1)[self.vv<2]

    def trackStat(self,ist=0,iend=-1):
        self.infoTrack['飞行时间']=time.strftime("%H时 %M分 %S秒",time.gmtime(self.tm[iend]-self.tm[ist]))
        self.infoTrack['获取高度']=self.zs[ist:iend].max()-self.zs[ist]
        self.infoTrack['失去高度']=self.zs[ist]-self.zs[ist:iend].min()
        self.infoTrack['最大上升'] =self.vv2[ist:iend].max()
        self.infoTrack['最大下沉'] =self.vv2[ist:iend].min()
        self.infoTrack['飞行距离']=round(abs(self.dis[iend]-self.dis[ist]),1)
        self.infoTrack['最远距离'] =round(self.dis[ist:iend].max(),1)
        self.infoTrack['水平航迹']=round(self.vh[ist:iend].sum()/3.6,1)
        self.infoTrack['垂直航迹']=np.fabs(self.vv[ist:iend]).sum()
        self.infoTrack['最大速度'] =round(self.vh[ist:iend].max(),1)
        self.infoTrack['最大空速'] =round(self.v3d[ist:iend].max(),1)
        self.infoTrack['最小速度'] =round(self.vh[ist:iend].min(),1)
        self.infoTrack['平均速度'] =round(np.average(self.vh[ist:iend]),1)


