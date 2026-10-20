#1️⃣ Basisinstellingen en libraries

# --- Libraries ---------------------------------------------------------------
needed <- c("dplyr","tidyr","data.table","rio","scclust","Hmisc","purrr","distances","terra","fields","RANN","ggplot2","scales","cowplot")
# packages
for(pkg in needed){
  if(!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg)
  library(pkg, character.only = TRUE)
}
options(dplyr.summarise.inform = FALSE)



representative_points <- function(data, cluster_col, vars = c("x", "y"), method = c("centroid", "medoid")) {
  library(dplyr)
  method <- match.arg(method)
  cluster_col <- rlang::ensym(cluster_col)
  
  # Helperfunctie voor medoid
  find_medoid <- function(mat) {
    dists <- as.matrix(dist(mat))
    medoid_idx <- which.min(rowMeans(dists))
    return(medoid_idx)
  }
  
  # Voeg een indexkolom toe (voor herkenning van originele rijen)
  data$.row_index <- seq_len(nrow(data))
  
  reps <- data %>%
    group_by(!!cluster_col) %>%
    group_modify(~ {
      X <- .x[, vars, drop = FALSE]
      if (method == "centroid") {
        centroid <- colMeans(X)
        dists <- sqrt(rowSums((X - matrix(centroid, nrow(X), ncol(X), byrow = TRUE))^2))
        chosen <- which.min(dists)
      } else if (method == "medoid") {
        chosen <- find_medoid(X)
      }
      .x[chosen, , drop = FALSE]
    }) %>%
    ungroup()
  
  reps
}


# ---------------------------------------------------------------
# Functie: find_best_matches_ann
# Alleen de kolommen die in 'weights' staan worden gebruikt
# ---------------------------------------------------------------

library(data.table)

find_best_matches_ann <- function(
    donors, targets, weights,
    top_n = 1
) {
  donors <- as.data.table(donors)
  targets <- as.data.table(targets)
  
  # --- Kolommen die we gebruiken
  cols <- names(weights)
  
  # --- Invoercontrole
  if (!all(cols %in% names(donors))) stop("Niet alle kolommen uit weights staan in donors.")
  if (!all(cols %in% names(targets))) stop("Niet alle kolommen uit weights staan in targets.")
  
  # --- Selecteer matrix van gespecificeerde kolommen
  donor_mat <- as.matrix(donors[, ..cols])
  target_mat <- as.matrix(targets[, ..cols])
  
  # --- Pas gewichten toe (door vermenigvuldiging met sqrt(w))
  donor_mat <- sweep(donor_mat, 2, sqrt(weights[cols]), FUN = "*")
  target_mat <- sweep(target_mat, 2, sqrt(weights[cols]), FUN = "*")
  
  # --- Approximate Nearest Neighbour
  if (!requireNamespace("RANN", quietly = TRUE)) {
    stop("Installeer eerst het pakket RANN: install.packages('RANN')")
  }
  
  any(!sapply(donor_mat, is.numeric))
  any(!sapply(target_mat, is.numeric))
  
  
  nn <- RANN::nn2(data = donor_mat, query = target_mat, k = 1)
  
  # --- Resultaat als data.table
  result_dt <- data.table(
    target_index = rep(1:nrow(target_mat), each = top_n),
    donor_index = as.vector(nn$nn.idx),
    distance = sqrt(as.vector(nn$nn.dists))  # RANN geeft kwadraten
  )
  
  # --- Voeg donorinfo toe (alleen de gewogen kolommen)
  donors[, donor_index := .I]  # unieke ID per rij
  result_dt <- merge(
    result_dt,
    donors[, c("donor_index", cols), with = FALSE],
    by = "donor_index",
    all.x = TRUE
  )
  
  return(result_dt[])
}

# ----------------------------------------------------------
# Bepalen van indices van representatieve (x,y) combinaties 
# voor alle (x_m, y_n)-percentielen
# ----------------------------------------------------------

representative_percentile_points <- function(x, y, 
                                             px = seq(0, 1, length = 5),
                                             py = seq(0, 1, length = 5),
                                             metric = "manhattan") {
  # x, y zijn numeric vectors
  # px, py zijn percentielen (0?1)
  # metric: "euclidean" of "manhattan"
  
  if (length(x) != length(y)) stop("x en y moeten even lang zijn")
  
  xo <- x
  yo <- y
  x <- robust_scalar(x)
  y <- robust_scalar(y)
  
  # percentiel-waarden
  xq <- quantile(x, probs = px, na.rm = TRUE)
  yq <- quantile(y, probs = py, na.rm = TRUE)
  
  # raster van percentiel-combinaties
  grid <- expand.grid(xq = xq, yq = yq)
  
  X <- cbind(x, y)
  
  idx <- integer(nrow(grid))
  
  for (i in seq_len(nrow(grid))) {
    target <- c(grid$xq[i], grid$yq[i])
    
    if (metric == "euclidean") {
      d <- (X[,1] - target[1])^2 + (X[,2] - target[2])^2
    } else { # manhattan
      d <- abs(X[,1] - target[1]) + abs(X[,2] - target[2])
    }
    
    idx[i] <- which.min(d)
  }
  
  # resultaat in een data.frame
  data.frame(
    px = rep(px, each = length(py)),
    py = rep(py, times = length(px)),
    xq = grid$xq,
    yq = grid$yq,
    index = idx,
    x_val = xo[idx],
    y_val = yo[idx]
  )
}

