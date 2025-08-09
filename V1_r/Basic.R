library("ffanalytics")

#Install packages that work with main libraries
#install.packages(c("reshape", "MASS", "psych", "Rglpk", "XML"), dependencies=TRUE)

source(paste(getwd(),"/R Scripts/Functions/Functions.R", sep=""))
source(paste(getwd(),"/R Scripts/Functions/League Settings.R", sep=""))

my_scrape <- scrape_data(src = c("CBS", "ESPN", "FantasyData", "FantasyPros",
                                 "FantasySharks", "FFToday", "FleaFlicker", "Yahoo",
                                 "FantasyFootballNerd", "NFL", "RTSports"), #"Walterfootball"
                         pos = c("QB", "RB", "WR", "TE", "DL", "LB", "DB"),
                         season = 2019, week = 0)

my_projections <- projections_table(my_scrape)
my_projections <- my_projections %>% add_ecr() %>% add_risk() 
#my_projections <- my_projections %>% add_adp(sources = c("CBS", "ESPN", "Yahoo","NFL", "FFC")) #%>% add_aav() #Not running in 3.6
my_projections <- my_projections %>% add_player_info()
weightedproj <- my_projections %>% filter(avg_type == "weighted")

####
#Stolen Functions Functions.R
nameMerge <- function(name){
  newName <- toupper(gsub("Sr|Jr|II|III|[[:punct:]]| ", "", name))
  return(newName)
}

projections <- read_csv("projections.csv")
adpcsv <- "https://fantasyfootballcalculator.com/adp/csv/half-ppr.csv?teams=10&position=all"
adpdata <- read.csv(adpcsv, skip = 7, stringsAsFactors = FALSE)

adpdata$mergename <- nameMerge(adpdata$Name)
projections$mergename <- nameMerge(projections$playerName)
weightedproj$mergename <- nameMerge(weightedproj$playerName)

playerData <- left_join(weightedproj, projections, by = "mergename", suffix = c("ffa","pff"))
playerData <- left_join(playerData,  adpdata)
