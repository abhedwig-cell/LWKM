# Explicit modern adapter: preserve source numerical rules, handle empty
# query/rest tables that the full-population historical script assumes exist.
args <- commandArgs(trailingOnly=TRUE)
if(length(args)!=3) stop("usage: replay_hru_component.R SOURCE INPUT_ROOT OUTPUT")
for(pkg in c("dplyr","tidyr","data.table","rio","scclust","Hmisc","purrr","distances","RANN","scales")) {
  if(!requireNamespace(pkg,quietly=TRUE)) stop(paste("Missing",pkg))
  suppressPackageStartupMessages(library(pkg,character.only=TRUE))
}
nn2 <- function(data,query,k=1,...) {
  if(nrow(query)==0) return(list(nn.idx=matrix(integer(0),0,k),nn.dists=matrix(numeric(0),0,k)))
  RANN::nn2(data=data,query=query,k=k,...)
}
root <- paste0(normalizePath(args[2]),"/");out <- args[3]
dir.create(out,recursive=TRUE,showWarnings=FALSE)
expressions <- parse(args[1])
for(i in seq_along(expressions)) {
  expr <- expressions[[i]]
  lhs <- if(is.call(expr) && as.character(expr[[1]]) %in% c("<-","=")) as.character(expr[[2]]) else ""
  if(identical(lhs,"needed")) next
  if(is.call(expr) && identical(expr[[1]],as.name("for")) && identical(expr[[2]],as.name("pkg"))) next
  if(identical(lhs,"dir")) {dir <- root;next}
  if(is.call(expr) && identical(expr[[1]],as.name("export"))) break
  if(is.call(expr) && length(expr)>=3 && is.call(expr[[2]]) &&
     identical(expr[[2]][[1]],as.name("$")) && identical(expr[[2]][[3]],as.name("label"))) {
    table_name <- as.character(expr[[2]][[2]])
    if(exists(table_name) && is.data.frame(get(table_name)) && nrow(get(table_name))==0) {
      empty <- get(table_name);empty$label <- character(0);assign(table_name,empty);next
    }
  }
  # Source uses zero-column data.frame() for remainder tables. Give empty
  # tables their declared schema, without adding targets or donor choices.
  is_empty_frame <- is.call(expr) && length(expr)>=3 && is.call(expr[[3]]) && identical(expr[[3]][[1]],as.name("data.frame")) && length(expr[[3]])==1
  if(is_empty_frame && length(lhs)==1 && lhs %in% c("df_ass","df_ass1")) {
    assign(lhs,data.frame(svat_target=integer(0),svat_donor=integer(0)));next
  }
  if(is_empty_frame && identical(lhs,"df_remainder")) {df_remainder <- targets[FALSE,];next}
  if(is_empty_frame && identical(lhs,"df_remainder1")) {df_remainder1 <- targets[FALSE,];next}
  cat(sprintf("expression %d %s\n",i,paste(lhs,collapse=" ")));flush.console()
  eval(expr,envir=.GlobalEnv)
}
write.csv(df_complete,file.path(out,"HRU_MEMBERSHIP.csv"),row.names=FALSE,na="")
write.csv(df_HRU,file.path(out,"HRU_REPRESENTATIVE.csv"),row.names=FALSE,na="")
writeLines(capture.output(sessionInfo()),file.path(out,"R-session.txt"))
writeLines("MODERN_EMPTY_GROUP_ADAPTER_COMPLETE",file.path(out,"COMPLETE"))
