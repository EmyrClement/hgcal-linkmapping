#!/usr/bin/env python3
import pandas as pd
import numpy as np
from rotate import rotate_to_sector_0
import matplotlib.pyplot as plt


pd.set_option('display.max_rows', None)

def loadDataFile():

    column_names=['layer', 'u', 'v', 'density', 'nDAQ', 'nTPG','DAQId1','nDAQeLinks1','DAQId2','nDAQeLinks2','TPGId1','nTPGeLinks1','TPGId2','nTPGeLinks2']

    #Read in data file
    data = pd.read_csv("data/FeMappingV3.txt",delim_whitespace=True,names=column_names)

    #For a given module you need to know the total number of e-links
    data['TPGeLinkSum'] = data[['nTPGeLinks1','nTPGeLinks2']].sum(axis=1).where( data['nTPG'] == 2 , data['nTPGeLinks1'])

    #And find the fraction taken by the first or second lpgbt
    data['TPGeLinkFrac1'] = np.where( (data['nTPG'] > 0), data['nTPGeLinks1']/data['TPGeLinkSum'], 0  )
    data['TPGeLinkFrac2'] = np.where( (data['nTPG'] > 1), data['nTPGeLinks2']/data['TPGeLinkSum'], 0  )
    return data

def getTCsPassing():

    #Set number of TCs by hand for now (In reality this number is taken per event from CMSSW)
    column_names=[ 'u', 'v', 'layer', 'nTCs', 'nWords' ]
    data = pd.read_csv("data/average_tcs_20200226.csv",names=column_names)

    return data
    
def getlpGBTLoadInfo(data,data_tcs_passing):
    #Loop over all lpgbts
        
    lpgbt_loads_tcs=[]
    lpgbt_loads_words=[]
    layers=[]

    for lpgbt in range(1,1600) :

        tc_load = 0.
        word_load = 0.
        lpgbt_layer = -1.
        lpgbt_found = False
        
        for tpg_index in ['TPGId1','TPGId2']:#lpgbt may be in the first or second position in the file

            for index, row in (data[data[tpg_index]==lpgbt]).iterrows():  
                if (row['density']==2):#ignore scintillator for now
                    continue

                lpgbt_found = True
                lpgbt_layer = row['layer']
                #Get the number of TCs passing threshold
                line = data_tcs_passing[(data_tcs_passing['layer']==row['layer'])&(data_tcs_passing['u']==row['u'])&(data_tcs_passing['v']==row['v'])]
                nwords = line['nWords'].values[0]
                ntcs = line['nTCs'].values[0]

                linkfrac = 'TPGeLinkFrac1'
                if ( tpg_index == 'TPGId2' ):
                    linkfrac = 'TPGeLinkFrac2'
                
                tc_load += row[linkfrac] * ntcs #Add the number of trigger cells from a given module to the lpgbt
                word_load += row[linkfrac] * nwords #Add the number of trigger cells from a given module to the lpgbt

        if (lpgbt_found):
            lpgbt_loads_tcs.append(tc_load)
            lpgbt_loads_words.append(word_load)
            layers.append( lpgbt_layer )

    return lpgbt_loads_tcs,lpgbt_loads_words,layers

def getHexModuleLoadInfo(data,data_tcs_passing):

    module_loads_words=[]
    layers = []
    
    for index, row in data.iterrows():  

        if ( row['TPGeLinkSum'] < 0 ):
            continue
        # if (row['density']==2):#ignore scintillator for now
        #     continue
        
        module_layer = row['layer']
        line = data_tcs_passing[(data_tcs_passing['layer']==row['layer'])&(data_tcs_passing['u']==row['u'])&(data_tcs_passing['v']==row['v'])]
        #print (line['nWords'].values[0])
        nwords = line['nWords'].values[0]
        ntcs = line['nTCs'].values[0]

        if ( ntcs == 0 ):
            print (row['layer'],row['u'],row['v'])
        word_load = nwords / (2 * row['TPGeLinkSum'] )
        module_loads_words.append(word_load)
        layers.append(module_layer)
        
    return module_loads_words,layers

def check_for_missing_modules(data,data_tcs_passing):

    mappingfile = data[['u','v','layer']]
    cmssw = data_tcs_passing[['u','v','layer','nTCs']]

    onlymapping = mappingfile.merge(cmssw.drop_duplicates(), on=['u','v','layer'],how='left', indicator=True)
    onlycmssw = cmssw.merge(mappingfile.drop_duplicates(), on=['u','v','layer'],how='left', indicator=True)

    onlycmssw = onlycmssw[onlycmssw['_merge'] == 'left_only']
    print (onlycmssw[onlycmssw['nTCs']>0][['layer','u','v']].to_string(index=False))
    
def plot(variable,savename="hist.png",binwidth=1,xtitle='Number of words on a single lpGBT'):
    fig = plt.figure()
    binwidth=binwidth
    plt.hist(variable, bins=np.arange(min(variable), max(variable) + binwidth, binwidth))
    plt.ylabel('Number of Entries')
    plt.xlabel(xtitle)
    plt.savefig(savename)
    

def plot2D(variable_x,variable_y,savename="hist2D.png",binwidthx=1,binwidthy=1,xtitle='Number of words on a single lpGBT'):
    
    fig = plt.figure()
    binwidth=binwidth
    plt.hist2d(variable_x,variable_y,bins=[np.arange(min(variable_x), max(variable_x) + binwidth, binwidth),np.arange(min(variable_y), max(variable_y) + binwidthy, binwidthy)])
    plt.colorbar()
    plt.ylabel('Layer')
    plt.xlabel(xtitle)
    plt.savefig(savename)

def main():

    #Load Data    
    data = loadDataFile() #dataframe
    data_tcs_passing = getTCsPassing() #from CMSSW
    #lpgbt_loads_tcs,lpgbt_loads_words,layers = getlpGBTLoadInfo(data,data_tcs_passing)

    #Check for missing modules
    #check_for_missing_modules(data,data_tcs_passing)
    
    module_loads_words,layers = getHexModuleLoadInfo(data,data_tcs_passing)
    
    #Plot Variables of interest

    # plot(lpgbt_loads_tcs,"loads_tcs.png",binwidth=0.1,xtitle='Number of TCs on a single lpGBT')
    # plot(lpgbt_loads_words,"loads_words.png",binwidth=0.1,xtitle='Number of words on a single lpGBT')
    # plot2D(lpgbt_loads_tcs,layers,"tcs_vs_layer.png",xtitle='Number of TCs on a single lpGBT')
    # plot2D(lpgbt_loads_words,layers,"words_vs_layer.png",xtitle='Number of words on a single lpGBT')


    plot(module_loads_words,"module_loads_words.png",binwidth=0.01,xtitle=r'Average number of words on a single module / $2 \times N_{e-links}$')
    plot2D(module_loads_words,layers,"module_words_vs_layer.png",binwidthx=0.05,binwidthy=1,xtitle=r'Average number of words on a single module / $2 \times N_{e-links}$')
    


    
main()
