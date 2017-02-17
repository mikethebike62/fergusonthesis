#############Mike Ferguson Thesis
#############Keep Your Eye on the Game: Analysis of Scoreboard Watching

'''Modules'''
import sys, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pylab
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.formula.api import ols

from dateutil import parser
####Display Options
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 10)
desired_width = 320
pd.set_option('display.width', desired_width)


'''import data'''
#currPath = os.getcwd()
#workPath = '/home/vmuser/Documents/thesis'
#currPath = workPath + '/' + 'data'
#outPath  = workPath + '/' + 'out'
currPath = 'C:/Users/Mike/Dropbox/FergusonThesis/workingdata'

dataManager = 'ManagerStats.csv'
dataScores = 'MLBScores.csv'
dataSalaries = 'Salaries.csv'
dataTeamStats = 'TeamStats.csv'
dataDates = 'DatesbyTeam.csv'

'''Manager Stats'''
dmgr = pd.read_csv(currPath + '/' + dataManager)
'''Team Payroll'''
dpay = pd.read_csv(currPath + '/' + dataSalaries)
'''Average age'''
dage =  pd.read_csv(currPath + '/' + dataTeamStats)
'''Dates'''
dd = pd.read_csv(currPath + '/' + dataDates)
dd['fullDate'] = dd.apply(lambda x: parser.parse(x['Date']),axis=1)
#dd = dd[(dd['Season']==2014)]

'''Scores'''
dc = pd.read_csv(currPath + '/' + dataScores)
dc = dc[dc['Date'] != 'Date'] #Remove extra heading rows
dc['Date'] = dc['Date'] + ', ' + dc['Season']
dc['Date'] = dc.apply(lambda x: parser.parse(x['Date']), axis=1)
dc['isthome'] = dc.apply(lambda x: 1 if x['Symbol']!="@" else 0, axis=1)

dc = dc.rename(columns={'Visitor': 'team', 'Home': 'opp', 'Visitor W/L': 'gameWL', 'Runs Visitor': 'teamRuns', 'Runs Home': 'oppRuns', 'D/N': 'DN', 'Gm': 'gn'})
dc = dc.drop(['Unnamed: 4', 'W-L', 'Win', 'Loss', 'Save', 'Rk', 'gameWL', 'Inn', 'GB', 'Rank', 'Streak', 'Time', 'Symbol'], axis=1)
dc[['Season', 'teamRuns', 'oppRuns', 'gn']] = dc[['Season', 'teamRuns', 'oppRuns', 'gn']].astype(float)  ####Convert values to floats

dc['druns'] = dc['teamRuns'] - dc['oppRuns']
dc['twin'] = dc.apply(lambda x: 1 if x['druns'] > 0 else 0, axis=1)
dc['tlos'] = dc.apply(lambda x: 1 if x['druns'] < 0 else 0, axis=1)

dc = dc.sort(['Season', 'team', 'gn'], ascending=[1, 1, 1])
dc = dc.set_index(['Season', 'team'])
#####Getting pre-game record
dc['tws'] = dc.groupby(level=['Season', 'team'])['twin'].cumsum() - dc['twin']
dc['tls'] = dc.groupby(level=['Season', 'team'])['tlos'].cumsum() - dc['tlos']
dc['twper'] = dc['tws'] / (dc['tws'] + dc['tls'])
dc['tgameday'] = 1
dc = dc.reset_index()
####Run entire loop together, lines 57 to 72
season_list = dc['Season'].unique()  ###Create list of seasons
team_list   = dc['team'].unique()    ###Create list of teams
dm = pd.DataFrame()             ####Create blank data frame

for season in season_list:
    dt = dc[dc['Season'] == season]    ####Create data for one season
    sta_date = dt['Date'].min()
    end_date = dt['Date'].max()
    for team in team_list:
        du = pd.DataFrame(data=None, columns=['team'], index=pd.date_range(sta_date, end_date)).reset_index()
        du = du.rename(columns={'index': 'Date'})
        du['team'] = team
        dv = pd.DataFrame()
        dv = pd.merge(du, dt, left_on=['Date', 'team'], right_on=['Date', 'team'], how='left').set_index(['Season', 'team']) ###Data for one team for one season
        dm = pd.concat([dm, dv], axis=0)
