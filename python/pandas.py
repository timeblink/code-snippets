#pandas备忘a

from pandas import Series,DataFrame
import pandas as pd

# csv data format
# project,author,submit
# LINUX/android,xxxx@gmail.com,2013-09-17

df = pd.read_csv('branch-master.csv',index_col=0)
df_filter = df.loc[:,['author']]
df_sort = df_filter.sort(['author'],ascending=False)
df_res = df_filter.groupby(['author'],sort=True).count()
df_res.to_csv('author-count.csv',tupleize_cols=False)

df = pd.read_csv('branch-master.csv',index_col=1)
df_filter = df.loc[:,['project']]
df_sort = df_filter.sort(['project'],ascending=False)
df_res = df_filter.groupby(['project'],sort=True).count()
df_res.to_csv('project-count.csv',tupleize_cols=False)

df = pd.read_csv('branch-master.csv',index_col=0)
df_filter = df.loc[:,['submit']]
df_sort = df_filter.sort(['submit'],ascending=False)
df_res = df_filter.groupby(['submit'],sort=True).count()
df_res.to_csv('date-count.csv',tupleize_cols=False)
