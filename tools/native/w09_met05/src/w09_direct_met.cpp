#include <algorithm>
#include <array>
#include <cmath>
#include <cctype>
#include <ctime>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <locale>
#include <map>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
struct Link {int pix;double w;};
struct Grid {int nc,nr;double x,y,cell,nodata;std::vector<double> v;};
struct Pt {int r,c,id;};
std::string trim(std::string s){auto a=s.find_first_not_of(" \r\n\t");return a==s.npos?"":s.substr(a,s.find_last_not_of(" \r\n\t")-a+1);}
std::map<std::string,std::string> config(const fs::path&p){std::ifstream f(p);if(!f)throw std::runtime_error("Config missing: "+p.string());std::map<std::string,std::string> m;std::string s;while(std::getline(f,s)){s=trim(s);if(s.empty()||s[0]=='#')continue;auto a=s.find('=');if(a==s.npos)throw std::runtime_error("Invalid config");m[trim(s.substr(0,a))]=trim(s.substr(a+1));}return m;}
std::string required(const std::map<std::string,std::string>&m,const std::string&k){auto it=m.find(k);if(it==m.end()||it->second.empty())throw std::runtime_error("Config missing "+k);return it->second;}
fs::path resolve(const fs::path&cfg,const std::string&s){fs::path p(s);return p.is_absolute()?p:cfg.parent_path()/p;}
Grid gridread(const fs::path&p){std::ifstream f(p);if(!f)throw std::runtime_error("Grid missing "+p.string());std::map<std::string,double> m;for(int i=0;i<6;i++){std::string k;double d;if(!(f>>k>>d))throw std::runtime_error("Invalid ASC header "+p.string());for(auto &ch:k)ch=char(std::tolower((unsigned char)ch));m[k]=d;}
 Grid g;g.nc=int(m.at("ncols"));g.nr=int(m.at("nrows"));g.cell=m.at("cellsize");g.nodata=m.at("nodata_value");g.x=m.count("xllcorner")?m.at("xllcorner"):m.at("xllcenter")-g.cell/2;g.y=m.count("yllcorner")?m.at("yllcorner"):m.at("yllcenter")-g.cell/2;
 if(g.nc<=0||g.nr<=0||g.nc>10000||g.nr>10000||g.cell<=0)throw std::runtime_error("Invalid grid geometry");g.v.resize(size_t(g.nc)*g.nr);for(auto &x:g.v)if(!(f>>x))throw std::runtime_error("Grid truncated "+p.string());return g;}
void match(const Grid&a,const Grid&b){if(a.nc!=b.nc||a.nr!=b.nr||a.x!=b.x||a.y!=b.y||a.cell!=b.cell)throw std::runtime_error("Grid geometry mismatch");}
bool valid(double d,double nv){return std::isfinite(d)&&d!=nv;}
std::map<int,std::vector<Link>> weights(const fs::path&p,int npix,std::vector<int>&needed){std::ifstream f(p);if(!f)throw std::runtime_error("Weights missing");std::string s;if(!std::getline(f,s)||trim(s)!="hru_id,grid_id,area_m2,weight")throw std::runtime_error("Weights header mismatch");std::map<int,std::vector<Link>> w;std::vector<unsigned char> used(npix);int line=1;while(std::getline(f,s)){++line;if(trim(s).empty())continue;std::istringstream z(s);std::string a,b,c,d;std::getline(z,a,',');std::getline(z,b,',');std::getline(z,c,',');std::getline(z,d,',');if(d.empty())throw std::runtime_error("Weight cols at "+std::to_string(line));int id=std::stoi(a),pix=std::stoi(b);double weight=std::stod(d);if(id<1||pix<0||pix>=npix||!std::isfinite(weight)||weight<0)throw std::runtime_error("Invalid weight at "+std::to_string(line));if(weight==0)continue;w[id].push_back({pix,weight});used[pix]=1;}
 for(const auto &[i,links]:w){double sum=0;for(auto &lk:links)sum+=lk.w;if(links.empty()||std::abs(sum-1)>1e-9)throw std::runtime_error("HRU weight sum != 1 HRU="+std::to_string(i)+" sum="+std::to_string(sum));}
 if(w.empty())throw std::runtime_error("No HRU weights");
 for(int i=0;i<npix;i++)if(used[i])needed.push_back(i);return w;}
