// Compact, streaming acceptance of LWKM-MSW-HRU-1.0.0 products.
// Windows: cl /std:c++17 /EHsc /O2 /MT accept_metaswap.cpp bcrypt.lib
// Linux qualification: g++ -std=c++17 -O2 accept_metaswap.cpp -lcrypto
#define NOMINMAX
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#else
#include <openssl/evp.h>
#endif
namespace fs=std::filesystem;
using V=std::array<double,15>;
const std::array<std::string,15> names={"MSW_EBS","MSW_EIC","MSW_EPD","MSW_ESP","MSW_TACT","MSW_TPOT","PSSW","PSGW","BDGETACT","E_SOIL_POND","E_INTERCEPTION_SPRINKLING","T_ACTUAL","ET_ACTUAL","IRR_TOTAL","BDGETACT_MINUS_ET"};
void check(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
std::string text(const fs::path&p){std::ifstream f(p,std::ios::binary);check(bool(f),"Missing file: "+p.string());return {std::istreambuf_iterator<char>(f),{}};}
std::vector<std::string> csv(std::string s){std::vector<std::string> v;std::string z;bool q=false;for(size_t i=0;i<s.size();++i){char c=s[i];if(c=='"'){if(q&&i+1<s.size()&&s[i+1]=='"'){z+=c;++i;}else q=!q;}else if(c==','&&!q){v.push_back(z);z.clear();}else if(c!='\r')z+=c;}check(!q,"Unterminated CSV quote");v.push_back(z);return v;}
int integer(const std::string&s){size_t p;int v=std::stoi(s,&p);check(p==s.size(),"Invalid integer");return v;}
double real(const std::string&s){size_t p;double v=std::stod(s,&p);check(p==s.size()&&std::isfinite(v),"Invalid/nonfinite number");return v;}
bool digest(const std::string&s){return s.size()==64&&s.find_first_not_of("0123456789abcdef")==std::string::npos;}
std::string hash(const fs::path&p){std::ifstream f(p,std::ios::binary);check(bool(f),"Cannot hash: "+p.string());std::vector<unsigned char> buf(1<<20);unsigned char out[32];
#ifdef _WIN32
 BCRYPT_ALG_HANDLE a;BCRYPT_HASH_HANDLE h;DWORD n,size;
 check(BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0)==0,"SHA provider");
 check(BCryptGetProperty(a,BCRYPT_OBJECT_LENGTH,(PUCHAR)&size,sizeof(size),&n,0)==0,"SHA property");std::vector<unsigned char> obj(size);
 check(BCryptCreateHash(a,&h,obj.data(),size,nullptr,0,0)==0,"SHA create");
 while(f){f.read((char*)buf.data(),buf.size());if(f.gcount())check(BCryptHashData(h,buf.data(),(ULONG)f.gcount(),0)==0,"SHA update");}check(f.eof(),"SHA read");
 check(BCryptFinishHash(h,out,32,0)==0,"SHA finish");BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(a,0);
#else
 EVP_MD_CTX *h=EVP_MD_CTX_new();check(h&&EVP_DigestInit_ex(h,EVP_sha256(),nullptr)==1,"SHA init");
 while(f){f.read((char*)buf.data(),buf.size());if(f.gcount())check(EVP_DigestUpdate(h,buf.data(),f.gcount())==1,"SHA update");}check(f.eof(),"SHA read");unsigned int n;check(EVP_DigestFinal_ex(h,out,&n)==1&&n==32,"SHA finish");EVP_MD_CTX_free(h);
#endif
 std::ostringstream s;s<<std::hex<<std::setfill('0');for(auto b:out)s<<std::setw(2)<<unsigned(b);return s.str();}