print 'loop complete'

dm = dm.reset_index(level=0)
dm['toffday'] = dm['tgameday'].apply(lambda x: 1 if x != 1 else 0)
dm = dm.fillna(method='bfill')
dm['month'] = dm['Date'].apply(lambda x: x.month)
dm = dm[dm['month'] > 4]   ####Only leave May results to the end of the season results
dm = dm.reset_index()

'''standings'''
dr = pd.DataFrame()
dr = dm[['Season', 'Date', 'League', 'Division', 'team', 'twin', 'tlos', 'gn', 'tws', 'tls', 'twper','Attendance','Streak1','PriorStreak']]
#dr = dr[dr['Season']==2014]
#dr = dr[(dr['League']=='AL') & (dr['Division']=='East')]
dr = dr.sort(['League', 'Division', 'Date', 'team', 'gn'], ascending=[1, 1, 1, 0, 1])
dr = dr.groupby(['League', 'Division', 'Date', 'team']).first().reset_index()

'''create standing related variables here'''
dr = dr.sort(['League', 'Division', 'Date', 'twper'], ascending=[1, 1, 1, 0])
dr['drank'] = dr.groupby(['League', 'Division', 'Date'])['twper'].rank(ascending = False)
dr = dr.sort(['League', 'Date', 'twper'], ascending=[1, 1, 0])
dr['lrank'] = dr.groupby(['League', 'Date'])['twper'].rank(ascending = False)

'''team and opp data frames'''
dt = dr[['Season', 'Date', 'League', 'Division', 'team', 'drank', 'lrank']]
dt = dt.rename(columns={'drank': 'tdrank', 'lrank': 'tlrank'})
do = dr
do = do.rename(columns={'team': 'opp', 'tws': 'ows', 'tls': 'ols', 'twper': 'owper', 'drank': 'odrank', 'lrank': 'olrank', 'gn': 'ogn', 'Streak1': 'ostreak','PriorStreak':'opriorstreak'})
dw = dr[dr['drank']==1][['Season', 'Date', 'League', 'Division', 'team', 'tws', 'tls', 'twper', 'twin', 'tlos']] ###division leader data
dw = dw.rename(columns={'team': 'dleader', 'tws': 'dlws', 'tls': 'dlls', 'twper': 'dlwper', 'twin': 'dltwin', 'tlos': 'dllos'})
dx = dr[dr['lrank']==1][['Season', 'Date', 'League', 'Division', 'team', 'tws', 'tls', 'twper', 'twin', 'tlos']] ####league leader data
dx = dx.rename(columns={'team': 'lleader', 'tws': 'llws', 'tls': 'llls', 'twper': 'llwper', 'twin': 'lltwin', 'tlos': 'lllos'})

'''analysis data'''
da = pd.DataFrame()
da = dm[dm['tgameday']==1][['Season', 'Date', 'League', 'Division', 'team', 'opp', 'teamRuns', 'oppRuns', 'isthome', 'druns', 'twin', 'tws', 'tls', 'twper','DN','PriorStreak']]
#da = da[da['Season']==2014]
#da = da[(da['League']=='AL') & (da['Division']=='East')]

'''merge standing related variables'''
da = pd.merge(da, dt, left_on=['Season', 'League', 'Division', 'Date', 'team'], right_on=['Season', 'League', 'Division', 'Date', 'team'])
da = pd.merge(da, do, left_on=['Season', 'Date', 'opp'] , right_on=['Season', 'Date', 'opp'])
da = pd.merge(da, dw, left_on=['Season', 'League_x', 'Division_x', 'Date'], right_on=['Season', 'League', 'Division', 'Date'])
da = pd.merge(da, dx, left_on=['Season', 'League_x', 'Date'], right_on=['Season', 'League', 'Date'])

'''playoff race indicative variables'''
da['gbll'] = (da['llws']-da['tws'] + da['tls']-da['llls'])/2
da['gbdl'] = (da['dlws']-da['tws'] + da['tls']-da['dlls'])/2