cluster_round_maxMAE <- function(df, indlist, aggr_no, cols_of_interest, 
                                 MinOppha, groupfraction, FlagClus,
                                 MAE_threshold_GHG, 
                                 MAE_threshold_Nkw,
                                 reduction_factor,
                                 minnosvats) {
  
  force(df); force(indlist); force(aggr_no); force(robust_scalar); force(cols_of_interest)
  force(MinOppha); force(groupfraction); force(FlagClus); force(MAE_threshold_GHG)
  force(MAE_threshold_Nkw); force(reduction_factor); force(minnosvats)
  
  dff <- df %>%
    group_by(across(all_of(indlist))) %>%
    summarise(Oppha = sum(Oppha, na.rm = TRUE)) %>%
    ungroup()
  
  dff <- dff |> filter(Oppha >= MinOppha)
  
  df_sel <- df %>% semi_join(dff, by = indlist)
  df_rem <- df %>% anti_join(df_sel, by = "svat")
  
  dfl_res <- list()
  
  # loop over aantal rijen in dataframe dff  
  for (i in seq_len(nrow(dff))) {
    
    dat <- df %>%
      semi_join(dff[i,], by = indlist)
    
    head(dat,0)
    minnosvats_adj <- minnosvats
    if(dat$LDGBclus[1] ==35 ){minnosvats_adj <- 4 }
    if(dat$LDGBclus[1] ==38 ){minnosvats_adj <- 4 }
    if(dat$LDGBclus[1] ==56 ){minnosvats_adj <- 4 }
    
    col1 <- cols_of_interest[1]
    col2 <- cols_of_interest[2]
    
    my_data <- data.frame(
      id = dat$svat,
      x1 = robust_scalar(as.data.frame(dat[, col1])[, 1]),
      x2 = robust_scalar(as.data.frame(dat[, col2])[, 1])
    )
    names(my_data) <- c("id", "x1", "x2")
    
    # Als alle waarden identiek zijn → geen clustering
    if (length(unique(my_data$x1)) == 1 & length(unique(my_data$x2)) == 1) {
      
      dat$clust_no <- 0
      
    } else {
      
      if (FlagClus) {
        
        # startwaarden
        gf <- groupfraction
        n  <- nrow(my_data)
        
        # afstandsmatrix
        my_dist <- distances(as.matrix(dist(my_data[, -1]), method = "manhattan"))
        
        repeat {
          
          minsize <- max(1, floor(n * gf))
          
          # clustering
          my_clustering <- sc_clustering(my_dist, minsize)
          dat$clust_no <- as.numeric(my_clustering)
          
          # MAE-controle
          mae_exceeds <- FALSE
          
          for (clus in unique(dat$clust_no)) {
            
            sub <- dat[dat$clust_no == clus, ]
            
            mae1 <- mean(abs(sub[, col1] - mean(sub[, col1], na.rm = TRUE)), na.rm = TRUE)
            mae2 <- mean(abs(sub[, col2] - mean(sub[, col2], na.rm = TRUE)), na.rm = TRUE)
            skew1 <- skewness(sub[, col1])
            skew2 <- skewness(sub[, col2])
            
            if (mae1 > MAE_threshold_GHG || mae2 > MAE_threshold_Nkw || skew1 > 2 || skew2 > 2) {
              mae_exceeds <- TRUE
              break
            }
          }
          
          # stop als MAE ok is
          if (!mae_exceeds) break
          
          # anders groupfraction verlagen
          old_gf <- gf
          gf <- gf * reduction_factor
          
          # stop als gf niet meer verandert of minsize te klein wordt
          if (gf == old_gf) break
          if (floor(n * gf) < minnosvats_adj) break
        }
        
      } else {
        
        my_dist <- distances(
          my_data,
          id_variable = "id",
          dist_variables = c("x1", "x2")
        )
        my_clustering <- sc_clustering(my_dist, nrow(my_data))
        dat$clust_no <- as.numeric(my_clustering)
      }
    }
    
    # extra outputvariables
    dat$combi_no <- i           # combinummer binnen aggregatieniveau
    dat$aggr_no  <- aggr_no     # aggregatieniveau
    dat$minOpp   <- MinOppha
    
    dfl_res[[i]] <- dat
  } # einde dff-loop
  
  dfl_res <- do.call("rbind", dfl_res)
  
  list(df_res = dfl_res, df_rem = df_rem)
}


# Functies
closest_to_median <- function(x) {x[which.min(abs(x - median(x)))]}
Perct <- function(x, w, prob) wtd.quantile(x, weights = w, probs = prob)
mae <- function(x) mean(abs(x - mean(x)))

robust_scalar <- function(x) {
  prob1 = 0.25
  prob2 = 1 - prob1
  med <- median(x, na.rm = TRUE)
  q1  <- quantile(x, prob1, na.rm = TRUE, type = 7)
  q3  <- quantile(x, prob2, na.rm = TRUE, type = 7)
  iqr <- q3 - q1
  if (iqr == 0 || is.na(iqr)) { return(rep(0, length(x))) }
  (x - med) / iqr
}
skewness <- function(x, na.rm = FALSE) {
  if (na.rm) x <- x[!is.na(x)]
  n <- length(x)
  m <- mean(x)
  s <- sd(x)
  ifelse(n>2, sum(((x - m) / s)^3) * n / ((n - 1) * (n - 2)), 0)
}


# Helper functie voor de modus
get_mode <- function(x) {
  ux <- unique(na.omit(x))
  ux[which.max(tabulate(match(x, ux)))]
}

# Log-modulus transformatie definieren
log_mod_trans <- function() {
  trans_new(
    name = "log_mod",
    transform = function(x) sign(x) * log1p(abs(x)),
    inverse   = function(x) sign(x) * (exp(abs(x)) - 1)
  )
}






#2️⃣ Instellingen en functies
# Parameters
 MinOppha <- 500          # dit komt overeen met 80 svats
 groupfraction <- 0.25    # 80 x 0.25 is 20 svats minimaal
 MAE_threshold_GHG <- 1000  
 MAE_threshold_Nkw <- 500
 minnosvats <- 10
 minsvatsinNRU <- 4
 reduction_factor <- 0.841
cdate <- format(Sys.time(), "%Y%m%d_%H%M%S")

dfpawn21piet <- data.frame(pawn21=c(1:21),codepawn21rankpiet=c(7,11,14,8,10,9,12,13,21,19,20,15,16,17,18,3,6,2,1,4,5))
dfpawn21os50 <- data.frame(pawn21=c(1:21),codepawn21rankos50=c(1,2,3,4,6,5,21,8,13,20,12,7,14,18,16,11,10,9,15,17,19))
dfpawn21oslu50 <- data.frame(pawn21=c(1:21),codepawn21rankoslu50=c(1,4,2,5,9,3,21,15,18,20,16,14,17,19,12,8,6,7,10,11,13))
# dfpawn21 <- data.frame(pawn21=c(1:21),codepawn21=c(7,11,14,8,10,9,12,13,21,19,20,15,16,17,18,3,6,2,1,4,5))
# dfgrondsoort4 <- data.frame(grondsoort4=c(1:4),codegrst=c(2,3,4,1)) #vzkl
dflu4 <- data.frame(lu4=c(1:4),codelu4=c(3,2,1,8))

