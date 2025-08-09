#
# This is the server logic of a Shiny web application. You can run the 
# application by clicking 'Run App' above.
#
# Find out more about building applications with Shiny here:
# 
#    http://shiny.rstudio.com/
#
setwd("~/R/FF2019")
library(shiny)
library(shinythemes)
library(shinyjs)
library(tidyverse)
library(readr)
library(ffanalytics)
library(DT)



#### SHINY TIME ####
shinyServer(function(input, output) {

  DraftPicks <- reactiveValues( read.csv(ActiveDraft))

  #### Draft Board ####
  DraftPicsCold <- observeEvent(input$draftNew,{
    ActiveDraft <<- BeginDraft(T,NULL)
  })

  DraftPicsWarm <- observeEvent(input$draftLoad,{
    ActiveDraft <<- BeginDraft(F,input$draftLoad$datapath)
  })
  
  # DraftPicks <- observeEvent(
  #   c(input$draftNew,input$draftLoad),
  #   {
  #     if(input$draftLoad){
  #       BeginDraft(F,input$draftLoad$datapath)
  #     }
  #     if(input$draftNew){
  #       BeginDraft(T,NULL)
  #     }
  #     else {data.frame()}
  #   }
  #   )
  
  output$value <- renderDataTable({
    req(exists(DraftPicks()))
    DraftPicks()
  })
  
  callModule(TeamBoxServer,"Stephen","Red")
  
  
  #### Position Info ####  
  output$PI_BoxPlot <- renderPlot({
    playerData %>% ggplot(aes(x = "position", y = "fantasyPoints")) + boxplot(x = "position")
  })
  #### Player Info ####

  #### Player Selection ####  
  output$PS_playersAvailable <- renderDataTable({
     datatable(playerData, filter = 'top', options = list(
        pageLength = 25, autoWidth = TRUE)) #,editable=TRUE
   })
   
})
