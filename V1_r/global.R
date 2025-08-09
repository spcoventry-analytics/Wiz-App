setwd("~/R/FF2019")
library(shiny)
library(shinythemes)
library(shinyjs)
library(tidyverse)
library(readr)
library(ffanalytics)
library(DT)
library(shinydashboardPlus)
source("Mod/PickBoxModule.R")

#### Functions ####
BeginDraft <- function(newD,loadD = NULL){
  if(newD){
    FantasyTeams <<- as.factor(c("Wiz", "Jarret", "Tye", "Ace", "Jason", "Chris", "Chad", "Joe", "Andy", "Miguel"))
    Snake <- c(FantasyTeams[1:10],FantasyTeams[10:1])
    DraftPics <- data.frame("Pick" = 1:(10*18), "Team" = Snake) 
    filename <- paste0("Data/ActiveDraft",Sys.Date(),".csv")
    write.csv(DraftPics,file = filename,row.names = F)
  }else{
    filename <- loadD
    DraftPics <- read.csv(filename)
    FantasyTeams <<- unique(DraftPics$Team)
  }
  return(filename)
}

#Stolen Functions 
nameMerge <- function(name){
  newName <- toupper(gsub("Sr|Jr|II|III|[[:punct:]]| ", "", name))
  return(newName)
}


#### Global Variables ####
projections <- read_csv("projections.csv")
projections$teamName <- as.factor(projections$teamName)
projections$position <- as.factor(projections$position)
adpcsv <- "https://fantasyfootballcalculator.com/adp/csv/half-ppr.csv?teams=10&position=all"
adpdata <- read.csv(adpcsv, skip = 7, stringsAsFactors = FALSE)

adpdata$mergename <- nameMerge(adpdata$Name)
projections$mergename <- nameMerge(projections$playerName)

#### Scrape ####
# source(paste(getwd(),"/R Scripts/Functions/Functions.R", sep=""))
# source(paste(getwd(),"/R Scripts/Functions/League Settings.R", sep=""))
# 
# my_scrape <- scrape_data(src = c("CBS", "ESPN", "FantasyData", "FantasyPros",
#                                  "FantasySharks", "FFToday", "FleaFlicker", "Yahoo",
#                                  "FantasyFootballNerd", "NFL", "RTSports"),
#                          pos = c("QB", "RB", "WR", "TE", "DL", "LB", "DB"),
#                          season = 2019, week = 0)
# 
# my_projections <- projections_table(my_scrape)
# my_projections <- my_projections %>% add_ecr() %>% add_risk()
# #my_projections <- my_projections %>% add_adp(sources = c("CBS", "ESPN", "Yahoo","NFL", "FFC")) #%>% add_aav() #Not running in 3.6
# my_projections <- my_projections %>% add_player_info()
# weightedproj <- my_projections %>% filter(avg_type == "weighted")
# weightedproj$mergename <- nameMerge(weightedproj$playerName)
# write.csv(weightedproj,"weightedproj.csv")
# 
# #### Quick Run With weightedproj ####
# #weightedproj <- read_csv("weightedproj.csv") ##if you don't run the scrape raw
# playerData <- left_join(weightedproj, projections, by = "mergename", suffix = c("ffa","pff"))
# playerData <- left_join(playerData,  adpdata)

#### Quick Run ####
playerData <- left_join(projections,  adpdata)
#Define server logic required to draw a histogram