cols_of_interest <- c("GHG_LHM43", "NettoKwel_LHM43")
items <- c("svat_donor", "svat","x", "y","glg(cm-mv)", "ghg(cm-mv)","kwelwegzijging(mm/j)","gt(1-8)","lu7","lu4","lu2","bodem370",
 "pawn21","grondsoort4","grondsoort2","kwelklasse4","islwkm(0/1)","isberegen(0/1)","isdrain(0/1)" )
cols <- c('LDGBclus','LDGB','lu7','lu4','lu2','bodem370','pawn21','grondsoort4','grondsoort2','GHG_LHM43','Gt_LHM43','NettoKwel_LHM43','kwelklasse4','isdrain')



#3️⃣ Data inlezen en voorbewerking/
dir <- "w:/PROJECTS/ESG_DB_PROJECTS/Waterkwaliteitsmodellen/Ontwikkeling LWKM2.0/Vaststellen HRUs/"
file_orig <- "Herschikking/20251114/SVAT_INFO.csv"
file <- "Herschikking/20251114/svat_info_lwkm_new.csv"


#################################################
df <- import(paste0(dir, file)) |> dplyr::select(items) |>
  rename(GLG_LHM43='glg(cm-mv)',GHG_LHM43='ghg(cm-mv)',NettoKwel_LHM43='kwelwegzijging(mm/j)',Gt_LHM43='gt(1-8)',isdrain='isdrain(0/1)' ) 
# dforg <- df
dfLBDG <- import(paste0(dir,'xyLDGBclus.csv'))
inLBDG <- semi_join(df, dfLBDG, by = c("x", "y")) |> left_join(dfLBDG, by = c("x", "y"))
naLBDG <- anti_join(df,dfLBDG,by=c('x','y') )
nn <- nn2(data = dfLBDG[, c("x", "y")],query = naLBDG[, c("x", "y")],k=1)$nn.idx[,1]
naLBDG <- bind_cols( naLBDG, dfLBDG[nn,c('LDGBclus','LDGB')])
df <- bind_rows( inLBDG, naLBDG ) |> 
  select(svat_donor,svat,x,y,LDGBclus,LDGB,lu7,lu4,lu2,bodem370,pawn21,grondsoort4,grondsoort2,GHG_LHM43,Gt_LHM43,NettoKwel_LHM43,kwelklasse4,isdrain) |>
  mutate(Oppha = 6.25,isdrain=case_when(lu2==2~0,TRUE~isdrain))

df_notok <- df |> filter(svat_donor!=svat)
df_suspected <- import(paste0(dir, file_orig)) |>
  rename(x='xc(m)',y='yc(m)',GLG_LHM43='glg(cm-mv)',GHG_LHM43='ghg(cm-mv)',NettoKwel_LHM43='kwelwegzijging(mm/j)',Gt_LHM43='gt(1-8)',isdrain='isdrain(0/1)',islwkm='islwkm(0/1)' ) |>
  filter(islwkm==1) |> filter(svat %in% df_notok$svat) |> left_join(dfLBDG,by=c('x','y')) |>  
  mutate(Oppha=6.25) |>  mutate(svat_donor=as.integer(NA)) |> select(names(df))
inLBDG <- semi_join(df_suspected, dfLBDG, by = c("x", "y")) 
naLBDG <- anti_join(df_suspected,dfLBDG,by=c('x','y') )
nn <- nn2(data = dfLBDG[, c("x", "y")],query = naLBDG[, c("x", "y")],k=1)$nn.idx[,1]
naLBDG <- bind_cols( naLBDG |> select(-c('LDGBclus','LDGB')), dfLBDG[nn,c('LDGBclus','LDGB')]) |> 
  relocate(LDGB, .after = y) |> relocate(LDGBclus, .after = y)
df_suspected <- bind_rows( inLBDG, naLBDG ) 
df_suspected$label <- 'suspected'

df_valid <- df |> filter(svat_donor==svat)
df_valid$label <- 'valid'

# Definieer aggregatieniveaus per ronde

indlists <- list(
  c("LDGBclus","lu2","lu4","lu7","grondsoort2","grondsoort4","pawn21","bodem370","Gt_LHM43","kwelklasse4","isdrain"),
  c("LDGBclus","lu2","lu4","lu7","grondsoort2","grondsoort4","pawn21","bodem370","Gt_LHM43","kwelklasse4"),
  c("LDGBclus","lu2","lu4",      "grondsoort2","grondsoort4","pawn21","bodem370","Gt_LHM43","kwelklasse4"),
  c("LDGBclus","lu2","lu4",      "grondsoort2","grondsoort4","pawn21",           "Gt_LHM43","kwelklasse4"),
  c("LDGBclus","lu2","lu4",      "grondsoort2","grondsoort4",                    "Gt_LHM43","kwelklasse4"),
  c("LDGBclus","lu2","lu4",      "grondsoort2","grondsoort4","pawn21",           "Gt_LHM43"              ),
  c("LDGBclus","lu2","lu4",      "grondsoort2","grondsoort4",                    "Gt_LHM43"              ),
  c("LDGBclus","lu2","lu4",      "grondsoort2","grondsoort4","pawn21",                      "kwelklasse4"),
  c("LDGBclus","lu2","lu4",      "grondsoort2","grondsoort4",                               "kwelklasse4"),
  c("LDGBclus","lu2","lu4",      "grondsoort2","grondsoort4","pawn21"                                    ),
  c("LDGBclus","lu2","lu4",      "grondsoort2","grondsoort4"                                             )
)

#5️⃣ Uitvoeren van alle rondes

df_rem <- df_valid
results <- list()
k <- 0
FlagClus <- TRUE

for (i in seq_along(indlists)) {
    k <- k + 1
#    message(sprintf("Ronde %d " , i))
    res <- cluster_round_maxMAE(df_rem, indlists[[i]], i, cols_of_interest, MinOppha, groupfraction, FlagClus,
                                     MAE_threshold_GHG, MAE_threshold_Nkw, reduction_factor,minnosvats)   
    
    results[[k]] <- res$df_res 
    df_rem <- res$df_rem
}
# 


#6️⃣ Resultaten combineren
# HUR's met te kleine omvang binnen een Landbouwdeelgebied toevoegen aan df_rem
df_res <- do.call("rbind", results) 