da = da.rename(columns={'League_x': 'tLeague', 'Division_x': 'tDivision', 'League_y': 'oLeague', 'Division_y': 'oDivision'})

#####Add tomorrow's date to dw so that it can be merged with da and get previous game result of division leader
import datetime
from datetime import timedelta
dw['one_day'] = datetime.timedelta(days=1)
dw['nextday'] = dw['Date']+dw['one_day']
dw['Date'].dtypes
dw

print 'Merge to get team with league leader'
d1 = pd.merge(da, dw, left_on=['Season', 'Date', 'dleader'],right_on=['Season', 'nextday', 'dleader'])
d1.dtypes
d1.describe()
d1.groupby(level=0).first()
print 'merge complete'

print 'create variables'
d1['month'] = d1['Date_x'].apply(lambda x: x.month)
d1['month2'] = d1['month']
d1['month2'] = d1.apply(lambda x: 9 if (x['month2'] > 9) else x['month2'] , axis=1)

d1['gb'] = d1.apply(lambda x: 2 if (x['gbdl'] > 10) else x['gbdl'] , axis=1)
d1['gb'] = d1.apply(lambda x: 0 if (x['gbdl'] <= 5) else x['gb'] , axis=1)
d1['gb'] = d1.apply(lambda x: 1 if (x['gbdl'] > 5) & (x['gbdl']<= 10) else x['gb'] , axis=1)

print 'data frame without division leaders'
d1 = d1[d1['gbdl'] > 0]

d1['Season']    = d1['Season'].astype(float)
d1['month']     = d1['month'].astype(float)
d1['gb']        = d1['gb'].astype(float)
d1['dltwin_x']  = d1['dltwin_x'].astype(float)
d1['twin_x']    = d1['twin_x'].astype(float)
d1['month2']    = d1['month2'].astype(float)
d1['PriorStreak']    = d1['PriorStreak'].astype(float)
d1['opriorstreak']    = d1['opriorstreak'].astype(float)


print '************analyses****************'

print 'Table 1. Summary stats'
d3 = d1.groupby(['month2', 'gb', 'dltwin_x'])['twin_x'].mean()
#d3.to_csv(outPath + '/' + 'mlbforanalysiswithoutseason2.csv')

d4 = d1.groupby(['month2', 'gb', 'dltwin_x'])['twin_x'].std()
#d4.to_csv(outPath + '/' + 'mlbforanalysiswithoutseason2standarddev.csv')

print 'regression'

d1['lngbdl']    = np.log(d1['gbdl'])
d1['dwper']     = d1['twper'] - d1['owper']
d1['dlw_gbdl']  = d1['dltwin_x'] * d1['gbdl']
d1['dll_gbdl']  = (1 - d1['dltwin_x']) * d1['gbdl']

d1['twperhalf'] = d1['twper']-0.5

Y = d1['twin_x']

