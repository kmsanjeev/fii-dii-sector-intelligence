import pandas as pd
def validate_columns(df:pd.DataFrame,required_columns:list[str])->bool:
    return all(col in df.columns for col in required_columns)
def validate_row_count(df:pd.DataFrame,minimum_rows:int)->bool:
    return len(df)>=minimum_rows
def validate_unique(df:pd.DataFrame,column:str)->bool:
    return df[column].nunique()==len(df)
