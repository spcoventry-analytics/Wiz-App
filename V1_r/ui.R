#
# This is the user-interface definition of a Shiny web application. You can
# run the application by clicking 'Run App' above.
#
# Find out more about building applications with Shiny here:
#
#    http://shiny.rstudio.com/
#

library(shiny)
library(shinyjs)
library(shinydashboard)
library(shinydashboardPlus)
library(shinyWidgets)

# Define UI for application that draws a histogram
dashboardPage(
  dashboardHeader(
    title = "The Wizard"
  ),
  dashboardSidebar(
    h1(img(src="FFLogo.jpg", width = 100), align="center"),
    actionButton("draftNew", label = "Begin New Draft"),
    fileInput("draftLoad", "Load Draft",
              multiple = FALSE,
              accept = c("text/csv",
                         "text/comma-separated-values,text/plain",
                         ".csv")),
    sidebarMenu(
      menuItem("Draft Board", tabName = 'DraftBoard', icon = icon("th")),
      menuItem("Position Info", tabName = 'PositionInfo', icon = icon("dashboard")),
      menuItem("Player Info", tabName = 'PlayerInfo', icon = icon("dashboard")),
      menuItem("Player Selection", tabName = 'PlayerSelection', icon = icon("dashboard"))
    )
  ),
  dashboardBody(
    tabItems(
      tabItem('DraftBoard',
              fluidPage(
                #dataTableOutput("value")
                TeamBoxUI(fTeam = "Stephen", fColor = "Blue"),
                TeamBoxUI(fTeam = "Stephen", fColor = "Black")
              )
      ), # tabItem('DraftBoard'
      tabItem('PositionInfo',
              sidebarLayout(
                sidebarPanel(
                  plotOutput("PI_BoxPlot",click = "PI_boxClick")
                ), #sidebarPanel
                # Show a plot of the generated distribution
                mainPanel(

                ) # mainPanel
              ) # SidebarLayout
      ), #tabItem('PositionInfo'
      tabItem('PlayerInfo',
              sidebarLayout(
                sidebarPanel(
                  
                ), #sidebarPanel
                mainPanel(
                  
                ) # mainPanel
              ) # SidebarLayout
      ), # tabItem('PlayerInfo'
      tabItem('PlayerSelection',
              verticalLayout(
                DT::dataTableOutput('PS_playersAvailable')
              ) # verticalLayout
      ) #tabItem('PlayerSelection'
    )#tabItems
  )#dashboardBody
)
