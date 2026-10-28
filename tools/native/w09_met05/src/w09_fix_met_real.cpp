#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <stdexcept>
#include <iomanip>
namespace fs=std::filesystem;
static bool number(const std::string& t){
 if(t.empty())return false;
 size_t i=0;if(t[i]=='-'||t[i]=='+')++i;
 bool digit=false;
 for(;i<t.size();++i){char c=t[i];
  if(c>='0'&&c<='9'){digit=true;continue;}
  if(c=='.'||c=='e'||c=='E'||c=='d'||c=='D')continue;
  if((c=='+'||c=='-')&&i>0&&(t[i-1]=='e'||t[i-1]=='E'||t[i-1]=='d'||t[i-1]=='D'))continue;
  return false;
 }
 return digit;
}
static std::string asreal(std::string t){
 if(!number(t))throw std::runtime_error("invalid real meteorological value: "+t);
 if(t.find_first_of(".eEdD")==std::string::npos)t+=".0";
 return t;
}
int main(int argc,char**argv){
 try{
  if(argc!=3)throw std::runtime_error("Usage: w09_fix_met_real.exe SOURCE_MET_DIRECTORY NEW_OUTPUT_DIRECTORY");
  fs::path src=fs::absolute(argv[1]),dest=fs::absolute(argv[2]),partial=dest;partial+=".partial";
  if(!fs::is_directory(src))throw std::runtime_error("source directory missing");
  if(fs::exists(dest)||fs::exists(partial))throw std::runtime_error("destination or partial already exists");
  fs::create_directories(partial);
  const std::string header="Station DD MM YYYY RAD Tmin Tmax HUM WIND RAIN ETref WET";
  long long rows_total=0,changed=0,ref_rows=-1;
  for(int id=1;id<=10242;id++){
   std::ostringstream name;name<<"HRU_"<<std::setw(5)<<std::setfill('0')<<id<<".met";
   fs::path in=src/name.str(),out=partial/name.str();
   std::ifstream fi(in,std::ios::binary);if(!fi)throw std::runtime_error("missing "+in.string());
   std::ofstream fo(out,std::ios::binary);if(!fo)throw std::runtime_error("cannot write "+out.string());
   std::string line;if(!std::getline(fi,line))throw std::runtime_error("empty "+in.string());
   if(!line.empty()&&line.back()=='\r')line.pop_back();
   if(line!=header)throw std::runtime_error("unexpected header in "+in.string());
   fo<<line<<"\n";
   long long records=0;
   while(std::getline(fi,line)){
    if(!line.empty()&&line.back()=='\r')line.pop_back();
    if(line.empty())throw std::runtime_error("empty data row in "+in.string());
    std::istringstream rr(line);std::vector<std::string> t;std::string v;
    while(rr>>v)t.push_back(v);
    if(t.size()!=12)throw std::runtime_error("expected 12 columns in "+in.string());
    if(t[0]!="'"+std::to_string(id)+"'")throw std::runtime_error("station mismatch in "+in.string());
    for(int k=4;k<12;k++){auto fixed=asreal(t[k]);if(fixed!=t[k])changed++;t[k]=fixed;}
    for(int k=0;k<12;k++)fo<<(k?" ":"")<<t[k];
    fo<<"\n";records++;rows_total++;
   }
   if(fi.bad()||!fo)throw std::runtime_error("I/O error in "+in.string());
   if(ref_rows<0)ref_rows=records;
   if(records!=ref_rows)throw std::runtime_error("inconsistent daily record count in "+in.string());
   if(id%1000==0)std::cout<<"PROGRESS "<<id<<"/10242 rows_per_hru="<<records<<"\n";
  }
  std::ofstream report(partial/"REAL_FORMAT_FIX_REPORT.txt");
  report<<"Expected HRUs: 10242\nDaily rows per HRU: "<<ref_rows
  <<"\nTotal data rows: "<<rows_total<<"\nInteger-lexical values changed: "<<changed
  <<"\nSource: "<<src.string()<<"\n";
  report.close();
  fs::rename(partial,dest);
  std::cout<<"DONE rows="<<rows_total<<" normalized="<<changed<<"\n";
  return 0;
 }catch(const std::exception&e){std::cerr<<"REAL_FIX ERROR: "<<e.what()<<"\n";return 2;}
}