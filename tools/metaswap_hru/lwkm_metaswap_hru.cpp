// LWKM MetaSWAP HRU processor, C++17. Windows x64, system DLLs only.
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
namespace fs=std::filesystem;
using A=std::array<double,9>;
const std::array<std::string,9> names={"MSW_EBS","MSW_EIC","MSW_EPD","MSW_ESP","MSW_TACT","MSW_TPOT","PSSW","PSGW","BDGETACT"};
const std::string version="LWKM-MSW-HRU-1.0.0";
void require(bool ok,const std::string&s){if(!ok)throw std::runtime_error(s);}
std::string trim(std::string s){auto a=s.find_first_not_of(" \t\r\n");return a==s.npos?"":s.substr(a,s.find_last_not_of(" \t\r\n")-a+1);}
std::vector<std::string> csv(std::string s){if(s.substr(0,3)=="\xef\xbb\xbf")s.erase(0,3);std::vector<std::string> v;std::string x;bool q=false;for(size_t i=0;i<s.size();++i){char c=s[i];if(c=='"'){if(q&&i+1<s.size()&&s[i+1]=='"'){x+=c;++i;}else q=!q;}else if(c==','&&!q){v.push_back(trim(x));x.clear();}else x+=c;}require(!q,"Unterminated CSV quote");v.push_back(trim(x));return v;}
int integer(const std::string&s){size_t p;int n=std::stoi(s,&p);require(p==s.size(),"Invalid integer: "+s);return n;}
double real(const std::string&s){size_t p;double n=std::stod(s,&p);require(p==s.size()&&std::isfinite(n),"Invalid number: "+s);return n;}
size_t col(const std::vector<std::string>&v,const std::string&s){auto i=std::find(v.begin(),v.end(),s);require(i!=v.end(),"Missing column "+s);return i-v.begin();}
std::string hashfile(const fs::path&p){
 std::ifstream f(p,std::ios::binary);require(bool(f),"Cannot hash "+p.string());
 BCRYPT_ALG_HANDLE alg=nullptr; BCRYPT_HASH_HANDLE h=nullptr;DWORD len=0,size=0;
 require(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)==0,"SHA256 provider error");
 require(BCryptGetProperty(alg,BCRYPT_OBJECT_LENGTH,(PUCHAR)&size,sizeof(size),&len,0)==0,"SHA256 property error");
 std::vector<unsigned char> obj(size),buffer(1024*1024);unsigned char digest[32];
 require(BCryptCreateHash(alg,&h,obj.data(),size,nullptr,0,0)==0,"SHA256 create error");
 while(f){f.read((char*)buffer.data(),buffer.size());auto n=f.gcount();if(n)require(BCryptHashData(h,buffer.data(),(ULONG)n,0)==0,"SHA256 update error");}
 require(f.eof(),"Hash read error "+p.string());require(BCryptFinishHash(h,digest,32,0)==0,"SHA256 finish error");
 BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(alg,0);std::ostringstream s;s<<std::hex<<std::setfill('0');for(auto b:digest)s<<std::setw(2)<<unsigned(b);return s.str();
}
std::string readtext(const fs::path&p){std::ifstream f(p,std::ios::binary);return std::string(std::istreambuf_iterator<char>(f),{});}
void writefile(const fs::path&p,const std::string&s){std::ofstream f(p,std::ios::binary|std::ios::trunc);require(bool(f),"Cannot write "+p.string());f<<s;f.close();require(bool(f),"Write failed "+p.string());}
void install(const fs::path&tmp,const fs::path&dest){require(MoveFileExW(tmp.c_str(),dest.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0,"Cannot install "+dest.string());}
struct Area{double a,x,y;};
struct Member{int id,h;double a,x,y;};
std::vector<Member> membership(const fs::path&ap,const fs::path&mp,int expected,std::map<int,double>&total){
 std::ifstream f(ap);require(bool(f),"Cannot open area_svat");std::string s;std::unordered_map<int,Area> areas;
 while(std::getline(f,s)){if(trim(s).empty()||s[0]=='*'||s[0]=='!')continue;std::istringstream in(s);std::vector<std::string> v;std::string t;while(in>>t)v.push_back(t);require(v.size()==14,"area_svat needs 14 fields");int id=integer(v[0]);Area a{real(v[1]),real(v[9]),real(v[10])};require(id>0&&a.a>0,"Invalid area/SVAT");require(areas.emplace(id,a).second,"Duplicate area SVAT");}
 std::ifstream m(mp);require(bool(m),"Cannot open SVAT-HRU mapping");std::getline(m,s);auto c=csv(s);auto si=col(c,"svat_orig"),hi=col(c,"HRU"),xi=col(c,"x"),yi=col(c,"y");std::set<int> seen;std::vector<Member> members;
 while(std::getline(m,s)){if(trim(s).empty())continue;auto v=csv(s);require(v.size()==c.size(),"Mapping column count mismatch");int id=integer(v[si]),h=integer(v[hi]);require(h>0&&seen.insert(id).second,"Invalid HRU or duplicate original SVAT");auto a=areas.find(id);require(a!=areas.end(),"SVAT not in area_svat: "+std::to_string(id));require(std::abs(real(v[xi])-a->second.x)<0.001&&std::abs(real(v[yi])-a->second.y)<0.001,"SVAT coordinate mismatch");auto z=a->second;members.push_back({id,h,z.a,z.x,z.y});total[h]+=z.a;}
 require(!members.empty(),"Empty membership");require(expected==0||int(total.size())==expected,"Expected "+std::to_string(expected)+" HRUs, found "+std::to_string(total.size()));return members;
}
struct Raster{int nc=0,nr=0;double xmin,xmax,ymin,ymax,dx,dy,nd;std::vector<double> v;};
template<class T>T get(std::ifstream&f){T x{};f.read((char*)&x,sizeof(x));require(bool(f),"Truncated IDF");return x;}
Raster idf(const fs::path&p){
 std::ifstream f(p,std::ios::binary);require(bool(f),"Cannot open IDF "+p.string());Raster r;int rec=get<int32_t>(f);require(rec==1271,"Unsupported IDF record marker (only single precision 1271): "+p.string());r.nc=get<int32_t>(f);r.nr=get<int32_t>(f);require(r.nc>0&&r.nr>0&&uint64_t(r.nc)*r.nr<=100000000,"Invalid IDF dimensions");
 r.xmin=get<float>(f);r.xmax=get<float>(f);r.ymin=get<float>(f);r.ymax=get<float>(f);get<float>(f);get<float>(f);r.nd=get<float>(f);auto ieq=get<uint8_t>(f),itb=get<uint8_t>(f);get<uint16_t>(f);require(ieq==0&&itb<=1,"Unsupported non-equidistant IDF grid");r.dx=get<float>(f);r.dy=get<float>(f);if(itb){get<float>(f);get<float>(f);}
 require(std::isfinite(r.dx)&&std::isfinite(r.dy)&&r.dx>0&&r.dy>0&&std::isfinite(r.xmin)&&std::isfinite(r.xmax)&&std::isfinite(r.ymin)&&std::isfinite(r.ymax),"Invalid IDF geometry");require(std::abs(r.xmax-r.xmin-r.nc*r.dx)<0.01&&std::abs(r.ymax-r.ymin-r.nr*r.dy)<0.01,"IDF extent/spacing mismatch");
 r.v.resize(size_t(r.nc)*r.nr);std::vector<float> data(r.v.size());f.read((char*)data.data(),data.size()*4);require(bool(f),"Truncated IDF raster");for(size_t i=0;i<data.size();++i)r.v[i]=data[i];
 if(f.peek()!=EOF){int records=get<int32_t>(f),words=get<int32_t>(f);require(records==1&&words>=0&&words<1000000,"Invalid IDF footer");std::vector<unsigned char>b(size_t(words)*4);f.read((char*)b.data(),b.size());require(bool(f)&&f.peek()==EOF,"Invalid IDF footer length");for(auto x:b)require(x==0||x==9||x==10||x==13||(x>=32&&x<=126),"Non-text IDF footer");}return r;
}
size_t position(const Raster&r,const Member&m){double cx=(m.x-r.xmin)/r.dx,ry=(r.ymax-m.y)/r.dy;require(std::isfinite(cx)&&std::isfinite(ry)&&cx>=0&&ry>=0&&cx<r.nc&&ry<r.nr,"SVAT outside IDF extent: "+std::to_string(m.id));int c=int(std::floor(cx)),row=int(std::floor(ry));require(std::abs(cx-c-0.5)<0.00001&&std::abs(ry-row-0.5)<0.00001,"SVAT not at IDF cell centre: "+std::to_string(m.id));return size_t(row)*r.nc+c;}
int monthdays(int y,int m){const int d[]={0,31,28,31,30,31,30,31,31,30,31,30,31};return d[m]+(m==2&&(y%4==0&&(y%100!=0||y%400==0)));}
struct Period{std::array<fs::path,9> path;std::array<bool,9> has{};int y,m,d,days;};
std::map<std::string,Period> sources(const fs::path&p,const fs::path&root){std::ifstream f(p);require(bool(f),"Cannot open sources.csv");std::string s;std::getline(f,s);require(csv(s)==std::vector<std::string>({"date","variable","relative_path"}),"Unexpected source columns");std::map<std::string,Period> all;
 while(std::getline(f,s)){if(trim(s).empty())continue;auto v=csv(s);require(v.size()==3&&v[0].size()==8,"Invalid source row");auto it=std::find(names.begin(),names.end(),v[1]);require(it!=names.end(),"Unknown source variable");auto j=it-names.begin();int y=integer(v[0].substr(0,4)),m=integer(v[0].substr(4,2)),d=integer(v[0].substr(6,2));require(y>=1900&&y<=2200&&m>=1&&m<=12,"Invalid date");require(d==10||d==20||d==monthdays(y,m),"Source date is not a decade end");auto &a=all[v[0]];require(!a.has[j],"Duplicate source "+v[0]+" "+v[1]);fs::path rel=fs::u8path(v[2]);require(!rel.is_absolute()&&!rel.has_root_name(),"Source path must be relative");for(auto&part:rel)require(part!="..","Source path traversal");a.path[j]=root/rel;a.has[j]=true;a.y=y;a.m=m;a.d=d;a.days=d<=20?10:d-20;}
 require(!all.empty(),"No periods");std::string previous;
 for(auto &[date,pd]:all){for(int j=0;j<9;++j)require(pd.has[j],"Missing variable for "+date);if(!previous.empty()){auto &pr=all.at(previous);int ny=pr.y,nm=pr.m,nd=pr.d==10?20:pr.d==20?monthdays(ny,nm):10;if(pr.d==monthdays(pr.y,pr.m)){if(++nm==13){nm=1;++ny;}}require(pd.y==ny&&pd.m==nm&&pd.d==nd,"Gap in decade inventory at "+date);}previous=date;}return all;
}
struct Lock{HANDLE h;Lock(const fs::path&p){h=CreateFileW(p.c_str(),GENERIC_READ|GENERIC_WRITE,0,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL|FILE_FLAG_DELETE_ON_CLOSE,nullptr);require(h!=INVALID_HANDLE_VALUE,"Output locked by another process: "+p.string());}~Lock(){CloseHandle(h);}};
int main(int argc,char**argv){fs::path output;try{
 require(argc==7||argc==8,"Usage: lwkm_metaswap_hru.exe area_svat.inp mapping.csv sources.csv source_root output_directory expected_hrus_or_0 [release_binding_sha256]");
 output=fs::u8path(argv[5]);fs::create_directories(output);Lock lock(output/".running");std::ofstream log(output/"run.log",std::ios::app);require(bool(log),"Cannot open log");auto report=[&](std::string s){std::cout<<s<<std::endl;log<<s<<std::endl;};report(version+" START");
 std::map<int,double> total;auto members=membership(fs::u8path(argv[1]),fs::u8path(argv[2]),integer(argv[6]),total);auto periods=sources(fs::u8path(argv[3]),fs::u8path(argv[4]));report("SVATs="+std::to_string(members.size())+" HRUs="+std::to_string(total.size())+" decades="+std::to_string(periods.size()));
 wchar_t exe[32768];DWORD length=GetModuleFileNameW(nullptr,exe,32768);require(length>0&&length<32768,"Cannot identify executable");
 std::string releaseBinding=argc==8?argv[7]:"";
 require(releaseBinding.empty() || (releaseBinding.size()==64 && std::all_of(releaseBinding.begin(),releaseBinding.end(),[](unsigned char ch){return (ch>='0'&&ch<='9')||(ch>='a'&&ch<='f')||(ch>='A'&&ch<='F');})),"Invalid release SHA256");
 std::string base=version+"\nrelease_binding_sha256="+releaseBinding+"\nrelease_identity_status=DECLARED_NOT_SOURCE_VERIFIED\nexe="+hashfile(fs::path(exe))+"\narea="+hashfile(fs::u8path(argv[1]))+"\nmapping="+hashfile(fs::u8path(argv[2]))+"\nsources="+hashfile(fs::u8path(argv[3]))+"\nunits=m3/m2_per_decade;factor=1000;sign=source;missing=blank_strict_support\n";
 writefile(output/"run_identity.txt",base);
 std::ostringstream support;support<<"hru_id,svats,area_m2\n"<<std::setprecision(15);std::map<int,int> counts;for(auto&m:members)++counts[m.h];for(auto &[h,a]:total)support<<h<<","<<counts[h]<<","<<a<<"\n";writefile(output/"hru_support.csv",support.str());
 size_t done=0,skipped=0;uint64_t incomplete=0;
 for(auto &[date,p]:periods){report("["+std::to_string(done+skipped+1)+"/"+std::to_string(periods.size())+"] "+date+" checking sources");std::string identity=base+"date="+date+"\n";std::array<uintmax_t,9> sizes;std::array<fs::file_time_type,9> times;
 for(int j=0;j<9;++j){require(fs::is_regular_file(p.path[j]),"Missing source "+p.path[j].string());sizes[j]=fs::file_size(p.path[j]);times[j]=fs::last_write_time(p.path[j]);identity+=names[j]+","+p.path[j].generic_u8string()+","+std::to_string(sizes[j])+","+hashfile(p.path[j])+"\n";}
 fs::path target=output/(date+".csv"),marker=output/(date+".sha256");
 if(fs::exists(target)&&fs::exists(marker)){fs::path qp=output/(date+"_qc.csv");std::string expected=identity+"output="+hashfile(target)+"\n";if(fs::exists(qp))expected+="qc="+hashfile(qp)+"\n";if(fs::exists(qp)&&readtext(marker)==expected){++skipped;report(date+" SKIP verified");continue;}}
 std::map<int,A> sums,covered;std::map<int,std::array<int,9>> missing;std::array<uint64_t,9> positive{},negative{};
 for(int j=0;j<9;++j){Raster r=idf(p.path[j]);for(auto &m:members){double z=r.v[position(r,m)];if(!std::isfinite(z)||z==r.nd){++missing[m.h][j];continue;}double q=z*1000*m.a;require(std::isfinite(q),"Nonfinite weighted value");sums[m.h][j]+=q;covered[m.h][j]+=m.a;if(z>0)++positive[j];if(z<0)++negative[j];}}
 for(int j=0;j<9;++j)require(sizes[j]==fs::file_size(p.path[j])&&times[j]==fs::last_write_time(p.path[j]),"Source changed during processing");
 fs::path tmp=target;tmp+=".partial";std::ofstream f(tmp,std::ios::binary);require(bool(f),"Cannot create output");f<<"hru_id,days,complete";for(auto &n:names)f<<","<<n;f<<",E_SOIL_POND,E_INTERCEPTION_SPRINKLING,T_ACTUAL,ET_ACTUAL,IRR_TOTAL,BDGETACT_MINUS_ET";for(auto &n:names)f<<",coverage_"<<n;f<<"\n"<<std::setprecision(10);
 uint64_t bad=0;for(auto &[h,a]:total){A v;std::array<bool,9> ok;bool full=true;for(int j=0;j<9;++j){ok[j]=missing[h][j]==0;full=full&&ok[j];v[j]=sums[h][j]/a;}if(!full)++bad;f<<h<<","<<p.days<<","<<int(full);for(int j=0;j<9;++j){f<<",";if(ok[j])f<<v[j];}auto emit=[&](bool valid,double z){f<<",";if(valid)f<<z;};bool e=ok[0]&&ok[2],ic=ok[1]&&ok[3],et=e&&ic&&ok[4];emit(e,v[0]+v[2]);emit(ic,v[1]+v[3]);emit(ok[4],v[4]);double etv=v[0]+v[1]+v[2]+v[3]+v[4];emit(et,etv);emit(ok[6]&&ok[7],v[6]+v[7]);emit(et&&ok[8],v[8]-etv);for(int j=0;j<9;++j)f<<","<<covered[h][j]/a;f<<"\n";}
 f.close();require(bool(f),"Output write error");install(tmp,target);
 std::ostringstream qc;qc<<"variable,positive_svat_values,negative_svat_values\n";for(int j=0;j<9;++j)qc<<names[j]<<","<<positive[j]<<","<<negative[j]<<"\n";writefile(output/(date+"_qc.csv"),qc.str());
 writefile(marker.string()+".partial",identity+"output="+hashfile(target)+"\nqc="+hashfile(output/(date+"_qc.csv"))+"\n");install(marker.string()+".partial",marker);++done;incomplete+=bad;report(date+" DONE incomplete_HRUs="+std::to_string(bad));
 }
 report("FINISHED new="+std::to_string(done)+" verified_existing="+std::to_string(skipped)+" new_incomplete_HRU_decades="+std::to_string(incomplete));report("OUTPUT "+fs::absolute(output).string());return 0;
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<std::endl;if(!output.empty()){std::ofstream log(output/"run.log",std::ios::app);log<<"ERROR: "<<e.what()<<std::endl;}return 1;}}
