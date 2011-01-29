"""Project-specific Code for Testing METE's SAD Predictions

Required input = Abundances per species per site for one sampling period
    
All data queries used can be found in MaxEnt/trunk/data:
    BBS_data_query
    CBC_data_query
    Gentry_data_query
        
"""
    
import macroeco_distributions as md
import mete
import csv
import macroeco
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import weestats

def run_test(input_filename, output_filename1, output_filename2, cutoff = 9):
    """Use data to compare the predicted and empirical SADs and get results in csv files
    
    Keyword arguments:
    input_filename -- path to file that has raw data in the format: 
                        'site','year','sp','ab'
    output_filename1 -- file that will store the pred and observed species-level 
                        abundances for each site in the input file
    output_filename2 -- file that will store the p-values and weights from 
                        dist_test for each site in the input file
    cutoff      --  minimum number of species required to run.
    
    """
    
    ifile = np.genfromtxt(input_filename, dtype = "S9,i8,S9,i8", 
                       names = ['site','year','sp','ab'], delimiter = ",")
    
    usites = np.sort(list(set(ifile["site"])))
    
    f1 = csv.writer(open(output_filename1,'a'))
    f2 = csv.writer(open(output_filename2,'a'))
    
    for i in range(0, len(usites)):
        subsites = ifile["site"][ifile["site"] == usites[i]]
        S = len(subsites)
        subab = np.sort(ifile["ab"][ifile["site"] == usites[i]])
        N = sum(subab)
        if S > cutoff:
            # Generate predicted values and p (e ** -lambda_sad) based on METE:
            mete_pred = mete.get_mete_sad(int(S),int(N))
            pred = np.array(mete_pred[0])
            p = mete_pred[1]
            subab = np.sort(subab)[::-1]
            # Calculate Akaike weight of log-series:
            L_logser = md.logser_ll(subab, p)        
            mu = np.mean(np.log(subab))
            sigma = np.std(np.log(subab))
            L_pln = md.pln_ll(mu,sigma,subab)        
            k1 = 1
            k2 = 2    
            AICc_logser = weestats.AICc(k1, L_logser, S)
            AICc_pln = weestats.AICc(k2, L_pln, S)
            weight = weestats.aic_weight(AICc_logser, AICc_pln, S, cutoff = 4) 
            #save results to a csv file:
            results = ((np.column_stack((subsites, subab, pred))))
            results2 = ((np.column_stack((usites[i], S, N, p, weight))))
            f1.writerows(results)
            f2.writerows(results2)
            
def plot_pred_obs(input_filename, title = ''): 
    """use output from run_test to plot observed vs. predicted abundances"""
    
    ifile = np.genfromtxt(input_filename, dtype = "S9,i8,i8", 
                       names = ['site','obs','pred'], delimiter = ",")
    
    pred = ((ifile["pred"]))
    obs = ((ifile["obs"]))
    
    plt.figure()
    macroeco.plot_color_by_pt_dens(pred, obs, 5, loglog=1)
    plt.title(title)
    plt.xlabel('Predicted abundances')
    plt.ylabel('Observed abundances')
    plt.show()    
    
def plot_weights(input_filename, data = 'raw', left = [0, 0.4, 0.8], 
                 width = 0.2, color = 'b', title = ''): 
    """use output from run_test to plot frequency distribution of Akaike weights"""
    
    ifile = np.genfromtxt(input_filename, dtype = "S9,i8,i8,f8,f8", 
                       names = ['site','S','N','p','weight'], delimiter = ",")
    
    weights = ((ifile["weight"]))
    weights=weights[weights>=0]
    bins = [0, 0.4, 0.6, 1]
    cts = np.histogram(weights, bins = bins)
    
    if data == 'raw':
        height = cts[0]  
    else:
        height = cts[0] * 100 / sum(cts[0])
    
    plot_obj = plt.subplot(111)
    plot_obj.bar(left, height, width, color = color)
    plot_obj.set_title(title)
    plot_obj.set_ylabel('Number of sites') 
    
    return plot_obj

def cross_taxa_weight_plot (input_filenames):
    """Plot histogram of weights across taxa
    
    Keyword arguments:
    input_filenames -- list of file names to be processed
    
    """     
    plt.figure(1) 
    n = len(input_filenames)
    colors = ['k', 'r', 'g', 'b']
    
    for i in range(0, n):
        input_filename = input_filenames[i]
        width = round(1.0/(3 + n * 3), 2)
        left = [(width * (i + 1)), (width * (i + n + 2)), (width * (i + n + 6))]
        plot_weights(input_filename, data = 'percent', left = left, 
                     color = colors[i], width = width)
    
    plt.ylabel('Percentage of sites')
    # TO DO: figure out universal means of determining xtick locations
    plt.xticks(((((3 + n * 3)/4.8) * width), (((3 + n * 3)/1.85) * width), 
               (((3 + n * 3)/1.14) * width)), 
               ('Log-normal', 'Indeterminate', 'Log-series') )
    # TO DO: figure out how to include a color-coded legend: 
    plt.legend(('CBC', 'BBS', 'Gentry'), loc = 'upper left')
    plt.show()
    
