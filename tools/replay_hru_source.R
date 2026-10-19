# Execute the hash-bound historical computational expressions, without plots,
# timestamp exports, package installation or hardcoded project paths.
args <- commandArgs(trailingOnly=TRUE)
if (length(args)!=3) stop("usage: replay_hru_source.R SOURCE INPUT_ROOT OUTPUT")
for (pkg in c("dplyr","tidyr","data.table","rio","scclust","Hmisc","purrr","distances","RANN","scales")) {
  if (!requireNamespace(pkg, quietly=TRUE)) stop(paste("Missing R package",pkg))
  suppressPackageStartupMessages(library(pkg,character.only=TRUE))
}
root <- paste0(normalizePath(args[2]),"/")
out <- args[3]
dir.create(out,recursive=TRUE,showWarnings=FALSE)
expressions <- parse(args[1], keep.source=TRUE)
for (i in seq_along(expressions)) {
  expr <- expressions[[i]]
  lhs <- if (is.call(expr) && as.character(expr[[1]]) %in% c("<-","=")) as.character(expr[[2]]) else ""
  # The only computational override is location, not scientific parameters.
  if (identical(lhs,"needed")) next
  if (is.call(expr) && identical(expr[[1]],as.name("for")) && identical(expr[[2]],as.name("pkg"))) next
  if (identical(lhs,"dir")) {dir <- root; next}
  if (is.call(expr) && identical(expr[[1]],as.name("export"))) break
  cat(sprintf("expression %d %s\n",i,paste(lhs,collapse=" "))); flush.console()
  eval(expr,envir=.GlobalEnv)
  if (identical(lhs,"df_complete") && "NRU" %in% names(df_complete)) {
    write.csv(df_complete,file.path(out,"HRU_MEMBERSHIP.csv"),row.names=FALSE,na="")
  }
}
for (pair in list(c("df_complete","HRU_MEMBERSHIP"),c("df_HRU","HRU_REPRESENTATIVE"),
                  c("df_NRU","NRU_SCHEMA"),c("df_ass","DONOR_ROUND1"),
                  c("df_ass1","DONOR_ROUND2"),c("HRUextra","DONOR_EXTRA"),
                  c("df_suspected","SUSPECTED_RESTORED"),c("p5","CLUSTER_ROUNDS"))) {
  write.csv(get(pair[1]),file.path(out,paste0(pair[2],".csv")),row.names=FALSE,na="")
}
writeLines(capture.output(sessionInfo()),file.path(out,"R-session.txt"))
writeLines("COMPUTATIONAL_SOURCE_REPLAY_COMPLETE",file.path(out,"COMPLETE"))
