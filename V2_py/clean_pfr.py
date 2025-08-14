import pandas as pd

def clean_pfr_data(file_path):
    df = pd.read_csv(file_path, header=None)
    # Perform cleaning operations on the DataFrame
    column_names_df = df.head(2)  # Display the first rows for header

    column_names = []
    for col in column_names_df.columns:
        column_values = column_names_df[col].astype(str)
        column_name = ' '.join(column_values)
        column_name = column_name.replace('nan ', ' ')
        column_names.append(column_name)
        
    df = df[2:]  # Remove the first two rows
    df.columns = column_names  # Set the column names
    df.columns = df.columns.str.strip()  # Remove leading/trailing whitespace from column names
    try:
        if len(df['Tm']) > 1:
            final_df = df
    except KeyError as e:
        print(f"KeyError: {e}")

    try:
        vc = df['Player'].value_counts()
        multi_team_players = vc[vc > 1].index
        multi_team_players_df = df[df['Player'].isin(multi_team_players)]
        multi_team_players_df = multi_team_players_df[multi_team_players_df['Team'].str.contains("TM")]
        single_team_players_df = df[~df['Player'].isin(multi_team_players)]
        final_dfs = [multi_team_players_df, single_team_players_df]
        final_df = pd.concat(final_dfs)
    except KeyError as e:
        print(f"KeyError: {e}")

    final_df.to_csv(file_path, index=False)
    return final_df



# clean_pfr_data("C:/Users/spcov/Data/Wiz-App/V2_py/Stats/Past_Offense/2024_Yards.csv") # Run Successfully
# clean_pfr_data("C:/Users/spcov/Data/Wiz-App/V2_py/Stats/Past_Offense/2024_Passing_Adv.csv") # Run Successfully
# clean_pfr_data("C:/Users/spcov/Data/Wiz-App/V2_py/Stats/Past_Offense/2024_Rec_Adv.csv") # Run Successfully
# clean_pfr_data("C:/Users/spcov/Data/Wiz-App/V2_py/Stats/Past_Offense/2024_Rushing_Adv.csv") # Run Successfully

# Not Player
# clean_pfr_data("C:/Users/spcov/Data/Wiz-App/V2_py/Stats/Past_Defense/2024_Team.csv") # Run Successfully
# clean_pfr_data("C:/Users/spcov/Data/Wiz-App/V2_py/Stats/Past_Defense/2024_Pass_Against.csv") # Run Successfully
# clean_pfr_data("C:/Users/spcov/Data/Wiz-App/V2_py/Stats/Past_Defense/2024_Rec_Against.csv") # Run Successfully
# clean_pfr_data("C:/Users/spcov/Data/Wiz-App/V2_py/Stats/Past_Defense/2024_Run_Against.csv") # Run Successfully