std::map<std::string,std::string> kv(const std::string&s){std::istringstream f(s);std::string line;std::map<std::string,std::string> m;while(std::getline(f,line)){if(!line.empty()&&line.back()=='\r')line.pop_back();auto n=line.find('=');if(n!=line.npos){check(m.emplace(line.substr(0,n),line.substr(n+1)).second,"Duplicate identity key");}}return m;}
int monthdays(int y,int m){const int d[]={0,31,28,31,30,31,30,31,31,30,31,30,31};return d[m]+(m==2&&(y%4==0&&(y%100!=0||y%400==0)));}
std::string next(std::string s){int y=integer(s.substr(0,4)),m=integer(s.substr(4,2)),d=integer(s.substr(6,2));if(d==10)d=20;else if(d==20)d=monthdays(y,m);else{d=10;if(++m==13){m=1;++y;}}std::ostringstream o;o<<y<<std::setfill('0')<<std::setw(2)<<m<<std::setw(2)<<d;return o.str();}
struct Sum{V value{},valid_area{};std::array<int,15> valid{};int periods=0;void add(const V&v,const std::array<bool,15>&ok,double area=1){++periods;for(int j=0;j<15;++j)if(ok[j]){value[j]+=v[j]*area;valid_area[j]+=area;++valid[j];}}};
void header(std::ostream&o,const std::string&prefix){o<<prefix;for(auto &n:names)o<<","<<n;for(auto &n:names)o<<",valid_"<<n;o<<"\n";}
void emit(std::ostream&o,const std::string&prefix,const Sum&s,bool weighted,double scale=1){o<<prefix;for(int j=0;j<15;++j){o<<",";if(s.valid[j]==s.periods)o<<(weighted?s.value[j]/s.valid_area[j]*scale:s.value[j]);}for(auto n:s.valid)o<<","<<n;o<<"\n";}
int main(int argc,char**argv){try{
 check(argc==5||argc==6,"Usage: accept_metaswap.exe OUTPUT SOURCES_CSV COMPACT_DIRECTORY EXPECTED_HRUS [--recorded-sources-only]");
 const fs::path root=fs::u8path(argv[1]),cfg=fs::u8path(argv[2]),dest=fs::u8path(argv[3]);int nh=integer(argv[4]);check(nh>0,"Invalid population");
 bool verify=argc==5;check(verify||std::string(argv[5])=="--recorded-sources-only","Unknown option");
 check(fs::absolute(root)!=fs::absolute(dest),"Output and compact directory must differ");fs::create_directories(dest);
 // Remove previous success marker before inspecting a new candidate.
 fs::remove(dest/"COMPLETE.txt");fs::remove(dest/"SHA256SUMS.txt");
 auto base=text(root/"run_identity.txt");check(base.rfind("LWKM-MSW-HRU-1.0.0",0)==0,"Unsupported producer");auto bk=kv(base);
 check(bk["sources"]==hash(cfg),"Configured inventory hash mismatch");for(auto k:{"exe","area","mapping","sources"})check(digest(bk[k]),"Missing/invalid producer identity");
 check(bk["units"]=="m3/m2_per_decade;factor=1000;sign=source;missing=blank_strict_support","Unknown amount/sign/missing contract");
 std::map<std::string,std::map<std::string,std::string>> periods;std::istringstream input(text(cfg));std::string s;std::getline(input,s);check(csv(s)==std::vector<std::string>({"date","variable","relative_path"}),"Invalid configuration header");
 while(std::getline(input,s)){if(s.empty())continue;auto r=csv(s);check(r.size()==3&&r[0].size()==8,"Invalid source binding");check(std::find(names.begin(),names.begin()+9,r[1])!=names.begin()+9,"Unknown variable");check(periods[r[0]].emplace(r[1],r[2]).second,"Duplicate variable/period");}
 check(!periods.empty(),"Empty configured period");std::string prev;
 for(auto &[d,p]:periods){int y=integer(d.substr(0,4)),m=integer(d.substr(4,2)),z=integer(d.substr(6,2));check(y>=1900&&y<=2200&&m>=1&&m<=12,"Invalid year/month");check(z==10||z==20||z==monthdays(y,m),"Invalid decade end");check(p.size()==9,"Missing configured variables");check(prev.empty()||next(prev)==d,"Configured decade gap");prev=d;}
 std::vector<double> area(nh+1);std::vector<int> support(nh+1);std::istringstream sup(text(root/"hru_support.csv"));std::getline(sup,s);check(csv(s)==std::vector<std::string>({"hru_id","svats","area_m2"}),"Invalid support header");
 while(std::getline(sup,s)){auto r=csv(s);check(r.size()==3,"Invalid support");int h=integer(r[0]);check(h>=1&&h<=nh&&!support[h],"Duplicate/unknown support HRU");support[h]=integer(r[1]);area[h]=real(r[2]);check(support[h]>0&&area[h]>0,"Invalid support area/count");}
 for(int h=1;h<=nh;++h)check(support[h]>0,"Missing support HRU");
 std::ofstream annual(dest/"annual_hru.csv"),seasonal(dest/"seasonal_population.csv"),decades(dest/"decadal_population.csv"),lineage(dest/"source_hashes.csv"),quality(dest/"decadal_qa.csv");
 for(auto f:{&annual,&seasonal,&decades,&lineage,&quality}){check(bool(*f),"Cannot write compact products");*f<<std::setprecision(12);}
 header(annual,"hru_id,year,configured_decades,full_calendar_year");header(seasonal,"year,season,configured_decades,expected_hru_decades");header(decades,"decade_end,days,expected_hrus");
 lineage<<"decade_end,variable,source_sha256,size_bytes,rehash_verified\n";
 quality<<"decade_end,complete_hrus,incomplete_hrus,et_comparison_hrus,residual_area_mean_mm,max_abs_residual_mm,residual_over_tolerance_hrus\n";
 std::vector<Sum> years(nh+1);std::map<std::string,Sum> seasons;int year=-1,year_periods=0;size_t missing=0,compared=0,over=0;double maxres=0;
 auto flush=[&](){if(year<0)return;for(int h=1;h<=nh;++h)emit(annual,std::to_string(h)+","+std::to_string(year)+","+std::to_string(year_periods)+","+std::to_string(year_periods==36),years[h],false);years.assign(nh+1,Sum{});year_periods=0;};
 for(auto &[d,p]:periods){
  std::cout<<d<<" checking"<<std::endl;auto marker=text(root/(d+".sha256"));check(marker.rfind(base,0)==0,"Mixed producer/input identity: "+d);auto mk=kv(marker);check(mk["date"]==d,"Marker date mismatch");
  check(mk["output"]==hash(root/(d+".csv")),"Output hash mismatch: "+d);check(mk["qc"]==hash(root/(d+"_qc.csv")),"QC hash mismatch: "+d);
  std::istringstream mi(marker);std::map<std::string,std::vector<std::string>> sources;while(std::getline(mi,s)){auto r=csv(s);if(r.size()==4&&std::find(names.begin(),names.begin()+9,r[0])!=names.begin()+9)check(sources.emplace(r[0],r).second,"Duplicate marker source");}
  check(sources.size()==9,"Missing source hashes");for(int j=0;j<9;++j){auto r=sources.at(names[j]);check(digest(r[3]),"Invalid raster SHA");std::string normalized=r[1],rel=p.at(names[j]);std::replace(normalized.begin(),normalized.end(),'\\','/');std::replace(rel.begin(),rel.end(),'\\','/');check(normalized.size()>rel.size()&&normalized.substr(normalized.size()-rel.size())==rel&&normalized[normalized.size()-rel.size()-1]=='/',"Source path/config mismatch");if(verify){auto source=fs::u8path(r[1]);check(fs::file_size(source)==std::stoull(r[2])&&hash(source)==r[3],"Source hash/size mismatch");}lineage<<d<<","<<names[j]<<","<<r[3]<<","<<r[2]<<","<<int(verify)<<"\n";}
  int y=integer(d.substr(0,4)),m=integer(d.substr(4,2)),z=integer(d.substr(6,2)),nd=z<=20?10:z-20;
  if(y!=year){flush();year=y;}++year_periods;
  std::string season=(m==12||m<=2)?"DJF":m<=5?"MAM":m<=8?"JJA":"SON",sk=std::to_string(y)+","+season;
  // Seasons use calendar-year month groups; December is not shifted forward.
  Sum dec;std::set<int> seen;int bad=0,nres=0,nover=0;double rsum=0,rarea=0,rmax=0;
  std::istringstream f(text(root/(d+".csv")));std::getline(f,s);auto columns=csv(s);std::vector<std::string> expected={"hru_id","days","complete"};for(auto &n:names)expected.push_back(n);for(int j=0;j<9;++j)expected.push_back("coverage_"+names[j]);check(columns==expected,"Unknown CSV output contract");
  while(std::getline(f,s)){auto r=csv(s);check(r.size()==expected.size(),"Wrong output columns");int h=integer(r[0]);check(h>=1&&h<=nh&&seen.insert(h).second,"Duplicate/unknown HRU");check(integer(r[1])==nd,"Wrong decade length");int complete=integer(r[2]);check(complete==0||complete==1,"Invalid complete flag");V v{};std::array<bool,15> ok{};bool full=true;
   for(int j=0;j<15;++j){ok[j]=!r[3+j].empty();if(ok[j])v[j]=real(r[3+j]);if(j<9){double coverage=real(r[18+j]);check(coverage>=0&&coverage<=1,"Coverage outside 0..1");check(ok[j]?(coverage>=1-1e-9):(coverage<1),"Value/coverage mismatch");full=full&&ok[j];}}
   check(complete==int(full),"Complete flag mismatch");if(!full){++bad;++missing;}
   const std::array<std::vector<int>,6> terms={std::vector<int>{0,2},std::vector<int>{1,3},std::vector<int>{4},std::vector<int>{0,1,2,3,4},std::vector<int>{6,7},std::vector<int>{8,0,1,2,3,4}};
   for(int k=0;k<6;++k){bool valid=true;double value=0;for(size_t i=0;i<terms[k].size();++i){int j=terms[k][i];valid=valid&&ok[j];value+=(k==5&&i>0?-1:1)*v[j];}check(ok[9+k]==valid,"Derived missing-value propagation");if(valid)check(std::abs(value-v[9+k])<=1e-6+1e-8*std::abs(value),"Derived component arithmetic mismatch");}
   if(ok[14]){double rabs=std::abs(v[14]);++nres;++compared;rsum+=v[14]*area[h];rarea+=area[h];rmax=std::max(rmax,rabs);maxres=std::max(maxres,rabs);if(rabs>1e-4){++nover;++over;}}
   years[h].add(v,ok);dec.add(v,ok,area[h]);seasons[sk].add(v,ok,area[h]);
  }
  check(int(seen.size())==nh,"Missing HRUs in decade: "+d);emit(decades,d+","+std::to_string(nd)+","+std::to_string(nh),dec,true);
  quality<<d<<","<<nh-bad<<","<<bad<<","<<nres<<",";if(nres)quality<<rsum/rarea;quality<<","<<rmax<<","<<nover<<"\n";
 }
 flush();for(auto &[key,su]:seasons)emit(seasonal,key+","+std::to_string(su.periods/nh)+","+std::to_string(su.periods),su,true,double(su.periods/nh));
 for(auto f:{&annual,&seasonal,&decades,&lineage,&quality}){f->close();check(bool(*f),"Compact write failure");}
 std::ofstream status(dest/"acceptance.txt");status<<"status=STRUCTURALLY_VERIFIED_CANDIDATE\nproduction_admitted=false\nsource_rehash_verified="<<int(verify)<<"\nconfigured_first="<<periods.begin()->first<<"\nconfigured_last="<<periods.rbegin()->first<<"\ndecades="<<periods.size()<<"\nhru_count="<<nh<<"\nincomplete_hru_decades="<<missing<<"\net_comparison_rows="<<compared<<"\nresidual_above_diagnostic_0.0001mm="<<over<<"\nmax_abs_residual_mm="<<std::setprecision(12)<<maxres<<"\nseason_definition=calendar_year_DJF_MAM_JJA_SON\nscientific_status=PENDING_REAL_DATA_INTERPRETATION\n";status.close();
 std::ofstream identity(dest/"producer_identity.txt");identity<<base;identity.close();
 std::ofstream sums(dest/"SHA256SUMS.txt");for(auto n:{"annual_hru.csv","seasonal_population.csv","decadal_population.csv","source_hashes.csv","decadal_qa.csv","acceptance.txt","producer_identity.txt"})sums<<hash(dest/n)<<"  "<<n<<"\n";sums.close();check(bool(sums),"Manifest write failed");
 std::ofstream done(dest/"COMPLETE.txt");done<<"sha256_manifest="<<hash(dest/"SHA256SUMS.txt")<<"\n";done.close();check(bool(done),"Completion write failed");
 std::cout<<"COMPACT_READY "<<dest.string()<<"; production_admitted=false"<<std::endl;return missing?2:0;
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<std::endl;return 1;}}