print 'Table 2'
print "all seasons"
print 'all months'
X = sm.add_constant(d1[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'may - aug'
dt = d1[d1['month2']<9]
Y = dt['twin_x']
X = sm.add_constant(dt[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'sept, oct'
ds = d1[d1['month2']>=9]
Y = ds['twin_x']
X = sm.add_constant(ds[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'teams still in race during sept/oct'
ds['gr'] = 162-ds['tws']-ds['tls']
dsi = ds[ds['gr']>=ds['gbdl']]

Y = dsi['twin_x']
X = sm.add_constant(dsi[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

Y = dsi['twin_x']
X = sm.add_constant(dsi[['dltwin_x', 'dwper', 'dlw_gbdl', 'dll_gbdl']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'august in race'
da = d1[d1['month2']==8]
da = da[da['gbdl']<=5]
Y = da['twin_x']
X = sm.add_constant(da[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'september in race'
dsi5 = dsi[dsi['gbdl']<=5]
Y = dsi5['twin_x']
X = sm.add_constant(dsi5[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'september in race with team fixed effects'
namesList = pd.get_dummies(dsi5['team'], prefix='TX') #indicator variables
dsi5 = dsi5.join(namesList) #merge with dsi5

Y = dsi5['twin_x']
X = sm.add_constant(dsi5[['dltwin_x', 'dwper', 'TX_ATL','TX_BAL', 'TX_BOS','TX_CIN','TX_CLE','TX_COL','TX_CHW','TX_DET','TX_HOU','TX_KCR','TX_LAA','TX_LAD','TX_MIA','TX_MIL','TX_MIN','TX_NYM','TX_NYY','TX_OAK','TX_PHI','TX_PIT','TX_SDP','TX_SFG','TX_STL','TX_TBR','TX_TEX','TX_WSN']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'september in race before 2012'
db2012 = dsi5[dsi5['Season']<2012]
Y = db2012['twin_x']
X = sm.add_constant(db2012[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'september in race 2012 to 2014'
da2012 = dsi5[dsi5['Season']>=2012]
Y = da2012['twin_x']
X = sm.add_constant(da2012[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'september in race home team'
dhome = dsi5[dsi5['isthome']==1]
Y = dhome['twin_x']
X = sm.add_constant(dhome[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'september in race away team'
daway = dsi5[dsi5['isthome']==0]
Y = daway['twin_x']
X = sm.add_constant(daway[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'september in race more than 20 games remaining'
d20 = dsi5[dsi5['gr']>20]
Y = d20['twin_x']
X = sm.add_constant(d20[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'september in race more than 10 to games remaining'
d10 = dsi5[dsi5['gr']>10]
d10 = d10[d10['gr']<=20]
Y = d10['twin_x']
X = sm.add_constant(d10[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'september in race 10 or fewer games remaining'
dend = dsi5[dsi5['gr']<=10]
Y = dend['twin_x']
X = sm.add_constant(dend[['dltwin_x', 'dwper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Scoreboard watching with Average Age'
dsage = pd.merge(dsi5,dage, left_on=['team', 'Season'], right_on=['Tm', 'Season'])
dsavg = pd.merge(dsage,dage, left_on=['opp', 'Season'], right_on=['Tm', 'Season'])
dsavg['diffage'] = dsavg['AvgAge_x'] - dsavg['AvgAge_y']
dsavg['intdiffage'] = dsavg['diffage']* dsavg['dltwin_x']
dsavg['diffagebat'] = dsavg['BatAge_x'] - dsavg['BatAge_y']
dsavg['intdiffagebat'] = dsavg['diffagebat']* dsavg['dltwin_x']
dsavg['diffagepit'] = dsavg['PAge_x'] - dsavg['PAge_y']
dsavg['intdiffagepit'] = dsavg['diffagepit']* dsavg['dltwin_x']

Y = dsavg['twin_x']
X = sm.add_constant(dsavg[['dltwin_x', 'dwper', 'intdiffage']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Based on Position Age'
Y = dsavg['twin_x']
X = sm.add_constant(dsavg[['dltwin_x', 'dwper', 'intdiffagebat', 'intdiffagepit']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Logs of difference in age'
dsavg['lnintdiffage']= np.log(dsavg['AvgAge_x']/dsavg['AvgAge_y'])* dsavg['dltwin_x']
Y = dsavg['twin_x']
X = sm.add_constant(dsavg[['dltwin_x', 'dwper', 'lnintdiffage']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Logs of difference in age by position'
dsavg['lnintdiffagebat']= np.log(dsavg['BatAge_x']/dsavg['BatAge_y'])* dsavg['dltwin_x']
dsavg['lnintdiffagepit']= np.log(dsavg['PAge_x']/dsavg['PAge_y'])* dsavg['dltwin_x']
Y = dsavg['twin_x']
X = sm.add_constant(dsavg[['dltwin_x', 'dwper', 'lnintdiffagebat', 'lnintdiffagepit']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Scoreboard watching with Team Payroll'
dspay = pd.merge(dsi5,dpay, left_on=['team', 'Season'], right_on=['Team', 'Year'])
dsal = pd.merge(dspay,dpay, left_on=['opp', 'Season'], right_on=['Team', 'Year'])
dsal['diffsal'] = dsal['End Pay_x'] - dsal['End Pay_y']
dsal['intdiffsal'] = dsal['diffsal']* dsal['dltwin_x']
dsal['diffrank'] = dsal['End Rank_x'] - dsal['End Rank_y']
dsal['intdiffrank'] = dsal['diffrank']* dsal['dltwin_x']
dsal['lnintdiffsal']= np.log(dsal['End Pay_x']/dsal['End Pay_y'])* dsal['dltwin_x']
dsal['lnintdiffrank']= np.log(dsal['End Rank_x']/dsal['End Rank_y'])* dsal['dltwin_x']

print 'Interaction of scoreboard watching with team payroll'
Y = dsal['twin_x']
X = sm.add_constant(dsal[['dltwin_x', 'dwper', 'lnintdiffsal']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Interaction of scoreboard watching with team payroll rank'
Y = dsal['twin_x']
X = sm.add_constant(dsal[['dltwin_x', 'dwper', 'lnintdiffrank']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Scoreboard watching with Manager Stats'
dman = pd.merge(dsi5,dmgr, left_on=['team', 'Season'], right_on=['Team', 'Season'])
dmanager = pd.merge(dman,dmgr, left_on=['opp', 'Season'], right_on=['Team', 'Season'])
dmanager['diffplayoff'] = dmanager['Prior Playoff_x'] - dmanager['Prior Playoff_y']
dmanager['intdiffplayoff'] = dmanager['diffplayoff']* dmanager['dltwin_x']
dmanager['diffseasons'] = dmanager['Prior Seasons Managed_x'] - dmanager['Prior Seasons Managed_y']
dmanager['intdiffseasons'] = dmanager['diffseasons']* dmanager['dltwin_x']
dmanager['diffplayper'] = dmanager['playoff per season_x'] - dmanager['playoff per season_y']
dmanager['intdiffplayper'] = dmanager['diffplayper']* dmanager['dltwin_x']

print 'Interaction of scoreboard watching with playoff seasons'
Y = dmanager['twin_x']
X = sm.add_constant(dmanager[['dltwin_x', 'dwper', 'intdiffplayoff']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Interaction of scoreboard watching with seasons managed'
Y = dmanager['twin_x']
X = sm.add_constant(dmanager[['dltwin_x', 'dwper', 'intdiffseasons']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Interaction of scoreboard watching with percent of seasons in playoffs'
Y = dmanager['twin_x']
X = sm.add_constant(dmanager[['dltwin_x', 'dwper', 'intdiffplayper']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Momentum and Streaks'
dsi5['diffstreak'] = dsi5['PriorStreak'] - dsi5['opriorstreak']
dsi5 ['intdiffstreak'] = dsi5['diffstreak']* dsi5['dltwin_x']
dwstreak = dsi5[dsi5['PriorStreak'] > 0]
dlstreak = dsi5[dsi5['PriorStreak'] < 0]

print 'Interaction of scoreboard watching with Streaks'
Y = dsi5['twin_x']
X = sm.add_constant(dsi5[['dltwin_x', 'dwper', 'intdiffstreak']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Interaction of scoreboard watching with Winning Streaks'
Y = dwstreak['twin_x']
X = sm.add_constant(dwstreak[['dltwin_x', 'dwper', 'intdiffstreak']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Interaction of scoreboard watching with Losing Streaks'
Y = dlstreak['twin_x']
X = sm.add_constant(dlstreak[['dltwin_x', 'dwper', 'intdiffstreak']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

dsi5 = dsi5[dsi5['Attendance'] > 1]

dsi5['Attendance']    = dsi5['Attendance'].astype(float)
dsi5['IntAttendance'] = ((dsi5['Attendance'])/1000)
dsi5['lnAttendance']= (np.log(dsi5['Attendance']))

print 'Interaction of scoreboard watching with Attendance'
Y = dsi5['twin_x']
X = sm.add_constant(dsi5[['dltwin_x', 'dwper', 'IntAttendance']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()

print 'Interaction of scoreboard watching with Log of Attendance'
Y = dsi5['twin_x']
X = sm.add_constant(dsi5[['dltwin_x', 'dwper', 'lnAttendance']])
tempOut = sm.OLS(Y, X).fit()
print tempOut.summary()
