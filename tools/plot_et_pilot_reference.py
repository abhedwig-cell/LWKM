"""Optional scientific figure from saved ET pilot diagnostics (requires matplotlib)."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def plot(results,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    results,output=Path(results),Path(output)
    annual=pd.read_csv(results/'annual-hru.csv')
    profiles=['arable_irrigated','arable_rainfed','grass_irrigated','grass_rainfed','maize_irrigated','maize_rainfed','nature_rainfed']
    labels=['Bouwland beregend','Bouwland onberegend','Gras beregend','Gras onberegend','Mais beregend','Mais onberegend','Natuur onberegend']
    annual_mean=annual.pivot_table(index='profile',columns='year',values='ET').loc[profiles]
    mean=pd.read_csv(results/'profile-mean-hru-year.csv').set_index('profile').loc[profiles]
    management=pd.read_csv(results/'management-diagnostics.csv').merge(pd.read_csv(results/'member-irrigation-support.csv')[['hru_id','irrigated_member_area_fraction']],on='hru_id')
    management['order']=management.profile.map(dict(zip(profiles,range(7))));management=management.sort_values(['order','hru_id'])
    fig,axes=plt.subplots(3,1,figsize=(12,13),gridspec_kw={'height_ratios':[1.15,1,1.15]})
    fig.subplots_adjust(left=.20,right=.90,top=.92,bottom=.17,hspace=.48)
    im=axes[0].imshow(annual_mean,aspect='auto',cmap='viridis',vmin=300,vmax=700)
    axes[0].set_yticks(range(7),labels);positions=[i for i,y in enumerate(annual_mean.columns) if y%10==0 or y==annual_mean.columns[-1]]
    axes[0].set_xticks(positions,annual_mean.columns[positions]);axes[0].set_title('A. Jaarlijkse ET, gemiddelde van de drie HRU’s per profiel',loc='left',pad=12)
    fig.colorbar(im,ax=axes[0],label='ET (mm/jaar)',fraction=.025,pad=.03)
    bottom=np.zeros(7)
    for name,label,color in [('T','Transpiratie','#1b9e77'),('E_SOIL','Bodem + plas','#d8a251'),('E_IC','Interceptie + beregeningsverlies','#467aac')]:
        axes[1].barh(range(7),mean[name],left=bottom,label=label,color=color,height=.65);bottom+=mean[name].to_numpy()
    axes[1].set_yticks(range(7),labels);axes[1].invert_yaxis();axes[1].set_xlabel('Gemiddelde over HRU’s en jaren 1970 tot en met 2024 (mm/jaar)')
    axes[1].set_title('B. Verdeling van de actuele ET',loc='left',pad=12);axes[1].legend(loc='upper center',bbox_to_anchor=(.5,-.22),ncol=3,frameon=False,fontsize=9)
    x=np.arange(len(management));axes[2].bar(x,management.mean_irrigation_mm_y,color='#64868e',width=.7)
    axes[2].set_xticks(x,management.hru_id,rotation=60);axes[2].set_ylabel('Gift (mm/jaar)');axes[2].set_xlabel('HRU, gerangschikt naar dezelfde profielen als boven')
    ax2=axes[2].twinx();ax2.plot(x,100*management.irrigated_member_area_fraction,'o',color='#aa4b39',markersize=4)
    ax2.set_ylim(0,105);ax2.set_ylabel('Statisch beregend ledenoppervlak (%)',color='#aa4b39')
    axes[2].set_title('C. Gemiddelde gift (balk) en statisch beregend ledenoppervlak (punt)',loc='left',pad=12)
    fig.suptitle('Ontvangen MetaSWAP-referenties: 21 pilot-HRU’s',fontsize=17,x=.20,ha='left')
    fig.text(.20,.04,'Diagnostische tekenhypothese: ET-bronnen -1, giften +1; bronwaarden behouden.\nProfielgemiddelden hebben gelijke HRU-gewichten. Dit zijn geen landelijke gemiddelden.\nStatische beregeningslabels bewijzen geen historisch beheer. Geen SWAP-kalibratie uitgevoerd.',fontsize=9,linespacing=1.6)
    fig.savefig(output,dpi=170,facecolor='white');plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();plot(a.results,a.output)