df_res$label <- paste0(df_res$label,' | HRU group size OK')
df_rem$label <- paste0(df_rem$label,' | HRU group size too small') 

# aantal voorbereiding op NRUs
df2 <- df_res |> as.data.frame() |> group_by(LDGBclus,LDGB,aggr_no,minOpp,combi_no,clust_no) |> summarise(N=n()) 
df2$minsvats <- ifelse(df2$LDGBclus %in% c(35,38,56), 2, minsvatsinNRU)


# tussenresultaten voor rapport
p5 <- df_res |> as.data.frame() |> group_by(LDGBclus,aggr_no,minOpp,combi_no,clust_no) |> summarise(N=n()) |> group_by(aggr_no) |> summarise(Aantal_toegewezen_svats=sum(N))
p5a <- df2 |> filter(N>=minsvats) |> group_by(aggr_no) |> summarise(Aantal_LDGB_gt_2=sum(N))
p5b <- df2 |> filter(N<minsvats) |> group_by(aggr_no) |> summarise(Aantal_LDGB_le_2=sum(N))
p5 <- p5 |> left_join(p5a,by='aggr_no') |> left_join(p5b,by='aggr_no')

# deze groep (df_tmp) heeft te kleine omvang binnen LDGB, en daaro, worden ze aan de restgroep toegevoegd
df_res2 <- df_res |> left_join(df2 ,by=c('LDGBclus','LDGB','aggr_no','minOpp','combi_no','clust_no') )
df_tosmall4NRU <- df_res2 |> filter(N<minsvats) |> select(-c(aggr_no,minOpp,combi_no,clust_no,N))
df_tosmall4NRU$label <- paste0(df_tosmall4NRU$label,' | NRU group size too small') 


df_rem <- bind_rows(df_rem, df_tosmall4NRU)
df_rem <- bind_rows(df_rem , df_suspected)

df_ok4NRU <- df_res2 |> filter(N>=minsvats)
df_ok4NRU$label <- paste0(df_ok4NRU$label,' | NRU group size OK') 
df_res <- df_ok4NRU |> select(-N)


vars   <- c('svat','LDGB','lu2','lu4','grondsoort2','grondsoort4','pawn21','Gt_LHM43','kwelklasse4','GHG_LHM43','NettoKwel_LHM43')
donors <-  df_res[,vars] |> left_join(dfpawn21oslu50,by='pawn21') |> left_join(dflu4,by='lu4') #|> left_join(df0[,c('x','y')],by='svat')
targets <- df_rem[,vars] |> left_join(dfpawn21oslu50,by='pawn21') |> left_join(dflu4,by='lu4') #|> left_join(df0[,c('x','y')],by='svat')

# Gewichten per kolom (alleen deze kolommen worden gebruikt)
#weights <- c(lu2 = 500, codelu4 = 250, grondsoort2 = 25, grondsoort4 = 10, codepawn21rankoslu50=0.5, Gt_LHM43=0.25, kwelklasse4=0.25, GHG_LHM43=0.01, NettoKwel_LHM43=0.01 )
weights <- c(grondsoort2 = 250, grondsoort4 = 100, codepawn21rankoslu50=10, Gt_LHM43=0.5, kwelklasse4=0.5, GHG_LHM43=0.01, NettoKwel_LHM43=0.01 )
n1 <- df_rem[,c('LDGB','lu4')] |> group_by(LDGB,lu4) |> summarise(Aantal=n()) |> as.data.frame() |> mutate(No=row_number())

df_ass <- data.frame()
df_remainder <- data.frame()
for (i in n1$No ) {
  don <- donors |> filter( LDGB==n1[i,1] & lu4==n1[i,2] )
  tar <- targets |> filter( LDGB==n1[i,1] & lu4==n1[i,2] )
#  if(nrow(tar)>2*nrow(don)) {
  if(nrow(don) <4) {
  df_remainder <- rbind(df_remainder,tar)
  } else {
    result_ann <- find_best_matches_ann(don, tar, weights = weights, top_n = 1)
    df_link <- as.data.frame(result_ann[,c(1:3)]) |> arrange(target_index)
    tmp <- as.data.frame(cbind(tar[df_link$target_index,c('svat')],don[df_link$donor_index,c('svat')])) |> 
      rename(svat_target=V1,svat_donor=V2) |> 
      left_join(tar[,c(1:11)] |> rename_with(~ paste0(.x, "_target")),by='svat_target') |> 
      left_join(don[,c(1:11)] |> rename_with(~ paste0(.x, "_donor")), by='svat_donor')  
    df_ass <- rbind(df_ass,tmp)
  }
}

weights <- c(codelu4 = 250,grondsoort2 = 250, grondsoort4 = 100, codepawn21rankoslu50=10, Gt_LHM43=0.5, kwelklasse4=0.5, GHG_LHM43=0.01, NettoKwel_LHM43=0.01 )
n1 <- df_remainder[,c('LDGB','lu2')]  |> group_by(LDGB,lu2) |> summarise(Aantal=n()) |> as.data.frame() |> mutate(No=row_number())
df_ass1 <- data.frame()
df_remainder1 <- data.frame()
for (i in n1$No ) {
  don <- donors |> filter( LDGB==n1[i,1] & lu2==n1[i,2] )
  tar <- df_remainder |> filter( LDGB==n1[i,1] & lu2==n1[i,2] )
  #  if(nrow(tar)>2*nrow(don)) {
  if(nrow(don) <2) {
    df_remainder1 <- rbind(df_remainder1,tar)
  } else {
    result_ann <- find_best_matches_ann(don, tar, weights = weights, top_n = 1)
    df_link <- as.data.frame(result_ann[,c(1:3)]) |> arrange(target_index)
    tmp <- as.data.frame(cbind(tar[df_link$target_index,c('svat')],don[df_link$donor_index,c('svat')])) |> 
      rename(svat_target=V1,svat_donor=V2) |> 
      left_join(tar[,c(1:11)] |> rename_with(~ paste0(.x, "_target")),by='svat_target') |> 
      left_join(don[,c(1:11)] |> rename_with(~ paste0(.x, "_donor")), by='svat_donor')  
    df_ass1 <- rbind(df_ass1,tmp)
  }
}


df_assT <- bind_rows(df_ass[,c(1:2)],df_ass1[,c(1:2)]) |> rename(svat_orig=svat_target)


