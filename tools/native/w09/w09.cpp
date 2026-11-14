#include <algorithm>
#include <array>
#include <cmath>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
struct Link {int grid;double weight;};
struct Grid {int ncol,nrow;double x,y,cell,nodata;std::vector<double> values;};
static std::string trim(std::string s){auto a=s.find_first_not_of(" \t\r\n");return a==std::string::npos?"":s.substr(a,s.find_last_not_of(" \t\r\n")-a+1);}
static std::map<std::string,std::string> cfgread(const fs::path&p){std::ifstream f(p);if(!f)throw std::runtime_error("missing config");std::map<std::string,std::string> c;std::string s;while(std::getline(f,s)){s=trim(s);if(s.empty()||s[0]=='#')continue;auto i=s.find('=');if(i==std::string::npos)throw std::runtime_error("bad config");c[trim(s.substr(0,i))]=trim(s.substr(i+1));}return c;}
static std::string get(const std::map<std::string,std::string>&c,const std::string&k){auto it=c.find(k);if(it==c.end()||it->second.empty())throw std::runtime_error("missing config "+k);return it->second;}
static Grid readgrid(const fs::path&p){std::ifstream f(p);if(!f)throw std::runtime_error("Missing grid "+p.string());std::map<std::string,double> h;for(int i=0;i<6;i++){std::string k;double v;if(!(f>>k>>v))throw std::runtime_error("Bad ASC header");std::transform(k.begin(),k.end(),k.begin(),[](unsigned char x){return char(std::tolower(x));});h[k]=v;}Grid g;g.ncol=int(h.at("ncols"));g.nrow=int(h.at("nrows"));g.x=h.at("xllcorner");g.y=h.at("yllcorner");g.cell=h.at("cellsize");g.nodata=h.at("nodata_value");if(g.ncol<=0||g.nrow<=0||g.ncol>10000||g.nrow>10000)throw std::runtime_error("invalid dimensions");g.values.resize(size_t(g.ncol)*g.nrow);for(double &v:g.values)if(!(f>>v))throw std::runtime_error("short grid "+p.string());return g;}
static void geometry(const Grid &g,const Grid &t){if(g.ncol!=t.ncol||g.nrow!=t.nrow||g.x!=t.x||g.y!=t.y||g.cell!=t.cell)throw std::runtime_error("grid geometry mismatch");}
static bool valid(double v,double nod){return std::isfinite(v)&&v!=nod;}
static void nearest(Grid &g){std::vector<int> source;for(int i=0;i<int(g.values.size());i++)if(valid(g.values[i],g.nodata))source.push_back(i);if(source.empty())throw std::runtime_error("no valid meteo pixel");auto orig=g.values;for(int i=0;i<int(g.values.size());i++)if(!valid(orig[i],g.nodata)){int r=i/g.ncol,c=i%g.ncol,best=-1,dist=std::numeric_limits<int>::max();for(int j:source){int dr=r-j/g.ncol,dc=c-j%g.ncol,d=dr*dr+dc*dc;if(d<dist||(d==dist&&j<best)){best=j;dist=d;}}g.values[i]=orig[best];}}
static std::map<int,std::vector<Link>> readweights(const fs::path&p,int count){std::ifstream f(p);if(!f)throw std::runtime_error("missing weights");std::string s;std::getline(f,s);if(trim(s)!="hru_id,grid_id,area_m2,weight")throw std::runtime_error("bad weights header");std::map<int,std::vector<Link>> w;while(std::getline(f,s)){std::stringstream z(s);std::string a,b,c,d;std::getline(z,a,',');std::getline(z,b,',');std::getline(z,c,',');std::getline(z,d,',');if(d.empty())throw std::runtime_error("bad weight row");int h=std::stoi(a),g=std::stoi(b);double v=std::stod(d);if(g<0||g>=count||v<=0||!std::isfinite(v))throw std::runtime_error("bad weight");w[h].push_back({g,v});}if(w.size()!=10242)throw std::runtime_error("expected 10242 HRUs");for(auto&item:w){double s=0;for(auto v:item.second)s+=v.weight;if(std::abs(s-1)>1e-10)throw std::runtime_error("weight sum !=1");}return w;}
static std::string daystr(const std::tm&tm){char a[16];std::strftime(a,sizeof a,"%Y%m%d",&tm);return a;}
static std::string expand(std::string p,const std::string&d){auto x=p.find("{date}");if(x==std::string::npos)throw std::runtime_error("missing date pattern");p.replace(x,6,d);return p;}
static void run(const fs::path &file){auto c=cfgread(file);Grid templ=readgrid(get(c,"template"));auto w=readweights(get(c,"weights"),int(templ.values.size()));fs::path outdir=get(c,"output");fs::create_directories(outdir);std::array<std::string,8> vars={"RD1","EV24","TN","TX","Q","FG","WIND","WET_RAW"};std::map<std::string,double> scale;for(auto n:vars){scale[n]=std::stod(get(c,"scale_"+n));if(!std::isfinite(scale[n])||scale[n]<=0)throw std::runtime_error("invalid scale");}
int first=std::stoi(get(c,"start_year")),last=std::stoi(get(c,"end_year"));if(first<1900||last>2100||last<first)throw std::runtime_error("invalid years");
for(int year=first;year<=last;year++){fs::path target=outdir/("met_"+std::to_string(year)+".csv"),temporary=target;temporary+=".tmp";std::ofstream f(temporary);if(!f)throw std::runtime_error("cannot write output");f<<"hru_id,date,rad_kj_m2_d,tmin_c,tmax_c,vapour_pressure_kpa,wind_m_s,rain_mm_d,etref_mm_d,wet_fraction\n"<<std::setprecision(12);std::tm day{};day.tm_year=year-1900;day.tm_mon=0;day.tm_mday=1;std::mktime(&day);int days=0;
while(day.tm_year==year-1900){auto ds=daystr(day);if(c.count("start_date")&&ds<get(c,"start_date")){day.tm_mday++;std::mktime(&day);continue;}if(c.count("end_date")&&ds>get(c,"end_date"))break;
std::array<Grid,8> grids;bool duration_any=false;for(size_t k=0;k<vars.size();k++){grids[k]=readgrid(expand(get(c,"path_"+vars[k]),ds));geometry(grids[k],templ);if(k==7){for(double x:grids[k].values)if(valid(x,grids[k].nodata))duration_any=true;if(duration_any)nearest(grids[k]);else std::fill(grids[k].values.begin(),grids[k].values.end(),0.0);}else nearest(grids[k]);for(double &x:grids[k].values)x*=scale[vars[k]];}
for(const auto&[id,links]:w){double rad=0,tn=0,tx=0,vap=0,wind=0,rain=0,etref=0,wet=0;for(const auto&lk:links){int g=lk.grid;double p=grids[0].values[g],d=grids[7].values[g],a=lk.weight;if(p<0||grids[1].values[g]<0||grids[4].values[g]<0||grids[6].values[g]<0||grids[3].values[g]<grids[2].values[g]||d<0||d>1)throw std::runtime_error("invalid meteo value on "+ds);rad+=a*grids[4].values[g];tn+=a*grids[2].values[g];tx+=a*grids[3].values[g];vap+=a*grids[5].values[g];wind+=a*grids[6].values[g];rain+=a*p;etref+=a*grids[1].values[g];wet+=a*(p==0?0:(d>0?d:0.1));}f<<id<<","<<ds.substr(0,4)<<"-"<<ds.substr(4,2)<<"-"<<ds.substr(6,2)<<","<<rad<<","<<tn<<","<<tx<<","<<vap<<","<<wind<<","<<rain<<","<<etref<<","<<wet<<"\n";}days++;day.tm_mday++;std::mktime(&day);}
f.close();if(!f)throw std::runtime_error("write failure");if(fs::exists(target))fs::remove(target);fs::rename(temporary,target);std::cout<<year<<" "<<days<<" days "<<w.size()<<" HRUs\n";}}
int main(int argc,char**argv){try{if(argc!=2){std::cerr<<"Usage: lwkm_w09_meteo.exe config.ini\n";return 2;}run(argv[1]);return 0;}catch(const std::exception&e){std::cerr<<"W09 ERROR: "<<e.what()<<"\n";return 1;}}
