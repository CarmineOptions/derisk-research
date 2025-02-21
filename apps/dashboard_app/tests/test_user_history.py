import pandas as pd
from main_chart_figure import get_user_history 

df = pd.read_csv("data.csv")  


user_id = "x04aa93bc6f2d76e90474cc82914c219bcdcfb9151122..."  
user_history = get_user_history(user_id, df)


print(user_history)