v <- df_remainder1 |> group_by(LDGB,lu4,grondsoort4,Gt_LHM43) |> summarise(N=n()) |> 
  ungroup() |> mutate(nummer=row_number())
v1 <- left_join(df_remainder1, v, by=c('LDGB','lu4','grondsoort4','Gt_LHM43')) 
v2 <- v1 |> group_by(nummer) |> slice(which.max(N)) |> relocate(nummer,.before='svat') |> select(1:2) |> rename(svat_donor=svat)
v1 <- v1 |> relocate(nummer,.before=svat) |> select(1:2) |> rename(svat_orig=svat)
# dit zijn nieuw HRU's
HRUextra <- left_join( v1, v2, by='nummer') |> relocate(nummer,.before=svat_orig) 

df_res2 <- left_join(df_res,as.data.frame(df_res) |> 
                      group_by(aggr_no,minOpp,combi_no,clust_no) |>  
                      summarise(n=n()) |>
                      ungroup() |> 
                      mutate(HRU=row_number()) |>
                      select(-n),by=c('aggr_no','minOpp','combi_no','clust_no') ) |>
  rename(svat_orig=svat) |> relocate(HRU,.before=svat_donor) |>
  select(-c(22:26),-Oppha)

df_res2 <- bind_cols( df_res2 %>% rename_with(~ paste0(.x, "_orig"), .cols = cols), df_res2[,cols] |> rename_with(~ paste0(.x, "_donor")) )



df_assT2 <- left_join(df_assT,df_res2[,c(1,2)],by='svat_donor') |> 
  left_join(df_res[,c("svat_donor",cols)], by="svat_donor" ) |> rename_with(~ paste0(.x, "_donor"), .cols = cols) |>
  left_join(df[,c("svat","x","y",cols)], by=c("svat_orig"="svat" )) |> rename_with(~ paste0(.x, "_orig"), .cols = cols) |>
  mutate(label = "Toegevoegd") |> select(names(df_res2))
  
df_res3 <- bind_rows(df_res2,df_assT2)

nmax <- max(df_res3$HRU)
HRUextra <- HRUextra |> mutate(HRU=nummer+nmax)
df_HRUextra <- HRUextra |> 
  left_join(df[,c('svat','x','y',cols)],by=c('svat_orig'='svat')) |> 
  rename_with(~ paste0(.x, "_orig"), .cols = cols) |>
  left_join(df[,c('svat',cols)],by=c('svat_donor'='svat')) |> 
  rename_with(~ paste0(.x, "_donor"), .cols = cols) |>
  mutate(label="Restgroep")  |> 
  select(-nummer) |> relocate(HRU,.before=svat_orig) |> select(names(df_res3))

df_complete <- bind_rows(df_res3,df_HRUextra) |> arrange(HRU,lu2_orig,lu4_orig,grondsoort2_orig,grondsoort4_orig,pawn21_orig,Gt_LHM43_orig,kwelklasse4_orig) 
df_complete <- df_complete |> mutate(NRUcode=paste0(HRU,"_",LDGB_orig)) |> relocate(NRUcode,.after=HRU) 
df_complete <- left_join(df_complete, as.data.frame(df_complete[,'NRUcode']) |> distinct()  |> mutate(NRU=row_number()) |> rename(NRUcode=1), by = 'NRUcode' ) |> relocate(NRU,.before=NRUcode)

df_analyse <- df_complete |> mutate(dif_lu2=lu2_orig-lu2_donor,
                                dif_lu4=lu4_orig-lu4_donor,
                                dif_lu7=lu7_orig-lu7_donor,
                                dif_grondsoort2=grondsoort2_orig-grondsoort2_donor,
                                dif_grondsoort4=grondsoort4_orig-grondsoort4_donor,
                                dif_pawn21=pawn21_orig-pawn21_donor,
                                dif_bodem370=bodem370_orig-bodem370_donor,
                                dif_Gt_LHM43=Gt_LHM43_orig-Gt_LHM43_donor,
                                dif_kwelklasse4=kwelklasse4_orig-kwelklasse4_donor,
                                dev_lu2=ifelse(dif_lu2!=0,1,0),
                                dev_lu4=ifelse(dif_lu4!=0,1,0),
                                dev_lu7=ifelse(dif_lu7!=0,1,0),
                                dev_grondsoort2=ifelse(dif_grondsoort2!=0,1,0),
                                dev_grondsoort4=ifelse(dif_grondsoort4!=0,1,0),
                                dev_pawn21=ifelse(dif_pawn21!=0,1,0),
                                dev_bodem370=ifelse(dif_bodem370!=0,1,0),
                                dev_Gt_LHM43=ifelse(dif_Gt_LHM43!=0,1,0),
                                dev_kwelklasse4=ifelse(dif_kwelklasse4!=0,1,0)) |>
  group_by(HRU,LDGBclus_orig) |> summarise(N=n(),
            dev_lu2=sum(dev_lu2),dev_lu4=sum(dev_lu4),dev_lu7=sum(dev_lu7),dev_grondsoort2=sum(dev_grondsoort2),dev_grondsoort4=sum(dev_grondsoort4),
            dev_pawn21=sum(dev_pawn21),dev_bodem370=sum(dev_bodem370),dev_Gt_LHM43=sum(dev_Gt_LHM43),dev_kwelklasse4=sum(dev_kwelklasse4)) |> ungroup() |>
  mutate(Purity_lu2         = round(100*(1-dev_lu2/N),0),
         Purity_lu4         = round(100*(1-dev_lu4/N),0),
         Purity_lu7         = round(100*(1-dev_lu7/N),0),
         Purity_grondsoort2 = round(100*(1-dev_grondsoort2/N),0),
         Purity_grondsoort4 = round(100*(1-dev_grondsoort4/N),0),
         Purity_pawn21      = round(100*(1-dev_pawn21/N),0),
         Purity_bodem370    = round(100*(1-dev_bodem370/N),0),
         Purity_Gt_LHM43    = round(100*(1-dev_Gt_LHM43/N),0),
         Purity_kwelklasse4 = round(100*(1-dev_kwelklasse4/N),0))