def rare_sp_count (input_filename, abundance_class):
    """Count and plot number of species observed and predicted in a given abundance class
    
    Keyword arguments:
    input_filename -- name of file containing observed and predicted abundances 
    in the format ['site', 'obs', 'pred'], as output from run_test
    abundance_class -- singleton, doubleton, rare(n <=10), or dominant
    
    """
    
    ifile = np.genfromtxt(input_filename, dtype = "S9,i8,i8", 
                       names = ['site','obs','pred'], delimiter = ",")
    
    site = ((ifile["site"]))    
    usites = list(set(site))  
    
    pred_class = []
    obs_class = []
    for i in range (0, len(usites)):
        pred = ifile["pred"][ifile["site"] == usites[i]]
        obs = ifile["obs"][ifile["site"] == usites[i]]
        if abundance_class == 'singleton':
            subpred = len(pred[pred == 1])
            subobs = len(obs[obs == 1])
        elif abundance_class == 'doubleton':
            subpred = len(pred[pred == 2])
            subobs = len(obs[obs == 2])
        elif abundance_class == 'dominant':
            subpred = max(pred)
            subobs = max(obs)
        elif abundance_class == 'rare':
            subpred = len(pred[pred <= 10])
            subobs = len(obs[obs <= 10])
        pred_class.append(subpred)
        obs_class.append(subobs)
        
    return(pred_class, obs_class)

def ab_class_test_plot(input_filename):
    """Regress number of species predicted vs. observed in a given abundance class
    
    Keyword arguments:
    input_filename -- name of file containing observed and predicted abundances 
    in the format ['site', 'obs', 'pred'], as output from run_test
    
    """
    abundance_classes = ['singleton', 'doubleton', 'rare', 'dominant']
    
    regr_results = []
    for i in range (0, len(abundance_classes)):
        results = rare_sp_count (input_filename, abundance_classes[i])
        pred = results[0]
        obs = results[1] 
        slope, intercept, r_value, p_value, std_err = stats.linregress(pred, obs)
        results2 = ((np.column_stack((slope, intercept, r_value, p_value, std_err))))
        regr_results.append(results2)
        #plt.subplot(2,2,i+1) had to change macroeco.py to accept i to generate subplots
        macroeco.plot_color_by_pt_dens(np.array(pred), np.array(obs), 1, i)
        plt.plot([0,max(max(pred),max(obs))+ 1], [0,max(max(pred),max(obs)) + 1])
        plt.xlim(0, max(max(pred),max(obs)) + 1)
        plt.ylim(0, max(max(pred),max(obs)) + 1)
        plt.title(abundance_classes[i])
        plt.xlabel('Predicted number of species')
        plt.ylabel('Observed number of species')
        r2 = ('r2 = ' + str(round(r_value**2, 2)))
        b = ('y = ' + str(round(slope, 2)) + 'x + ' + str(round(intercept)))
        plt.annotate(b, xy=(-10, 10), xycoords='axes points',
                horizontalalignment='right', verticalalignment='bottom',
                fontsize=14)
        plt.annotate(r2, xy=(-10, 30), xycoords='axes points',
                horizontalalignment='right', verticalalignment='bottom',
                fontsize=14)

    plt.show()   
    return(regr_results)


def multi_taxa_conf_hulls(input_filenames, radius, conf_interval, logscale=0):
    colors = ['r', 'g', 'b', 'k', 'c']
    plotmax = 0
    for i, filename in enumerate(input_filenames):
        infile = np.genfromtxt(filename, dtype = "S9,i8,i8", 
                       names = ['site','obs','pred'], delimiter = ",")
        hull_points = macroeco.confidence_hull(infile['pred'], infile['obs'], 2,
                                               logscale=logscale,
                                               color=colors[i], alpha=0.75-float(i)/10)
        plotmax = max([plotmax, np.max(hull_points)])
    plt.loglog([0.5, plotmax * 2], [0.5, plotmax * 2], 'k-')
    plt.xlim(.5, plotmax * 2)
    plt.ylim(.5, plotmax * 2)
    plt.xlabel('Predicted abundance')
    plt.ylabel('Observed abundance')
    plt.show()