// Exact Euclidean nearest donor; tie resolves to lowest row-major raster index.
struct Kd {std::vector<Pt> pts;struct Node{Pt p;int left=-1,right=-1,axis;};std::vector<Node> nodes;int root=-1;
 int build(int a,int b,int depth){if(a>=b)return -1;int axis=depth%2,mid=(a+b)/2;auto comp=[axis](const Pt&a,const Pt&b){int va=axis?a.c:a.r,vb=axis?b.c:b.r;return va==vb?a.id<b.id:va<vb;};std::nth_element(pts.begin()+a,pts.begin()+mid,pts.begin()+b,comp);int n=int(nodes.size());nodes.push_back({pts[mid],-1,-1,axis});nodes[n].left=build(a,mid,depth+1);nodes[n].right=build(mid+1,b,depth+1);return n;}
 explicit Kd(const Grid&g){for(int i=0;i<int(g.v.size());i++)if(valid(g.v[i],g.nodata))pts.push_back({i/g.nc,i%g.nc,i});if(pts.empty())throw std::runtime_error("No valid weather cells");nodes.reserve(pts.size());root=build(0,int(pts.size()),0);}
 void search(int node,int r,int c,long long&best,int&id)const{if(node<0)return;auto &n=nodes[node];long long dr=static_cast<long long>(r)-n.p.r,dc=static_cast<long long>(c)-n.p.c,d=dr*dr+dc*dc;if(d<best||(d==best&&n.p.id<id)){best=d;id=n.p.id;}long long delta=n.axis?dc:dr;int near=delta<0?n.left:n.right,far=delta<0?n.right:n.left;search(near,r,c,best,id);if(delta*delta<=best)search(far,r,c,best,id);}
 int closest(int pix,int cols)const{int id=std::numeric_limits<int>::max();long long best=std::numeric_limits<long long>::max();search(root,pix/cols,pix%cols,best,id);return id;}
};
std::string expand(std::string s,const std::string&date){auto p=s.find("{date}");if(p==s.npos)throw std::runtime_error("Missing {date} pattern");s.replace(p,6,date);return s;}
std::string date(int yr,int day){std::tm t{};t.tm_year=yr-1900;t.tm_mon=0;t.tm_mday=day;t.tm_isdst=-1;std::mktime(&t);char c[20];std::strftime(c,sizeof(c),"%Y%m%d",&t);return c;}
int ndays(int yr){return yr%400==0||(yr%4==0&&yr%100!=0)?366:365;}
std::string filemet(int id){std::ostringstream ss;ss<<"HRU_"<<std::setw(5)<<std::setfill('0')<<id<<".met";return ss.str();}
void run(const fs::path&cp){auto cfg=config(cp);Grid ref=gridread(resolve(cp,required(cfg,"template")));std::vector<int> needed;auto w=weights(resolve(cp,required(cfg,"weights")),int(ref.v.size()),needed);
 fs::path target=resolve(cp,required(cfg,"output_met"));if(fs::exists(target))throw std::runtime_error("Output already exists: "+target.string());fs::path part=target;part+=".partial";if(fs::exists(part))throw std::runtime_error("Partial output exists: "+part.string());fs::create_directories(part);
 std::array<std::string,8> names={"RD1","EV24","TN","TX","Q","FG","WIND","WET_RAW"};std::array<double,8> scale;for(int i=0;i<8;i++){scale[i]=std::stod(required(cfg,"scale_"+names[i]));if(!std::isfinite(scale[i])||scale[i]<=0)throw std::runtime_error("Invalid scale");}
 int first=std::stoi(required(cfg,"start_year")),last=std::stoi(required(cfg,"end_year"));if(first<1900||last>2100||last<first)throw std::runtime_error("Invalid years");
 std::ofstream log(part/"PERFORMANCE.csv");log<<"year,days,ascii_seconds,nearest_seconds,aggregate_seconds,write_seconds,nearest_queries\n";
 for(int yr=first;yr<=last;yr++){std::map<int,std::string> lines;for(const auto &[id,links]:w)lines[id].reserve(365*100);double io=0,nn=0,agg=0,write=0;long long queries=0;
 for(int day=1;day<=ndays(yr);day++){auto ds=date(yr,day);if(cfg.count("start_date")&&ds<cfg.at("start_date"))continue;if(cfg.count("end_date")&&ds>cfg.at("end_date"))continue;
 std::array<std::vector<double>,8> vals;
 for(int k=0;k<8;k++){auto t=Clock::now();Grid g=gridread(resolve(cp,expand(required(cfg,"path_"+names[k]),ds)));match(ref,g);io+=std::chrono::duration<double>(Clock::now()-t).count();t=Clock::now();
 if(k==7){bool any=false;for(auto x:g.v)if(valid(x,g.nodata)){any=true;break;}if(!any){for(int pix:needed)g.v[pix]=0;}}
 bool requires=false;for(int pix:needed)if(!valid(g.v[pix],g.nodata)){requires=true;break;}
 if(requires){Kd tree(g);for(int pix:needed)if(!valid(g.v[pix],g.nodata)){g.v[pix]=g.v[tree.closest(pix,g.nc)];queries++;}}
 vals[k].reserve(needed.size()); // use direct grid indexing for weighted aggregation
 // store full raster; only a subset is accessed
 vals[k]=std::move(g.v);nn+=std::chrono::duration<double>(Clock::now()-t).count();}
 auto t=Clock::now();int m=std::stoi(ds.substr(4,2)),d=std::stoi(ds.substr(6,2));for(const auto &[id,links]:w){
 std::array<double,8> v{};for(auto lk:w[id]){int pix=lk.pix;double p=vals[0][pix]*scale[0],wet=vals[7][pix]*scale[7];if(p<0||vals[1][pix]*scale[1]<0||vals[4][pix]*scale[4]<0||vals[6][pix]*scale[6]<0||vals[3][pix]*scale[3]<vals[2][pix]*scale[2]||wet<0||wet>1)throw std::runtime_error("Invalid meteorological value "+ds+" HRU "+std::to_string(id));for(int k=0;k<8;k++)v[k]+=lk.w*vals[k][pix]*scale[k];}
 // Preserve original W09 WET rule: weighted (rain pixel > 0 ? max(wet,0.1 if zero) : 0).
 double wet=0;for(auto lk:w[id]){double p=vals[0][lk.pix]*scale[0],raw=vals[7][lk.pix]*scale[7];wet+=lk.w*(p==0?0:(raw>0?raw:0.1));}
 std::ostringstream record;record.imbue(std::locale::classic());record<<std::setprecision(12)<<"'"<<id<<"' "<<d<<" "<<m<<" "<<yr<<" "<<v[4]<<" "<<v[2]<<" "<<v[3]<<" "<<v[5]<<" "<<v[6]<<" "<<v[0]<<" "<<v[1]<<" "<<wet<<"\n";lines[id]+=record.str();}
 agg+=std::chrono::duration<double>(Clock::now()-t).count();}
 auto t=Clock::now();for(int id=1;id<=10242;id++){std::ofstream out(part/filemet(id),std::ios::binary|(yr==first?std::ios::out:std::ios::app));if(!out)throw std::runtime_error("Cannot open output");if(yr==first)out<<"Station DD MM YYYY RAD Tmin Tmax HUM WIND RAIN ETref WET\n";out<<lines[id];if(!out)throw std::runtime_error("Write failed");}write+=std::chrono::duration<double>(Clock::now()-t).count();log<<yr<<","<<ndays(yr)<<","<<io<<","<<nn<<","<<agg<<","<<write<<","<<queries<<"\n";log.flush();std::cout<<"YEAR "<<yr<<" ascii="<<io<<" nearest="<<nn<<" aggregate="<<agg<<" write="<<write<<" nearest_queries="<<queries<<"\n";}
 std::ofstream manifest(part/"MANIFEST.txt");manifest<<"LWKM MET03 direct ASCII to HRU MET; NOT SWAP-qualified. HRUs="<<w.size()<<" Years="<<first<<".."<<last<<"\n";manifest.close();log.close();fs::rename(part,target);
}
int main(int argc,char**argv){try{if(argc!=2)throw std::runtime_error("Usage: w09_direct_met config.ini");run(argv[1]);return 0;}catch(const std::exception&e){std::cerr<<"W09 MET03 ERROR: "<<e.what()<<"\n";return 2;}}