df_HRU <- df_complete |> group_by(HRU,LDGBclus_orig) |> 
  summarise(N=n(),
            code=get_mode(lu2_donor+10*lu4_donor+100*grondsoort2_donor+1000*grondsoort4_donor+10000*pawn21_donor),
            code1=get_mode(lu2_donor+10*lu4_donor+100*grondsoort2_donor+1000*grondsoort4_donor),
            code2=get_mode(lu2_donor+10*lu4_donor+100*grondsoort2_donor),
            code3=get_mode(lu2_donor+10*grondsoort2_donor),
            code4=get_mode(lu2_donor),
            lu2 = code %% 10,
            lu4 = (code %% 100) %/% 10, 
            grondsoort2= (code %% 1000) %/% 100,
            grondsoort4 = (code %% 10000) %/% 1000,
            pawn21 = round(code/10000,0),
            bodem370=get_mode(bodem370_donor),
            Gt_LHM43=get_mode(Gt_LHM43_donor),
            kwelklasse4=get_mode(kwelklasse4_donor),
            GHG_average = mean(GHG_LHM43_donor,na.rm=TRUE),
            GHG_median = median(GHG_LHM43_donor,na.rm=TRUE),
            GHG_sd = sd(GHG_LHM43_donor,na.rm=TRUE),
            NettoKwel_average = mean(NettoKwel_LHM43_donor,na.rm=TRUE),
            NettoKwel_median = median(NettoKwel_LHM43_donor,na.rm=TRUE),
            NettoKwel_sd = sd(NettoKwel_LHM43_donor,na.rm=TRUE),
            MAE_GHG = mean(abs(GHG_LHM43_donor - GHG_average)),
            RMSE_GHG = sqrt(mean((GHG_LHM43_donor - GHG_average)^2)),
            MAE_NKw = mean(abs(NettoKwel_LHM43_donor - NettoKwel_average)),
            RMSE_NKw = sqrt(mean((NettoKwel_LHM43_donor - NettoKwel_average)^2)),
            Skew_GHG = skewness(GHG_LHM43_donor),
            Skew_NKw = skewness(NettoKwel_LHM43_donor))


df_NRU <- df_complete |> group_by(NRU,HRU,LDGB_orig) |> summarise(N=n()) |> 
  left_join(df_HRU[,c('HRU','LDGBclus_orig','lu2','lu4','grondsoort2','grondsoort4','pawn21','bodem370','Gt_LHM43','kwelklasse4')], by='HRU') |> arrange(HRU) |>
  ungroup() |> mutate(NRU)

svat_repr <- vector()
nt <- 0
tmp0 <- df_complete |> mutate(code = lu2_donor+10*lu4_donor+100*grondsoort2_donor+1000*grondsoort4_donor+10000*pawn21_donor,
                              code1 = lu2_donor+10*lu4_donor+100*grondsoort2_donor+1000*grondsoort4_donor,
                              code2 = lu2_donor+10*lu4_donor+100*grondsoort2_donor,
                              code3 = lu2_donor+10*grondsoort2_donor,
                              code4 = lu2_donor )           

for (i in 1:nrow(df_HRU)) {
#  i <- 1
  tmp <- tmp0 |> filter( HRU == i )
  tmp <- tmp |> filter( code == df_HRU[i,'code'] )
  if(nrow(tmp)==0) {
    tmp <- tmp0 |> filter( HRU == i )
    tmp <- tmp |> filter( code1 == df_HRU[i,'code1'] )
  }
  if(nrow(tmp)==0) {
    tmp <- tmp0 |> filter( HRU == i )
    tmp <- tmp |> filter( code1 == df_HRU[i,'code1'] )
  }
  if(nrow(tmp)==0) {
    tmp <- tmp0 |> filter( HRU == i )
    tmp <- tmp |> filter( code2 == df_HRU[i,'code2'] )
  }
  if(nrow(tmp)==0) {
    tmp <- tmp0 |> filter( HRU == i )
    tmp <- tmp |> filter( code3 == df_HRU[i,'code3'] )
  }
  if(nrow(tmp)==0) {
    tmp <- tmp0 |> filter( HRU == i )
    tmp <- tmp |> filter( code4 == df_HRU[i,'code4'] )
  }
  if(nrow(tmp)==0 ) {
    svat_repr[i] <- -9999
  }  else {
    svat_repr[i] <- representative_points(tmp, HRU, c('GHG_LHM43_donor','NettoKwel_LHM43_donor') , method = "medoid")$svat_donor
  }
}
df_HRU <- bind_cols(df_HRU |> select(-c(code,code1,code2,code3,code4)), svat_repr=svat_repr)
tmp0 <- df_complete |> arrange(HRU) |> group_by(HRU) |>
  reframe(
    representative_percentile_points(
      x = .data[["GHG_LHM43_donor"]],
      y = .data[["NettoKwel_LHM43_donor"]],
      px = c(0.1,0.9),
      py = c(0.1,0.9),
      metric = "euclidean")) |>
  left_join(df_complete |> arrange(HRU) |> group_by(HRU) |>  mutate(indno=row_number()) |> dplyr::select(svat_donor,HRU,indno), by=c('index'='indno','HRU'='HRU')) |>
  mutate(px=paste0('p',px),py=paste0('p',py),xq=NULL,yq=NULL,index=NULL) |> 
  rename(GHG=x_val,NettoKwel=y_val) |>
  pivot_wider(names_from = c(px,py), values_from = c(svat_donor,GHG,NettoKwel)) |> ungroup()
df_HRU <- df_HRU |> left_join(tmp0,by='HRU')


################################################################################

export(df_complete , paste0(dir, "Result/export_svat_HRU_NRU_",cdate,".csv"))

df_complete[,c('x','y','HRU')] |> rast(type="xyz") |>
  writeRaster(paste0(dir, "Result/HRU_LWKM20_",cdate,".asc"),overwrite=TRUE, filetype="AAIGrid", datatype="INT2S", NAflag=-9999)
df_complete[,c('x','y','NRU')] |> rast(type="xyz") |>
  writeRaster(paste0(dir, "Result/HRU_LWKM20_",cdate,".asc"),overwrite=TRUE, filetype="AAIGrid", datatype="INT2S", NAflag=-9999)

