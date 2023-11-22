# -*- coding: utf-8 -*-
"""
Created on Wed May  2 20:32:16 2018

@author: jaymz
"""

import sys
from PyQt5 import QtGui, uic, QtWidgets
from form import Ui_Dialog
import numpy as np

import optics
import pickle
import copy

#plotting backend
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class MyDialog(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MyDialog, self).__init__()
        
        self.ui = Ui_Dialog()
        
        self.ui.setupUi(self)
        
        self.ui.table.setRowCount(4)
        self.ui.table.setColumnCount(4)
        
        self.ui.table.setHorizontalHeaderLabels(("Element Type;Position;Property;Label;").split(";"))
        self.elems = pickle.load(open('./configurations/nirModematch.pkl','rb'))
        self.populateListFromElems(self.elems)
        optics.wavelength = self.ui.box_wavelength.value()/1e6
        
        self.inversionPoints = None
        self.plotData = [None, None]
        
        print(self.ui.table.item(3,1).text())
        
         #----Set up plotting capabilities---------------
        self.plot_figure = Figure()
        self.plot_canvas = FigureCanvas(self.plot_figure)
        self.plot_toolbar= NavigationToolbar(self.plot_canvas, self)
        self.plot_ax = None
        
        #-----Add plots to UI---------------------------
        self.ui.plotLayout.addWidget(self.plot_toolbar)
        self.ui.plotLayout.addWidget(self.plot_canvas)

                
        #-----Connect interface events to functions
        self.ui.table.currentCellChanged.connect(self.cellClick)
        self.ui.table.cellChanged.connect(self.cellChanged)
        
        self.ui.button_rowAddA.clicked.connect(self.addRowAbove)
        self.ui.button_rowAddB.clicked.connect(self.addRowBelow)
        self.ui.button_rowDel.clicked.connect(self.delRow)
        self.ui.button_save.clicked.connect(self.saveSetup)
        self.ui.button_load.clicked.connect(self.loadSetup)
        #self.ui.button_load.clicked.connect(self.loadSetup_old)
        self.ui.button_export.clicked.connect(self.exportBeamProfile)
        self.ui.button_replot.clicked.connect(self.plotBeamProfile)
        self.ui.checkBox_grid.stateChanged.connect(self.plotBeamProfile)
        
        self.depLabel = 0
        
        self.plotBeamProfile()
        
        #self.ui.list.show()
        
#----------------------Utility Functions-----------------------
    def sortElements(self, elements):
        out = copy.deepcopy(elements)
        for i in range(0,len(out)):
            for j in range(i+1,len(out)):
                if(out[i]['pos'] > out[j]['pos']):
                    temp = copy.copy(out[i])
                    out[i] = out[j]
                    out[j] = temp
        return out
                    
    def populateListFromElems(self,elements):
        elems = self.sortElements(elements)
        self.ui.table.setRowCount(len(elems))
        for i in range(len(elems)):
            typeIn = elems[i]['type']
            typeStr = ''
            if(typeIn == 'l' or typeIn == 'lens'):
                typeStr = 'lens'
            elif(typeIn == 'i' or typeIn == 'info' or typeIn == 'label'):
                typeStr = 'label'
            self.ui.table.setItem(i,0,QtWidgets.QTableWidgetItem(typeStr))
            self.ui.table.setItem(i,1,QtWidgets.QTableWidgetItem(str(elems[i]['pos'])))
            if('val' in elems[i]):
                self.ui.table.setItem(i,2,QtWidgets.QTableWidgetItem(str(elems[i]['val'])))
            if('label' in elems[i]):
                self.ui.table.setItem(i,3,QtWidgets.QTableWidgetItem(elems[i]['label']))
            
    def populateElemsFromList(self):
        i = 0
        self.elems = []
        while self.ui.table.item(i,0) is not None:
            typ, pos, prop, lbl = None, None, None, None
            typ = self.ui.table.item(i,0).text()
            if(self.ui.table.item(i,1) is not None):
                pos = float(self.ui.table.item(i,1).text())
            if(self.ui.table.item(i,2) is not None):
                try:
                    prop = float(self.ui.table.item(i,2).text())
                except ValueError:
                    prop = None
            if(self.ui.table.item(i,3) is not None):
                lbl = self.ui.table.item(i,3).text()
            elem = {'pos':pos, 'label':lbl, 'type': typ, 'val':prop}
            self.elems.append(elem)
            i = i+1
        self.elems = self.sortElements(self.elems)
        #print(self.elems)
        
    def sysMatrixAtPos(self,position):
        matrixOut = np.matrix([[1.0,0.0],[0.0,1.0]])
        elements = []
        for i in range(len(self.elems)):
            if(self.elems[i]['type'] != 'i' and self.elems[i]['type'] != 'label'):
                elements.append(self.elems[i])
                if(elements[-1]['type'] == 'l' or elements[-1]['type'] == 'lens'):
                    elements[-1]['matrix'] = optics.lens(elements[-1]['val'])
        if(position > elements[0]['pos']):
            matrixOut =  elements[0]['matrix'] * optics.propagate(elements[0]['pos'])
        else:
            return optics.propagate(position)
        for i in range(1,len(elements)):
            if(position > elements[i]['pos']):
                matrixOut =  elements[i]['matrix'] * optics.propagate(elements[i]['pos']-elements[i-1]['pos']) * matrixOut
            else:
                return optics.propagate(position - elements[i-1]['pos'])*matrixOut
        
        return optics.propagate(position - elements[-1]['pos']) * matrixOut
     
    def qAtPos(self,qi,position):
        return optics.transferQ(qi,self.sysMatrixAtPos(position))

        
