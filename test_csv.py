import pandas as pd

df = pd.read_csv("국민건강보험공단_건강검진정보_2024.CSV", encoding="cp949")
print(df.columns.tolist())