df_a <- df_complete |> select(svat=svat_orig,x,y,HRU,GHG_LHM43=GHG_LHM43_orig,NettoKwel_LHM43=NettoKwel_LHM43_orig) |>
  left_join(df_HRU[,c('HRU','GHG_average','NettoKwel_average','MAE_GHG','RMSE_GHG','MAE_NKw','RMSE_NKw')],by='HRU') |>
  mutate(difGHG=GHG_LHM43-GHG_average,difNKw=NettoKwel_LHM43-NettoKwel_average,
         reldifGHG=case_when(GHG_average==0~difGHG,TRUE~difGHG/GHG_average))

rastdifGHG <- rast(df_a[,c('x','y','difGHG')], type="xyz")
rastdifNKw <- rast(df_a[,c('x','y','difNKw')], type="xyz")
rastreldifGHG <- rast(df_a[,c('x','y','reldifGHG')], type="xyz")
writeRaster(rastdifGHG, paste0(dir, "Result/difGHG_SVATs_HRUs.asc"),overwrite=TRUE, filetype="AAIGrid", datatype= "FLT4S", NAflag=-9999)
writeRaster(rastdifNKw, paste0(dir, "Result/difNKw_SVATs_HRUs.asc"),overwrite=TRUE, filetype="AAIGrid", datatype= "FLT4S", NAflag=-9999)
writeRaster(rastreldifGHG, paste0(dir, "Result/reldifGHG_SVATs_HRUs.asc"),overwrite=TRUE, filetype="AAIGrid", datatype= "FLT4S", NAflag=-9999)

df_purity <- left_join(df_complete[,c('x','y','HRU')], df_analyse[,c('HRU','Purity_lu2','Purity_lu4','Purity_grondsoort2','Purity_grondsoort4','Purity_pawn21')], by='HRU')


export(df_analyse , paste0(dir, "Result/export_HRUpurity_",cdate,".csv"))
export(df_HRU , paste0(dir, "Result/export_HRUschema_",cdate,".csv"))
export(df_NRU , paste0(dir, "Result/export_NRUschema_",cdate,".csv"))


################################################################################


breaks <- c(-1000, -100, -10, -1, 0, 1, 10, 100, 1000)
labels <- breaks   # labels gelijk aan de waarden

p <- ggplot(df_a, aes(x = difGHG)) +
  geom_density(fill = "lightblue", alpha = 0.4, colour = "blue", linewidth = 1.2) +
  scale_x_continuous(trans  = log_mod_trans(),
                     breaks = breaks,
                     labels = labels) +
  labs(title = "Dichtheidsplot GHG_svat - GHG_HRU (cm)",
       x = "x (log-modulus schaal)",
       y = "Dichtheid") +
  theme_minimal()
ggsave( filename = paste0(dir, "Result/density_logmod_",cdate,".png"),
        plot = p, width = 10, height = 6, dpi = 300 )

r <- rastdifGHG
r_log <- sign(r) * log10(1 + abs(r))
pal <- colorRampPalette(c("blue", "green", "white", "grey","white","orange","red"))(200)

png(paste0(dir, "Result/difGHG_SVATs_HRUs_",cdate,".png"), width=3200, height=2400, res = 600)
plot(r_log, col = pal, legend = FALSE, main = "GHG verschil svat - HRU (cm)",cex.main = 0.8)
ticks_orig <- c(-1000, -100, -10, 0, 10, 100, 1000)
ticks_log <- sign(ticks_orig) * log10(1 + abs(ticks_orig))
image.plot(legend.only = TRUE,
           zlim = range(values(r_log), na.rm = TRUE),
           col = pal,
           axis.args = list(
             at = ticks_log,
             labels = ticks_orig,
             cex.axis = 0.8
           ),
           legend.args = list(text = "", side = 3, line = 1),
           legend.shrink = 1.2)
dev.off()

r <- rastdifNKw
r_log <- sign(r) * log10(1 + abs(r))

pal <- colorRampPalette(c("blue", "green", "white", "grey","white","orange","red"))(200)

png(paste0(dir, "Result/difNKw_SVATs_HRUs_",cdate,".png"), width=3200, height=2400, res = 600)
plot(r_log, col = pal, legend = FALSE, main = "NettoKwel verschil svat - HRU (mm/jr)",cex.main = 0.8)
ticks_orig <- c(-1000, -100, -10, 0, 10, 100, 1000)
ticks_log <- sign(ticks_orig) * log10(1 + abs(ticks_orig))
image.plot(legend.only = TRUE,
           zlim = range(values(r_log), na.rm = TRUE),
           col = pal,
           axis.args = list(
             at = ticks_log,
             labels = ticks_orig,
             cex.axis = 0.8
           ),
           legend.args = list(text = "", side = 3, line = 1),
           legend.shrink = 1.2)
dev.off()

r <- 100*rastreldifGHG
r_log <- sign(r) * log10(1 + abs(r))

pal <- colorRampPalette(c("blue", "green", "white","white","orange","red"))(200)

png(paste0(dir, "Result/reldifGHG_SVATs_HRUs_",cdate,".png"), width=3200, height=2400, res = 600)
plot(r_log, col = pal, legend = FALSE, colNA = "white", main = "relatief GHG verschil svat - HRU (%)",cex.main = 0.8)
ticks_orig <- c(-1000, -100, -10, 0, 10, 100, 1000)
ticks_log <- sign(ticks_orig) * log10(1 + abs(ticks_orig))
image.plot(legend.only = TRUE,
           zlim = range(values(r_log), na.rm = TRUE),
           col = pal,
           axis.args = list(
             at = ticks_log,
             labels = ticks_orig,
             cex.axis = 0.8
           ),
           legend.args = list(text = "", side = 3, line = 1),
           legend.shrink = 1.2)
dev.off()

dfy <- df_a[,c('x','y','MAE_GHG','MAE_NKw')] |> 
  left_join(df_complete[,c('x','y','LDGBclus_orig')],by=c('x','y'))
dfy1 <- dfy |> group_by(LDGBclus_orig) |>
  summarise(meanMAE_GHG=mean(MAE_GHG,na.rm=TRUE),meanMAE_NKw=mean(MAE_NKw,na.rm=TRUE))
dfy <- dfy |> left_join(dfy1,by='LDGBclus_orig')
meanMAEGHG <- rast(dfy[,c('x','y','meanMAE_GHG')], type="xyz") 
meanMAENKw <- rast(dfy[,c('x','y','meanMAE_NKw')], type="xyz") 