#----------------------Action Methods, No arguments-----------------------

    def cellClick(self,row,col,rp,cp):
        print("Click on " + str(row) + " " + str(col))
        #print(dialog)
    
    def cellChanged(self,row,col):
        self.populateElemsFromList()
        self.plotBeamProfile()
        
    def addRowAbove(self):
        row = self.ui.table.currentRow()
        self.ui.table.insertRow(row)
        self.populateElemsFromList()
        self.plotBeamProfile()
    def addRowBelow(self):
        row = self.ui.table.currentRow()
        self.ui.table.insertRow(row+1)
        self.populateElemsFromList()
        self.plotBeamProfile()
    
    def delRow(self):
        row = self.ui.table.currentRow()
        self.ui.table.removeRow(row)
        self.populateElemsFromList()
        self.plotBeamProfile()
        
    def saveSetup(self):
        info = QtWidgets.QFileDialog.getSaveFileName(self, "Save Data Parameters",
                                                     './configurations/',
                                                     "Pickle File (*.pkl)")
        filename = info[0]
        if(info[1] != ''):
            print("Saving to selected pickle filename: " + filename)
            datSave = {'elems' : self.elems,
                       'wavelen' : self.ui.box_wavelength.value(),
                       'plot_params':   [self.ui.box_range1.value(),
                                         self.ui.box_range2.value(),
                                         self.ui.box_plotNumPoints.value()],
                        'inputQ' : self.ui.box_compQ.text()}
            pickle.dump(datSave, open(filename, 'wb'))
            print("Done.")
        else:
            print("No file selected.")
            return
    
    def loadSetup_old(self,info):
        
        filename = info[0]
        if(info[1] != ''):
            self.ui.table.cellChanged.disconnect()
            print("Loading pickle file: " + filename)
            self.elems = pickle.load(open(filename,'rb'))
            self.populateListFromElems(self.elems)
            self.plotBeamProfile()
            self.ui.table.cellChanged.connect(self.cellChanged)
        else:
            print("No file selected.")
    
    def loadSetup(self):
        info = QtWidgets.QFileDialog.getOpenFileName(self, "Open Configuration File",
                                                     './configurations/',
                                                     "Pickle File (*.pkl)")
        filename = info[0]
        if(info[1] != ''):
            datIn = pickle.load(open(filename,'rb'))
            if('elems' not in datIn):
                print("-----Using deprecated load function!------------")
                self.loadSetup_old(info)
                return
            self.elems = datIn['elems']
            self.ui.table.cellChanged.disconnect()
            self.populateListFromElems(self.elems)
            self.ui.box_wavelength.setValue(datIn['wavelen'])
            plotParams = datIn['plot_params']
            self.ui.box_range1.setValue(plotParams[0])
            self.ui.box_range2.setValue(plotParams[1])
            self.ui.box_plotNumPoints.setValue(plotParams[2])
            self.ui.box_compQ.setText(datIn['inputQ'])
            self.plotBeamProfile()
            self.ui.table.cellChanged.connect(self.cellChanged)
        else:
            print("No file selected.")

    
    def exportBeamProfile(self):
        info = QtWidgets.QFileDialog.getSaveFileName(self, "Export raw plot points",
                                                     './configurations/',
                                                     "Comma Separated Values (*.csv);;Pickle File (*.pkl)")
        if(info[1] == ''):
            print("No file selected.")
            return
        elif(info[1] == "Comma Separated Values (*.csv)"):
            fName = info[0]
            if(len(fName.split('.csv'))<2):
                fName = fName + '.csv'
            if(self.plotData[0] is None):
                print("No Data to Export!")
                return
            np.savetxt(fName, np.transpose(self.plotData), delimiter = '\t')
        elif(info[1] == "Pickle File (*.pkl)"):
            fName = info[0]
            if(len(fName.split('.pkl'))<2):
                fName = fName + '.pkl'
            if(self.plotData[0] is None):
                print("No Data to Export!")
                return
            exportDat = {"x" : self.plotData[0], 'y' : self.plotData[1], "elements" : self.elems}
            pickle.dump(exportDat, open(fName,'wb'))
            
        print("Saved plot data to:\n" + fName)
            
        
        
    def plotBeamProfile(self):
        optics.wavelength = self.ui.box_wavelength.value()/1e6
        plotRange = sorted([self.ui.box_range1.value(), self.ui.box_range2.value()])
        plotPoints = self.ui.box_plotNumPoints.value()
        inputQ = complex(self.ui.box_compQ.text())
        self.inversionPoints = []
        elements = []
        labels = []
        for i in range(len(self.elems)):
            if(self.elems[i]['type'] != 'i' and self.elems[i]['type'] != 'label'):
                elements.append(self.elems[i])
            else:
                labels.append(self.elems[i])
        xp  = np.linspace(plotRange[0],plotRange[1],plotPoints)
        wX = [0.0]*len(xp)
        rX = [0.0]*len(xp)
        minW, maxW, minR, maxR = np.inf, -np.inf, np.inf, -np.inf
        for i in range(0,len(xp)):
            q = self.qAtPos(inputQ,xp[i])
            wX[i]=optics.width(q)
            rX[i]=optics.radiusRecip(q)
            if(i > 0 and rX[i-1]*rX[i]<0):
                self.inversionPoints.append((xp[i]*rX[i-1]-xp[i-1]*rX[i])/(rX[i-1]-rX[i]))
            
            minW=min(minW,wX[i])
            maxW=max(maxW,wX[i])
            minR=min(minR,rX[i])
            maxR=max(maxR,rX[i])
        
    #    plt.subplot(211)
        self.plotData = [xp,wX]
        ax = self.plot(self.plot_figure, self.plot_canvas, self.plot_ax, xp, wX,
                       xlabel="Propagation Distance (mm)",
                       ylabel="Beam Width (mm)")
        self.plot_ax = ax
        if(self.ui.checkBox_grid.isChecked()):
            print("Setting grid")
            ax.grid()
        ax.set_title('Beam width')
        for i in range(0,len(elements)):
            x = elements[i]['pos']
            print("Beam Width at " + elements[i]['label'] + ":\t%.4f"%(optics.width(self.qAtPos(inputQ,x))))
            if('label' in elements[i]):
                ax.annotate(elements[i]['label'],xy = (x,maxW),xytext = (x,maxW))
            self.plotAppend(ax,self.plot_canvas, [x,x],[minW,maxW])
        
        for i in range(0,len(labels)):
            x= labels[i]['pos']
            q=self.qAtPos(inputQ,x)
            print("Beam Width at " + labels[i]['label'] + ":\t%.4f"%(optics.width(q)) + '\tComplexQ: {:.2f}'.format(q) + '\tSlope: %.4e' % (optics.widthSlope(q)))
            self.plotAppend(ax,self.plot_canvas, [x,x],[minW,maxW])
            ax.annotate(labels[i]['label'],xytext = (x,maxW),xy = (x,maxW))
        
        print("Beam Waist locations (approximate):")
        for iP in self.inversionPoints:
            print("%.2f\t\tWaist Size:%.4f" % (iP, optics.width(self.qAtPos(inputQ,iP))))
        ax.set_xlabel("Propagation Distance (mm)")
        ax.set_ylabel("Beam Size")
        
    def plot(self, fig, canv, ax, x, y, **kwargs):
        if(ax is None):
            ax = fig.add_subplot(111,label = str(self.depLabel))
        ax.clear()
        
        ax.plot(x,y)

        if('ylabel' in kwargs):
            ax.set_ylabel(kwargs['ylabel'])
        if('xlabel' in kwargs):
            ax.set_xlabel(kwargs['xlabel'])
        
        canv.draw()
        return ax
    
    def plotAppend(self, ax, canv, x, y):
        ax.plot(x,y)
        canv.draw()
        return ax
    
    
        
        
if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        myapp = MyDialog()
        myapp.show()
        sys.exit(app.exec_())
