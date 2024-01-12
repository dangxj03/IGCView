import numpy as np
from PySide6.QtWidgets import QApplication, QFileDialog, QWidget
from PySide6.QtUiTools import QUiLoader
import pyqtgraph  as pg
import pyqtgraph.opengl as gl

from IGCReader import IGCReader

class IGCView:
    def __init__(self):
        file_name = 'mwin.ui' # 当前ui文件的名称
        loade = QUiLoader()
        loade.registerCustomWidget(pg.opengl.GLViewWidget) # 注册GLViewWidget类
        self.file_ui = loade.load(file_name) # 加载ui文件
        self.file_ui.show()
        self.igc=IGCReader()

        # 轨迹tab 相关
        self.glwin=gl.GLViewWidget()
        # self.glwin.setBackgroundColor('w')
        self.glwin.setWindowTitle('IGC GL3D')
        #self.glwin.setGeometry(0, 110, 1920, 1080)
        # self.glwin.setCameraPosition(distance=30, elevation=12)
        self.gridx = gl.GLGridItem()  # 网格控件
        self.gridy = gl.GLGridItem()
        self.gridz = gl.GLGridItem()
        self.gridx.rotate(90, 0, 1, 0)
        self.gridy.rotate(90, 1, 0, 0)
        self.glwin.addItem(self.gridx)
        self.glwin.addItem(self.gridy)
        self.glwin.addItem(self.gridz)
        # 坐标轴标签
        self.lbx=[]
        self.lby=[]
        self.lbz=[]
        self.lbz1=[]
        self.ngd=10
        self.dgd=0
        self.minx=0
        self.miny=0
        self.minz=0
        for i in range(self.ngd):
            self.lbx.append(gl.GLTextItem())
            self.lby.append(gl.GLTextItem())
            self.lbz.append(gl.GLTextItem())
            self.lbz1.append(gl.GLTextItem())
            self.glwin.addItem(self.lbx[i])
            self.glwin.addItem(self.lby[i])
            self.glwin.addItem(self.lbz[i])
            self.glwin.addItem(self.lbz1[i])

        self.file_ui.verticalLayout.addWidget(self.glwin)
        self.mPlot=gl.GLLinePlotItem(color=pg.glColor((125, 125,125)), width=2, antialias=True)
        self.pPlot=gl.GLScatterPlotItem(pxMode=True)
        self.glwin.addItem(self.mPlot)
        # self.glwin.addItem(self.pPlot)

        self.file_ui.pushButtonOpenFile.clicked.connect(self.ReadIGCFile)
        self.file_ui.pushButtonBestUp.clicked.connect(self.showBestUp)
        self.file_ui.pushButtonBestDown.clicked.connect(self.showBestDown)
        self.file_ui.horizontalSliderStart.valueChanged.connect(self.updateSpin)
        self.file_ui.horizontalSliderEnd.valueChanged.connect(self.updateSpin)
        self.file_ui.spinBoxStart.valueChanged.connect(self.updateSlider)
        self.file_ui.spinBoxEnd.valueChanged.connect(self.updateSlider)
        self.file_ui.checkBoxP.stateChanged.connect(self.addPlotP)
        self.file_ui.checkBoxGPS.stateChanged.connect(self.addPlotGPS)

        self.updateSpin()

        # 曲线绘制tab相关
        date_axis = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation='bottom')

        # pw = pg.GraphicsView()
        pw = pg.PlotWidget(axisItems={'bottom': date_axis})
        pw.setBackground(pg.glColor((229, 229,229)))
        self.file_ui.horizontalLayout.addWidget(pw)
        l = pg.GraphicsLayout()
        pw.setCentralWidget(l)
        # pI = pg.PlotItem()
        penw=3
        self.plotH=pw.plot([0,1,2],[300,600,900],pen=pg.mkPen((148, 17,0),width=penw))
        self.plotD=pw.plot(pen=pg.mkPen((148, 82,0),width=penw))
        self.plotVV=pg.PlotCurveItem([0,1,2],[50,40,30],pen=pg.mkPen((79, 143,0),width=penw))
        self.plotVH=pg.PlotCurveItem(pen=pg.mkPen((0, 84,147),width=penw))
        self.plotV3D=pg.PlotCurveItem(pen=pg.mkPen((148, 33,147),width=penw))
        a2 = pg.AxisItem("right")
        self.vbCurve1=pw.getPlotItem().vb
        self.vbCurve2 = pg.ViewBox()
        self.vbCurve1.removeItem(self.plotD) #开始不显示
        l.addItem(pw.getPlotItem(), col=1)
        l.addItem(a2, col=2)
        l.scene().addItem(self.vbCurve2)
        a2.linkToView(self.vbCurve2)
        self.vbCurve2.setXLink(self.vbCurve1)
        # v1.addItem(pg.PlotCurveItem([0,1,2],[300,600,900]))
        self.vbCurve2.addItem(self.plotVV)
        self.vbCurve2.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)
        self.curveLgd=pg.LegendItem(offset=(50,5),labelTextColor='m',labelTextSize='18pt',colCount=6)
        self.curveLgd.setParentItem(pw.getPlotItem())
        self.curveLgd.addItem(self.plotH,'高度')
        self.curveLgd.addItem(self.plotVV,'上升速度')

        def updateViews():
            # setGeometry设置几何图形
            # sceneBoundingRect场景边界矩形
            self.vbCurve2.setGeometry(self.vbCurve1.sceneBoundingRect())
        self.vbCurve1.sigResized.connect(updateViews)

        self.file_ui.checkBoxH.stateChanged.connect(self.addPlotH)
        self.file_ui.checkBoxDis.stateChanged.connect(self.addPlotD)
        self.file_ui.checkBoxVV.stateChanged.connect(self.addPlotVV)
        self.file_ui.checkBoxV3D.stateChanged.connect(self.addPlotV3D)
        self.file_ui.checkBoxVH.stateChanged.connect(self.addPlotVH)




    def ReadIGCFile (self):
        filename, _ = QFileDialog.getOpenFileName (self.file_ui,"打开IGC文件","",
            "IGC文件 (*.igc)",)
        if filename:
            self.igc.readFile (filename)
            self.file_ui.listWidgetFileInfo.clear()
            for i in self.igc.infoFile:
                self.file_ui.listWidgetFileInfo.addItem(self.igc.infoFile[i])
            nmax=len(self.igc.xs)-1
            self.file_ui.horizontalSliderStart.setMaximum(nmax)
            self.file_ui.horizontalSliderStart.setValue(0)
            self.file_ui.horizontalSliderEnd.setMaximum(nmax)
            self.file_ui.horizontalSliderEnd.setValue(nmax)
            self.file_ui.spinBoxStart.setMaximum(nmax)
            self.file_ui.spinBoxStart.setValue(0)
            self.file_ui.spinBoxEnd.setMaximum(nmax)
            self.file_ui.spinBoxEnd.setValue(nmax)
            self.updateSpin()

    def addPlotP(self,state):
        if state:
            self.glwin.addItem(self.pPlot)
        else:
            self.glwin.removeItem(self.pPlot)
    def addPlotGPS(self,state):
        if state:
            self.glwin.addItem(self.mPlot)
        else:
            self.glwin.removeItem(self.mPlot)

    def addPlotH(self,state):
        if state:
            self.vbCurve1.addItem(self.plotH)
            self.curveLgd.addItem(self.plotH, '高度')
        else:
            self.curveLgd.removeItem(self.plotH)
            self.vbCurve1.removeItem(self.plotH)
    def addPlotD(self,state):
        if state:
            self.vbCurve1.addItem(self.plotD)
            self.curveLgd.addItem(self.plotD, '水平距离')
        else:
            self.curveLgd.removeItem(self.plotD)
            self.vbCurve1.removeItem(self.plotD)
    def addPlotVV(self,state):
        if state:
            self.vbCurve2.addItem(self.plotVV)
            self.curveLgd.addItem(self.plotVV, '上升速度')
        else:
            self.vbCurve2.removeItem(self.plotVV)
            self.curveLgd.removeItem(self.plotVV)
    def addPlotVH(self,state):
        if state:
            self.vbCurve2.addItem(self.plotVH)
            self.curveLgd.addItem(self.plotVH, '水平速度')
        else:
            self.vbCurve2.removeItem(self.plotVH)
            self.curveLgd.removeItem(self.plotVH)
    def addPlotV3D(self,state):
        if state:
            self.vbCurve2.addItem(self.plotV3D)
            self.curveLgd.addItem(self.plotV3D, '空间速度')
        else:
            self.vbCurve2.removeItem(self.plotV3D)
            self.curveLgd.removeItem(self.plotV3D)

    def updateSpin(self):
        self.pist=self.file_ui.horizontalSliderStart.value()
        self.piend=self.file_ui.horizontalSliderEnd.value()
        if self.piend<=self.pist:
            self.piend=self.pist+1
            self.file_ui.horizontalSliderEnd.setValue(self.piend)
        self.file_ui.spinBoxStart.setValue(self.pist)
        self.file_ui.spinBoxEnd.setValue(self.piend)
        self.updatePlot()
        self.updateCurve()

    def updateSlider(self):
        self.pist=self.file_ui.spinBoxStart.value()
        self.piend=self.file_ui.spinBoxEnd.value()
        if self.piend<=self.pist:
            self.piend=self.pist+1
            self.file_ui.spinBoxEnd.setValue(self.piend)
        self.file_ui.horizontalSliderStart.setValue(self.pist)
        self.file_ui.horizontalSliderEnd.setValue(self.piend)
        self.updatePlot()
        self.updateCurve()

    def updateCurve(self):
        if len(self.igc.xs) <5:
            return
        xdat=self.igc.tm[self.pist:self.piend]
        self.plotH.setData(xdat,self.igc.zs[self.pist:self.piend])
        self.plotD.setData(xdat,self.igc.dis[self.pist:self.piend])
        self.plotVV.setData(xdat,self.igc.vv[self.pist:self.piend])
        self.plotVH.setData(xdat,self.igc.vh[self.pist:self.piend])
        self.plotV3D.setData(xdat,self.igc.v3d[self.pist:self.piend])
        self.file_ui.listWidgetTrackInfo.clear()
        self.igc.trackStat(self.pist,self.piend)
        for i in self.igc.infoTrack:
            self.file_ui.listWidgetTrackInfo.addItem(str(i)+': '+str(self.igc.infoTrack[i]))

    def updatePlot(self):
        if len(self.igc.xs)>5:
            dat=np.column_stack ([self.igc.xs[self.pist:self.piend],self.igc.ys[self.pist:self.piend],self.igc.zs[self.pist:self.piend]])
            self.mPlot.setData(pos=self.igc.dataP[self.pist:self.piend,:])
            self.pPlot.setData(pos=self.igc.dataP[self.pist:self.piend,:],color=self.igc.colorP[self.pist:self.piend],size=self.igc.sizeP[self.pist:self.piend])
        self.setAxses()

    def setAxses(self):
        self.gridx.translate(-self.minx, -self.miny-self.dgd*self.ngd/2, -self.minz-self.dgd*self.ngd/2)
        self.gridy.translate(-self.minx-self.dgd*self.ngd/2, -self.miny, -self.minz-self.dgd*self.ngd/2)
        self.gridz.translate(-self.minx-self.dgd*self.ngd/2, -self.miny-self.dgd*self.ngd/2, -self.minz)
        self.minx=self.pist
        self.miny=self.pist
        self.minz=self.pist
        spanv=self.piend-self.pist
        if len(self.igc.xs) > 5:
            self.minx = int(self.igc.xs[self.pist:self.piend].min())
            self.miny = int(self.igc.ys[self.pist:self.piend].min())
            self.minz = int(self.igc.zs[self.pist:self.piend].min())
            spanv = self.igc.xs[self.pist:self.piend].max()-self.minx
            tmp=self.igc.ys[self.pist:self.piend].max()+1
            if tmp-self.miny>spanv:
                spanv=tmp-self.miny
            tmp=self.igc.zs[self.pist:self.piend].max()+1
            if tmp-self.minz>spanv:
                spanv = tmp-self.minz
        sps=int(spanv/self.ngd)
        spanv=sps*self.ngd
        self.dgd=sps
        self.gridx.setSpacing(x=sps,y=sps,z=sps)
        self.gridy.setSpacing(x=sps,y=sps,z=sps)
        self.gridz.setSpacing(x=sps,y=sps,z=sps)
        self.gridx.setSize(x=spanv,y=spanv,z=spanv)
        self.gridy.setSize(x=spanv,y=spanv,z=spanv)
        self.gridz.setSize(x=spanv,y=spanv,z=spanv)
        self.gridx.translate(self.minx, self.miny+self.dgd*self.ngd/2, self.minz+self.dgd*self.ngd/2)
        self.gridy.translate(self.minx+self.dgd*self.ngd/2, self.miny, self.minz+self.dgd*self.ngd/2)
        self.gridz.translate(self.minx+self.dgd*self.ngd/2, self.miny+self.dgd*self.ngd/2, self.minz)
        for i in range(self.ngd):
            self.lbx[i].setData(pos=(self.minx+i*sps,self.miny+self.dgd*self.ngd,self.minz-self.dgd/2),text=str(self.minx+i*sps))
            self.lby[i].setData(pos=(self.minx+self.dgd*self.ngd,self.miny+i*sps,self.minz-self.dgd/2),text=str(self.miny+i*sps))
            self.lbz[i].setData(pos=(self.minx,self.miny+self.dgd*self.ngd,self.minz+i*sps),text=str(self.minz+i*sps))
            self.lbz1[i].setData(pos=(self.minx+self.dgd*self.ngd,self.miny-self.dgd/2,self.minz+i*sps),text=str(self.minz+i*sps))
        # 视角
        self.glwin.setCameraPosition(pos=pg.Vector(self.minx,self.miny,self.minz), distance=spanv*3)
        # self.glwin.opts['center'] =pg.Vector(self.minx,self.miny,self.minz)
        # self.glwin.opts['distance'] =spanv*3

    def showBestUp(self):
        ist=self.igc.vv5[self.pist:self.piend].argmax()+self.pist
        iend =ist
        for i in range(ist,self.pist,-1):
            if self.igc.vv5[i]<-0.5:
                ist=i
                break
        for i in range(iend,self.piend):
            if self.igc.vv5[i]<-0.5:
                iend=i
                break
        self.updateRange(ist,iend)
    def updateRange(self,ist,iend):
        if ist+6<iend:
            ist-=5
            iend+=5
        self.pist=ist
        self.piend=iend
        self.file_ui.horizontalSliderStart.setValue(ist)
        self.file_ui.horizontalSliderEnd.setValue(iend)
        self.file_ui.spinBoxStart.setValue(ist)
        self.file_ui.spinBoxEnd.setValue(iend)
        self.updatePlot()
        self.updateCurve()

    def showBestDown(self):
        ist=self.igc.vv5[self.pist:self.piend].argmin()+self.pist
        iend =ist
        for i in range(ist,self.pist,-1):
            if self.igc.vv5[i]>-1.8:
                ist=i
                break
        for i in range(iend,self.piend):
            if self.igc.vv5[i]>-1.8:
                iend=i
                break
        self.updateRange(ist,iend)

if __name__ == '__main__':
    app = QApplication()
    window = IGCView()
    app.exec()