# Maak één PNG-bestand met twee kaarten naast elkaar
png(
  paste0(dir, "Result/GebiedsmeanMAE_GHG_NKw_", cdate, ".png"),
  width = 4500, height = 2400, res = 600
)

# Twee panelen naast elkaar
par(mfrow = c(1, 2), mar = c(4, 4, 4, 6))  # extra ruimte rechts voor colorbar

### ---- Kaart 1: GHG ---- ###
r <- meanMAEGHG
pal <- colorRampPalette(c("grey", "yellow", "orange", "red"))(200)

plot(
  r, col = pal, legend = FALSE, colNA = "white",
  main = "Gebiedsgemiddelde MAE van GHG (cm)", cex.main = 0.8
)

ticks_orig <- c(0, 100, 200, 300, 400)
image.plot(
  legend.only = TRUE,
  zlim = range(values(r), na.rm = TRUE),
  col = pal,
  axis.args = list(
    at = ticks_orig,
    labels = ticks_orig,
    cex.axis = 0.8
  ),
  legend.args = list(text = "", side = 3, line = 1),
  legend.shrink = 1.2
)

### ---- Kaart 2: NKw ---- ###
r <- meanMAENKw
pal <- colorRampPalette(c("grey", "yellow", "orange", "red"))(200)

plot(
  r, col = pal, legend = FALSE, colNA = "white",
  main = "Gebiedsgemiddelde MAE van NettoKwel (mm/jr)", cex.main = 0.8
)

ticks_orig <- c(0, 50, 100, 150, 200)
image.plot(
  legend.only = TRUE,
  zlim = range(values(r), na.rm = TRUE),
  col = pal,
  axis.args = list(
    at = ticks_orig,
    labels = ticks_orig,
    cex.axis = 0.8
  ),
  legend.args = list(text = "", side = 3, line = 1),
  legend.shrink = 1.2
)

dev.off()



png(paste0(dir, "Result/HRU_purity", cdate, ".png"),width = 4500, height = 7200, res = 600)
# Twee panelen naast elkaar; drie onder elkaar
par(mfrow = c(2, 2), mar = c(4, 4, 4, 6))  # extra ruimte rechts voor colorbar
pal <- colorRampPalette(c( "red","orange","yellow","white"))(200)

#---
r <- rast(df_purity[,c('x','y',"Purity_lu4")], type="xyz") 
plot(r, col = pal, legend = FALSE, colNA = "white",main = "Purity_lu4", cex.main = 0.8)
ticks_orig <- c(0, 20, 40, 60, 80, 100)
image.plot(
  legend.only = TRUE,
  zlim = range(0,100),
  col = pal,
  axis.args = list(at = ticks_orig,labels = ticks_orig,cex.axis = 0.8),
  legend.args = list(text = "", side = 3, line = 1),
  legend.shrink = 1.2
)
#---
r <- rast(df_purity[,c('x','y','Purity_grondsoort2')], type="xyz") 
plot(r, col = pal, legend = FALSE, colNA = "white",main = "Purity_grondsoort2", cex.main = 0.8)
ticks_orig <- c(0, 20, 40, 60, 80, 100)
image.plot(
  legend.only = TRUE,
  zlim = range(0,100),
  col = pal,
  axis.args = list(at = ticks_orig,labels = ticks_orig,cex.axis = 0.8),
  legend.args = list(text = "", side = 3, line = 1),
  legend.shrink = 1.2
)
#---
r <- rast(df_purity[,c('x','y','Purity_grondsoort4')], type="xyz")
plot(r, col = pal, legend = FALSE, colNA = "white",main = "Purity_grondsoort4", cex.main = 0.8)
ticks_orig <- c(0, 20, 40, 60, 80, 100)
image.plot(
  legend.only = TRUE,
  zlim = range(0,100),
  col = pal,
  axis.args = list(at = ticks_orig,labels = ticks_orig,cex.axis = 0.8),
  legend.args = list(text = "", side = 3, line = 1),
  legend.shrink = 1.2
)
#---
r <- rast(df_purity[,c('x','y','Purity_pawn21')], type="xyz")
plot(r, col = pal, legend = FALSE, colNA = "white",main = "Purity_pawn21", cex.main = 0.8)
ticks_orig <- c(0, 20, 40, 60, 80, 100)
image.plot(
  legend.only = TRUE,
  zlim = range(0,100),
  col = pal,
  axis.args = list(at = ticks_orig,labels = ticks_orig,cex.axis = 0.8),
  legend.args = list(text = "", side = 3, line = 1),
  legend.shrink = 1.2
)
dev.off()



breaks <- c(-1000, -100, -10, -1, 0, 1, 10, 100, 1000)
labels <- breaks   # labels gelijk aan de waarden


p1 <- ggplot(df_a, aes(x = difGHG)) +
  geom_density(fill = "lightblue", alpha = 0.4, colour = "blue", linewidth = 1.2) +
  scale_x_continuous(trans  = log_mod_trans(),
                     breaks = breaks,
                     labels = labels) +
  labs(
    title = expression("Dichtheidsplot " ~ GHG[svat] ~ "-" ~ GHG[HRU] ~ "(cm)"),
    x = "x (log-modulus schaal)",
    y = "Dichtheid"
  ) +
  theme_minimal() +     # basisgrootte groter
  theme(
    axis.title = element_text(size = 16),
    axis.text  = element_text(size = 14),
    plot.title = element_text(size = 18, face = "bold")
  )

p2 <- ggplot(df_a, aes(x = difNKw)) +
  geom_density(fill = "lightblue", alpha = 0.4, colour = "blue", linewidth = 1.2) +
  scale_x_continuous(trans  = log_mod_trans(),
                     breaks = breaks,
                     labels = labels) +
  labs(
    title = expression("Dichtheidsplot " ~ NKw[svat] ~ "-" ~ NKw[HRU] ~ "(mm/jr)"),
    x = "x (log-modulus schaal)",
    y = "Dichtheid"
  ) +
  theme_minimal() +     # basisgrootte groter
  theme(
    axis.title = element_text(size = 16),
    axis.text  = element_text(size = 14),
    plot.title = element_text(size = 18, face = "bold")
  )

p_combined <- plot_grid(p1, p2, ncol = 2)
ggsave(
  filename = paste0(dir, "Result/densitydif_SVATs_HRUs_",cdate,".png"),
  plot = p_combined,
  width = 12,
  height = 6,
  dpi = 300
)
