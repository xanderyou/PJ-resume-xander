from apyori import apriori
import plotly.express as px
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import pandas as pd
import numpy as np
import os

# %%
# load data
alldata = pd.read_csv("sales_data.csv")


# %%
alldata.info()
alldata.head()

# %%
# 計算每一個產品賣出的個數
sells_counts = alldata["產品"].value_counts()
print(sells_counts)

# %%
# 製作利潤表格
# 1.groupby & mean
profit_df = alldata.copy()
profit_df  = profit_df.groupby("產品", as_index=False)[["單價",'成本']].mean()
# add ["利潤"]
profit_df["利潤"] = profit_df["單價"]-profit_df["成本"]

# %%
# top3 series of price_sum 
top3_series = alldata.groupby("系列", as_index=False)["單價"].sum()
top3_series = top3_series.sort_values("單價", ascending=False)
top3_series = top3_series.iloc[0:3, ::]
top3_series

# %% 
# 建立購物籃清單
def market_basket_preprocessing(top_series, alldata):
    record=[]
    for s in top_series['系列']:
        series_data = alldata[alldata["系列"] == s]
        order_number = np.unique(series_data["訂單編號"])
        
        # 新增各系列的資料夾
        try:
            os.mkdir(s + "商品搭配分析") # 創建各系列資料夾
        except:
            print(s + "商品搭配分析的資料夾已經有囉")
            
        for i in order_number:
            cart = series_data[series_data["訂單編號"]==i]["產品"].values
            record.append(cart)
            print( '訂單編號： ', i)
            print(cart)
    return record

record = market_basket_preprocessing(top_series = top3_series, alldata = alldata)
record[0:10]

# %% 
# apriori ananysis
association_rules = apriori(record, min_support=0.001, min_lift=1.000000001, max_length=2) # set ananysis rule
association_results = list(association_rules) # ananysis result lists

# transform to Dataframe
association_results_df = pd.DataFrame(association_results)
association_results[0:10]


# %%
# 建立各商品組合及 support 表
def association_results_preprocessing(results):
    lhs         = [tuple(result[2][0][0])[0] for result in results]
    rhs         = [tuple(result[2][0][1])[0] for result in results]
    supports    = [result[1] for result in results]
    confidences = [result[2][0][2] for result in results]
    lifts       = [result[2][0][3] for result in results]
    results2 = list(zip(lhs, rhs, supports, confidences, lifts))
    resultsinDataFrame = pd.DataFrame(results2, columns = ['p0', 'p1', 'support', 'confidence', 'lift'])
    return resultsinDataFrame


separate = association_results_preprocessing(association_results)
separate


# %%
# 利潤計算
def association_results_profit(separate, profit_df, product):

    # 1. 篩選相同產品(p0)與其他產品搭配購買機率
    data = separate[separate["p0"]==product]

    # 2. 利潤計算
    profit_list = []
    for p in data["p1"]:
        cart_profit = profit_df[profit_df["產品"]==p]["利潤"].values + profit_df[profit_df["產品"]==product]["利潤"].values
        profit_list.append(cart_profit[0])


    # 3. 產出 dataframe 並放入各項資訊
    sortval = pd.DataFrame({
                "當購買時":product,
                "購買產品":data["p1"],
                "機率":data["confidence"],
                "提升度":data["lift"],
                "產品組合利潤":profit_list,
                # "產品組合利潤":data["confidence"]*profit_list 
                }) 
    return sortval

# %%
# 使用For迴圈產出每一種組合的產品組合利潤
# 產出各系列購物籃分析表

all_result = []


for i in np.unique(separate["p0"]):
    
    # 利潤計算
    sortval = association_results_profit(separate=separate, profit_df=profit_df, product=i)
    
    # 請依照機率排序，由高至低
    sortval = sortval.sort_values('機率', ascending=False)

    # 輸出資料
    
    s = "系列" + i.split("-")[0].replace('產品', '')
    sortval.to_csv(os.getcwd() + "/" + s + "商品搭配分析/" + s + "_當購買 " + i + " 時購買以下商品機率.csv", encoding = "utf-8-sig")
    
    all_result.append(sortval)

all_result


# %%

# --模組化-- #
def association_results_profit_all(separate, profit_df):
    
    # 產出各系列購物籃分析表
    all_result = []

    for i in np.unique(separate["p0"]):
        
        # 利潤計算
        sortval = association_results_profit(separate=separate, profit_df=profit_df, product=i)
            
        # 產出 csv
        sortval = sortval.sort_values(by=["機率"], ascending=False)
        s = "系列" + i.split("-")[0].split('產品')[1]
        sortval.to_csv(os.getcwd() + "/" + s + "商品搭配分析/" + s + "_當購買 " + i + " 時購買以下商品機率.csv", encoding = "utf-8-sig")
        all_result.append(sortval)
    return all_result

all_result = association_results_profit_all(separate, profit_df)


# %%
# 利潤資料視覺化

all_result = pd.concat(all_result)
all_result[0:10]


# %%
# 系列1~3
fig = px.sunburst(all_result, path=["當購買時", "購買產品"], values="產品組合利潤",
                  color="產品組合利潤",
                  hover_data=['機率'],
                  color_continuous_scale='RdBu')

fig.update_layout(title = "全系列利潤")
plot(fig,filename="全系列利潤朝陽圖.html", auto_open=False)


# %%

